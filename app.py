import datetime
from flask import Flask, request, session, jsonify, render_template, redirect, flash, Response
from functools import wraps
from models.database import Db
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string
from config import config
import hashlib
import json
import threading

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


sse_clients = []

def sse_event(data, event_type=None):
    message = f"data: {json.dumps(data)}\n\n"
    if event_type:
        message = f"event: {event_type}\n{message}"
    
    disconnected_clients = []
    for i, client in enumerate(sse_clients):
        try:
            client_queue = client.get('queue')
            if client_queue:
                client_queue.put(message)
        except:
            disconnected_clients.append(i)
    
    for i in reversed(disconnected_clients):
        sse_clients.pop(i)

@app.route('/sse')
def sse_stream():
    def event_stream():
        import queue
        client_queue = queue.Queue()
        sse_clients.append({'queue': client_queue})
        
        try:
            yield "data: {\"message\": \"connected\"}\n\n"
            
            while True:
                message = client_queue.get()
                yield message
        except GeneratorExit:
            sse_clients.remove({'queue': client_queue})
    
    return Response(event_stream(), mimetype="text/event-stream")

user_requests = {}
user_requests_lock = threading.Lock()

def generate_session_token(username):
    timestamp = str(datetime.datetime.now().timestamp())
    raw_token = f"{username}{timestamp}{secrets.token_hex(16)}"
    return hashlib.sha256(raw_token.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')

        username = session.get('user_id')
        if not username or not Db.username_exists(username):
            session.clear()
            flash('Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.')
            return redirect('/login')

        return f(*args, **kwargs)
    return decorated_function

def redirect_if_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_in'):
            return redirect('/home')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        
        username = session.get('user_id')
        if not username or not Db.username_exists(username):
            session.clear()
            flash('Phiên đăng nhập không hợp lệ.')
            return redirect('/login')

        role = Db.get_user_role(username)
        if role != 'admin':
            flash('Bạn không có quyền truy cập trang này!')
            return redirect('/home')
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_role():
    if not session.get('logged_in'):
        return 'guest'
    username = session.get('user_id')
    return Db.get_user_role(username)

def is_admin():
    return get_current_user_role() == 'admin'

def check_spam(user_id, action):
    current_time = time.time()
    
    with user_requests_lock:
        if user_id not in user_requests:
            user_requests[user_id] = {}
        
        if action not in user_requests[user_id]:
            user_requests[user_id][action] = []
        
        user_requests[user_id][action] = [t for t in user_requests[user_id][action] if current_time - t < 60]
        
        if len(user_requests[user_id][action]) >= 10:
            return True
        
        user_requests[user_id][action].append(current_time)
        return False

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))

def send_email(to_email, subject, body):
    if not config.EMAIL_ENABLED:
        return False
        
    try:
        msg = MIMEMultipart() 
        msg['From'] = config.EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(config.EMAIL_SERVER, config.EMAIL_PORT)
        server.starttls()
        server.login(config.EMAIL_USERNAME, config.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False

@app.context_processor
def utility_processor():
    return dict(
        get_current_user_role=get_current_user_role,
        is_admin=is_admin,
        config=config
    )

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect('/home')
    return render_template('index.html')

@app.route('/login')
@redirect_if_logged_in 
def login_page(): 
    return render_template('login.html')

@app.route('/register')
@redirect_if_logged_in
def register_page():
    return render_template('register.html')

@app.route('/forgot_password')
@redirect_if_logged_in
def forgot_password_page():
    if not config.EMAIL_ENABLED:
        flash('Tính năng khôi phục mật khẩu tạm thời không khả dụng.')
        return redirect('/login')
    return render_template('forgot_password.html')

@app.route('/api/login', methods=['POST'])
def login_api():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Vui lòng nhập đầy đủ thông tin!')
        return redirect('/login')
    
    if Db.verify_user(username, password):
        session_token = generate_session_token(username)
        Db.update_session_token(username, session_token)
        
        session['user_id'] = username 
        session['logged_in'] = True
        session['session_token'] = session_token
        return redirect('/home')
    else:
        flash('Sai tên đăng nhập hoặc mật khẩu!')
        return redirect('/login')

@app.route('/api/logout_all_devices', methods=['POST'])
@login_required
def logout_all_devices_api():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'})
    
    username = session['user_id']
    
    new_token = generate_session_token(username)
    
    if Db.update_session_token(username, new_token):
        session.clear()
        return jsonify({
            'success': True, 
            'message': 'Đã đăng xuất khỏi tất cả thiết bị. Vui lòng đăng nhập lại.'
        })
    else:
        return jsonify({
            'success': False, 
            'message': 'Có lỗi xảy ra. Vui lòng thử lại.'
        })

@app.route('/api/register', methods=['POST'])
def register_api():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not username or not email or not password:
        flash('Vui lòng nhập đầy đủ thông tin!')
        return redirect('/register')
    
    if Db.username_exists(username):
        flash('Tên đăng nhập đã tồn tại!')
        return redirect('/register')
    
    if Db.email_exists(email):
        flash('Email đã được sử dụng!')
        return redirect('/register')
    
    if Db.add_user(username, email, password):
        flash('Đăng ký thành công! Vui lòng đăng nhập.')
        return redirect('/login')
    else:
        flash('Đăng ký thất bại! Vui lòng thử lại.')
        return redirect('/register')

@app.route('/api/forgot_password', methods=['POST'])
def forgot_password_api():
    if not config.EMAIL_ENABLED:
        flash('Tính năng khôi phục mật khẩu tạm thời không khả dụng.')
        return redirect('/login')
    
    username = request.form.get('username')
    email = request.form.get('email')
    
    if not username or not email:
        flash('Vui lòng nhập đầy đủ username và email!')
        return redirect('/forgot_password')
    
    user = Db.get_user_by_username(username)
    if not user or user[2] != email:
        flash('success', 'Nếu username và email khớp, mật khẩu mới sẽ được gửi đến email của bạn.')
        return redirect('/login')
    
    new_password = generate_random_password()
    
    if Db.update_user_password(username, new_password):
        subject = "AC Bank - Mật khẩu mới của bạn"
        body = f"""
        <html>
            <body>
                <h2>AC Bank - Khôi phục mật khẩu</h2>
                <p>Xin chào <strong>{username}</strong>,</p>
                <p>Mật khẩu mới của bạn là: <strong>{new_password}</strong></p>
                <p>Vui lòng đăng nhập và đổi mật khẩu ngay sau khi đăng nhập.</p>
                <br>
                <p>Trân trọng,<br>Đội ngũ AC Bank</p>
            </body>
        </html>
        """
        
        if send_email(email, subject, body):
            flash('success', 'Mật khẩu mới đã được gửi đến email của bạn.')
        else:
            flash('error', 'Có lỗi xảy ra khi gửi email. Vui lòng thử lại sau.')
    else:
        flash('error', 'Có lỗi xảy ra khi đặt lại mật khẩu. Vui lòng thử lại sau.')
    
    return redirect('/login')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect('/')

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/create_solution')
@login_required
def create_solution_page():
    return render_template('create_solution.html')

@app.route('/edit_solution/<int:solution_id>')
@login_required
def edit_solution_page(solution_id):
    solution = Db.get_solution_by_id(solution_id)
    if not solution:
        flash('Solution không tồn tại!')
        return redirect('/home')
    
    user_id = Db.get_user_id_by_username(session['user_id'])
    user_role = get_current_user_role()
    
    if solution[7] != user_id and user_role != 'admin':
        flash('Bạn không có quyền chỉnh sửa solution này!')
        return redirect('/home')
    
    solution_dict = {
        'id': solution[0],
        'url': solution[1],
        'title': solution[2],
        'isac': bool(solution[3]),
        'ispublic': bool(solution[4]),
        'summary': solution[5],
        'code': solution[6],
        'username': solution[9]
    }
    
    return render_template('edit_solution.html', solution=solution_dict, solution_id=solution_id)

@app.route('/view_solution/<int:solution_id>')
@login_required
def view_solution_page(solution_id):
    solution = Db.get_solution_by_id(solution_id)
    if not solution:
        flash('Solution không tồn tại!')
        return redirect('/home')
    
    solution_dict = {
        'id': solution[0],
        'url': solution[1],
        'title': solution[2],
        'isac': bool(solution[3]),
        'ispublic': bool(solution[4]),
        'summary': solution[5],
        'code': solution[6],
        'username': solution[9],
        'created_at': solution[8]
    }
    
    return render_template('view_solution.html', solution=solution_dict)

@app.route('/api/create_solution', methods=['POST'])
@login_required
def create_solution_api():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!')
        return redirect('/login')
    
    user_id = session['user_id']
    if check_spam(user_id, 'create_solution'):
        flash('Bạn đã tạo quá nhiều solution trong thời gian ngắn! Vui lòng chờ 1 phút.')
        return redirect('/create_solution')
    
    url = request.form.get('url')
    title = request.form.get('title')
    isac = True if request.form.get('isac') == '1' else False
    ispublic = True if request.form.get('ispublic') == '1' else False
    summary = request.form.get('summary')
    code = request.form.get('code')
    
    if not url or not title:
        flash('Vui lòng nhập URL và Tiêu đề!')
        return redirect('/create_solution')
    
    if not code or not code.strip():
        flash('Vui lòng nhập phần giải!')
        return redirect('/create_solution')
    
    user_id_db = Db.get_user_id_by_username(session['user_id'])
    
    if not user_id_db:
        flash('Lỗi xác thực người dùng!')
        return redirect('/create_solution')
    
    if Db.add_solution(url, title, isac, ispublic, summary, code, user_id_db):
        Db.add_points(session['user_id'], 10)
        sse_event({'message': 'New solution added'}, 'new_solution')
        flash('Tạo solution thành công! +10 điểm')
        return redirect('/home')
    else:
        flash('Tạo solution thất bại! Vui lòng thử lại.')
        return redirect('/create_solution')

@app.route('/api/update_solution/<int:solution_id>', methods=['POST'])
@login_required
def update_solution_api(solution_id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!')
        return redirect('/login')
    
    user_id = session['user_id']
    if check_spam(user_id, 'update_solution'):
        flash('Bạn đã cập nhật quá nhiều trong thời gian ngắn! Vui lòng chờ 1 phút.')
        return redirect(f'/edit_solution/{solution_id}')
    
    url = request.form.get('url')
    title = request.form.get('title')
    isac = True if request.form.get('isac') == '1' else False
    ispublic = True if request.form.get('ispublic') == '1' else False
    summary = request.form.get('summary')
    code = request.form.get('code')
    
    if not url or not title:
        flash('Vui lòng nhập URL và Tiêu đề!')
        return redirect(f'/edit_solution/{solution_id}')
    
    if not code or not code.strip():
        flash('Vui lòng nhập phần giải!')
        return redirect(f'/edit_solution/{solution_id}')
    
    user_id_db = Db.get_user_id_by_username(session['user_id'])
    user_role = get_current_user_role()
    
    if not user_id_db:
        flash('Lỗi xác thực người dùng!')
        return redirect(f'/edit_solution/{solution_id}')
    
    if user_role == 'admin':
        success = Db.admin_update_solution(solution_id, url, title, isac, ispublic, summary, code)
    else:
        success = Db.update_solution(solution_id, url, title, isac, ispublic, summary, code, user_id_db)
    
    if success:
        sse_event({'message': 'Solution updated'}, 'update_solution')
        flash('Cập nhật solution thành công!')
        return redirect('/home')
    else:
        flash('Cập nhật solution thất bại! Vui lòng thử lại.')
        return redirect(f'/edit_solution/{solution_id}')

@app.route('/api/delete_solution/<int:solution_id>', methods=['DELETE'])
@login_required
def delete_solution_api(solution_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'})
    
    user_id = session['user_id']
    if check_spam(user_id, 'delete_solution'):
        return jsonify({'success': False, 'message': 'Bạn đã xoá quá nhiều trong thời gian ngắn!'})
    
    user_id_db = Db.get_user_id_by_username(session['user_id'])
    user_role = get_current_user_role()
    
    if not user_id_db:
        return jsonify({'success': False, 'message': 'Lỗi xác thực người dùng!'})
    
    solution = Db.get_solution_by_id(solution_id)
    if not solution:
        return jsonify({'success': False, 'message': 'Solution không tồn tại!'})
    
    if user_role == 'admin':
        success = Db.admin_delete_solution(solution_id)
    else:
        if solution[7] != user_id_db:
            return jsonify({'success': False, 'message': 'Bạn không có quyền xoá solution này!'})
        success = Db.delete_solution(solution_id, user_id_db)
    
    if success:
        sse_event({'message': 'Solution deleted'}, 'delete_solution')
        return jsonify({'success': True, 'message': 'Xoá solution thành công!'})
    else:
        return jsonify({'success': False, 'message': 'Xoá solution thất bại!'})

@app.route('/api/my_solutions')
@login_required
def api_my_solutions():
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '')
    limit = 10
    offset = (page - 1) * limit
    
    user_id = Db.get_user_id_by_username(session['user_id'])
    solutions = Db.get_my_solutions(user_id, offset, limit, search)
    
    solution_dicts = []
    for solution in solutions:
        solution_dicts.append({
            'id': solution[0],
            'url': solution[1],
            'title': solution[2],
            'isac': bool(solution[3]),
            'ispublic': bool(solution[4]),
            'summary': solution[5],
            'code': solution[6],
            'user_id': solution[7],
            'created_at': solution[8],
            'username': solution[9]
        })
    
    return jsonify({
        'solutions': solution_dicts,
        'page': page
    })

@app.route('/api/public_solutions')
@login_required
def api_public_solutions():
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '')
    limit = 10
    offset = (page - 1) * limit
    
    solutions = Db.get_public_solutions(offset, limit, search)
    
    solution_dicts = []
    for solution in solutions:
        solution_dicts.append({
            'id': solution[0],
            'url': solution[1],
            'title': solution[2],
            'isac': bool(solution[3]),
            'ispublic': bool(solution[4]),
            'summary': solution[5],
            'code': solution[6],
            'user_id': solution[7],
            'created_at': solution[8],
            'username': solution[9]
        })
    
    return jsonify({
        'solutions': solution_dicts,
        'page': page
    })

@app.route('/api/all_users')
@login_required
@admin_required
def api_all_users():
    try:
        users = Db.get_all_users()
        result = [
            {'username': u[0], 'email': u[1], 'created_at': u[2].strftime('%Y-%m-%d %H:%M')}
            for u in users
        ]
        return jsonify({'users': result})
    except Exception as e:
        print(e)
        return jsonify({'users': []})

@app.route('/api/all_solutions')
@login_required
@admin_required
def api_all_solutions():
    try:
        sols = Db.get_all_solutions_admin()
        result = [
            {
                'id': s[0],
                'title': s[1],
                'url': s[2],
                'username': s[3],
                'isac': bool(s[4]),
                'ispublic': bool(s[5]),
                'created_at': s[6].strftime('%Y-%m-%d %H:%M')
            }
            for s in sols
        ]
        return jsonify({'solutions': result})
    except Exception as e:
        print(e)
        return jsonify({'solutions': []})

@app.route('/api/all_points')
@login_required
@admin_required
def api_all_points():
    try:
        rows = Db.get_all_points_admin()
        result = [
            {'username': r[0], 'point': r[1], 'total_point': r[2]}
            for r in rows
        ]
        return jsonify({'points': result})
    except Exception as e:
        print(e)
        return jsonify({'points': []})

@app.route('/api/all_roles')
@login_required
@admin_required
def api_all_roles():
    try:
        rows = Db.get_all_roles_admin()
        result = [
            {'username': r[0], 'role': r[1]}
            for r in rows
        ]
        return jsonify({'roles': result})
    except Exception as e:
        print(e)
        return jsonify({'roles': []})

@app.route('/api/set_role/<username>', methods=['POST'])
@login_required
@admin_required
def api_set_role(username):
    new_role = request.json.get('role')
    if new_role not in ['default', 'admin']:
        return jsonify({'success': False, 'message': 'Role không hợp lệ'})

    conn = Db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO roles (username, role) VALUES (%s, %s)
            ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role
        ''', (username, new_role))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/delete_user/<username>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_user(username):
    if username == session['user_id']:
        return jsonify({'success': False, 'message': 'Không thể tự xóa chính mình!'})

    conn = Db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM solutions WHERE user_id = (SELECT id FROM users WHERE username = %s)', (username,))
        cursor.execute('DELETE FROM points WHERE username = %s', (username,))
        cursor.execute('DELETE FROM roles WHERE username = %s', (username,))
        cursor.execute('DELETE FROM users WHERE username = %s', (username,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        print(e)
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/user_points')
@login_required
def api_user_points():
    username = session.get('user_id')
    current_point, total_point = Db.get_user_points(username)
    return jsonify({
        'current_point': current_point,
        'total_point': total_point
    })

@app.route('/rank')
@login_required
def rank_page():
    return render_template('rank.html')

@app.route('/api/rankings')
@login_required
def api_rankings():
    users_points = Db.get_all_users_points()
    
    rankings = []
    for user in users_points:
        rankings.append({
            'username': user[0],
            'total_point': user[1]
        })
    
    return jsonify({
        'rankings': rankings
    })

@app.route('/change_password')
@login_required
def change_password_page():
    return render_template('change_password.html')

@app.route('/api/change_password', methods=['POST'])
@login_required
def change_password_api():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập!')
        return redirect('/login')
    
    username = session['user_id']
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('error', 'Vui lòng nhập đầy đủ thông tin!')
        return redirect('/change_password')
    
    if len(new_password) < 6:
        flash('error', 'Mật khẩu mới phải có ít nhất 6 ký tự!')
        return redirect('/change_password')
    
    if new_password != confirm_password:
        flash('error', 'Mật khẩu xác nhận không khớp!')
        return redirect('/change_password')
    
    if not Db.verify_user(username, current_password):
        flash('error', 'Mật khẩu hiện tại không đúng!')
        return redirect('/change_password')
    
    if Db.update_user_password(username, new_password):
        flash('success', 'Đổi mật khẩu thành công!')
        return redirect('/home')
    else:
        flash('error', 'Đổi mật khẩu thất bại! Vui lòng thử lại.')
        return redirect('/change_password')

@app.route('/admin')
@login_required
@admin_required
def admin_page():
    return render_template('admin.html')

@app.route('/api/admin_set_points', methods=['POST'])
@login_required
@admin_required
def api_admin_set_points():
    data = request.get_json()
    username = data.get('username')
    point = data.get('point', 0)
    total_point = data.get('total_point', 0)

    if point < 0 or total_point < 0:
        return jsonify({'success': False, 'message': 'Điểm không được âm'})

    if point > total_point:
        return jsonify({'success': False, 'message': 'Point không được lớn hơn total_point'})

    conn = Db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO points (username, point, total_point)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                point = EXCLUDED.point,
                total_point = EXCLUDED.total_point
        ''', (username, point, total_point))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        print(f"Error setting points: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.before_request
def before_request():
    if request.path.startswith(('/login', '/register', '/forgot_password', '/static', '/api/forgot_password', '/api/login', '/api/register', '/sse')):
        return

    if session.get('logged_in'):
        username = session.get('user_id')
        if username and not Db.username_exists(username):
            session.clear()
            flash('Phiên đăng nhập đã hết hạn hoặc tài khoản không tồn tại. Vui lòng đăng nhập lại.')
            return redirect('/login')
        
        current_token = session.get('session_token')
        if current_token:
            try:
                valid_token = Db.get_session_token(username)
                if valid_token is not None and current_token != valid_token:
                    session.clear()
                    flash('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
                    return redirect('/login')
            except Exception as e:
                print(f"Warning: Session token check failed: {e}")

@app.before_first_request
def create_tables():
    Db.create_accounts_table()

if __name__ == '__main__':
    Db.create_accounts_table()
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
