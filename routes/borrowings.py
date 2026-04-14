from flask import Blueprint, request, jsonify, session
from database import db, FactBorrowing, DimBook, DimDate, DimBorrower, DimStaff
from sqlalchemy import func
from sqlalchemy.orm import aliased
from datetime import datetime

borrowings_bp = Blueprint('borrowings', __name__)

@borrowings_bp.route('/request', methods=['POST'])
def request_borrowing():
    if session.get("role") != "borrower":
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Missing book_id"}), 400
        
    borrower_id = session.get("user_id")
    
    existing = db.session.query(FactBorrowing).filter(
        FactBorrowing.borrower_id == borrower_id,
        FactBorrowing.book_id == book_id,
        FactBorrowing.status.in_(['pending', 'borrowed'])
    ).first()
    
    if existing:
        return jsonify({"error": "You already have an active request for this book."}), 409
        
    today_yymmdd = datetime.now().strftime("%y%m%d")
    borrowing_prefix = f"BORR{today_yymmdd}"
    branch_id = "BRCH0001"
    
    pattern = f"{borrowing_prefix}%{branch_id}"
    max_record = db.session.query(func.max(FactBorrowing.borrowing_id)).filter(
        FactBorrowing.borrowing_id.like(pattern)
    ).scalar()
    
    if max_record:
        try:
            curr_seq = int(max_record[10:13])
        except ValueError:
            curr_seq = 0
    else:
        curr_seq = 0
        
    seq = f"{curr_seq + 1:03d}"
    new_borrowing_id = f"{borrowing_prefix}{seq}{branch_id}"
    
    new_borrowing = FactBorrowing(
        borrowing_id=new_borrowing_id,
        borrower_id=borrower_id,
        staff_id="STAFF0001",
        book_id=book_id,
        branch_id=branch_id,
        borrow_date_id=None,
        return_date_id=None,
        status="pending"
    )
    
    db.session.add(new_borrowing)
    db.session.commit()
    
    return jsonify({
        "message": "Borrow request submitted.",
        "borrowing_id": new_borrowing_id
    }), 201

@borrowings_bp.route('/cancel', methods=['DELETE'])
def cancel_borrowing():
    role = session.get("role")
    if role not in ["borrower", "staff"]:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    borrowing_id = data.get("borrowing_id")
    if not borrowing_id:
        return jsonify({"error": "Missing borrowing_id"}), 400
        
    if role == "borrower":
        borrower_id = session.get("user_id")
        borrowing = db.session.query(FactBorrowing).filter_by(
            borrowing_id=borrowing_id,
            borrower_id=borrower_id
        ).first()
    else:
        borrowing = db.session.query(FactBorrowing).filter_by(
            borrowing_id=borrowing_id
        ).first()
    
    if not borrowing:
        return jsonify({"error": "Borrowing not found."}), 404
        
    if borrowing.status != "pending":
        return jsonify({"error": "Only pending requests can be cancelled."}), 400
        
    db.session.delete(borrowing)
    db.session.commit()
    
    return jsonify({"message": "Request cancelled."}), 200

@borrowings_bp.route('/pending', methods=['GET'])
def get_pending_borrowings():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
        
    query = db.session.query(FactBorrowing, DimBook, DimBorrower).join(
        DimBook, FactBorrowing.book_id == DimBook.book_id
    ).join(
        DimBorrower, FactBorrowing.borrower_id == DimBorrower.borrower_id
    ).filter(
        FactBorrowing.status == 'pending'
    ).all()
    
    results = []
    for fb, b, db_borrower in query:
        results.append({
            "borrowing_id": fb.borrowing_id,
            "book_id": fb.book_id,
            "title": b.title,
            "borrower_id": fb.borrower_id,
            "borrower_name": db_borrower.user_name,
            "borrower_email": db_borrower.email_address,
            "branch_id": fb.branch_id
        })
        
    return jsonify(results), 200

@borrowings_bp.route('/approve', methods=['PATCH'])
def approve_borrowing():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    borrowing_id = data.get("borrowing_id")
    if not borrowing_id:
        return jsonify({"error": "Missing borrowing_id"}), 400
        
    borrowing = db.session.query(FactBorrowing).filter_by(
        borrowing_id=borrowing_id
    ).first()
    
    if not borrowing:
        return jsonify({"error": "Borrowing not found."}), 404
        
    if borrowing.status != "pending":
        return jsonify({"error": "Only pending requests can be approved."}), 400
        
    borrowing.status = 'borrowed'
    borrowing.staff_id = session.get("user_id")
    borrowing.borrow_date_id = int(datetime.now().strftime("%Y%m%d"))
    
    db.session.commit()
    
    return jsonify({"message": "Request approved."}), 200

@borrowings_bp.route('/all-borrowed', methods=['GET'])
def get_all_borrowed():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
        
    query = db.session.query(FactBorrowing, DimBook, DimBorrower, DimDate, DimStaff).join(
        DimBook, FactBorrowing.book_id == DimBook.book_id
    ).join(
        DimBorrower, FactBorrowing.borrower_id == DimBorrower.borrower_id
    ).outerjoin(
        DimDate, FactBorrowing.borrow_date_id == DimDate.date_id
    ).outerjoin(
        DimStaff, FactBorrowing.staff_id == DimStaff.staff_id
    ).filter(
        FactBorrowing.status == 'borrowed'
    ).all()
    
    results = []
    for fb, b, db_borrower, d, s in query:
        results.append({
            "borrowing_id": fb.borrowing_id,
            "book_id": fb.book_id,
            "title": b.title,
            "borrower_id": fb.borrower_id,
            "borrower_name": db_borrower.user_name,
            "borrower_email": db_borrower.email_address,
            "borrow_date": d.full_date if d else None,
            "approved_by": s.alias if s else None
        })
        
    return jsonify(results), 200

@borrowings_bp.route('/return', methods=['PATCH'])
def return_borrowing():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json() or {}
    borrowing_id = data.get("borrowing_id")
    if not borrowing_id:
        return jsonify({"error": "Missing borrowing_id"}), 400
        
    borrowing = db.session.query(FactBorrowing).filter_by(
        borrowing_id=borrowing_id
    ).first()
    
    if not borrowing:
        return jsonify({"error": "Borrowing not found."}), 404
        
    if borrowing.status != "borrowed":
        return jsonify({"error": "Only borrowed books can be marked as returned."}), 400
        
    borrowing.status = 'returned'
    borrowing.return_date_id = int(datetime.now().strftime("%Y%m%d"))
    
    db.session.commit()
    
    return jsonify({"message": "Book marked as returned."}), 200

@borrowings_bp.route('/all-returned', methods=['GET'])
def get_all_returned():
    if session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403
        
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 100))
    
    BorrowDate = aliased(DimDate)
    ReturnDate = aliased(DimDate)
    
    query = db.session.query(FactBorrowing, DimBook, DimBorrower, BorrowDate, ReturnDate).join(
        DimBook, FactBorrowing.book_id == DimBook.book_id
    ).join(
        DimBorrower, FactBorrowing.borrower_id == DimBorrower.borrower_id
    ).outerjoin(
        BorrowDate, FactBorrowing.borrow_date_id == BorrowDate.date_id
    ).outerjoin(
        ReturnDate, FactBorrowing.return_date_id == ReturnDate.date_id
    ).filter(
        FactBorrowing.status == 'returned'
    ).order_by(
        FactBorrowing.return_date_id.desc(),
        FactBorrowing.borrowing_id.desc()
    ).offset(offset).limit(limit).all()
    
    results = []
    for fb, b, db_borrower, b_date, r_date in query:
        results.append({
            "borrowing_id": fb.borrowing_id,
            "book_id": fb.book_id,
            "title": b.title,
            "borrower_name": db_borrower.user_name,
            "borrower_email": db_borrower.email_address,
            "borrow_date": b_date.full_date if b_date else None,
            "return_date": r_date.full_date if r_date else None,
            "rating": float(fb.rating) if fb.rating else None
        })
        
    return jsonify(results), 200

@borrowings_bp.route('/my', methods=['GET'])
def get_my_borrowings():
    if session.get("role") != "borrower":
        return jsonify({"error": "Unauthorized"}), 403
        
    borrower_id = session.get("user_id")
    
    query = db.session.query(FactBorrowing, DimBook).join(
        DimBook, FactBorrowing.book_id == DimBook.book_id
    ).filter(
        FactBorrowing.borrower_id == borrower_id,
        FactBorrowing.status == 'pending'
    ).all()
    
    results = []
    for fb, b in query:
        results.append({
            "borrowing_id": fb.borrowing_id,
            "book_id": fb.book_id,
            "title": b.title,
            "thumbnail_url": b.thumbnail_url,
            "status": fb.status,
            "borrow_date_id": fb.borrow_date_id
        })
        
    return jsonify(results), 200

@borrowings_bp.route('/borrowed', methods=['GET'])
def get_borrowed():
    if session.get("role") != "borrower":
        return jsonify({"error": "Unauthorized"}), 403
        
    borrower_id = session.get("user_id")
    
    query = db.session.query(FactBorrowing, DimBook, DimDate).join(
        DimBook, FactBorrowing.book_id == DimBook.book_id
    ).outerjoin(
        DimDate, FactBorrowing.borrow_date_id == DimDate.date_id
    ).filter(
        FactBorrowing.borrower_id == borrower_id,
        FactBorrowing.status == 'borrowed'
    ).all()
    
    results = []
    for fb, b, d in query:
        results.append({
            "borrowing_id": fb.borrowing_id,
            "book_id": fb.book_id,
            "title": b.title,
            "thumbnail_url": b.thumbnail_url,
            "borrow_date": d.full_date if d else None,
            "rating": float(fb.rating) if fb.rating else None
        })
        
    return jsonify(results), 200

@borrowings_bp.route('/rate', methods=['PATCH'])
def rate_borrowing():
    if session.get("role") != "borrower":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    borrowing_id = data.get("borrowing_id")
    rating = data.get("rating")

    if not borrowing_id:
        return jsonify({"error": "Missing borrowing_id"}), 400

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be between 1 and 5."}), 400

    borrower_id = session.get("user_id")
    borrowing = db.session.query(FactBorrowing).filter_by(
        borrowing_id=borrowing_id
    ).first()

    if not borrowing:
        return jsonify({"error": "Borrowing not found."}), 404

    if borrowing.borrower_id != borrower_id:
        return jsonify({"error": "Unauthorized"}), 403

    if borrowing.status != 'borrowed':
        return jsonify({"error": "You can only rate a book that has been approved."}), 400

    if borrowing.rating is not None:
        return jsonify({"error": "You have already rated this book."}), 409

    borrowing.rating = float(rating)
    db.session.commit()

    return jsonify({"message": "Rating submitted.", "rating": rating}), 200
