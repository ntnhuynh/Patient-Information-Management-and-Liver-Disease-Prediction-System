#app.py
from flask import Flask
from config import Config
from extensions import db, mail
from routes.auth_routes import auth_bp
from routes.department_routes import department_bp
from routes.patient_routes import patient_bp
from routes.medical_record_routes import medical_record_bp
from flask_migrate import Migrate
from routes.stats_routes import stats_bp
from routes.home_routes import app as home_bp
from datetime import timedelta
from flask import session



app = Flask(__name__)

app.config.from_object(Config)
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)

@app.context_processor
def inject_session():
    return dict(session=session)



app.config['APPROVAL_TOKEN_EXPIRY_HOURS']
app.config['CONFIRMATION_TOKEN_EXPIRY_HOURS']

# Đăng ký các blueprint
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(department_bp, url_prefix="/department")
app.register_blueprint(patient_bp, url_prefix="/patient")
app.register_blueprint(stats_bp, url_prefix="/stats")
app.register_blueprint(medical_record_bp, url_prefix="/medical-record")
app.register_blueprint(home_bp)