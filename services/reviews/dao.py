"""
Reviews DAO with raw MySQL queries.

Author: Hassan Fouani
"""

from typing import Any, Dict, List, Optional, Sequence

from mysql.connector.connection import MySQLConnection


def create_review(
    connection: MySQLConnection,
    user_id: int,
    room_id: int,
    booking_id: Optional[int],
    rating: int,
    title: Optional[str],
    comment: Optional[str],
    pros: Optional[str],
    cons: Optional[str],
) -> int:
    cursor = connection.cursor()
    query = """
        INSERT INTO reviews (
            user_id, room_id, booking_id, rating, title, comment, pros, cons,
            is_flagged, is_hidden, helpful_count, unhelpful_count
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE, FALSE, 0, 0)
    """
    cursor.execute(
        query,
        (user_id, room_id, booking_id, rating, title, comment, pros, cons),
    )
    review_id = cursor.lastrowid
    cursor.close()
    return review_id


def get_review_by_id(connection: MySQLConnection, review_id: int) -> Optional[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT r.*, u.username, rm.name AS room_name
        FROM reviews r
        LEFT JOIN users u ON r.user_id = u.id
        LEFT JOIN rooms rm ON r.room_id = rm.id
        WHERE r.id = %s
    """
    cursor.execute(query, (review_id,))
    row = cursor.fetchone()
    cursor.close()
    return row


def get_room_reviews(connection: MySQLConnection, room_id: int, include_hidden: bool = False) -> List[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM reviews WHERE room_id = %s"
    params: List[Any] = [room_id]
    if not include_hidden:
        query += " AND is_hidden = FALSE"
    query += " ORDER BY created_at DESC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_user_reviews(connection: MySQLConnection, user_id: int) -> List[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reviews WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def update_review(connection: MySQLConnection, review_id: int, **kwargs) -> bool:
    if not kwargs:
        return False

    fields = []
    params: List[Any] = []
    for key, value in kwargs.items():
        fields.append(f"{key} = %s")
        params.append(value)

    params.append(review_id)
    sql = f"UPDATE reviews SET {', '.join(fields)} WHERE id = %s"
    cursor = connection.cursor()
    cursor.execute(sql, tuple(params))
    updated = cursor.rowcount > 0
    cursor.close()
    return updated


def delete_review(connection: MySQLConnection, review_id: int) -> bool:
    cursor = connection.cursor()
    cursor.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
    deleted = cursor.rowcount > 0
    cursor.close()
    return deleted


def flag_review(connection: MySQLConnection, review_id: int, flagged_by: int, flag_reason: str) -> bool:
    cursor = connection.cursor()
    query = """
        UPDATE reviews
        SET is_flagged = TRUE, flag_reason = %s, flagged_by = %s, flagged_at = NOW()
        WHERE id = %s
    """
    cursor.execute(query, (flag_reason, flagged_by, review_id))
    updated = cursor.rowcount > 0
    cursor.close()
    return updated


def get_flagged_reviews(connection: MySQLConnection) -> List[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reviews WHERE is_flagged = TRUE ORDER BY flagged_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    return rows


def moderate_review(connection: MySQLConnection, review_id: int, is_hidden: bool, hidden_reason: Optional[str]) -> bool:
    cursor = connection.cursor()
    query = """
        UPDATE reviews
        SET is_hidden = %s, hidden_reason = %s, is_flagged = FALSE, flag_reason = NULL, flagged_by = NULL, flagged_at = NULL
        WHERE id = %s
    """
    cursor.execute(query, (is_hidden, hidden_reason, review_id))
    updated = cursor.rowcount > 0
    cursor.close()
    return updated


def increment_helpful(connection: MySQLConnection, review_id: int) -> bool:
    cursor = connection.cursor()
    cursor.execute("UPDATE reviews SET helpful_count = helpful_count + 1 WHERE id = %s", (review_id,))
    updated = cursor.rowcount > 0
    cursor.close()
    return updated


def increment_unhelpful(connection: MySQLConnection, review_id: int) -> bool:
    cursor = connection.cursor()
    cursor.execute("UPDATE reviews SET unhelpful_count = unhelpful_count + 1 WHERE id = %s", (review_id,))
    updated = cursor.rowcount > 0
    cursor.close()
    return updated


def get_room_average_rating(connection: MySQLConnection, room_id: int) -> Optional[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT 
            AVG(rating) AS average_rating,
            COUNT(*) AS total_reviews,
            SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) AS five_star,
            SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) AS four_star,
            SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) AS three_star,
            SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) AS two_star,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS one_star
        FROM reviews
        WHERE room_id = %s AND is_hidden = FALSE
    """
    cursor.execute(query, (room_id,))
    result = cursor.fetchone()
    cursor.close()
    return result


def get_rating_distribution(connection: MySQLConnection, room_id: int) -> List[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT rating, COUNT(*) AS count
        FROM reviews
        WHERE room_id = %s AND is_hidden = FALSE
        GROUP BY rating
    """
    cursor.execute(query, (room_id,))
    rows = cursor.fetchall()
    cursor.close()
    return rows
