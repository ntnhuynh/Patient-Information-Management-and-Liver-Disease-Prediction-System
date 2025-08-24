from flask import Blueprint, jsonify, session, request
from models.models import Patient, Department, User
from sqlalchemy import func, extract
from extensions import db
from datetime import datetime
stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/departments/<int:khoa_id>/staff", methods=["GET"])
def department_staff(khoa_id):
    if "user_id" not in session:
        return jsonify({'error': 'Chưa đăng nhập'}), 401

    dept = Department.query.get_or_404(khoa_id)

    truong_khoa = User.query.filter_by(khoa_id=dept.id, role="department head").first()
    bac_si_list = User.query.filter_by(khoa_id=dept.id, role="doctor").all()

    # Nếu không có trưởng khoa và không có bác sĩ
    if not truong_khoa and not bac_si_list:
        return jsonify({
            "ten_khoa": dept.name,
            "message": "Khoa chưa có nhân sự nào."
        })

    truong_khoa_info = None
    if truong_khoa:
        truong_khoa_info = {
            "id": truong_khoa.id,
            "full_name": truong_khoa.full_name,
            "email": truong_khoa.email,
            "gender": truong_khoa.gender,
            "birth_date": str(truong_khoa.birth_date) if truong_khoa.birth_date else None
        }

    bac_si_info = [{
        "id": bs.id,
        "full_name": bs.full_name,
        "email": bs.email,
        "gender": bs.gender,
        "birth_date": str(bs.birth_date) if bs.birth_date else None
    } for bs in bac_si_list]

    return jsonify({
        "ten_khoa": dept.name,
        "truong_khoa": truong_khoa_info,
        "bac_si": bac_si_info
    })


@stats_bp.route("/khoa/<int:khoa_id>/monthly", methods=["GET"])
def stats_by_department_monthly(khoa_id):
    if "user_id" not in session:
        return jsonify({'error': 'Chưa đăng nhập'}), 401

    user = User.query.get(session["user_id"])
    if user.role.lower() != 'director' and (user.khoa_id!=khoa_id and user.role!="department head" ):
        return jsonify({'error': 'Bạn không có quyền xem thống kê'}), 403

    department = Department.query.get(khoa_id)
    if not department:
        return jsonify({'error': 'Khoa không tồn tại'}), 404

    # Lấy năm từ query string, mặc định là năm hiện tại
    from datetime import datetime
    year = request.args.get("year", datetime.now().year, type=int)

    from sqlalchemy import func, extract
    monthly_counts = []
    for month in range(1, 13):
        count = db.session.query(func.count(Patient.id))\
            .filter(Patient.khoa_id == khoa_id)\
            .filter(extract("year", Patient.created_at) == year)\
            .filter(extract("month", Patient.created_at) == month)\
            .scalar()
        monthly_counts.append(count)

    return jsonify({
        "status": "success",
        "khoa": department.name.title(),
        "year": year,
        "labels": [f"Tháng {i}" for i in range(1, 13)],
        "data": monthly_counts,
        "message": f"Thống kê bệnh nhân của khoa {department.name.title()} trong năm {year}"
    }), 200
