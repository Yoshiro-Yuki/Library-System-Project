from flask import Blueprint, request, jsonify, session, current_app
from database import db, DimBook, BorrowerSavedBook, BookAuthor, DimAuthor, BookCategory, DimCategory
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os
import re
import uuid

books_bp = Blueprint('books', __name__)

# ====================================================================
# Allowed image extensions for cover uploads
# ====================================================================
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if the uploaded file has an allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@books_bp.route('/', methods=['GET'])
def get_all_books():
    all_books = db.session.query(DimBook).all()
    results = []
    for b in all_books:
        authors = db.session.query(DimAuthor.author_name).join(
            BookAuthor, DimAuthor.author_id == BookAuthor.author_id
        ).filter(BookAuthor.book_id == b.book_id).all()

        categories = db.session.query(DimCategory.category_name).join(
            BookCategory, DimCategory.category_id == BookCategory.category_id
        ).filter(BookCategory.book_id == b.book_id).all()

        results.append({
            "id": b.book_id,
            "book_id": b.book_id,
            "title": b.title,
            "subtitle": b.subtitle or "",
            "description": b.description or "",
            "thumbnail_url": b.thumbnail_url,
            "info_link": b.info_link,
            "average_rating": float(b.average_rating) if b.average_rating else 0.0,
            "author": ", ".join([a[0] for a in authors]) if authors else "Unknown",
            "genre": categories[0][0] if categories else "Uncategorized",
            "authors": [a[0] for a in authors],
            "categories": [c[0] for c in categories],
            "tags": [c[0] for c in categories],
            "copies_available": b.copies_available if b.copies_available is not None else 1,
            "publication_year": b.publication_year
        })
    return jsonify(results), 200

@books_bp.route('/genres', methods=['GET'])
def get_genres():
    cats = db.session.query(DimCategory.category_name).order_by(DimCategory.category_name).all()
    return jsonify([c[0] for c in cats]), 200

# ====================================================================
# ADD BOOK — Staff-only endpoint to add a new book to the catalog
# Accepts JSON (Content-Type: application/json) from the React frontend.
# Key fix: uses no_autoflush to prevent premature FK constraint errors
# when creating new author/category records alongside junction rows.
# ====================================================================
@books_bp.route('/add', methods=['POST'])
def add_book():
    # --- Auth check: only staff can add books ---
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized. Staff access required."}), 403

    # --- Extract fields from JSON body ---
    # Support both JSON and form-data for flexibility
    if request.is_json:
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        author = (data.get("author") or "").strip()
        isbn = (data.get("isbn") or "").strip()
        category = (data.get("category") or "").strip()
        year_str = str(data.get("publication_year") or "").strip()
        description = (data.get("description") or "").strip()
        copies_str = str(data.get("copies_available") or "").strip()
        cover_url = (data.get("cover_image_url") or "").strip()
    else:
        title = (request.form.get("title") or "").strip()
        author = (request.form.get("author") or "").strip()
        isbn = (request.form.get("isbn") or "").strip()
        category = (request.form.get("category") or "").strip()
        year_str = (request.form.get("publication_year") or "").strip()
        description = (request.form.get("description") or "").strip()
        copies_str = (request.form.get("copies_available") or "").strip()
        cover_url = ""

    # --- Server-side validation ---
    errors = {}

    # Required field checks
    if not title:
        errors["title"] = "Book title is required."
    if not author:
        errors["author"] = "Author name is required."
    if not category:
        errors["category"] = "Genre/Category is required."

    # Publication year: must be a valid 4-digit number
    publication_year = None
    if not year_str:
        errors["publication_year"] = "Publication year is required."
    else:
        try:
            publication_year = int(year_str)
            if publication_year < 1000 or publication_year > 9999:
                errors["publication_year"] = "Year must be a 4-digit number (e.g. 2024)."
        except ValueError:
            errors["publication_year"] = "Year must be a valid number."

    # Copies available: must be a positive integer
    copies_available = None
    if not copies_str:
        errors["copies_available"] = "Number of copies is required."
    else:
        try:
            copies_available = int(copies_str)
            if copies_available < 1:
                errors["copies_available"] = "Copies must be at least 1."
        except ValueError:
            errors["copies_available"] = "Copies must be a valid number."

    # ISBN format check (optional field, but validate if provided)
    isbn_clean = None
    if isbn:
        isbn_clean = isbn.replace("-", "").replace(" ", "")
        if not (re.match(r'^\d{13}$', isbn_clean) or re.match(r'^\d{9}[\dXx]$', isbn_clean)):
            errors["isbn"] = "ISBN must be a valid ISBN-10 or ISBN-13 format."
        else:
            # Check for duplicate ISBN in database
            existing_isbn = db.session.query(DimBook).filter(
                DimBook.isbn_13 == isbn_clean
            ).first()
            if existing_isbn:
                errors["isbn"] = f"A book with ISBN {isbn_clean} already exists."

    # If any validation errors, return them all at once
    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 400

    # === DATABASE INSERTS (wrapped in no_autoflush to avoid premature FK errors) ===
    try:
        with db.session.no_autoflush:
            # --- Generate next sequential book_id (BK####) ---
            max_id_record = db.session.query(func.max(DimBook.book_id)).filter(
                DimBook.book_id.like("BK%")
            ).scalar()

            if max_id_record and max_id_record.startswith("BK"):
                try:
                    current_num = int(max_id_record[2:])
                except ValueError:
                    current_num = 0
                next_id = f"BK{current_num + 1:04d}"
            else:
                next_id = "BK0001"

            # --- Step 1: Create or reuse DimAuthor record ---
            existing_author = db.session.query(DimAuthor).filter(
                func.lower(DimAuthor.author_name) == author.lower()
            ).first()

            if existing_author:
                author_id = existing_author.author_id
            else:
                max_auth = db.session.query(func.max(DimAuthor.author_id)).filter(
                    DimAuthor.author_id.like("AUTH%")
                ).scalar()
                if max_auth and max_auth.startswith("AUTH"):
                    try:
                        auth_num = int(max_auth[4:])
                    except ValueError:
                        auth_num = 0
                    author_id = f"AUTH{auth_num + 1:04d}"
                else:
                    author_id = "AUTH0001"
                new_author = DimAuthor(author_id=author_id, author_name=author)
                db.session.add(new_author)
                # Flush the author first so FK is satisfied
                db.session.flush()

            # --- Step 2: Create or reuse DimCategory record ---
            existing_cat = db.session.query(DimCategory).filter(
                func.lower(DimCategory.category_name) == category.lower()
            ).first()

            if existing_cat:
                category_id = existing_cat.category_id
            else:
                max_cat = db.session.query(func.max(DimCategory.category_id)).filter(
                    DimCategory.category_id.like("CAT%")
                ).scalar()
                if max_cat and max_cat.startswith("CAT"):
                    try:
                        cat_num = int(max_cat[4:])
                    except ValueError:
                        cat_num = 0
                    category_id = f"CAT{cat_num + 1:04d}"
                else:
                    category_id = "CAT0001"
                new_cat = DimCategory(category_id=category_id, category_name=category)
                db.session.add(new_cat)
                # Flush the category so FK is satisfied
                db.session.flush()

            # --- Step 3: Create the new book record ---
            thumbnail_url = cover_url if cover_url else None
            new_book = DimBook(
                book_id=next_id,
                isbn_13=isbn_clean,
                title=title,
                subtitle=None,
                description=description or None,
                page_count=None,
                language="en",
                thumbnail_url=thumbnail_url,
                info_link=None,
                copies_available=copies_available,
                publication_year=publication_year
            )
            db.session.add(new_book)
            db.session.flush()

            # --- Step 4: Create junction records (FK parents now exist) ---
            book_author = BookAuthor(book_id=next_id, author_id=author_id)
            db.session.add(book_author)

            book_cat = BookCategory(book_id=next_id, category_id=category_id)
            db.session.add(book_cat)

        # --- Commit everything ---
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({
        "message": f"Book '{title}' added successfully.",
        "book_id": next_id,
        "title": title,
        "author": author,
        "category": category,
        "thumbnail_url": thumbnail_url
    }), 201


@books_bp.route('/save', methods=['POST'])
def save_book():
    if session.get("role") != "borrower":
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Missing book_id"}), 400
        
    borrower_id = session.get("user_id")
    
    existing = db.session.query(BorrowerSavedBook).filter_by(
        borrower_id=borrower_id, book_id=book_id
    ).first()
    
    if existing:
        return jsonify({"error": "Already saved."}), 409
        
    new_saved = BorrowerSavedBook(borrower_id=borrower_id, book_id=book_id)
    db.session.add(new_saved)
    db.session.commit()
    
    return jsonify({"message": "Book saved."}), 201

@books_bp.route('/unsave', methods=['DELETE'])
def unsave_book():
    if session.get("role") != "borrower":
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Missing book_id"}), 400
        
    borrower_id = session.get("user_id")
    
    saved = db.session.query(BorrowerSavedBook).filter_by(
        borrower_id=borrower_id, book_id=book_id
    ).first()
    
    if saved:
        db.session.delete(saved)
        db.session.commit()
        
    return jsonify({"message": "Book unsaved."}), 200

@books_bp.route('/saved', methods=['GET'])
def get_saved_books():
    if session.get("role") != "borrower":
        return jsonify({"error": "Unauthorized"}), 403
        
    borrower_id = session.get("user_id")
    
    joined_query = db.session.query(DimBook).join(
        BorrowerSavedBook, DimBook.book_id == BorrowerSavedBook.book_id
    ).filter(BorrowerSavedBook.borrower_id == borrower_id).all()
    
    results = []
    for b in joined_query:
        authors = db.session.query(DimAuthor.author_name).join(
            BookAuthor, DimAuthor.author_id == BookAuthor.author_id
        ).filter(BookAuthor.book_id == b.book_id).all()
        
        categories = db.session.query(DimCategory.category_name).join(
            BookCategory, DimCategory.category_id == BookCategory.category_id
        ).filter(BookCategory.book_id == b.book_id).all()
        
        results.append({
            "id": b.book_id,
            "book_id": b.book_id,
            "title": b.title,
            "subtitle": b.subtitle,
            "thumbnail_url": b.thumbnail_url,
            "info_link": b.info_link,
            "average_rating": float(b.average_rating) if b.average_rating else 0.0,
            "author": ", ".join([a[0] for a in authors]) if authors else "Unknown",
            "genre": categories[0][0] if categories else "Uncategorized",
            "authors": [a[0] for a in authors],
            "categories": [c[0] for c in categories]
        })
        
    return jsonify(results), 200

