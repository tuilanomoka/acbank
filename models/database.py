import sqlite3
import hashlib
import os

class Db:
    @staticmethod
    def create_accounts_table():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL DEFAULT 'default',
                    FOREIGN KEY (username) REFERENCES users (username)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    point INTEGER NOT NULL DEFAULT 0,
                    total_point INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (username) REFERENCES users (username)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    isac BOOLEAN NOT NULL DEFAULT 0,
                    ispublic BOOLEAN NOT NULL DEFAULT 0,
                    summary TEXT,
                    code TEXT,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            print("Tables created successfully")
        except sqlite3.Error as e:
            print(e)
        finally:
            conn.close()
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def add_user(username, email, password):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            hashed_password = Db.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            
            cursor.execute('''
                INSERT INTO roles (username, role)
                VALUES (?, ?)
            ''', (username, 'default'))
            
            conn.commit()
            print(f"User {username} added successfully")
            return True
        except sqlite3.IntegrityError:
            print("Username or email already exists")
            return False
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_user_role(username):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT role FROM roles WHERE username = ?''', (username,))
            result = cursor.fetchone()
            return result[0] if result else 'default'
        except sqlite3.Error as e:
            print(e)
            return 'default'
        finally:
            conn.close()

    @staticmethod
    def set_user_role(username, role):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO roles (username, role)
                VALUES (?, ?)
            ''', (username, role))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_all_users():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT u.username, u.email, r.role, u.created_at 
                FROM users u 
                LEFT JOIN roles r ON u.username = r.username
            ''')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(e)
            return []
        finally:
            conn.close()

    @staticmethod
    def get_all_solutions(offset=0, limit=10, search=None):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            query = '''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
            '''
            params = []
            
            if search:
                query += ' WHERE (s.url LIKE ? OR s.title LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += ' ORDER BY s.created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(e)
            return []
        finally:
            conn.close()

    @staticmethod
    def count_all_solutions(search=None):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            query = 'SELECT COUNT(*) FROM solutions'
            params = []
            
            if search:
                query += ' WHERE (url LIKE ? OR title LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(e)
            return 0
        finally:
            conn.close()

    @staticmethod
    def admin_update_solution(solution_id, url, title, isac, ispublic, summary, code):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE solutions 
                SET url = ?, title = ?, isac = ?, ispublic = ?, summary = ?, code = ?
                WHERE id = ?
            ''', (url, title, isac, ispublic, summary, code, solution_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def admin_delete_solution(solution_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM solutions WHERE id = ?', (solution_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def verify_user(username, plain_password):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT password FROM users WHERE username = ?''', (username,))
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
        except sqlite3.Error as e:
            print(e)
        finally:
            conn.close()
            
    @staticmethod
    def get_user_by_username(username):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, username, email, created_at 
                FROM users WHERE username = ?
            ''', (username,))
            user = cursor.fetchone()
            return user
        except sqlite3.Error as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def username_exists(username):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT id FROM users WHERE username = ?''', (username,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def email_exists(email):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT id FROM users WHERE email = ?''', (email,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def add_solution(url, title, isac, ispublic, summary, code, user_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO solutions (url, title, isac, ispublic, summary, code, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (url, title, isac, ispublic, summary, code, user_id))
            conn.commit()
            print(f"Solution added successfully by user {user_id}")
            return True
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_user_id_by_username(username):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT id FROM users WHERE username = ?''', (username,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def get_my_solutions(user_id, offset=0, limit=10, search=None):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            query = '''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.user_id = ?
            '''
            params = [user_id]
            
            if search:
                query += ' AND (s.url LIKE ? OR s.title LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += ' ORDER BY s.created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(e)
            return []
        finally:
            conn.close()

    @staticmethod
    def get_public_solutions(offset=0, limit=10, search=None):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            query = '''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.ispublic = 1
            '''
            params = []
            
            if search:
                query += ' AND (s.url LIKE ? OR s.title LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += ' ORDER BY s.created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(e)
            return []
        finally:
            conn.close()

    @staticmethod
    def count_my_solutions(user_id, search=None):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            query = 'SELECT COUNT(*) FROM solutions WHERE user_id = ?'
            params = [user_id]
            
            if search:
                query += ' AND (url LIKE ? OR title LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(e)
            return 0
        finally:
            conn.close()

    @staticmethod
    def count_public_solutions(search=None):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            query = 'SELECT COUNT(*) FROM solutions WHERE ispublic = 1'
            params = []
            
            if search:
                query += ' AND (url LIKE ? OR title LIKE ?)'
                params.extend([f'%{search}%', f'%{search}%'])
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(e)
            return 0
        finally:
            conn.close()

    @staticmethod
    def get_solution_by_id(solution_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT s.*, u.username 
                FROM solutions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.id = ?
            ''', (solution_id,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(e)
            return None
        finally:
            conn.close()

    @staticmethod
    def update_solution(solution_id, url, title, isac, ispublic, summary, code, user_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE solutions 
                SET url = ?, title = ?, isac = ?, ispublic = ?, summary = ?, code = ?
                WHERE id = ? AND user_id = ?
            ''', (url, title, isac, ispublic, summary, code, solution_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_solution(solution_id, user_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM solutions 
                WHERE id = ? AND user_id = ?
            ''', (solution_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def add_user(username, email, password):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            hashed_password = Db.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            
            cursor.execute('''
                INSERT INTO roles (username, role)
                VALUES (?, ?)
            ''', (username, 'default'))
            
            cursor.execute('''
                INSERT INTO points (username, point, total_point)
                VALUES (?, ?, ?)
            ''', (username, 0, 0))
            
            conn.commit()
            print(f"User {username} added successfully")
            return True
        except sqlite3.IntegrityError:
            print("Username or email already exists")
            return False
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def add_points(username, points_to_add):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO points (username, point, total_point)
                VALUES (?, 
                    COALESCE((SELECT point FROM points WHERE username = ?), 0) + ?,
                    COALESCE((SELECT total_point FROM points WHERE username = ?), 0) + ?
                )
            ''', (username, username, points_to_add, username, points_to_add))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_user_points(username):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''SELECT point, total_point FROM points WHERE username = ?''', (username,))
            result = cursor.fetchone()
            return result if result else (0, 0)
        except sqlite3.Error as e:
            print(e)
            return (0, 0)
        finally:
            conn.close()

    @staticmethod
    def get_all_users_points():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT u.username, p.point, p.total_point 
                FROM users u 
                LEFT JOIN points p ON u.username = p.username
                ORDER BY p.point DESC
            ''')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(e)
            return []
        finally:
            conn.close()