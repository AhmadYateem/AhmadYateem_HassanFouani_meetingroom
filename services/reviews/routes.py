"""
Flask routes for the Reviews service using raw MySQL DAO.
"""

from flask import Blueprint, jsonify, request

from database.connection import MySQLConnectionPool, get_connection
from services.reviews import dao


bp = Blueprint("reviews", __name__)


def _error(message: str, code: int = 400):
    return jsonify({"error": message}), code


def _success(payload, code: int = 200):
    return jsonify(payload), code


@bp.route("/health", methods=["GET"])
def health():
    return _success({"status": "healthy", "service": "reviews"})


@bp.route("/api/reviews", methods=["POST"])
def create_review_route():
    data = request.get_json() or {}
    required = ["user_id", "room_id", "rating"]
    for key in required:
        if key not in data:
            return _error(f"Missing required field: {key}")

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        review_id = dao.create_review(
            conn,
            user_id=data["user_id"],
            room_id=data["room_id"],
            booking_id=data.get("booking_id"),
            rating=data["rating"],
            title=data.get("title"),
            comment=data.get("comment"),
            pros=data.get("pros"),
            cons=data.get("cons"),
        )
    return _success({"id": review_id, "message": "Review created"}, 201)


@bp.route("/api/reviews/<int:review_id>", methods=["GET"])
def get_review(review_id: int):
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        review = dao.get_review_by_id(conn, review_id)
    if not review:
        return _error("Review not found", 404)
    return _success(review)


@bp.route("/api/reviews/<int:review_id>", methods=["PUT"])
def update_review_route(review_id: int):
    data = request.get_json() or {}
    allowed = {"rating", "title", "comment", "pros", "cons"}
    update_data = {k: v for k, v in data.items() if k in allowed}
    if not update_data:
        return _error("No valid fields to update")

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        updated = dao.update_review(conn, review_id, **update_data)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Review updated"})


@bp.route("/api/reviews/<int:review_id>", methods=["DELETE"])
def delete_review_route(review_id: int):
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        deleted = dao.delete_review(conn, review_id)
    if not deleted:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Review deleted"})


@bp.route("/api/reviews/room/<int:room_id>", methods=["GET"])
def room_reviews(room_id: int):
    include_hidden = request.args.get("include_hidden", "false").lower() == "true"
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        reviews = dao.get_room_reviews(conn, room_id, include_hidden=include_hidden)
    return _success(reviews)


@bp.route("/api/reviews/user/<int:user_id>", methods=["GET"])
def user_reviews(user_id: int):
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        reviews = dao.get_user_reviews(conn, user_id)
    return _success(reviews)


@bp.route("/api/reviews/<int:review_id>/flag", methods=["POST"])
def flag_review_route(review_id: int):
    data = request.get_json() or {}
    flagged_by = data.get("flagged_by")
    flag_reason = data.get("flag_reason")
    if not flagged_by or not flag_reason:
        return _error("flagged_by and flag_reason are required")

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        updated = dao.flag_review(conn, review_id, flagged_by=flagged_by, flag_reason=flag_reason)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Review flagged"})


@bp.route("/api/reviews/flagged", methods=["GET"])
def flagged_reviews():
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        reviews = dao.get_flagged_reviews(conn)
    return _success(reviews)


@bp.route("/api/reviews/<int:review_id>/moderate", methods=["PUT"])
def moderate_review_route(review_id: int):
    data = request.get_json() or {}
    is_hidden = data.get("is_hidden")
    hidden_reason = data.get("hidden_reason")
    if is_hidden is None:
        return _error("is_hidden is required")

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        updated = dao.moderate_review(conn, review_id, is_hidden=bool(is_hidden), hidden_reason=hidden_reason)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Review moderated"})


@bp.route("/api/reviews/<int:review_id>/helpful", methods=["POST"])
def mark_helpful(review_id: int):
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        updated = dao.increment_helpful(conn, review_id)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Marked helpful"})


@bp.route("/api/reviews/<int:review_id>/unhelpful", methods=["POST"])
def mark_unhelpful(review_id: int):
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        updated = dao.increment_unhelpful(conn, review_id)
    if not updated:
        return _error("Review not found", 404)
    return _success({"id": review_id, "message": "Marked unhelpful"})


@bp.route("/api/reviews/room/<int:room_id>/stats", methods=["GET"])
def room_rating_stats(room_id: int):
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        stats = dao.get_room_average_rating(conn, room_id)
        distribution = dao.get_rating_distribution(conn, room_id)
    return _success({"stats": stats, "distribution": distribution})
