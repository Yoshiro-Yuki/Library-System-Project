"""
Migration script: Add copies_available and publication_year columns to dim_books.
SQLAlchemy's db.create_all() only creates NEW tables, not alter existing ones.
This script manually adds the missing columns.
"""
import os
import pymysql
import ssl
from dotenv import load_dotenv

load_dotenv()

# --- Build SSL context using the isrgroot.pem certificate ---
ssl_ctx = ssl.create_default_context(cafile=os.environ.get("DB_SSL_CA", "isrgroot.pem"))

# --- Connect to TiDB ---
conn = pymysql.connect(
    host=os.environ.get("DB_HOST"),
    port=int(os.environ.get("DB_PORT", 4000)),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    database=os.environ.get("DB_NAME", "library_db"),
    ssl=ssl_ctx
)

cursor = conn.cursor()

# --- Add copies_available column if missing ---
try:
    cursor.execute("ALTER TABLE dim_books ADD COLUMN copies_available INT DEFAULT 1;")
    conn.commit()
    print("✓ Added 'copies_available' column to dim_books")
except pymysql.err.OperationalError as e:
    if e.args[0] == 1060:  # Duplicate column name
        print("· 'copies_available' column already exists, skipping")
    else:
        raise

# --- Add publication_year column if missing ---
try:
    cursor.execute("ALTER TABLE dim_books ADD COLUMN publication_year INT;")
    conn.commit()
    print("✓ Added 'publication_year' column to dim_books")
except pymysql.err.OperationalError as e:
    if e.args[0] == 1060:  # Duplicate column name
        print("· 'publication_year' column already exists, skipping")
    else:
        raise

cursor.close()
conn.close()
print("\nMigration complete!")
