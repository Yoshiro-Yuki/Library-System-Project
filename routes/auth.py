from flask import Blueprint, request, jsonify, session
from database import db, DimBorrower, DimStaff
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    existing_user = db.session.query(DimBorrower).filter_by(email_address=email).first()
    if existing_user:
        return jsonify({"error": "An account with this email already exists."}), 409

    # Generate next borrower_id
    max_id_record = db.session.query(func.max(DimBorrower.borrower_id)).scalar()
    if max_id_record and max_id_record.startswith('BORR'):
        current_num = int(max_id_record[4:])
        next_id = f"BORR{current_num + 1:04d}"
    else:
        next_id = "BORR0001"

    borrower_account = username.lower().replace(" ", ".")
    hashed_password = generate_password_hash(password)

    new_borrower = DimBorrower(
        borrower_id=next_id,
        borrower_account=borrower_account,
        user_name=username,
        email_address=email,
        hashed_password=hashed_password
    )
    
    db.session.add(new_borrower)
    db.session.commit()

    session["user_id"] = new_borrower.borrower_id
    session["role"] = "borrower"

    return jsonify({
        "message": "Account created.",
        "role": "borrower",
        "username": username,
        "email": email
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    borrower = db.session.query(DimBorrower).filter(
        (DimBorrower.email_address == email) | (DimBorrower.borrower_account == email)
    ).first()
    if borrower and check_password_hash(borrower.hashed_password, password):
        session["user_id"] = borrower.borrower_id
        session["role"] = "borrower"
        return jsonify({
            "message": "Logged in.",
            "role": "borrower",
            "username": borrower.user_name,
            "email": borrower.email_address
        }), 200

    staff = db.session.query(DimStaff).filter(
        (DimStaff.email_address == email) | (DimStaff.staff_account == email)
    ).first()
    if staff and check_password_hash(staff.hashed_password, password):
        session["user_id"] = staff.staff_id
        session["role"] = "staff"
        return jsonify({
            "message": "Logged in.",
            "role": "staff",
            "username": staff.alias,
            "email": staff.email_address
        }), 200

    return jsonify({"error": "Invalid email or password."}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out."}), 200
