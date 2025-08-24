from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from models.models import Department
from flask import make_response
from datetime import datetime, date
app = Blueprint("app", __name__)

@app.route("/")
def home():
    return render_template('login.html', page_type="login")

@app.route("/register")
def register():
    departments = Department.query.all()
    return render_template('register.html', departments=departments, page_type="register")

@app.route("/login")
def login():
    if "user_id" in session:
        session.clear()
        return render_template("login.html",page_type="login")
    elif "user_id" not in session:
        return render_template('login.html', page_type="login")
    return render_template('login.html', page_type="login")



@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    username = session.get("username")
    role = session.get("role")
    if role == "director":
        response = make_response(render_template("admin_dashboard.html", username=username, page_type="admin"))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
        response.headers["Pragma"] = "no-cache"
        return response
    elif role == "department head":
        khoa_id = session.get("khoa_id")
        user_id = session.get("user_id")
        response = make_response(render_template("department_dashboard.html", username=username, page_type="department_head", khoa_id = khoa_id, user_id = user_id))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
        response.headers["Pragma"] = "no-cache"
        return response
    elif role == "doctor":
        khoa_id = session.get("khoa_id")
        user_id = session.get("user_id")
        full_name = session.get("full_name")
        response = make_response(render_template("doctor_dashboard.html", username=username, page_type="doctor", khoa_id = khoa_id, user_id = user_id, full_name=full_name))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
        response.headers["Pragma"] = "no-cache"
        return response
    else:
        return redirect(url_for("app.login"))


@app.route("/profile/view")
def profile_view():
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    role = session.get("role")
    username = session.get("username")
    user_id = session.get("user_id")
    if role == "director":
        return render_template("profile_view.html", page_type="profile", username=username)
    elif role == "department head":
        return render_template("profile_view.html", page_type="profile_department", username=username)
    else:
        return render_template("profile_view.html", page_type="doctor", username=username, user_id=user_id)


@app.route("/profile/update")
def profile_update():
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    role = session.get("role")
    username = session.get("username")
    if role == "director":
        return render_template("profile_update.html", page_type="profile", username=username)
    elif role == "department head":
        return render_template("profile_update.html", page_type="profile_department", username=username)
    else:
        return render_template("profile_update.html", page_type="doctor", username=username)


@app.route("/change-password")
def change_password():
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    role = session.get("role")
    username = session.get("username")
    if role == "director":
        return render_template("change_password.html", page_type="change_password", username=username)
    elif role == "department head":
        return render_template("change_password.html", page_type="change_password_department", username=username)
    else:
        return render_template("change_password.html", page_type="doctor", username=username)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("app.login"))

@app.route("/create/department")
def create_department():
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    elif session.get("role") == "director":
        username = session.get("username")
        return render_template("create_department.html",username=username, page_type = "admin")
    else:
        session.clear()
        return render_template("login.html",page_type="login")

@app.route("/stats/khoa/<int:khoa_id>/view")
def stats_department_monthly(khoa_id):
    role = session.get("role")
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    elif role in ["director", "department head"]:
        username = session.get("username")
        if role == "director":
            return render_template("stats_department_monthly.html", khoa_id=khoa_id,username=username, current_year=datetime.now().year, page_type = "admin")
        else:
            return render_template("stats_department_monthly.html", khoa_id=khoa_id,username=username, current_year=datetime.now().year, page_type = "department_head")
    else:
        session.clear()
        return render_template("login.html", page_type="login")
    
@app.route("/departments/<int:khoa_id>/staff")
def stats_doctor(khoa_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    elif session.get("role") in ["director", "department head"]:
        username = session.get("username")
        return render_template("stats_doctor.html", khoa_id=khoa_id,username=username, page_type = "admin")
    else:
        session.clear()
        return render_template("login.html", page_type="login")

@app.route("/patients/<int:khoa_id>/staff")
def stats_patient(khoa_id):
    print("Session:", session)
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    elif session.get("role") in ["director", "department head"]:
        khoa_id_doctor = session.get("khoa_id")
        username = session.get("username")
        role = session.get("role")
        if role == "director":
            return render_template("patient_staff.html", khoa_id=khoa_id,username=username, page_type = "admin")
        else:
            if int(khoa_id_doctor) == khoa_id:
               return render_template("patient_staff.html", khoa_id=khoa_id,username=username, page_type = "department_head") 
            else:
                return redirect(url_for("app.login"))
    else:
        session.clear()
        return render_template("login.html", page_type="login")

@app.route("/create/patient")
def create_patient():
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    elif session.get("role") in ["department head", "doctor"]:
        return render_template("create_patient.html", page_type = "admin")
    else:
        session.clear()
        return render_template("login.html", page_type="login")

@app.route("/patients/<int:patient_id>/detail")
def patient_detail(patient_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    elif session.get("role") in ["director","department head", "doctor"]:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        user_id = session.get("user_id")
        role = session.get("role")
        if role == "director":
            return render_template("patient_detail.html", patient_id=patient_id,username=username, page_type = "admin")
        elif role == "department head":
            return render_template("patient_detail.html",khoa_id = int(khoa_id), patient_id=patient_id,username=username, page_type = "department_head") 
        else:
            return render_template("patient_detail.html",khoa_id = int(khoa_id), patient_id=patient_id,username=username, page_type = "doctor", user_id=user_id) 

    else:
        session.clear()
        return render_template("login.html", page_type="login")

@app.route("/medical-records/<int:patient_id>")
def add_records(patient_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    elif session.get("role") in ["department head"]:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        role = session.get("role")
        return render_template("add_records.html",khoa_id = int(khoa_id), patient_id=patient_id,username=username, page_type = "department_head_medical",  current_date=date.today().isoformat())
    elif session.get("role") in ["doctor"]:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        role = session.get("role")
        user_id = session.get("user_id")
        return render_template("add_records.html",khoa_id = int(khoa_id), patient_id=patient_id,username=username, page_type = "doctor",  current_date=date.today().isoformat(), user_id=user_id)
    else:
        session.clear()
        return render_template("login.html", page_type="login")

@app.route("/medical-records_detail/<int:record_id>")
def medical_records_detail(record_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    else:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        user_id = session.get("user_id")
        role = session.get("role")
        if role == "director":
            return render_template("medical_records_detail.html",record_id=record_id,username=username, page_type = "admin",  current_date=date.today().isoformat(), user_id=user_id) 
        elif role == "department head":
            return render_template("medical_records_detail.html",khoa_id = int(khoa_id),record_id=record_id,username=username, page_type = "department_head_list",  current_date=date.today().isoformat()) 
        else:
            return render_template("medical_records_detail.html",khoa_id = int(khoa_id),record_id=record_id,username=username, page_type = "doctor",  current_date=date.today().isoformat(), user_id=user_id) 
@app.route("/medical-records_detail/<int:record_id>/edit")
def medical_records_edit(record_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    else:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        role = session.get("role")
        user_id = session.get("user_id")
        if role == "department head":
            return render_template("medical_records_edit.html",khoa_id = int(khoa_id),record_id=record_id,username=username, page_type = "department_head",  current_date=date.today().isoformat(), user_id=user_id) 
        else:
            return render_template("medical_records_edit.html",khoa_id = int(khoa_id),record_id=record_id,username=username, page_type = "doctor",  current_date=date.today().isoformat(), user_id=user_id)
@app.route("/patients/<int:patient_id>/update")
def patient_edit(patient_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    else:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        role = session.get("role")
        user_id = session.get("user_id")
        if role == "department head":
            return render_template("patient_update.html",khoa_id = int(khoa_id),patient_id=patient_id,username=username, page_type = "department_head",  current_date=date.today().isoformat())
        else:
            return render_template("patient_update.html",khoa_id = int(khoa_id),patient_id=patient_id,username=username, page_type = "doctor",  current_date=date.today().isoformat(), user_id=user_id)

@app.route("/medical-records_detail/<int:record_id>/share")
def medical_share(record_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    else:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        role = session.get("role")
        user_id = session.get("user_id")
        if role == "department head":
            return render_template("medical_share.html",khoa_id = int(khoa_id),record_id=record_id,username=username, page_type = "department_head",  current_date=date.today().isoformat())
        else:
            return render_template("medical_share.html",khoa_id = int(khoa_id),record_id=record_id,username=username, page_type = "doctor",  current_date=date.today().isoformat(), user_id=user_id)

@app.route("/list_medical_share/<int:user_id>")
def list_medical_share(user_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    else:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        return render_template("list_medical_share.html",khoa_id = int(khoa_id),user_id=user_id,username=username, page_type = "department_head_list",  current_date=date.today().isoformat())


@app.route("/patients_by_doctor/<int:user_id>/staff")
def list_patients_by_doctor(user_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    else:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        full_name = session.get("full_name")
        return render_template("patients_by_doctor.html",khoa_id = int(khoa_id),user_id=user_id,username=username, page_type = "doctor",  current_date=date.today().isoformat(), full_name=full_name)

@app.route("/predict/<int:record_id>")
def predict(record_id):
    if "user_id" not in session:
        return redirect(url_for("app.login"))
    else:
        username = session.get("username")
        khoa_id = session.get("khoa_id")
        full_name = session.get("full_name")
        user_id = session.get("user_id")
        role = session.get("role")
        vaitro = ""
        if role == "department head":
            vaitro = "Trưởng khoa"
            return render_template("predict.html",khoa_id = int(khoa_id),user_id=user_id,username=username, page_type = "department_head_list",  current_date=date.today().isoformat(), full_name=full_name, record_id=record_id, vaitro=vaitro)
        else:
            vaitro = "Bác sĩ"
            return render_template("predict.html",khoa_id = int(khoa_id),user_id=user_id,username=username, page_type = "doctor",  current_date=date.today().isoformat(), full_name=full_name, record_id = record_id, vaitro=vaitro)