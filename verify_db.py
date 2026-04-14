from app import app, db
from sqlalchemy import text

with app.app_context():
    tables = ['dim_books', 'dim_borrower', 'dim_staff', 'fact_borrowings']
    for table in tables:
        print(f"\n--- {table} Schema ---")
        try:
            result = db.session.execute(text(f"DESCRIBE {table}")).fetchall()
            for row in result:
                field, type_, null, key, default, extra = row
                print(f"{field:<20} {type_:<20} | Null: {null:<4} | Key: {key:<4} | Default: {default}")
        except Exception as e:
            print(f"Error querying {table}: {e}")
