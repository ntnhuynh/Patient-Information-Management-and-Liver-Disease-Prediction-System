from flask import Blueprint, request, jsonify, session
from models.models import Patient,  User, FullMedicalRecord, SharedAccess
from datetime import datetime
from extensions import db
medical_record_bp = Blueprint("medical_record", __name__, url_prefix="/medical-record")
def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
@medical_record_bp.route('/add_medical-records', methods=['POST'])
def create_record():
    if 'user_id' not in session:
        return jsonify({'error': 'Chưa đăng nhập'}), 401

    user_id = session['user_id']
    data = request.json
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Không nhận được dữ liệu'}), 400

    patient_id = data.get('patient_id')
    if not patient_id:
        return jsonify({'error': 'Thiếu patient_id'}), 400

    try:
        new_record = FullMedicalRecord(
            patient_id=data['patient_id'],
            created_by=user_id,
            department_id=data.get('department_id'),
            visit_date=data.get('visit_date'),
            reason_for_visit=data.get('reason_for_visit'),
            main_symptoms=data.get('main_symptoms'),
            onset_time=data.get('onset_time'),

            # Khám lâm sàng
            blood_pressure=data.get('blood_pressure'),
            heart_rate=data.get('heart_rate'),
            temperature = safe_float(data.get('temperature')),
            respiratory_rate=data.get('respiratory_rate'),
            weight=data.get('weight'),
            height=data.get('height'),
            exam_cardio=data.get('exam_cardio'),
            exam_respiratory=data.get('exam_respiratory'),
            exam_digestive=data.get('exam_digestive'),
            exam_neuro=data.get('exam_neuro'),
            exam_skin=data.get('exam_skin'),

            # Cận lâm sàng
            orders=data.get('orders'),
            result_summary=data.get('result_summary'),
            total_bilirubin=data.get('total_bilirubin'),
            direct_bilirubin=data.get('direct_bilirubin'),
            alkaline_phosphotase=data.get('alkaline_phosphotase'),
            alamine_aminotransferase=data.get('alamine_aminotransferase'),
            aspartate_aminotransferase=data.get('aspartate_aminotransferase'),
            total_proteins=data.get('total_proteins'),
            albumin=data.get('albumin'),
            albumin_globulin_ratio=data.get('albumin_globulin_ratio'),

            # Chẩn đoán
            preliminary_diagnosis=data.get('preliminary_diagnosis'),
            confirmed_diagnosis=data.get('confirmed_diagnosis'),

            # Kế hoạch điều trị
            medications=data.get('medications'),
            procedures=data.get('procedures'),
            follow_up_instructions=data.get('follow_up_instructions'),
            follow_up_date=data.get('follow_up_date'),

            # Ghi chú quá trình
            progress_note=data.get('progress_note'),

            # Tóm tắt xuất viện
            admission_date=data.get('admission_date'),
            discharge_date=data.get('discharge_date'),
            discharge_diagnosis=data.get('discharge_diagnosis'),
            treatment_outcome=data.get('treatment_outcome'),
            post_discharge_instructions=data.get('post_discharge_instructions')
        )

        db.session.add(new_record)
        db.session.commit()
        print(new_record.id)
        return jsonify({
            'message': 'Hồ sơ đã được tạo thành công',
            'record_id': new_record.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Tạo hồ sơ thất bại', 'details': str(e)}), 400

@medical_record_bp.route('/get_medical-records/<int:record_id>', methods=['GET'])
def get_record(record_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Chưa đăng nhập'}), 401

    user = User.query.get(session['user_id'])
    record = FullMedicalRecord.query.get_or_404(record_id)

    # Phân quyền truy cập
    is_creator = record.created_by == user.id
    is_department_head = user.role == 'department head' and user.khoa_id == record.department_id
    is_director = user.role == 'director'
    is_shared = SharedAccess.query.filter_by(record_id=record_id, shared_with=user.id).first()
    print(record_id, user.id)
    if not (is_creator or is_department_head or is_director or is_shared):
        return jsonify({'error': 'Không có quyền xem hồ sơ này'}), 403
    patient = Patient.query.get(record.patient_id)
    user_create = User.query.get(record.created_by)
    return jsonify({
        "id": record.id,
        "patient_id": record.patient_id,
        "created_by": user_create.full_name,
        "department_id": record.department_id,
        "created_at": record.created_at.isoformat() if record.created_at else None,

        # Thông tin khám ban đầu
        "visit_date": record.visit_date.isoformat() if record.visit_date else None,
        "reason_for_visit": record.reason_for_visit,
        "main_symptoms": record.main_symptoms,
        "onset_time": record.onset_time,

        # Khám lâm sàng
        "blood_pressure": record.blood_pressure,
        "heart_rate": record.heart_rate,
        "temperature": record.temperature,
        "respiratory_rate": record.respiratory_rate,
        "weight": record.weight,
        "height": record.height,
        "exam_cardio": record.exam_cardio,
        "exam_respiratory": record.exam_respiratory,
        "exam_digestive": record.exam_digestive,
        "exam_neuro": record.exam_neuro,
        "exam_skin": record.exam_skin,

        # Cận lâm sàng
        "orders": record.orders,
        "result_summary": record.result_summary,
        "total_bilirubin": record.total_bilirubin,
        "direct_bilirubin": record.direct_bilirubin,
        "alkaline_phosphotase": record.alkaline_phosphotase,
        "alamine_aminotransferase": record.alamine_aminotransferase,
        "aspartate_aminotransferase": record.aspartate_aminotransferase,
        "total_proteins": record.total_proteins,
        "albumin": record.albumin,
        "albumin_globulin_ratio": record.albumin_globulin_ratio,

        # Chẩn đoán
        "preliminary_diagnosis": record.preliminary_diagnosis,
        "confirmed_diagnosis": record.confirmed_diagnosis,

        # Kế hoạch điều trị
        "medications": record.medications,
        "procedures": record.procedures,
        "follow_up_instructions": record.follow_up_instructions,
        "follow_up_date": record.follow_up_date.isoformat() if record.follow_up_date else None,

        # Ghi chú quá trình
        "progress_note": record.progress_note,

        # Tóm tắt xuất viện
        "admission_date": record.admission_date.isoformat() if record.admission_date else None,
        "discharge_date": record.discharge_date.isoformat() if record.discharge_date else None,
        "discharge_diagnosis": record.discharge_diagnosis,
        "treatment_outcome": record.treatment_outcome,
        "post_discharge_instructions": record.post_discharge_instructions,
        #Thông tin bệnh nhân
        "name": patient.name,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "gender": patient.gender,
        "address": patient.address,
        "phone": patient.phone,
        "occupation": patient.occupation,
        "insurance_code": patient.insurance_code,
        "identity_number": patient.identity_number,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "emergency_contact_relation": patient.emergency_contact_relation
    }), 200


@medical_record_bp.route('/update_medical-records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Chưa đăng nhập'}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    record = FullMedicalRecord.query.get_or_404(record_id)

    # Kiểm tra quyền cập nhật
    is_creator = record.created_by == user_id
    is_department_head = user.role == 'head' and user.department_id == record.department_id
    is_director = user.role == 'director'

    if not (is_creator or is_department_head or is_director):
        return jsonify({'error': 'Không có quyền cập nhật hồ sơ này'}), 403

    data = request.json

    # Cập nhật tất cả các trường
    record.visit_date = data.get('visit_date', record.visit_date)
    record.reason_for_visit = data.get('reason_for_visit', record.reason_for_visit)
    record.main_symptoms = data.get('main_symptoms', record.main_symptoms)
    record.onset_time = data.get('onset_time', record.onset_time)

    record.blood_pressure = data.get('blood_pressure', record.blood_pressure)
    record.heart_rate = data.get('heart_rate', record.heart_rate)
    record.temperature = data.get('temperature', record.temperature)
    record.respiratory_rate = data.get('respiratory_rate', record.respiratory_rate)
    record.weight = data.get('weight', record.weight)
    record.height = data.get('height', record.height)
    record.exam_cardio = data.get('exam_cardio', record.exam_cardio)
    record.exam_respiratory = data.get('exam_respiratory', record.exam_respiratory)
    record.exam_digestive = data.get('exam_digestive', record.exam_digestive)
    record.exam_neuro = data.get('exam_neuro', record.exam_neuro)
    record.exam_skin = data.get('exam_skin', record.exam_skin)

    record.orders = data.get('orders', record.orders)
    record.result_summary = data.get('result_summary', record.result_summary)
    record.total_bilirubin = data.get('total_bilirubin', record.total_bilirubin)
    record.direct_bilirubin = data.get('direct_bilirubin', record.direct_bilirubin)
    record.alkaline_phosphotase = data.get('alkaline_phosphotase', record.alkaline_phosphotase)
    record.alamine_aminotransferase = data.get('alamine_aminotransferase', record.alamine_aminotransferase)
    record.aspartate_aminotransferase = data.get('aspartate_aminotransferase', record.aspartate_aminotransferase)
    record.total_proteins = data.get('total_proteins', record.total_proteins)
    record.albumin = data.get('albumin', record.albumin)
    record.albumin_globulin_ratio = data.get('albumin_globulin_ratio', record.albumin_globulin_ratio)

    record.preliminary_diagnosis = data.get('preliminary_diagnosis', record.preliminary_diagnosis)
    record.confirmed_diagnosis = data.get('confirmed_diagnosis', record.confirmed_diagnosis)

    record.medications = data.get('medications', record.medications)
    record.procedures = data.get('procedures', record.procedures)
    record.follow_up_instructions = data.get('follow_up_instructions', record.follow_up_instructions)
    record.follow_up_date = data.get('follow_up_date', record.follow_up_date)

    record.progress_note = data.get('progress_note', record.progress_note)

    record.admission_date = data.get('admission_date', record.admission_date)
    record.discharge_date = data.get('discharge_date', record.discharge_date)
    record.discharge_diagnosis = data.get('discharge_diagnosis', record.discharge_diagnosis)
    record.treatment_outcome = data.get('treatment_outcome', record.treatment_outcome)
    record.post_discharge_instructions = data.get('post_discharge_instructions', record.post_discharge_instructions)

    db.session.commit()
    return jsonify({'message': 'Hồ sơ đã được cập nhật thành công'})


@medical_record_bp.route("/medical-records/<int:record_id>/share", methods=["POST"])
def share_record(record_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    data = request.get_json()
    shared_with_id = data.get("shared_with")

    if not shared_with_id:
        return jsonify({"error": "Thiếu thông tin bác sĩ cần chia sẻ"}), 400

    # Kiểm tra hồ sơ tồn tại
    record = FullMedicalRecord.query.get_or_404(record_id)

    # Tạo bản ghi chia sẻ
    shared = SharedAccess(record_id=record_id, shared_with=shared_with_id)
    db.session.add(shared)
    db.session.commit()

    return jsonify({"message": "Chia sẻ hồ sơ thành công"})
@medical_record_bp.route("/shared-records/<int:user_id>", methods=["GET"])
def get_shared_records(user_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    # Kiểm tra người dùng tồn tại
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404

    # Truy xuất các bản ghi đã được chia sẻ
    shared_entries = SharedAccess.query.filter_by(shared_with=user_id).all()
    shared_record_ids = [entry.record_id for entry in shared_entries]

    return jsonify({
        "record_ids": shared_record_ids,
        "count": len(shared_record_ids)
    })
@medical_record_bp.route("/shared-records/count/<int:user_id>", methods=["GET"])
def count_shared_records_by_user(user_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    shared_count = SharedAccess.query.filter_by(shared_with=user_id).count()

    return jsonify({
        "user_id": user_id,
        "shared_record_count": shared_count
    }), 200

@medical_record_bp.route('/count', methods=['GET'])
def count_full_medical_records():
    total = FullMedicalRecord.query.count()
    return jsonify({'total_records': total})