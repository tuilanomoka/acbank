import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Db

def list_all_users():
    users = Db.get_all_users()
    print("All users:")
    print("-" * 50)
    for user in users:
        print(f"Username: {user[0]}")
        print(f"Email: {user[1]}")
        print(f"Role: {user[2]}")
        print(f"Created: {user[3]}")
        print("-" * 50)

if __name__ == '__main__':
    list_all_users()