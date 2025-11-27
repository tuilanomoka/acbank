import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Db

def set_user_role(username, role):
    if role not in ['admin', 'default']:
        print("Role must be 'admin' or 'default'")
        return False
    
    if not Db.username_exists(username):
        print(f"User {username} does not exist")
        return False
    
    if Db.set_user_role(username, role):
        print(f"Successfully set {username} to {role}")
        return True
    else:
        print(f"Failed to set role for {username}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python set_role.py <username> <admin|default>")
        sys.exit(1)
    
    username = sys.argv[1]
    role = sys.argv[2]
    set_user_role(username, role)