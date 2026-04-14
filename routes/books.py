from flask import Blueprint, request, jsonify, session
from database import db, DimBook, BorrowerSavedBook, BookAuthor, DimAuthor, BookCategory, DimCategory

books_bp = Blueprint('books', __name__)

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
            "tags": [c[0] for c in categories]
        })
    return jsonify(results), 200

@books_bp.route('/genres', methods=['GET'])
def get_genres():
    cats = db.session.query(DimCategory.category_name).order_by(DimCategory.category_name).all()
    return jsonify([c[0] for c in cats]), 200

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
