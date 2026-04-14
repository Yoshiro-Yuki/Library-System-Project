from app import app
from database import db, DimStaff
from werkzeug.security import generate_password_hash

with app.app_context():
    # Update STAFF0001 password and get their email
    staff = DimStaff.query.filter_by(staff_id="STAFF0001").first()
    if staff:
        staff.hashed_password = generate_password_hash("staff123")
        db.session.commit()
        print(f"STAFF EMAIL: {staff.email_address}")
    else:
        print("STAFF0001 not found")
