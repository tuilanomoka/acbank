import psycopg2
import hashlib
from config import config
import threading
import queue
import time

class Db:
    _connection_pool = None
    _pool_lock = threading.Lock()
    _max_connections = 20
    _pool_timeout = 30

    @classmethod
    def _initialize_pool(cls):
        if cls._connection_pool is None:
            with cls._pool_lock:
                if cls._connection_pool is None:
                    try:
                        cls._connection_pool = queue.Queue(maxsize=cls._max_connections)
                        
                        for _ in range(5):
                            conn = psycopg2.connect(config.DATABASE_URL)
                            cls._connection_pool.put(conn)
                        
                        print("Database connection pool initialized with 5 connections")
                    except Exception as e:
                        print(f"Error initializing connection pool: {e}")
                        cls._connection_pool = None

    @staticmethod
    def get_connection():
        if Db._connection_pool is None:
            Db._initialize_pool()
        
        if Db._connection_pool is None:
            return psycopg2.connect(config.DATABASE_URL)
        
        try:
            conn = Db._connection_pool.get(timeout=Db._pool_timeout)
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
                return conn
            except:
                conn.close()
                new_conn = psycopg2.connect(config.DATABASE_URL)
                return new_conn
                
        except queue.Empty:
            print("Connection pool empty, creating new connection")
            return psycopg2.connect(config.DATABASE_URL)
        except Exception as e:
            print(f"Error getting connection from pool: {e}")
            return psycopg2.connect(config.DATABASE_URL)

    @staticmethod
    def return_connection(conn):
        if Db._connection_pool and conn:
            try:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute('SELECT 1')
                    Db._connection_pool.put(conn, timeout=5)
                except:
                    conn.close()
            except queue.Full:
                conn.close()
            except Exception as e:
                print(f"Error returning connection to pool: {e}")
                conn.close()

    @staticmethod
    def close_all_connections():
        if Db._connection_pool:
            while not Db._connection_pool.empty():
                try:
                    conn = Db._connection_pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
            print("All database connections closed")

    @staticmethod
    def create_accounts_table():
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
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
            if conn:
                conn.rollback()
        finally:
            if conn:
                Db.return_connection(conn)
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def add_user(username, email, password):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
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
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            print(f"Error adding user: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def update_user_password(username, new_password):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            hashed_password = Db.hash_password(new_password)
            cursor.execute('''
                UPDATE users 
                SET password = %s
                WHERE username = %s
            ''', (hashed_password, username))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating password: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_user_role(username):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT role FROM roles WHERE username = %s', (username,))
            result = cursor.fetchone()
            return result[0] if result else 'default'
        except Exception as e:
            print(f"Error getting user role: {e}")
            return 'default'
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def set_user_role(username, role):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO roles (username, role)
                VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE SET role = %s
            ''', (username, role, role))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error setting user role: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_all_users():
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, email, created_at FROM users ORDER BY created_at DESC
            ''')
            users = cursor.fetchall()
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_all_solutions_admin():
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.id, s.title, s.url, u.username, s.isac, s.ispublic, s.created_at
                FROM solutions s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.created_at DESC
            ''')
            sols = cursor.fetchall()
            return sols
        except Exception as e:
            print(f"Error getting all solutions: {e}")
            return []
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_all_points_admin():
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.username, COALESCE(p.point, 0), COALESCE(p.total_point, 0)
                FROM users u
                LEFT JOIN points p ON u.username = p.username
                ORDER BY COALESCE(p.total_point, 0) DESC
            ''')
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error getting all points: {e}")
            return []
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_all_roles_admin():
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.username, COALESCE(r.role, 'default')
                FROM users u
                LEFT JOIN roles r ON u.username = r.username
                ORDER BY u.username
            ''')
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error getting all roles: {e}")
            return []
        finally:
            if conn:
                Db.return_connection(conn)


    @staticmethod
    def verify_user(username, plain_password):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
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
            print(f"Error verifying user: {e}")
            return False
        finally:
            if conn:
                Db.return_connection(conn)
            
    @staticmethod
    def get_user_by_username(username):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, created_at 
                FROM users WHERE username = %s
            ''', (username,))
            user = cursor.fetchone()
            return user
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def username_exists(username):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking username exists: {e}")
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def email_exists(email):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking email exists: {e}")
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def add_solution(url, title, isac, ispublic, summary, code, user_id):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO solutions (url, title, isac, ispublic, summary, code, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (url, title, isac, ispublic, summary, code, user_id))
            conn.commit()
            print(f"Solution added successfully by user {user_id}")
            return True
        except Exception as e:
            print(f"Error adding solution: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_user_id_by_username(username):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting user ID: {e}")
            return None
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_my_solutions(user_id, offset=0, limit=10, search=None):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
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
            print(f"Error getting my solutions: {e}")
            return []
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_public_solutions(offset=0, limit=10, search=None):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
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
            print(f"Error getting public solutions: {e}")
            return []
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_solution_by_id(solution_id):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.id = %s
            ''', (solution_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error getting solution by ID: {e}")
            return None
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def update_solution(solution_id, url, title, isac, ispublic, summary, code, user_id):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE solutions 
                SET url = %s, title = %s, isac = %s, ispublic = %s, summary = %s, code = %s
                WHERE id = %s AND user_id = %s
            ''', (url, title, isac, ispublic, summary, code, solution_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating solution: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def admin_update_solution(solution_id, url, title, isac, ispublic, summary, code):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE solutions 
                SET url = %s, title = %s, isac = %s, ispublic = %s, summary = %s, code = %s
                WHERE id = %s
            ''', (url, title, isac, ispublic, summary, code, solution_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error admin updating solution: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def delete_solution(solution_id, user_id):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM solutions 
                WHERE id = %s AND user_id = %s
            ''', (solution_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting solution: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def admin_delete_solution(solution_id):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM solutions WHERE id = %s', (solution_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error admin deleting solution: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def add_points(username, points_to_add):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
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
            print(f"Error adding points: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_user_points(username):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT point, total_point FROM points WHERE username = %s', (username,))
            result = cursor.fetchone()
            return result if result else (0, 0)
        except Exception as e:
            print(f"Error getting user points: {e}")
            return (0, 0)
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_all_users_points():
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.username, COALESCE(p.total_point, 0)
                FROM users u 
                LEFT JOIN points p ON u.username = p.username
                ORDER BY COALESCE(p.total_point, 0) DESC
            ''')
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting all users points: {e}")
            return []
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def update_session_token(username, session_token):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET session_token = %s
                WHERE username = %s
            ''', (session_token, username))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating session token: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                Db.return_connection(conn)

    @staticmethod
    def get_session_token(username):
        conn = None
        try:
            conn = Db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_token FROM users WHERE username = %s
            ''', (username,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting session token: {e}")
            return None
        finally:
            if conn:
                Db.return_connection(conn)