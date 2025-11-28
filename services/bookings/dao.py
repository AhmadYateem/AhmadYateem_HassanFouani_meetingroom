"""
Data Access Object for Bookings Service.
Handles all MySQL database operations with conflict detection.

Author: Ahmad Yateem
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any


def create_booking(connection, user_id: int, room_id: int, title: str, 
                   description: str, start_time: datetime, end_time: datetime,
                   attendees: int, is_recurring: bool = False, 
                   recurrence_pattern: str = None, recurrence_end_date: datetime = None) -> int:
    """
    Create a new booking.

    Args:
        connection: MySQL connection
        user_id: User ID
        room_id: Room ID
        title: Booking title
        description: Booking description
        start_time: Start datetime
        end_time: End datetime
        attendees: Number of attendees
        is_recurring: Whether booking is recurring
        recurrence_pattern: Recurrence pattern (daily, weekly, monthly)
        recurrence_end_date: End date for recurring bookings

    Returns:
        Booking ID
    """
    cursor = connection.cursor()
    query = """
        INSERT INTO bookings (user_id, room_id, title, description, start_time, 
                             end_time, status, attendees, is_recurring, 
                             recurrence_pattern, recurrence_end_date, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'confirmed', %s, %s, %s, %s, NOW(), NOW())
    """
    cursor.execute(query, (user_id, room_id, title, description, start_time, 
                          end_time, attendees, is_recurring, recurrence_pattern, 
                          recurrence_end_date))
    connection.commit()
    booking_id = cursor.lastrowid
    cursor.close()
    return booking_id


def get_booking_by_id(connection, booking_id: int) -> Optional[Dict[str, Any]]:
    """
    Get booking by ID with user and room details.

    Args:
        connection: MySQL connection
        booking_id: Booking ID

    Returns:
        Booking dictionary with joined data or None
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT 
            b.id, b.user_id, b.room_id, b.title, b.description,
            b.start_time, b.end_time, b.status, b.attendees,
            b.is_recurring, b.recurrence_pattern, b.recurrence_end_date,
            b.cancellation_reason, b.cancelled_at, b.cancelled_by,
            b.created_at, b.updated_at,
            u.username, u.email, u.full_name,
            r.name as room_name, r.capacity as room_capacity,
            r.floor as room_floor, r.building as room_building
        FROM bookings b
        INNER JOIN users u ON b.user_id = u.id
        INNER JOIN rooms r ON b.room_id = r.id
        WHERE b.id = %s
    """
    cursor.execute(query, (booking_id,))
    booking = cursor.fetchone()
    cursor.close()
    return booking


def get_all_bookings(connection, limit: int = 20, offset: int = 0,
                     room_id: Optional[int] = None, user_id: Optional[int] = None,
                     status: Optional[str] = None, start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Get all bookings with filters.

    Args:
        connection: MySQL connection
        limit: Number of records
        offset: Starting position
        room_id: Filter by room
        user_id: Filter by user
        status: Filter by status
        start_date: Filter by start date
        end_date: Filter by end date

    Returns:
        List of booking dictionaries
    """
    cursor = connection.cursor(dictionary=True)
    
    query = """
        SELECT 
            b.id, b.user_id, b.room_id, b.title, b.description,
            b.start_time, b.end_time, b.status, b.attendees,
            b.created_at, b.updated_at,
            u.username, u.full_name,
            r.name as room_name, r.floor as room_floor, r.building as room_building
        FROM bookings b
        INNER JOIN users u ON b.user_id = u.id
        INNER JOIN rooms r ON b.room_id = r.id
        WHERE 1=1
    """
    params = []
    
    if room_id is not None:
        query += " AND b.room_id = %s"
        params.append(room_id)
    
    if user_id is not None:
        query += " AND b.user_id = %s"
        params.append(user_id)
    
    if status is not None:
        query += " AND b.status = %s"
        params.append(status)
    
    if start_date is not None:
        query += " AND b.start_time >= %s"
        params.append(start_date)
    
    if end_date is not None:
        query += " AND b.end_time <= %s"
        params.append(end_date)
    
    query += " ORDER BY b.start_time DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cursor.execute(query, tuple(params))
    bookings = cursor.fetchall()
    cursor.close()
    return bookings


def count_bookings(connection, room_id: Optional[int] = None, 
                   user_id: Optional[int] = None, status: Optional[str] = None,
                   start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None) -> int:
    """
    Count bookings with filters.

    Args:
        connection: MySQL connection
        room_id: Filter by room
        user_id: Filter by user
        status: Filter by status
        start_date: Filter by start date
        end_date: Filter by end date

    Returns:
        Total booking count
    """
    cursor = connection.cursor()
    
    query = "SELECT COUNT(*) FROM bookings WHERE 1=1"
    params = []
    
    if room_id is not None:
        query += " AND room_id = %s"
        params.append(room_id)
    
    if user_id is not None:
        query += " AND user_id = %s"
        params.append(user_id)
    
    if status is not None:
        query += " AND status = %s"
        params.append(status)
    
    if start_date is not None:
        query += " AND start_time >= %s"
        params.append(start_date)
    
    if end_date is not None:
        query += " AND end_time <= %s"
        params.append(end_date)
    
    cursor.execute(query, tuple(params))
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def get_user_bookings(connection, user_id: int, limit: int = 20, 
                      offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get user's bookings.

    Args:
        connection: MySQL connection
        user_id: User ID
        limit: Number of records
        offset: Starting position

    Returns:
        List of booking dictionaries
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


def update_booking(connection, booking_id: int, **kwargs) -> bool:
    """
    Update booking fields.

    Args:
        connection: MySQL connection
        booking_id: Booking ID
        **kwargs: Fields to update

    Returns:
        True if updated
    """
    if not kwargs:
        return False
    
    cursor = connection.cursor()
    
    allowed_fields = ['title', 'description', 'start_time', 'end_time', 
                     'attendees', 'status']
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
    params.append(booking_id)
    
    query = f"UPDATE bookings SET {', '.join(updates)} WHERE id = %s"
    cursor.execute(query, tuple(params))
    connection.commit()
    
    affected_rows = cursor.rowcount
    cursor.close()
    return affected_rows > 0


def cancel_booking(connection, booking_id: int, cancelled_by: int, 
                   cancellation_reason: str = None) -> bool:
    """
    Cancel a booking.

    Args:
        connection: MySQL connection
        booking_id: Booking ID
        cancelled_by: User ID who cancelled
        cancellation_reason: Reason for cancellation

    Returns:
        True if cancelled
    """
    cursor = connection.cursor()
    query = """
        UPDATE bookings 
        SET status = 'cancelled',
            cancelled_by = %s,
            cancellation_reason = %s,
            cancelled_at = NOW(),
            updated_at = NOW()
        WHERE id = %s
    """
    cursor.execute(query, (cancelled_by, cancellation_reason, booking_id))
    connection.commit()
    
    affected_rows = cursor.rowcount
    cursor.close()
    return affected_rows > 0


def delete_booking(connection, booking_id: int) -> bool:
    """
    Delete a booking.

    Args:
        connection: MySQL connection
        booking_id: Booking ID

    Returns:
        True if deleted
    """
    cursor = connection.cursor()
    query = "DELETE FROM bookings WHERE id = %s"
    cursor.execute(query, (booking_id,))
    connection.commit()
    
    affected_rows = cursor.rowcount
    cursor.close()
    return affected_rows > 0


def check_availability(connection, room_id: int, start_time: datetime, 
                       end_time: datetime, exclude_booking_id: int = None) -> bool:
    """
    Check if room is available for given time slot.

    Args:
        connection: MySQL connection
        room_id: Room ID
        start_time: Start datetime
        end_time: End datetime
        exclude_booking_id: Booking ID to exclude from check

    Returns:
        True if available
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT COUNT(*) as conflict_count
        FROM bookings
        WHERE room_id = %s
        AND status IN ('pending', 'confirmed')
        AND (
            (start_time <= %s AND end_time > %s) OR
            (start_time < %s AND end_time >= %s) OR
            (start_time >= %s AND end_time <= %s)
        )
    """
    params = [room_id, start_time, start_time, end_time, end_time, start_time, end_time]
    
    if exclude_booking_id:
        query += " AND id != %s"
        params.append(exclude_booking_id)
    
    cursor.execute(query, tuple(params))
    result = cursor.fetchone()
    cursor.close()
    return result['conflict_count'] == 0


def get_conflicts(connection, room_id: int, start_time: datetime, 
                  end_time: datetime) -> List[Dict[str, Any]]:
    """
    Get overlapping bookings for a room.

    Args:
        connection: MySQL connection
        room_id: Room ID
        start_time: Start datetime
        end_time: End datetime

    Returns:
        List of conflicting bookings
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT 
            b.id, b.title, b.start_time, b.end_time, b.status,
            u.username, u.full_name
        FROM bookings b
        INNER JOIN users u ON b.user_id = u.id
        WHERE b.room_id = %s
        AND b.status IN ('pending', 'confirmed')
        AND (
            (b.start_time <= %s AND b.end_time > %s) OR
            (b.start_time < %s AND b.end_time >= %s) OR
            (b.start_time >= %s AND b.end_time <= %s)
        )
        ORDER BY b.start_time
    """
    cursor.execute(query, (room_id, start_time, start_time, end_time, 
                          end_time, start_time, end_time))
    conflicts = cursor.fetchall()
    cursor.close()
    return conflicts


def create_recurring_bookings(connection, user_id: int, room_id: int, 
                              title: str, description: str, start_time: datetime,
                              end_time: datetime, attendees: int, 
                              pattern: str, end_date: datetime) -> List[int]:
    """
    Create recurring bookings.

    Args:
        connection: MySQL connection
        user_id: User ID
        room_id: Room ID
        title: Booking title
        description: Booking description
        start_time: Start datetime
        end_time: End datetime
        attendees: Number of attendees
        pattern: Recurrence pattern (daily, weekly, monthly)
        end_date: End date for recurrence

    Returns:
        List of created booking IDs
    """
    booking_ids = []
    current_start = start_time
    current_end = end_time
    duration = end_time - start_time
    
    cursor = connection.cursor()
    
    while current_start <= end_date:
        if check_availability(connection, room_id, current_start, current_end):
            query = """
                INSERT INTO bookings (user_id, room_id, title, description, 
                                     start_time, end_time, status, attendees,
                                     is_recurring, recurrence_pattern, 
                                     recurrence_end_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'confirmed', %s, TRUE, %s, %s, NOW(), NOW())
            """
            cursor.execute(query, (user_id, room_id, title, description,
                                  current_start, current_end, attendees, 
                                  pattern, end_date))
            booking_ids.append(cursor.lastrowid)
        
        if pattern == 'daily':
            current_start += timedelta(days=1)
        elif pattern == 'weekly':
            current_start += timedelta(weeks=1)
        elif pattern == 'monthly':
            current_start += timedelta(days=30)
        
        current_end = current_start + duration
    
    connection.commit()
    cursor.close()
    return booking_ids


def get_availability_matrix(connection, room_id: int, date: datetime) -> List[Dict[str, Any]]:
    """
    Get hourly availability matrix for a room on a specific date.

    Args:
        connection: MySQL connection
        room_id: Room ID
        date: Date to check

    Returns:
        List of hourly slots with availability status
    """
    cursor = connection.cursor(dictionary=True)
    
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    query = """
        SELECT start_time, end_time
        FROM bookings
        WHERE room_id = %s
        AND status IN ('pending', 'confirmed')
        AND start_time < %s
        AND end_time > %s
        ORDER BY start_time
    """
    cursor.execute(query, (room_id, end_of_day, start_of_day))
    bookings = cursor.fetchall()
    cursor.close()
    
    availability = []
    for hour in range(24):
        slot_start = start_of_day + timedelta(hours=hour)
        slot_end = slot_start + timedelta(hours=1)
        
        is_available = True
        for booking in bookings:
            if (booking['start_time'] < slot_end and booking['end_time'] > slot_start):
                is_available = False
                break
        
        availability.append({
            'hour': hour,
            'start_time': slot_start,
            'end_time': slot_end,
            'available': is_available
        })
    
    return availability


def get_room_bookings_by_date_range(connection, room_id: int, 
                                     start_date: datetime, 
                                     end_date: datetime) -> List[Dict[str, Any]]:
    """
    Get all bookings for a room within date range.

    Args:
        connection: MySQL connection
        room_id: Room ID
        start_date: Start date
        end_date: End date

    Returns:
        List of bookings
    """
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT 
            b.id, b.title, b.start_time, b.end_time, b.status,
            u.username, u.full_name
        FROM bookings b
        INNER JOIN users u ON b.user_id = u.id
        WHERE b.room_id = %s
        AND b.start_time < %s
        AND b.end_time > %s
        AND b.status IN ('pending', 'confirmed')
        ORDER BY b.start_time
    """
    cursor.execute(query, (room_id, end_date, start_date))
    bookings = cursor.fetchall()
    cursor.close()
    return bookings
