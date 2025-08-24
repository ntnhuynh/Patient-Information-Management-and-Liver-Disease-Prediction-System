from flask import Blueprint, request, jsonify, session
from models.models import Patient, Department, User, FullMedicalRecord
import joblib
import numpy as np
from datetime import datetime, date
from extensions import db
patient_bp = Blueprint("patient", __name__)

@patient_bp.route("/add-patient", methods=["POST"])
def add_patient():
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user_obj = User.query.get(session["user_id"])
    if not user_obj:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    data = request.get_json()

    # Lấy và chuẩn hóa dữ liệu
    name = data.get("name", "").strip()
    birth_date_str = data.get("birth_date", "").strip()
    gender = data.get("gender", "").strip().lower()
    address = data.get("address", "").strip()
    phone = data.get("phone", "").strip()
    occupation = data.get("occupation", "").strip()
    insurance_code = data.get("insurance_code", "").strip()
    identity_number = data.get("identity_number", "").strip()
    emergency_contact_name = data.get("emergency_contact_name", "").strip()
    emergency_contact_phone = data.get("emergency_contact_phone", "").strip()
    emergency_contact_relation = data.get("emergency_contact_relation", "").strip()
    # Kiểm tra bắt buộc
    if not name or not birth_date_str or not gender:
        return jsonify({"error": "Vui lòng nhập đầy đủ thông tin: name, birth_date, gender"}), 400

    if gender not in ['nam', 'nữ']:
        return jsonify({"error": "Giới tính phải là 'nam' hoặc 'nữ'"}), 400

    try:
        birth_date = datetime.strptime(birth_date_str, "%d/%m/%Y").date()
    except ValueError:
        return jsonify({"error": "Ngày sinh không hợp lệ, định dạng đúng là DD/MM/YYYY"}), 400

    # Tạo bệnh nhân
    patient = Patient(
        name=name,
        birth_date=birth_date,
        gender=gender,
        address=address,
        phone=phone,
        occupation=occupation,
        insurance_code=insurance_code,
        identity_number=identity_number,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_phone=emergency_contact_phone,
        emergency_contact_relation=emergency_contact_relation,
        khoa_id=user_obj.khoa_id,
        created_by=user_obj.id
    )

    try:
        db.session.add(patient)
        db.session.commit()
        return jsonify({"msg": "Thêm bệnh nhân thành công", "patient_id": patient.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

@patient_bp.route("/predict/<int:record_id>", methods=["GET"])
def predict_disease(record_id):
    # Kiểm tra đăng nhập
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user_obj = User.query.get(session["user_id"])
    if not user_obj:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404

    # Truy xuất hồ sơ bệnh án
    record = FullMedicalRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "Không tìm thấy hồ sơ bệnh án"}), 404

    patient = record.patient
    if not patient:
        return jsonify({"error": "Không tìm thấy bệnh nhân"}), 404

    # Kiểm tra dữ liệu xét nghiệm
    required_fields = {
        "total_bilirubin": record.total_bilirubin,
        "direct_bilirubin": record.direct_bilirubin,
        "alkaline_phosphotase": record.alkaline_phosphotase,
        "alamine_aminotransferase": record.alamine_aminotransferase,
        "aspartate_aminotransferase": record.aspartate_aminotransferase,
        "total_proteins": record.total_proteins,
        "albumin": record.albumin,
        "albumin_globulin_ratio": record.albumin_globulin_ratio
    }

    missing_fields = [key for key, value in required_fields.items() if value is None]
    if missing_fields:
        return jsonify({
            "error": "Thiếu dữ liệu xét nghiệm để dự đoán",
            "missing_fields": missing_fields
        }), 400

    try:
        # Chuẩn bị dữ liệu đầu vào cho mô hình
        age = date.today().year - patient.birth_date.year
        gender_encoded = 1 if patient.gender.lower() == "nam" else 0

        features = np.array([[ 
            age,
            gender_encoded,
            *required_fields.values()
        ]])

        # Dự đoán bằng mô hình AI
        liver_model = joblib.load("liver_model.pkl")
        prediction_result = liver_model.predict(features)[0]

        prediction = "Bị bệnh gan" if prediction_result == 1 else "Không bị bệnh gan"

        # Ghi chú vào hồ sơ
        record.progress_note = f"Dự đoán AI: {prediction} bởi bác sĩ {user_obj.full_name}"
        db.session.commit()

        # Trả về kết quả
        return jsonify({
            "prediction": prediction,
            "record_id": record.id,
            "patient_info": {
                "id": patient.id,
                "full_name": patient.name,
                "gender": patient.gender,
                "birth_date": patient.birth_date.isoformat(),
                "age": age
            },
            "lab_values": required_fields
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500



@patient_bp.route("/list/<int:khoa_id>/patients", methods=["GET"])
def list_patients_by_department(khoa_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user_obj = User.query.get(session["user_id"])
    if not user_obj:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404

    #  Kiểm tra quyền truy cập
    if user_obj.role == "department head" and user_obj.khoa_id != khoa_id:
        return jsonify({"error": "Bạn không có quyền xem danh sách bệnh nhân của khoa này"}), 403
    elif user_obj.role not in ["director", "department head"]:
        return jsonify({"error": "Không có quyền truy cập"}), 403

    #  Truy vấn bệnh nhân theo khoa
    query = Patient.query.filter_by(khoa_id=khoa_id)

    #  Phân trang
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    patients = pagination.items
    department = Department.query.get(khoa_id)
    department_name = department.name.title() if department else "Không rõ"

    result = [{
        "id": p.id,
        "name": p.name,
        "birth_date": p.birth_date.strftime("%d-%m-%Y") if p.birth_date else None,
        "gender": p.gender,
        "address": p.address or "",
        "doctor_name": p.creator.full_name if p.creator else "Không rõ",
 
    } for p in patients]


    return jsonify({
        "department_name": department_name,
        "patients": result,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total
        }
    }), 200


@patient_bp.route("/detail/<int:patient_id>", methods=["GET"])
def patient_detail(patient_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "Không tìm thấy user"}), 404

    patient = Patient.query.get_or_404(patient_id)

    # Phân quyền truy cập
    if user.role == "doctor" and patient.created_by != user.id:
        return jsonify({"error": "Bạn không có quyền xem bệnh nhân này"}), 403
    if user.role == "department head" and patient.khoa_id != user.khoa_id:
        return jsonify({"error": "Bạn không có quyền xem bệnh nhân này"}), 403

    records = FullMedicalRecord.query.filter_by(patient_id=patient_id).order_by(FullMedicalRecord.created_at.desc()).all()

    record_list = []
    for r in records:
        record_list.append({
            "id": r.id,
            "visit_date": r.visit_date.isoformat() if r.visit_date else None,
            "reason_for_visit": r.reason_for_visit,
            "main_symptoms": r.main_symptoms,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "progress_note": r.progress_note or ""
        })

    return jsonify({
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
            "gender": patient.gender,
            "address": patient.address or "",
            "doctor_id": patient.created_by
        },
        "records": record_list
    }), 200




@patient_bp.route("/update/<int:patient_id>", methods=["PUT"])
def update_patient(patient_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "Người dùng không tồn tại"}), 404

    patient = Patient.query.get_or_404(patient_id)

    # Phân quyền:
    if user.role == "doctor" and patient.created_by != user.id:
        return jsonify({"error": "Không có quyền cập nhật"}), 403
    if user.role == "department head" and patient.khoa_id != user.khoa_id:
        return jsonify({"error": "Không có quyền cập nhật"}), 403

    data = request.json

    # Cập nhật tên
    if "name" in data:
        patient.name = data["name"].strip()

    # Cập nhật ngày sinh
    birth_date_str = data.get("birth_date")
    if birth_date_str:
        try:
            patient.birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Ngày sinh không hợp lệ. Định dạng phải là YYYY-MM-DD"}), 400

    # Cập nhật giới tính
    gender = data.get("gender")
    if gender:
        gender = gender.strip().capitalize()
        if gender not in ["Nam", "Nữ"]:
            return jsonify({"error": "Giới tính phải là 'Nam' hoặc 'Nữ'"}), 400
        patient.gender = gender

    # Cập nhật địa chỉ
    if "address" in data:
        patient.address = data["address"].strip()

    db.session.commit()
    return jsonify({"message": "Cập nhật thông tin bệnh nhân thành công"}), 200
@patient_bp.route("/patients/count/<int:khoa_id>", methods=["GET"])
def count_patients_by_department(khoa_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    patient_count = Patient.query.filter_by(khoa_id=khoa_id).count()

    return jsonify({
        "khoa_id": khoa_id,
        "patient_count": patient_count
    }), 200
@patient_bp.route('/created-by/<int:user_id>', methods=['GET'])
def get_patients_by_creator(user_id):
    patients = Patient.query.filter_by(created_by=user_id).all()

    result = []
    for p in patients:
        result.append({
            'id': p.id,
            'name': p.name,
            'birth_date': p.birth_date.isoformat() if p.birth_date else None,
            'gender': p.gender,
            'phone': p.phone,
            'address': p.address,
            'occupation': p.occupation,
            'insurance_code': p.insurance_code,
            'identity_number': p.identity_number,
            'emergency_contact_name': p.emergency_contact_name,
            'emergency_contact_phone': p.emergency_contact_phone,
            'emergency_contact_relation': p.emergency_contact_relation,
            'created_at': p.created_at.isoformat() if p.created_at else None
        })

    return jsonify({
        'created_by': user_id,
        'patient_count': len(result),
        'patients': result
    }), 200
@patient_bp.route('/count-by-creator/<int:user_id>', methods=['GET'])
def count_patients_by_creator(user_id):
    count = Patient.query.filter_by(created_by=user_id).count()
    return jsonify({
        'created_by': user_id,
        'patient_count': count
    }), 200
