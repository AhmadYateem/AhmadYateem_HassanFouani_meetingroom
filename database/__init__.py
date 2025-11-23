"""Database package exports."""

from database.connection import (
    MySQLConnectionPool,
    create_pool_from_env,
    get_connection,
)
from database.init import initialize_schema
from database.models import (
    User,
    Room,
    Booking,
    Review,
    AuditLog,
    create_user,
    get_user_by_email,
    list_rooms,
    create_room,
    check_booking_conflict,
    create_booking,
    create_review,
    add_audit_log,
    to_dict,
)

__all__ = [
    "MySQLConnectionPool",
    "create_pool_from_env",
    "get_connection",
    "initialize_schema",
    "User",
    "Room",
    "Booking",
    "Review",
    "AuditLog",
    "create_user",
    "get_user_by_email",
    "list_rooms",
    "create_room",
    "check_booking_conflict",
    "create_booking",
    "create_review",
    "add_audit_log",
    "to_dict",
]
