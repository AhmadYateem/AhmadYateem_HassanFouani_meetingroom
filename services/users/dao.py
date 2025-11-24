"""
Data Access Object for Users Service.
Handles all MySQL database operations using raw SQL queries.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any


def create_user(connection, username: str, email: str, password_hash: str, 
                full_name: str, role: str = 'user') -> int:
    """
    Create a new user.

    Args:
        connection: MySQL connection
        username: Unique username
        email: User email
        password_hash: Hashed password
        full_name: User's full name
        role: User role

    Returns:
        User ID of created user
    """
    cursor = connection.cursor()
    query = """
        INSERT INTO users (username, email, password_hash, full_name, role, 
                          is_active, failed_login_attempts, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, TRUE, 0, NOW(), NOW())
    """
    cursor.execute(query, (username, email, password_hash, full_name, role))
    connection.commit()
    user_id = cursor.lastrowid
    cursor.close()
    return user_id


def get_user_by_id(connection, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user by ID.

    Args:
        connection: MySQL connection
        user_id: User ID

    Returns:
        User dictionary or None
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT id, username, email, password_hash, full_name, role, is_active,
               last_login, failed_login_attempts, locked_until, created_at, updated_at
        FROM users
        WHERE id = %s
    """
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user


def get_user_by_username(connection, username: str) -> Optional[Dict[str, Any]]:
    """
    Get user by username.

    Args:
        connection: MySQL connection
        username: Username

    Returns:
        User dictionary or None
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT id, username, email, password_hash, full_name, role, is_active,
               last_login, failed_login_attempts, locked_until, created_at, updated_at
        FROM users
        WHERE username = %s
    """
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()
    return user


def get_user_by_email(connection, email: str) -> Optional[Dict[str, Any]]:
    """
    Get user by email.

    Args:
        connection: MySQL connection
        email: Email address

    Returns:
        User dictionary or None
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT id, username, email, password_hash, full_name, role, is_active,
               last_login, failed_login_attempts, locked_until, created_at, updated_at
        FROM users
        WHERE email = %s
    """
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    return user


def get_user_by_username_or_email(connection, username_or_email: str) -> Optional[Dict[str, Any]]:
    """
    Get user by username or email.

    Args:
        connection: MySQL connection
        username_or_email: Username or email

    Returns:
        User dictionary or None
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT id, username, email, password_hash, full_name, role, is_active,
               last_login, failed_login_attempts, locked_until, created_at, updated_at
        FROM users
        WHERE username = %s OR email = %s
    """
    cursor.execute(query, (username_or_email, username_or_email))
    user = cursor.fetchone()
    cursor.close()
    return user


def get_all_users(connection, limit: int = 20, offset: int = 0, 
                  role: Optional[str] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """
    Get all users with pagination and filters.

    Args:
        connection: MySQL connection
        limit: Number of records
        offset: Starting position
        role: Filter by role
        is_active: Filter by active status

    Returns:
        List of user dictionaries
    """
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT id, username, email, full_name, role, is_active,
               last_login, created_at, updated_at
        FROM users
        WHERE 1=1
    """
    params = []
    
    if role is not None:
        query += " AND role = %s"
        params.append(role)
    
    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)
    
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cursor.execute(query, tuple(params))
    users = cursor.fetchall()
    cursor.close()
    return users


def count_users(connection, role: Optional[str] = None, is_active: Optional[bool] = None) -> int:
    """
    Count total users with filters.

    Args:
        connection: MySQL connection
        role: Filter by role
        is_active: Filter by active status

    Returns:
        Total user count
    """
    cursor = connection.cursor()
    
    query = "SELECT COUNT(*) FROM users WHERE 1=1"
    params = []
    
    if role is not None:
        query += " AND role = %s"
        params.append(role)
    
    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)
    
    cursor.execute(query, tuple(params))
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def update_user(connection, user_id: int, **kwargs) -> bool:
    """
    Update user fields.

    Args:
        connection: MySQL connection
        user_id: User ID
        **kwargs: Fields to update (email, full_name, password_hash, is_active, role)

    Returns:
        True if updated, False otherwise
    """
    if not kwargs:
        return False
    
    cursor = connection.cursor()
    
    allowed_fields = ['email', 'full_name', 'password_hash', 'is_active', 'role']
    updates = []
    params = []
    
    for field, value in kwargs.items():
        if field in allowed_fields:
            updates.append(f"{field} = %s")
            params.append(value)
    
    if not updates:
        cursor.close()
        return False
    
    updates.append("updated_at = NOW()")
    params.append(user_id)
    
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
    cursor.execute(query, tuple(params))
    connection.commit()
    
    affected_rows = cursor.rowcount
    cursor.close()
    return affected_rows > 0


def delete_user(connection, user_id: int) -> bool:
    """
    Delete a user.

    Args:
        connection: MySQL connection
        user_id: User ID

    Returns:
        True if deleted, False otherwise
    """
    cursor = connection.cursor()
    query = "DELETE FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    connection.commit()
    
    affected_rows = cursor.rowcount
    cursor.close()
    return affected_rows > 0


def increment_failed_login(connection, user_id: int) -> None:
    """
    Increment failed login attempts.

    Args:
        connection: MySQL connection
        user_id: User ID
    """
    cursor = connection.cursor()
    query = """
        UPDATE users 
        SET failed_login_attempts = failed_login_attempts + 1,
            updated_at = NOW()
        WHERE id = %s
    """
    cursor.execute(query, (user_id,))
    connection.commit()
    cursor.close()


def lock_account(connection, user_id: int, locked_until: datetime) -> None:
    """
    Lock user account until specified time.

    Args:
        connection: MySQL connection
        user_id: User ID
        locked_until: Lock expiration datetime
    """
    cursor = connection.cursor()
    query = """
        UPDATE users 
        SET locked_until = %s,
            updated_at = NOW()
        WHERE id = %s
    """
    cursor.execute(query, (locked_until, user_id))
    connection.commit()
    cursor.close()


def reset_failed_login(connection, user_id: int) -> None:
    """
    Reset failed login attempts to 0.

    Args:
        connection: MySQL connection
        user_id: User ID
    """
    cursor = connection.cursor()
    query = """
        UPDATE users 
        SET failed_login_attempts = 0,
            locked_until = NULL,
            last_login = NOW(),
            updated_at = NOW()
        WHERE id = %s
    """
    cursor.execute(query, (user_id,))
    connection.commit()
    cursor.close()


def get_user_bookings(connection, user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get user bookings with room details (JOIN query).

    Args:
        connection: MySQL connection
        user_id: User ID
        limit: Number of records
        offset: Starting position

    Returns:
        List of booking dictionaries with room details
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT 
            b.id, b.title, b.description, b.start_time, b.end_time, 
            b.status, b.attendees, b.created_at,
            r.id as room_id, r.name as room_name, r.capacity as room_capacity,
            r.floor as room_floor, r.building as room_building
        FROM bookings b
        INNER JOIN rooms r ON b.room_id = r.id
        WHERE b.user_id = %s
        ORDER BY b.start_time DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, (user_id, limit, offset))
    bookings = cursor.fetchall()
    cursor.close()
    return bookings


def count_user_bookings(connection, user_id: int) -> int:
    """
    Count total bookings for a user.

    Args:
        connection: MySQL connection
        user_id: User ID

    Returns:
        Total booking count
    """
    cursor = connection.cursor()
    query = "SELECT COUNT(*) FROM bookings WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    return count
