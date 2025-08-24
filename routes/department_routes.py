# department_routes.py
from flask import Blueprint, request, jsonify, session
from extensions import db
from models.models import Department, User
import logging
import re
department_bp = Blueprint("department_bp", __name__)
logger = logging.getLogger(__name__)
@department_bp.route("/create_dp", methods=["POST"])
def create_department():
    if "user_id" not in session:
        return jsonify({'error': 'Chưa đăng nhập'}), 401

    user = User.query.get(session["user_id"])
    if not user or user.role.lower() != 'director':
        return jsonify({'error': 'Bạn không có quyền tạo khoa'}), 403

    if not request.is_json:
        return jsonify({'error': 'Dữ liệu gửi lên phải ở dạng JSON'}), 400

    data = request.get_json()
    name_raw = data.get('name')

    if not name_raw or not isinstance(name_raw, str):
        return jsonify({'error': 'Tên khoa là bắt buộc'}), 400

    normalized_name = name_raw.strip()

    # Kiểm tra ký tự đặc biệt (chỉ cho phép chữ, số, khoảng trắng)
    if not re.match(r'^[a-zA-Z0-9\s]+$', normalized_name):
        return jsonify({'error': 'Tên khoa không được chứa ký tự đặc biệt'}), 400

    # Chuẩn hóa để tránh trùng lặp
    normalized_name_lower = normalized_name.lower()

    if Department.query.filter(db.func.lower(Department.name) == normalized_name_lower).first():
        return jsonify({'error': 'Tên khoa đã tồn tại'}), 400

    new_department = Department(name=normalized_name)

    try:
        db.session.add(new_department)
        db.session.commit()

        return jsonify({
            'message': 'Tạo khoa thành công',
            'department_id': new_department.id,
            'name': new_department.name.title()  # Trả về viết hoa
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Lỗi server. Không thể tạo khoa.'}), 500
@department_bp.route("/list", methods=["GET"])
def list_departments():
    departments = Department.query.order_by(Department.name).all()
    return jsonify([
        {
            "id": d.id,                #  ID thật sự của khoa
            "name": d.name.title()     #  Hiển thị tên khoa đẹp hơn
        } for d in departments
    ])
@department_bp.route('/count', methods=['GET'])
def count_departments():
    total = Department.query.count()
    return jsonify({'total_departments': total})
@department_bp.route('/count-by-department/<int:khoa_id>', methods=['GET'])
def count_users_by_department(khoa_id):
    count = User.query.filter_by(khoa_id=khoa_id).count()
    return jsonify({
        'khoa_id': khoa_id,
        'user_count': count
    })
