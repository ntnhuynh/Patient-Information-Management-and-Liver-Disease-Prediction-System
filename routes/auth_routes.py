from flask import Blueprint, request, jsonify, url_for, session, redirect
from models.models import User, Department, EmailVerificationToken
from utils.security import hash_password, verify_password
from extensions import db, mail
import random
from datetime import datetime, timedelta, timezone
import pytz
from flask import render_template
from flask_mail import Message
import re
from flask import current_app
import secrets

auth_bp = Blueprint("auth", __name__)


def is_strong_password(pw):
    return (
        len(pw) >= 8 and
        re.search(r"[A-Z]", pw) and
        re.search(r"[a-z]", pw) and
        re.search(r"\d", pw) and
        re.search(r"[^\w\s]", pw)
    )
def translate_role(role):
    translations = {
        "doctor": "Bác sĩ",
        "department head": "Trưởng khoa",
        "director": "Giám đốc",
    }
    return translations.get(role, role)  # nếu không có thì giữ nguyên

def send_approval_email_to_superior(superior_email, user):
    token = secrets.token_urlsafe(32)
    vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    expires = datetime.now(vietnam_tz) + timedelta(
        hours=current_app.config['APPROVAL_TOKEN_EXPIRY_HOURS']
    )

    token_entry = EmailVerificationToken(
        user_id=user.id,
        token=token,
        token_type='approval',
        expires_at=expires
    )
    db.session.add(token_entry)
    db.session.commit()

    approve_link = url_for('auth.approve_user', user_id=user.id, token=token, _external=True)
    department_name = "Không rõ"
    if user.khoa_id:
        department = Department.query.get(user.khoa_id)
        if department:
            department_name = department.name
    current_time = datetime.now(vietnam_tz).strftime("%H:%M:%S %d-%m-%Y")
    expires_at = expires.strftime("%H:%M:%S %d-%m-%Y")

    html_body = render_template(
        "email/approval_email.html",
        full_name=user.full_name,
        birth_date=user.birth_date.strftime('%d/%m/%Y') if user.birth_date else "",
        gender=user.gender,
        email=user.email,
        role=translate_role(user.role),
        department_name=department_name,
        approve_link=approve_link,
        timestamp=current_time,
        expires_at=expires_at
    )
    print("Đã render")
    print("superior_email:", superior_email)
    msg = Message("📩 Phê duyệt tài khoản mới", recipients=[superior_email])
    msg.html = html_body  # dùng HTML thay vì text
    try:
        mail.send(msg)
        print("✅ Mail phê duyệt đã được gửi.")
    except Exception as e:
        print("❌ Lỗi gửi mail:", str(e))
        

def send_verification_to_user(user, token):
    verify_link = url_for('auth.final_verify_user', user_id=user.id, token=token, _external=True)
    vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    current_time = datetime.now(vietnam_tz).strftime("%H:%M:%S %d-%m-%Y")

    # Dùng cấu hình thời hạn từ app.config
    expiry_hours = current_app.config['CONFIRMATION_TOKEN_EXPIRY_HOURS']
    expires_at = (datetime.now(vietnam_tz) + timedelta(hours=expiry_hours)).strftime("%H:%M:%S %d-%m-%Y")

    html_body = render_template(
        "email/user_verification_email.html",
        verify_link=verify_link,
        timestamp=current_time,
        expires_at=expires_at
    )
    print("[DEBUG] Creating Message with subject:", "📩 Phê duyệt tài khoản mới")
    msg = Message("Xác nhận tài khoản", recipients=[user.email])
    msg.html = html_body
    try:
        mail.send(msg)
        print("✅ Mail xác nhận đã được gửi.")
    except Exception as e:
        print("❌ Lỗi gửi mail xác nhận:", str(e))


@auth_bp.route("/register", methods=["POST"])
def register():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"msg": "Dữ liệu không hợp lệ"}), 400

    username = json_data.get("username")
    email = json_data.get("email")
    password = json_data.get("password")
    role = json_data.get("role")

    if not username or not email or not password or not role:
        return jsonify({"msg": "Thiếu thông tin bắt buộc"}), 400

    if role == "director":
        return jsonify({"msg": "Không được phép đăng ký vai trò giám đốc"}), 403

    if User.query.filter(User.username.ilike(username)).first():
        return jsonify({"msg": "Username đã tồn tại"}), 400

    if User.query.filter(User.email.ilike(email)).first():
        return jsonify({"msg": "Email đã được sử dụng"}), 400

    if not is_strong_password(password):
        return jsonify({
            "msg": "Mật khẩu phải có ít nhất 8 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt"
        }), 400

    # Xác định cấp trên
    superior = None
    if role == "doctor":
        khoa_id = json_data.get("khoa_id")
        if not khoa_id:
            return jsonify({"msg": "Bác sĩ cần chọn khoa"}), 400
        superior = User.query.filter_by(role="department head", khoa_id=khoa_id).first()
        if not superior:
            return jsonify({"msg": "Không tìm thấy trưởng khoa xác thực"}), 400
    elif role == "department head":
        superior = User.query.filter_by(role="director").first()
        if not superior:
            return jsonify({"msg": "Không tìm thấy giám đốc xác thực"}), 400

    # Kiểm tra ngày sinh
    birth_date_str = json_data.get("birth_date")
    if not birth_date_str:
        return jsonify({"msg": "Thiếu ngày sinh"}), 400
    try:
        birth_date = datetime.strptime(birth_date_str, '%d/%m/%Y').date()
    except ValueError:
        return jsonify({"msg": "Ngày sinh không hợp lệ. Định dạng đúng: dd/mm/yyyy"}), 400

    hashed_pw = hash_password(password)

    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        full_name=json_data.get("full_name"),
        gender=json_data.get("gender"),
        birth_date=birth_date,
        role=role,
        khoa_id=json_data.get("khoa_id"),
        created_by=superior.id if superior else None,
        is_verified_by_self=False,
        is_approved_by_superior=False
    )
    db.session.add(new_user)
    db.session.commit()
    if superior:
        try:
            send_approval_email_to_superior(superior.email, new_user)
            print("✅ Đã gọi hàm send_approval_email_to_superior")

        except Exception as e:
            print("❌ Khong gửi mail được:", str(e))

    return jsonify({"msg": "Đăng ký thành công. Vui lòng chờ cấp trên phê duyệt qua email"}), 201

@auth_bp.route("/approve/<int:user_id>/<token>", methods=["GET"])
def approve_user(user_id, token):
    user = User.query.get_or_404(user_id)

    token_entry = EmailVerificationToken.query.filter_by(
        user_id=user_id, token=token, token_type='approval'
    ).first()

    if not token_entry or token_entry.is_expired():
        return jsonify({"msg": "Token không hợp lệ hoặc đã hết hạn"}), 400

    if user.is_approved_by_superior or not user.is_active:
        return jsonify({"msg": "Tài khoản không thể xác thực."}), 400

    user.is_approved_by_superior = True
    db.session.delete(token_entry)

    # Thêm generate token và gửi mail xác thực
    verification_token = secrets.token_urlsafe(32)
    vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    expires = datetime.now(vietnam_tz) + timedelta(
        hours=current_app.config['CONFIRMATION_TOKEN_EXPIRY_HOURS']
    )

    existing_token = EmailVerificationToken.query.filter_by(
        user_id=user.id, token_type='confirmation'
    ).first()

    if existing_token and not existing_token.is_expired():
        return jsonify({"msg": "Đã gửi email xác thực trước đó. Vui lòng kiểm tra hộp thư."}), 200

    confirmation_token_entry = EmailVerificationToken(
        user_id=user.id,
        token=verification_token,
        token_type='confirmation',
        expires_at=expires
    )
    db.session.add(confirmation_token_entry)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"msg": "Lỗi máy chủ khi cập nhật trạng thái phê duyệt."}), 500

    # Gửi mail xác thực cho user
    try:
        send_verification_to_user(user, verification_token)
        print("✅ Đã gửi mail xác thực cho người dùng")
    except Exception as e:
        db.session.delete(confirmation_token_entry)
        db.session.commit()
        print("❌ Lỗi gửi mail xác thực cho user:", str(e))

    return render_template("approval_success.html"), 200

@auth_bp.route("/verify/<int:user_id>/<token>", methods=["GET"])
def final_verify_user(user_id, token):
    user = User.query.get_or_404(user_id)

    token_entry = EmailVerificationToken.query.filter_by(
        user_id=user_id,
        token=token,
        token_type='confirmation'
    ).first()

    if not token_entry:
        return jsonify({"msg": "❌ Token không hợp lệ"}), 400

    if token_entry.is_expired():
        try:
            db.session.delete(token_entry)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({"msg": "⏰ Token đã hết hạn"}), 400

    if user.is_verified_by_self:
        return jsonify({"msg": "✅ Tài khoản đã được xác thực trước đó."}), 200

    user.is_verified_by_self = True
    db.session.delete(token_entry)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Lỗi máy chủ khi xác minh tài khoản."}), 500

    return render_template("verification_success.html"), 200


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()

    if not username or not password:
        return jsonify({"msg": "Thiếu thông tin đăng nhập"}), 400
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"msg": "Sai thông tin đăng nhập"}), 401
    if not user.is_active:
        return jsonify({"msg": "Tài khoản đã bị khóa"}), 403
    if not user.is_approved_by_superior:
        return jsonify({"msg": "Tài khoản chưa được cấp trên phê duyệt"}), 403
    if not user.is_verified_by_self:
        return jsonify({"msg": "Tài khoản chưa được xác thực bởi bạn"}), 403

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role
    session["khoa_id"] = str(user.khoa_id)
    session["full_name"] = str(user.full_name)
    return jsonify({"msg": "Đăng nhập thành công", "redirect": url_for("app.admin_dashboard")}), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"msg": "Đăng xuất thành công"}), 200

@auth_bp.route("/profile", methods=["GET"])
def view_profile():
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user_id = session["user_id"]
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404

    user_data = {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "gender": user.gender,
        "birth_date": user.birth_date.strftime("%d/%m/%Y") if user.birth_date else None,
        "role": user.role
    }

    return jsonify(user_data), 200
@auth_bp.route("/update_profile", methods=["PUT"])
def update_profile():
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user_id = session["user_id"]
    user = User.query.get_or_404(user_id)

    data = request.get_json()
    user.full_name = data.get("full_name", user.full_name)
    user.gender = data.get("gender", user.gender)
    try:
        if data.get("birth_date"):
            user.birth_date = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"msg": "Ngày sinh không hợp lệ. Định dạng đúng là Y-M-D"}), 400

    db.session.commit()
    return jsonify({"msg": "Cập nhật thông tin thành công"})


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user_id = session["user_id"]
    user = User.query.get_or_404(user_id)

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"msg": "Thiếu mật khẩu cũ hoặc mới"}), 400

    if not verify_password(old_password, user.password_hash):
        return jsonify({"msg": "Mật khẩu cũ không chính xác"}), 400

    user.password_hash = hash_password(new_password)
    db.session.commit()

    return jsonify({"msg": "✅ Đổi mật khẩu thành công"})
@auth_bp.route('/count', methods=['GET'])
def count_users():
    total_users = User.query.count()
    return jsonify({'total_users': total_users})
