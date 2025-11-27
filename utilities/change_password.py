import sys
import os
import getpass
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Db

def change_password():
    print("Đổi mật khẩu")
    username = input("Nhập username: ").strip()
    
    if not Db.username_exists(username):
        print("Username không tồn tại!")
        return
    
    print(f"Đang đổi mật khẩu cho user: {username}")
    
    new_password = getpass.getpass("Nhập mật khẩu mới: ")
    confirm_password = getpass.getpass("Xác nhận mật khẩu mới: ")
    
    if new_password != confirm_password:
        print("Mật khẩu xác nhận không khớp!")
        return
    
    if len(new_password) < 6:
        print("Mật khẩu mới phải có ít nhất 6 ký tự!")
        return
    
    if Db.update_user_password(username, new_password):
        print("Đổi mật khẩu thành công!")
    else:
        print("Đổi mật khẩu thất bại!")

if __name__ == '__main__':
    change_password()