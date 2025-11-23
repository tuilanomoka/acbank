from flask import Flask, request, session, jsonify, render_template, redirect, url_for, flash
from functools import wraps
from models.database import Db
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import math
import time
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
socketio = SocketIO(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

user_requests = {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not os.path.exists('database.db'):
            session.clear()
            flash('Hệ thống đang khởi tạo lại. Vui lòng đăng nhập lại.')
            return redirect('/login')

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
        if not os.path.exists('database.db'):
            session.clear()
            flash('Hệ thống đang khởi tạo lại. Vui lòng đăng nhập lại.')
            return redirect('/login')
            
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
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    if action not in user_requests[user_id]:
        user_requests[user_id][action] = []
    
    user_requests[user_id][action] = [t for t in user_requests[user_id][action] if current_time - t < 60]
    
    if len(user_requests[user_id][action]) >= 10:
        return True
    
    user_requests[user_id][action].append(current_time)
    return False

@app.context_processor
def utility_processor():
    return dict(
        get_current_user_role=get_current_user_role,
        is_admin=is_admin
    )

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect('/home')
    return render_template('index.html')

@app.route('/login')
@redirect_if_logged_in 
@limiter.limit("10 per minute")
def login_page(): 
    return render_template('login.html')

@app.route('/register')
@redirect_if_logged_in
@limiter.limit("5 per minute")
def register_page():
    return render_template('register.html')

@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login_api():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Vui lòng nhập đầy đủ thông tin!')
        return redirect('/login')
    
    if Db.verify_user(username, password):
        session['user_id'] = username 
        session['logged_in'] = True
        return redirect('/home')
    else:
        flash('Sai tên đăng nhập hoặc mật khẩu!')
        return redirect('/login')

@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
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

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect('/')

@app.route('/home')
@login_required
@limiter.limit("30 per minute")
def home():
    return render_template('home.html')

@app.route('/create_solution')
@login_required
@limiter.limit("20 per minute")
def create_solution_page():
    return render_template('create_solution.html')

@app.route('/edit_solution/<int:solution_id>')
@login_required
@limiter.limit("20 per minute")
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
@limiter.limit("30 per minute")
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
@limiter.limit("10 per minute")
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
        socketio.emit('new_solution', {'message': 'New solution added'})
        flash('Tạo solution thành công! +10 điểm')
        return redirect('/home')
    else:
        flash('Tạo solution thất bại! Vui lòng thử lại.')
        return redirect('/create_solution')

@app.route('/api/update_solution/<int:solution_id>', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
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
        socketio.emit('update_solution', {'message': 'Solution updated'})
        flash('Cập nhật solution thành công!')
        return redirect('/home')
    else:
        flash('Cập nhật solution thất bại! Vui lòng thử lại.')
        return redirect(f'/edit_solution/{solution_id}')

@app.route('/api/delete_solution/<int:solution_id>', methods=['DELETE'])
@login_required
@limiter.limit("10 per minute")
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
        socketio.emit('delete_solution', {'message': 'Solution deleted'})
        return jsonify({'success': True, 'message': 'Xoá solution thành công!'})
    else:
        return jsonify({'success': False, 'message': 'Xoá solution thất bại!'})

@app.route('/api/my_solutions')
@login_required
@limiter.limit("30 per minute")
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
@limiter.limit("30 per minute")
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

@app.route('/api/all_solutions')
@login_required
@admin_required
@limiter.limit("30 per minute")
def api_all_solutions():
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '')
    limit = 10
    offset = (page - 1) * limit
    
    solutions = Db.get_all_solutions(offset, limit, search)
    
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

@app.errorhandler(429)
def ratelimit_handler(e):
    flash('Quá nhiều request! Vui lòng thử lại sau.')
    return redirect(request.referrer or '/')

@app.route('/api/user_points')
@login_required
@limiter.limit("30 per minute")
def api_user_points():
    username = session.get('user_id')
    current_point, total_point = Db.get_user_points(username)
    return jsonify({
        'current_point': current_point,
        'total_point': total_point
    })

@app.before_request
def before_request():
    if request.path.startswith(('/login', '/register', '/static')):
        return

    if session.get('logged_in'):
        username = session.get('user_id')
        if username and not Db.username_exists(username):
            session.clear()
            flash('Phiên đăng nhập đã hết hạn hoặc tài khoản không tồn tại. Vui lòng đăng nhập lại.')
            return redirect('/login')

if __name__ == '__main__':
    Db.create_accounts_table()
    socketio.run(app, debug=True)