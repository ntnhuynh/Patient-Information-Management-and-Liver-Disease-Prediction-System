from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, hash_pw):
    return check_password_hash(hash_pw, password)
