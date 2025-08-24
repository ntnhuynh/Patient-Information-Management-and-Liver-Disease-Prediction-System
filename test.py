# from app import app
# from extensions import mail
# from flask_mail import Message

# with app.app_context():
#     msg = Message("🔧 Test gửi mail", recipients=["nthientam0202@gmail.com"])
#     msg.body = "Test gửi mail thành công."
#     mail.send(msg)
#     print("✅ Đã gửi mail test.")
# import numpy as np
# print(np.__version__)
# print(np.array([1, 2, 3]) + 5)
import flask, flask_sqlalchemy, flask_mail, flask_jwt_extended
import numpy, joblib, sklearn

print("Flask:", flask.__version__)
print("Flask-SQLAlchemy:", flask_sqlalchemy.__version__)
print("Flask-Mail:", flask_mail.__version__)
print("Flask-JWT-Extended:", flask_jwt_extended.__version__)
print("Numpy:", numpy.__version__)
print("Joblib:", joblib.__version__)
print("Scikit-learn:", sklearn.__version__)
