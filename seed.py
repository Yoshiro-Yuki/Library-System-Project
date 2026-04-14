from app import app, db
from database import DimStaff
from werkzeug.security import generate_password_hash

def seed_database():
    with app.app_context():
        # Ensure tables like borrower_saved_books exist
        db.create_all()
        
        # Check if dim_staff is empty
        staff_count = db.session.query(DimStaff).count()
        if staff_count == 0:
            print("Seeding dim_staff with initial accounts...")
            
            staff1 = DimStaff(
                staff_id="STAFF0061",
                staff_account="staff.admin",
                alias="Staff Admin",
                position="Administrator",
                hashed_password=generate_password_hash("librarian123"),
                email_address="STAFF0061@bibliotheca.edu.com",
                branch_id="BRCH0001"
            )
            
            staff2 = DimStaff(
                staff_id="STAFF0062",
                staff_account="librarian.two",
                alias="Librarian Two",
                position="Librarian",
                hashed_password=generate_password_hash("librarian123"),
                email_address="STAFF0062@bibliotheca.edu.com",
                branch_id="BRCH0001"
            )
            
            db.session.add(staff1)
            db.session.add(staff2)
            db.session.commit()
            print("Successfully seeded dim_staff.")
        else:
            print(f"dim_staff already contains {staff_count} rows. Skipping seed.")

if __name__ == "__main__":
    seed_database()
