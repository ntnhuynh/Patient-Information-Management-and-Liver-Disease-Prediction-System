from app import app
from extensions import db
from models.models import User
from utils.security import hash_password
from datetime import datetime
import getpass
import sys
sys.stdout.reconfigure(encoding='utf-8')

def create_director():
    with app.app_context():
        db.create_all()
        if User.query.filter_by(role="director").first():
            print("Giám đốc đã tồn tại.")
            return

        print("Tạo giám đốc đầu tiên")

        # Thu thập dữ liệu từ CLI
        full_name = input("Họ tên: ")
        username = input("Tên đăng nhập: ")
        email = input("Email: ")
        gender = input("Giới tính (nam/nữ): ")
        birth_date_str = input("Ngày sinh (dd-mm-yyyy): ")
        password = getpass.getpass("Mật khẩu: ")

        # Parse ngày sinh
        try:
            birth_date = datetime.strptime(birth_date_str, "%d-%m-%Y").date()
        except ValueError:
            print("Ngày sinh không hợp lệ (đúng định dạng dd-mm-yyyy).")
            return

        director = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            gender=gender,
            birth_date=birth_date,
            role="director",
            is_approved_by_superior = True,
            is_verified_by_self = True
        )

        db.session.add(director)
        db.session.commit()
        print("Giám đốc đã được tạo thành công.")

if __name__ == "__main__":
    create_director()
