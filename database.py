from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, Text, Numeric, Date, Boolean, TIMESTAMP, ForeignKey, func, Enum
from sqlalchemy.dialects.mysql import TINYINT

db = SQLAlchemy()

class DimBook(db.Model):
    __tablename__ = 'dim_books'
    __table_args__ = {"extend_existing": True}

    book_id = Column(String(20), primary_key=True)
    isbn_13 = Column(String(13))
    title = Column(String(500), nullable=False)
    subtitle = Column(String(500))
    description = Column(Text)
    page_count = Column(Integer)
    language = Column(String(10))
    thumbnail_url = Column(Text)
    info_link = Column(Text)
    average_rating = Column(Numeric(3, 2), server_default="0.00")
    copies_available = Column(Integer, server_default="1")
    publication_year = Column(Integer)

class DimAuthor(db.Model):
    __tablename__ = 'dim_authors'
    __table_args__ = {"extend_existing": True}

    author_id = Column(String(20), primary_key=True)
    author_name = Column(String(255), nullable=False)

class DimCategory(db.Model):
    __tablename__ = 'dim_categories'
    __table_args__ = {"extend_existing": True}

    category_id = Column(String(20), primary_key=True)
    category_name = Column(String(255), nullable=False)

class BookAuthor(db.Model):
    __tablename__ = 'book_authors'
    __table_args__ = {"extend_existing": True}

    book_id = Column(String(20), ForeignKey('dim_books.book_id'), primary_key=True)
    author_id = Column(String(20), ForeignKey('dim_authors.author_id'), primary_key=True)

class BookCategory(db.Model):
    __tablename__ = 'book_categories'
    __table_args__ = {"extend_existing": True}

    book_id = Column(String(20), ForeignKey('dim_books.book_id'), primary_key=True)
    category_id = Column(String(20), ForeignKey('dim_categories.category_id'), primary_key=True)

class DimBranch(db.Model):
    __tablename__ = 'dim_branch'
    __table_args__ = {"extend_existing": True}

    branch_id = Column(String(10), primary_key=True)
    branch_name = Column(String(100), nullable=False)
    address = Column(Text)
    region = Column(String(50))
    phone_number = Column(String(20))

class DimDate(db.Model):
    __tablename__ = 'dim_date'
    __table_args__ = {"extend_existing": True}

    date_id = Column(Integer, primary_key=True)
    full_date = Column(Date, nullable=False)
    day = Column(Integer)
    month = Column(Integer)
    year = Column(Integer)
    quarter = Column(Integer)
    day_of_week = Column(String(10))
    is_weekend = Column(TINYINT(1))
    is_holiday = Column(TINYINT(1), server_default="0")

class DimBorrower(db.Model):
    __tablename__ = 'dim_borrower'
    __table_args__ = {"extend_existing": True}

    borrower_id = Column(String(10), primary_key=True)
    borrower_account = Column(String(50), nullable=False, unique=True)
    user_name = Column(String(100), nullable=False)
    email_address = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class DimStaff(db.Model):
    __tablename__ = 'dim_staff'
    __table_args__ = {"extend_existing": True}

    staff_id = Column(String(10), primary_key=True)
    staff_account = Column(String(50), nullable=False, unique=True)
    alias = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email_address = Column(String(100))
    hire_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    branch_id = Column(String(10), ForeignKey('dim_branch.branch_id'))

class FactBorrowing(db.Model):
    __tablename__ = 'fact_borrowings'
    __table_args__ = {"extend_existing": True}

    borrowing_id = Column(String(30), primary_key=True)
    borrower_id = Column(String(10), ForeignKey('dim_borrower.borrower_id'), nullable=False)
    staff_id = Column(String(10), ForeignKey('dim_staff.staff_id'), nullable=False)
    book_id = Column(String(20), ForeignKey('dim_books.book_id'), nullable=False)
    branch_id = Column(String(10), ForeignKey('dim_branch.branch_id'), nullable=False)
    borrow_date_id = Column(Integer, ForeignKey('dim_date.date_id'), nullable=True)
    return_date_id = Column(Integer, ForeignKey('dim_date.date_id'), nullable=True)
    rating = Column(Numeric(3, 1))
    status = Column(Enum('pending', 'borrowed', 'returned'), nullable=False, server_default='pending')

class BorrowerSavedBook(db.Model):
    __tablename__ = 'borrower_saved_books'
    
    borrower_id = Column(String(10), ForeignKey('dim_borrower.borrower_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    book_id = Column(String(20), ForeignKey('dim_books.book_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    saved_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
