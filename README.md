---------- HƯỚNG DẪN CÀI ĐẶT HỆ THỐNG ------------------

# Kiểm tra phiên bản Python
python --version
# Nếu chưa phải 3.11, tải tại: https://www.python.org/downloads/release/python-3110/

# Cài đặt các thư viện cần thiết, hoặc truy cập file requirements.txt để lấy danh sách thư viện yêu cầu
pip install Flask==3.1.1

pip install Flask-SQLAlchemy==3.1.1

pip install Flask-Mail==0.9.1

pip install Joblib==1.5.1

pip install Numpy==2.3.2

# hoặc
pip install -r requirements.txt

# Cài đặt MySQL và thư viện kết nối

# Cài đặt thư viện kết nối (chọn 1 trong 2)
pip install mysqlclient

# hoặc
pip install PyMySQL

# Cấu hình kết nối MySQL trong ứng dụng

# Trong file .env hoặc config.py, bạn cần khai báo chuỗi kết nối như sau:

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://username:password@localhost/db_name"

# Ngoài ra cần cấu hình lại các mục trong file .env.example để hệ thống vận hành đúng đắn
# Cần tạo database bên MySQL trước, ví dụ:

CREATE DATABASE my_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Cần tạo thư mục migrations/ để khởi tạo Alembic
flask db init

# Tạo bản ghi (migration script)
flask db migrate -m "Initial migration"

# Áp dụng migration script vào database
flask db upgrade

# Sau những bước này, bạn đã có thể chạy hệ thống.
python run.py

# Chạy file manage.py để tạo giám đốc đầu tiên.
