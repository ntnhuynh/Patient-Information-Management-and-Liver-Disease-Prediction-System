from sqlalchemy import CheckConstraint
from datetime import datetime
from extensions import db

class Department(db.Model):
    __tablename__ = 'department'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Quan hệ ngược với User và Patient
    users = db.relationship('User', backref=db.backref('department', lazy=True))
    patients = db.relationship('Patient', backref=db.backref('department', lazy=True))


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=False)

    # Quan hệ với Department
    khoa_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)

    # Quan hệ với người tạo tài khoản
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    creator = db.relationship('User', remote_side=[id], backref=db.backref('created_users', lazy=True))

    is_approved_by_superior = db.Column(db.Boolean, default=False)
    is_verified_by_self = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("role IN ('director', 'department head', 'doctor')", name="check_role_valid"),
        CheckConstraint("gender IN ('nam', 'nữ')", name="check_gender"),
    )


class Patient(db.Model):
    __tablename__ = 'patient'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    occupation = db.Column(db.String(100)) #nghề nghiệp
    insurance_code = db.Column(db.String(50)) #Mã bảo hiểm y tế
    identity_number = db.Column(db.String(50)) #CCCD
    emergency_contact_name = db.Column(db.String(100)) #Tên người liên hệ
    emergency_contact_phone = db.Column(db.String(20)) #SDT người liên hệ
    emergency_contact_relation = db.Column(db.String(50)) #Mối quan hệ

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    khoa_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    creator = db.relationship('User', backref=db.backref('created_patients', lazy=True))
    # department = db.relationship('Department', backref=db.backref('patients', lazy=True))

    __table_args__ = (
        CheckConstraint("gender IN ('nam', 'nữ')", name="check_genderv2"),
    )
class FullMedicalRecord(db.Model):
    __tablename__ = 'full_medical_record'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # bác sĩ tạo hồ sơ
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Thông tin khám ban đầu
    visit_date = db.Column(db.Date)
    reason_for_visit = db.Column(db.Text)
    main_symptoms = db.Column(db.Text)
    onset_time = db.Column(db.String(100))

    # Khám lâm sàng
    blood_pressure = db.Column(db.String(20))
    heart_rate = db.Column(db.String(20))
    temperature = db.Column(db.String(20))
    respiratory_rate = db.Column(db.String(20))
    weight = db.Column(db.String(20))
    height = db.Column(db.String(20))
    exam_cardio = db.Column(db.Text)
    exam_respiratory = db.Column(db.Text)
    exam_digestive = db.Column(db.Text)
    exam_neuro = db.Column(db.Text)
    exam_skin = db.Column(db.Text)

    # Cận lâm sàng
    orders = db.Column(db.JSON)
    result_summary = db.Column(db.Text)
    total_bilirubin = db.Column(db.Float)
    direct_bilirubin = db.Column(db.Float)
    alkaline_phosphotase = db.Column(db.Float)
    alamine_aminotransferase = db.Column(db.Float)
    aspartate_aminotransferase = db.Column(db.Float)
    total_proteins = db.Column(db.Float)
    albumin = db.Column(db.Float)
    albumin_globulin_ratio = db.Column(db.Float)

    # Chẩn đoán
    preliminary_diagnosis = db.Column(db.Text)
    confirmed_diagnosis = db.Column(db.Text)

    # Kế hoạch điều trị
    medications = db.Column(db.JSON)
    procedures = db.Column(db.Text)
    follow_up_instructions = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)

    # Ghi chú quá trình
    progress_note = db.Column(db.Text)

    # Tóm tắt xuất viện
    admission_date = db.Column(db.Date)
    discharge_date = db.Column(db.Date)
    discharge_diagnosis = db.Column(db.Text)
    treatment_outcome = db.Column(db.String(50))
    post_discharge_instructions = db.Column(db.Text)

    # Quan hệ
    patient = db.relationship("Patient", backref=db.backref("full_medical_records", lazy=True))
    doctor = db.relationship("User", backref=db.backref("full_records_created", lazy=True))
    department = db.relationship("Department", backref=db.backref("full_medical_records", lazy=True))

class SharedAccess(db.Model):
    __tablename__ = 'shared_access'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('full_medical_record.id'), nullable=False)
    shared_with = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    record = db.relationship('FullMedicalRecord', backref=db.backref('shared_users', lazy=True))
    user = db.relationship('User', backref=db.backref('shared_records', lazy=True))



class EmailVerificationToken(db.Model):
    __tablename__ = 'email_verification_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    token_type = db.Column(db.String(20), nullable=False)  # 'approval' hoặc 'confirmation'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('email_tokens', lazy=True))

    def is_expired(self):
        return datetime.utcnow() > self.expires_at
