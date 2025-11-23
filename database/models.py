"""
Lightweight data access layer using mysql-connector.
Provides dataclass representations and helper functions for common queries.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence

from database.connection import MySQLConnectionPool, get_connection


def _row_to_dict(cursor, row) -> Dict[str, Any]:
    """Convert a cursor row to a dict using column names."""
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


@dataclass
class User:
    id: Optional[int]
    username: str
    email: str
    password_hash: str
    full_name: str
    role: str = "user"
    is_active: bool = True
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_row(cursor, row) -> "User":
        data = _row_to_dict(cursor, row)
        return User(**data)


@dataclass
class Room:
    id: Optional[int]
    name: str
    capacity: int
    floor: Optional[int] = None
    building: Optional[str] = None
    location: Optional[str] = None
    equipment: Optional[Any] = None
    amenities: Optional[Any] = None
    status: str = "available"
    hourly_rate: Optional[float] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_row(cursor, row) -> "Room":
        data = _row_to_dict(cursor, row)
        return Room(**data)


@dataclass
class Booking:
    id: Optional[int]
    user_id: int
    room_id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    status: str = "confirmed"
    attendees: Optional[int] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_row(cursor, row) -> "Booking":
        data = _row_to_dict(cursor, row)
        return Booking(**data)


@dataclass
class Review:
    id: Optional[int]
    user_id: int
    room_id: int
    booking_id: Optional[int]
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    is_flagged: bool = False
    flag_reason: Optional[str] = None
    flagged_by: Optional[int] = None
    flagged_at: Optional[datetime] = None
    is_hidden: bool = False
    hidden_reason: Optional[str] = None
    helpful_count: int = 0
    unhelpful_count: int = 0
    edited_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_row(cursor, row) -> "Review":
        data = _row_to_dict(cursor, row)
        return Review(**data)


@dataclass
class AuditLog:
    id: Optional[int]
    user_id: Optional[int]
    service: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    old_values: Optional[Any] = None
    new_values: Optional[Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_row(cursor, row) -> "AuditLog":
        data = _row_to_dict(cursor, row)
        return AuditLog(**data)


# --- User queries ---

def create_user(pool: MySQLConnectionPool, user: User) -> int:
    query = """
    INSERT INTO users (username, email, password_hash, full_name, role, is_active, last_login,
                       failed_login_attempts, locked_until)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        user.username,
        user.email,
        user.password_hash,
        user.full_name,
        user.role,
        user.is_active,
        user.last_login,
        user.failed_login_attempts,
        user.locked_until,
    )
    with get_connection(pool) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        user_id = cur.lastrowid
        cur.close()
    return user_id


def get_user_by_email(pool: MySQLConnectionPool, email: str) -> Optional[User]:
    query = "SELECT * FROM users WHERE email = %s"
    with get_connection(pool) as conn:
        cur = conn.cursor()
        cur.execute(query, (email,))
        row = cur.fetchone()
        result = User.from_row(cur, row) if row else None
        cur.close()
    return result


# --- Room queries ---

def list_rooms(pool: MySQLConnectionPool, status: Optional[str] = None) -> List[Room]:
    query = "SELECT * FROM rooms"
    params: Sequence[Any] = ()
    if status:
        query += " WHERE status = %s"
        params = (status,)
    with get_connection(pool) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        results = [Room.from_row(cur, row) for row in rows]
        cur.close()
    return results


def create_room(pool: MySQLConnectionPool, room: Room) -> int:
    query = """
    INSERT INTO rooms (name, capacity, floor, building, location, equipment, amenities,
                       status, hourly_rate, image_url)
    VALUES (%s, %s, %s, %s, %s, CAST(%s AS JSON), CAST(%s AS JSON), %s, %s, %s)
    """
    params = (
        room.name,
        room.capacity,
        room.floor,
        room.building,
        room.location,
        room.equipment or "[]",
        room.amenities or "[]",
        room.status,
        room.hourly_rate,
        room.image_url,
    )
    with get_connection(pool) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        room_id = cur.lastrowid
        cur.close()
    return room_id


# --- Booking queries ---

def check_booking_conflict(
    pool: MySQLConnectionPool,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[int] = None,
) -> bool:
    query = """
    SELECT 1 FROM bookings
    WHERE room_id = %s
      AND status IN ('pending', 'confirmed')
      AND (
           (start_time <= %s AND end_time > %s)
        OR (start_time < %s AND end_time >= %s)
        OR (start_time >= %s AND end_time <= %s)
      )
    """
    params: List[Any] = [room_id, start_time, start_time, end_time, end_time, start_time, end_time]
    if exclude_booking_id:
        query += " AND id <> %s"
        params.append(exclude_booking_id)
    with get_connection(pool) as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        conflict = cur.fetchone() is not None
        cur.close()
    return conflict


def create_booking(pool: MySQLConnectionPool, booking: Booking) -> int:
    query = """
    INSERT INTO bookings (
        user_id, room_id, title, description, start_time, end_time, status, attendees,
        is_recurring, recurrence_pattern, recurrence_end_date, cancellation_reason,
        cancelled_at, cancelled_by
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        booking.user_id,
        booking.room_id,
        booking.title,
        booking.description,
        booking.start_time,
        booking.end_time,
        booking.status,
        booking.attendees,
        booking.is_recurring,
        booking.recurrence_pattern,
        booking.recurrence_end_date,
        booking.cancellation_reason,
        booking.cancelled_at,
        booking.cancelled_by,
    )
    with get_connection(pool) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        booking_id = cur.lastrowid
        cur.close()
    return booking_id


# --- Review queries ---

def create_review(pool: MySQLConnectionPool, review: Review) -> int:
    query = """
    INSERT INTO reviews (
        user_id, room_id, booking_id, rating, title, comment, pros, cons,
        is_flagged, flag_reason, flagged_by, flagged_at,
        is_hidden, hidden_reason, helpful_count, unhelpful_count, edited_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        review.user_id,
        review.room_id,
        review.booking_id,
        review.rating,
        review.title,
        review.comment,
        review.pros,
        review.cons,
        review.is_flagged,
        review.flag_reason,
        review.flagged_by,
        review.flagged_at,
        review.is_hidden,
        review.hidden_reason,
        review.helpful_count,
        review.unhelpful_count,
        review.edited_at,
    )
    with get_connection(pool) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        review_id = cur.lastrowid
        cur.close()
    return review_id


# --- Audit log queries ---

def add_audit_log(pool: MySQLConnectionPool, log: AuditLog) -> int:
    query = """
    INSERT INTO audit_logs (
        user_id, service, action, resource_type, resource_id,
        old_values, new_values, ip_address, user_agent,
        success, error_message
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        log.user_id,
        log.service,
        log.action,
        log.resource_type,
        log.resource_id,
        log.old_values,
        log.new_values,
        log.ip_address,
        log.user_agent,
        log.success,
        log.error_message,
    )
    with get_connection(pool) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        log_id = cur.lastrowid
        cur.close()
    return log_id


# Utility to convert dataclasses to dictionaries

def to_dict(instance) -> Dict[str, Any]:
    return asdict(instance)
