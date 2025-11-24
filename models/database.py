import psycopg2
import hashlib
from config import config

class Db:
    @staticmethod
    def get_connection():
        return psycopg2.connect(config.DATABASE_URL)

    @staticmethod
    def create_accounts_table():
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    session_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL DEFAULT 'default',
                    FOREIGN KEY (username) REFERENCES users (username)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS points (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    point INTEGER NOT NULL DEFAULT 0,
                    total_point INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (username) REFERENCES users (username)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solutions (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    isac BOOLEAN NOT NULL DEFAULT FALSE,
                    ispublic BOOLEAN NOT NULL DEFAULT FALSE,
                    summary TEXT,
                    code TEXT,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            print("Tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def add_user(username, email, password):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            hashed_password = Db.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s)
            ''', (username, email, hashed_password))
            
            cursor.execute('''
                INSERT INTO roles (username, role)
                VALUES (%s, %s)
            ''', (username, 'default'))
            
            cursor.execute('''
                INSERT INTO points (username, point, total_point)
                VALUES (%s, %s, %s)
            ''', (username, 0, 0))
            
            conn.commit()
            print(f"User {username} added successfully")
            return True
        except psycopg2.IntegrityError:
            print("Username or email already exists")
            return False
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def update_user_password(username, new_password):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            hashed_password = Db.hash_password(new_password)
            cursor.execute('''
                UPDATE users 
                SET password = %s
                WHERE username = %s
            ''', (hashed_password, username))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_user_role(username):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT role FROM roles WHERE username = %s''', (username,))
            result = cursor.fetchone()
            return result[0] if result else 'default'
        except Exception as e:
            print(e)
            return 'default'
        finally:
            conn.close()

    @staticmethod
    def set_user_role(username, role):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO roles (username, role)
                VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE SET role = %s
            ''', (username, role, role))
            conn.commit()
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_all_users():
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT u.username, u.email, r.role, u.created_at 
                FROM users u 
                LEFT JOIN roles r ON u.username = r.username
            ''')
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return []
        finally:
            conn.close()

    @staticmethod
    def get_all_solutions(offset=0, limit=10, search=None):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            query = '''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
            '''
            params = []
            
            if search:
                query += ' WHERE (s.url LIKE %s OR s.title LIKE %s)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += ' ORDER BY s.created_at DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return []
        finally:
            conn.close()

    @staticmethod
    def count_all_solutions(search=None):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            query = 'SELECT COUNT(*) FROM solutions'
            params = []
            
            if search:
                query += ' WHERE (url LIKE %s OR title LIKE %s)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except Exception as e:
            print(e)
            return 0
        finally:
            conn.close()

    @staticmethod
    def admin_update_solution(solution_id, url, title, isac, ispublic, summary, code):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE solutions 
                SET url = %s, title = %s, isac = %s, ispublic = %s, summary = %s, code = %s
                WHERE id = %s
            ''', (url, title, isac, ispublic, summary, code, solution_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def admin_delete_solution(solution_id):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM solutions WHERE id = %s', (solution_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def verify_user(username, plain_password):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT password FROM users WHERE username = %s''', (username,))
            result = cursor.fetchone()
            if result:
                stored_hash = result[0]
                input_hash = Db.hash_password(plain_password)
                if stored_hash == input_hash:
                    print(f"User {username} verified successfully")
                    return True
                else:
                    print(f"User {username} wrong password!")
                    return False
            else:
                print(f"User {username} not found")
                return False
        except Exception as e:
            print(e)
        finally:
            conn.close()
            
    @staticmethod
    def get_user_by_username(username):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, username, email, created_at 
                FROM users WHERE username = %s
            ''', (username,))
            user = cursor.fetchone()
            return user
        except Exception as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def username_exists(username):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT id FROM users WHERE username = %s''', (username,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def email_exists(email):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT id FROM users WHERE email = %s''', (email,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def add_solution(url, title, isac, ispublic, summary, code, user_id):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO solutions (url, title, isac, ispublic, summary, code, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (url, title, isac, ispublic, summary, code, user_id))
            conn.commit()
            print(f"Solution added successfully by user {user_id}")
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_user_id_by_username(username):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT id FROM users WHERE username = %s''', (username,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def get_my_solutions(user_id, offset=0, limit=10, search=None):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            query = '''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.user_id = %s
            '''
            params = [user_id]
            
            if search:
                query += ' AND (s.url LIKE %s OR s.title LIKE %s)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += ' ORDER BY s.created_at DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return []
        finally:
            conn.close()

    @staticmethod
    def get_public_solutions(offset=0, limit=10, search=None):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            query = '''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.ispublic = TRUE
            '''
            params = []
            
            if search:
                query += ' AND (s.url LIKE %s OR s.title LIKE %s)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += ' ORDER BY s.created_at DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return []
        finally:
            conn.close()

    @staticmethod
    def count_my_solutions(user_id, search=None):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            query = 'SELECT COUNT(*) FROM solutions WHERE user_id = %s'
            params = [user_id]
            
            if search:
                query += ' AND (url LIKE %s OR title LIKE %s)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except Exception as e:
            print(e)
            return 0
        finally:
            conn.close()

    @staticmethod
    def count_public_solutions(search=None):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            query = 'SELECT COUNT(*) FROM solutions WHERE ispublic = TRUE'
            params = []
            
            if search:
                query += ' AND (url LIKE %s OR title LIKE %s)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except Exception as e:
            print(e)
            return 0
        finally:
            conn.close()

    @staticmethod
    def get_solution_by_id(solution_id):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.id = %s
            ''', (solution_id,))
            return cursor.fetchone()
        except Exception as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def update_solution(solution_id, url, title, isac, ispublic, summary, code, user_id):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE solutions 
                SET url = %s, title = %s, isac = %s, ispublic = %s, summary = %s, code = %s
                WHERE id = %s AND user_id = %s
            ''', (url, title, isac, ispublic, summary, code, solution_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_solution(solution_id, user_id):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM solutions 
                WHERE id = %s AND user_id = %s
            ''', (solution_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def add_points(username, points_to_add):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO points (username, point, total_point)
                VALUES (%s, 
                    COALESCE((SELECT point FROM points WHERE username = %s), 0) + %s,
                    COALESCE((SELECT total_point FROM points WHERE username = %s), 0) + %s
                )
                ON CONFLICT (username) DO UPDATE SET
                    point = EXCLUDED.point,
                    total_point = EXCLUDED.total_point
            ''', (username, username, points_to_add, username, points_to_add))
            conn.commit()
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_user_points(username):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT point, total_point FROM points WHERE username = %s''', (username,))
            result = cursor.fetchone()
            return result if result else (0, 0)
        except Exception as e:
            print(e)
            return (0, 0)
        finally:
            conn.close()

    @staticmethod
    def get_all_users_points():
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT u.username, COALESCE(p.total_point, 0)
                FROM users u 
                LEFT JOIN points p ON u.username = p.username
                ORDER BY COALESCE(p.total_point, 0) DESC
            ''')
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return []
        finally:
            conn.close()
    @staticmethod
    def update_session_token(username, session_token):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET session_token = %s
                WHERE username = %s
            ''', (session_token, username))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating session token: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_session_token(username):
        conn = Db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT session_token FROM users WHERE username = %s
            ''', (username,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting session token: {e}")
            return None
        finally:
            conn.close()