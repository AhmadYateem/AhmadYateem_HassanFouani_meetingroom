"""
Flask routes for the Reviews service using raw MySQL DAO.

Author: Hassan Fouani
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from database.connection import MySQLConnectionPool, get_connection
from services.reviews import dao
from utils.validators import validate_required_fields, validate_rating, validate_string_length
from utils.sanitizers import sanitize_string, sanitize_html
from utils.auth import get_current_user, moderator_required


bp = Blueprint("reviews", __name__)


def _error(message: str, code: int = 400):
    return jsonify({"error": message}), code


def _success(payload, code: int = 200):
    return jsonify(payload), code


@bp.route("/health", methods=["GET"])
def health():
    return _success({"status": "healthy", "service": "reviews"})


@bp.route("/api/reviews", methods=["GET"])
@jwt_required()
def get_all_reviews():
    """Get all reviews with optional pagination and filtering."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    room_id = request.args.get("room_id", type=int)
    
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        if room_id:
            reviews = dao.get_room_reviews(conn, room_id, include_hidden=False)
        else:
            # Get all reviews from the database
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT r.*, u.username, u.full_name
                FROM reviews r
                LEFT JOIN users u ON r.user_id = u.id
                WHERE r.is_hidden = FALSE
                ORDER BY r.created_at DESC
                LIMIT %s OFFSET %s
            """, (per_page, (page - 1) * per_page))
            reviews = cursor.fetchall()
            cursor.close()
    
    return _success({
        "data": reviews,
        "pagination": {
            "page": page,
            "per_page": per_page
        }
    })


@bp.route("/api/reviews", methods=["POST"])
@jwt_required()
def create_review_route():
    current_user = get_current_user()
    data = request.get_json() or {}
    
    required = ["room_id", "rating"]
    for key in required:
        if key not in data:
            return _error(f"Missing required field: {key}")
    
    rating = data["rating"]
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return _error("Rating must be an integer between 1 and 5")
    
    title = sanitize_string(data.get("title", "")) if data.get("title") else None
    comment = sanitize_html(data.get("comment", "")) if data.get("comment") else None
    pros = sanitize_string(data.get("pros", "")) if data.get("pros") else None
    cons = sanitize_string(data.get("cons", "")) if data.get("cons") else None

    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        review_id = dao.create_review(
            conn,
            user_id=current_user["user_id"],
            room_id=data["room_id"],
            booking_id=data.get("booking_id"),
            rating=rating,
            title=title,
            comment=comment,
            pros=pros,
            cons=cons,
        )
    return _success({"id": review_id, "message": "Review created"}, 201)


@bp.route("/api/reviews/<int:review_id>", methods=["GET"])
def get_review(review_id: int):
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        review = dao.get_review_by_id(conn, review_id)
    if not review:
        return _error("Review not found", 404)
    return _success(review)


@bp.route("/api/reviews/<int:review_id>", methods=["PUT"])
@jwt_required()
def update_review_route(review_id: int):
    current_user = get_current_user()
    data = request.get_json() or {}
    
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        review = dao.get_review_by_id(conn, review_id)
        if not review:
            return _error("Review not found", 404)
        
        if review["user_id"] != current_user["user_id"] and current_user["role"] not in ["admin", "moderator"]:
            return _error("Unauthorized to update this review", 403)
        
        allowed = {"rating", "title", "comment", "pros", "cons"}
        update_data = {}
        
        if "rating" in data:
            rating = data["rating"]
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return _error("Rating must be an integer between 1 and 5")
            update_data["rating"] = rating
        
        if "title" in data:
            update_data["title"] = sanitize_string(data["title"])
        if "comment" in data:
            update_data["comment"] = sanitize_html(data["comment"])
        if "pros" in data:
            update_data["pros"] = sanitize_string(data["pros"])
        if "cons" in data:
            update_data["cons"] = sanitize_string(data["cons"])
        
        if not update_data:
            return _error("No valid fields to update")
        
        updated = dao.update_review(conn, review_id, **update_data)
    
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Review updated"})


@bp.route("/api/reviews/<int:review_id>", methods=["DELETE"])
@jwt_required()
def delete_review_route(review_id: int):
    current_user = get_current_user()
    
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        review = dao.get_review_by_id(conn, review_id)
        if not review:
            return _error("Review not found", 404)
        
        if review["user_id"] != current_user["user_id"] and current_user["role"] not in ["admin", "moderator"]:
            return _error("Unauthorized to delete this review", 403)
        
        deleted = dao.delete_review(conn, review_id)
    
    if not deleted:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Review deleted"})


@bp.route("/api/reviews/room/<int:room_id>", methods=["GET"])
def room_reviews(room_id: int):
    include_hidden = request.args.get("include_hidden", "false").lower() == "true"
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        reviews = dao.get_room_reviews(conn, room_id, include_hidden=include_hidden)
    return _success(reviews)


@bp.route("/api/reviews/user/<int:user_id>", methods=["GET"])
@jwt_required()
def user_reviews(user_id: int):
    current_user = get_current_user()
    
    if current_user["user_id"] != user_id and current_user["role"] not in ["admin", "moderator"]:
        return _error("Unauthorized to view these reviews", 403)
    
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        reviews = dao.get_user_reviews(conn, user_id)
    return _success(reviews)


@bp.route("/api/reviews/<int:review_id>/flag", methods=["POST"])
@jwt_required()
def flag_review_route(review_id: int):
    current_user = get_current_user()
    data = request.get_json() or {}
    
    flag_reason = data.get("flag_reason")
    if not flag_reason:
        return _error("flag_reason is required")
    
    flag_reason = sanitize_string(flag_reason)

    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        updated = dao.flag_review(conn, review_id, flagged_by=current_user["user_id"], flag_reason=flag_reason)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Review flagged"})


@bp.route("/api/reviews/flagged", methods=["GET"])
@jwt_required()
@moderator_required
def flagged_reviews():
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        reviews = dao.get_flagged_reviews(conn)
    return _success(reviews)


@bp.route("/api/reviews/<int:review_id>/moderate", methods=["PUT"])
@jwt_required()
@moderator_required
def moderate_review_route(review_id: int):
    data = request.get_json() or {}
    is_hidden = data.get("is_hidden")
    hidden_reason = data.get("hidden_reason")
    if is_hidden is None:
        return _error("is_hidden is required")
    
    if hidden_reason:
        hidden_reason = sanitize_string(hidden_reason)

    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        updated = dao.moderate_review(conn, review_id, is_hidden=bool(is_hidden), hidden_reason=hidden_reason)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Review moderated"})


@bp.route("/api/reviews/<int:review_id>/helpful", methods=["POST"])
@jwt_required()
def mark_helpful(review_id: int):
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        updated = dao.increment_helpful(conn, review_id)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Marked helpful"})


@bp.route("/api/reviews/<int:review_id>/unhelpful", methods=["POST"])
@jwt_required()
def mark_unhelpful(review_id: int):
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        updated = dao.increment_unhelpful(conn, review_id)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Marked unhelpful"})


@bp.route("/api/reviews/room/<int:room_id>/stats", methods=["GET"])
def room_rating_stats(room_id: int):
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        stats = dao.get_room_average_rating(conn, room_id)
        distribution = dao.get_rating_distribution(conn, room_id)
    return _success({"stats": stats, "distribution": distribution})
