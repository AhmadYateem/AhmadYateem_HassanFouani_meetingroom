"""
Flask routes for Bookings Service.
Handles all booking-related API endpoints with conflict detection.

Author: Ahmad Yateem
"""

from flask import Blueprint, request, current_app
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from utils.validators import (
    validate_required_fields, validate_datetime, validate_positive_integer,
    validate_booking_times, validate_string_length
)
from utils.sanitizers import sanitize_string, sanitize_html
from utils.responses import (
    success_response, error_response, validation_error_response,
    not_found_response, conflict_error_response, paginated_response
)
from utils.decorators import handle_errors, rate_limit
from utils.exceptions import ValidationError, NotFoundError, ConflictError
from . import dao


bookings_bp = Blueprint('bookings', __name__)


@bookings_bp.route('/api/bookings', methods=['GET'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=100, time_window=60)
def get_bookings():
    """
    Get all bookings with filters.

    Returns:
        Paginated list of bookings
    """
    db_pool = current_app.config['DB_POOL']
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    room_id = request.args.get('room_id', type=int)
    user_id = request.args.get('user_id', type=int)
    status = request.args.get('status', type=str)
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        start_date_obj = datetime.fromisoformat(start_date)
    if end_date:
        end_date_obj = datetime.fromisoformat(end_date)
    
    offset = (page - 1) * per_page
    
    with db_pool.get_connection() as connection:
        bookings = dao.get_all_bookings(
            connection, 
            limit=per_page, 
            offset=offset,
            room_id=room_id,
            user_id=user_id,
            status=status,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        total = dao.count_bookings(
            connection,
            room_id=room_id,
            user_id=user_id,
            status=status,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
    
    return paginated_response(bookings, total, page, per_page)


@bookings_bp.route('/api/bookings/<int:booking_id>', methods=['GET'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=100, time_window=60)
def get_booking(booking_id):
    """
    Get booking by ID.

    Args:
        booking_id: Booking ID

    Returns:
        Booking details
    """
    db_pool = current_app.config['DB_POOL']
    
    with db_pool.get_connection() as connection:
        booking = dao.get_booking_by_id(connection, booking_id)
    
    if not booking:
        return not_found_response('Booking')
    
    return success_response(booking)


@bookings_bp.route('/api/bookings', methods=['POST'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=20, time_window=60)
def create_booking():
    """
    Create a new booking with conflict detection.

    Returns:
        Created booking
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    validate_required_fields(data, ['room_id', 'title', 'start_time', 'end_time', 'attendees'])
    
    room_id = validate_positive_integer(data.get('room_id'), 'room_id')
    title = sanitize_string(data.get('title'))
    description = sanitize_html(data.get('description', ''))
    attendees = validate_positive_integer(data.get('attendees'), 'attendees')
    
    validate_string_length(title, 'title', min_length=3, max_length=200)
    validate_string_length(description, 'description', max_length=1000)
    
    start_time = validate_datetime(data.get('start_time'))
    end_time = validate_datetime(data.get('end_time'))
    
    validate_booking_times(start_time, end_time)
    
    db_pool = current_app.config['DB_POOL']
    
    with db_pool.get_connection() as connection:
        is_available = dao.check_availability(connection, room_id, start_time, end_time)
        
        if not is_available:
            conflicts = dao.get_conflicts(connection, room_id, start_time, end_time)
            return conflict_error_response(
                'Room is not available for the selected time slot',
                {'conflicts': conflicts}
            )
        
        booking_id = dao.create_booking(
            connection,
            user_id=current_user_id,
            room_id=room_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees
        )
        
        booking = dao.get_booking_by_id(connection, booking_id)
    
    return success_response(booking, message='Booking created successfully', status_code=201)


@bookings_bp.route('/api/bookings/<int:booking_id>', methods=['PUT'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=30, time_window=60)
def update_booking(booking_id):
    """
    Update a booking.

    Args:
        booking_id: Booking ID

    Returns:
        Updated booking
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get('role', 'user')
    
    db_pool = current_app.config['DB_POOL']
    
    with db_pool.get_connection() as connection:
        booking = dao.get_booking_by_id(connection, booking_id)
        
        if not booking:
            return not_found_response('Booking')
        
        if booking['user_id'] != current_user_id and user_role != 'admin':
            return error_response('Unauthorized to update this booking', status_code=403)
        
        if booking['status'] == 'cancelled':
            return error_response('Cannot update cancelled booking', status_code=400)
        
        updates = {}
        
        if 'title' in data:
            title = sanitize_string(data['title'])
            validate_string_length(title, 'title', min_length=3, max_length=200)
            updates['title'] = title
        
        if 'description' in data:
            description = sanitize_html(data['description'])
            validate_string_length(description, 'description', max_length=1000)
            updates['description'] = description
        
        if 'attendees' in data:
            updates['attendees'] = validate_positive_integer(data['attendees'], 'attendees')
        
        if 'start_time' in data or 'end_time' in data:
            start_time = validate_datetime(data.get('start_time', booking['start_time']))
            end_time = validate_datetime(data.get('end_time', booking['end_time']))
            
            validate_booking_times(start_time, end_time)
            
            is_available = dao.check_availability(
                connection, 
                booking['room_id'], 
                start_time, 
                end_time,
                exclude_booking_id=booking_id
            )
            
            if not is_available:
                conflicts = dao.get_conflicts(connection, booking['room_id'], start_time, end_time)
                return conflict_error_response(
                    'Room is not available for the selected time slot',
                    {'conflicts': conflicts}
                )
            
            updates['start_time'] = start_time
            updates['end_time'] = end_time
        
        if updates:
            dao.update_booking(connection, booking_id, **updates)
            booking = dao.get_booking_by_id(connection, booking_id)
    
    return success_response(booking, message='Booking updated successfully')


@bookings_bp.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=30, time_window=60)
def delete_booking(booking_id):
    """
    Cancel a booking.

    Args:
        booking_id: Booking ID

    Returns:
        Success message
    """
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get('role', 'user')
    
    cancellation_reason = sanitize_string(data.get('cancellation_reason', ''))
    
    db_pool = current_app.config['DB_POOL']
    
    with db_pool.get_connection() as connection:
        booking = dao.get_booking_by_id(connection, booking_id)
        
        if not booking:
            return not_found_response('Booking')
        
        if booking['user_id'] != current_user_id and user_role != 'admin':
            return error_response('Unauthorized to cancel this booking', status_code=403)
        
        if booking['status'] == 'cancelled':
            return error_response('Booking is already cancelled', status_code=400)
        
        dao.cancel_booking(connection, booking_id, current_user_id, cancellation_reason)
    
    return success_response(None, message='Booking cancelled successfully')


@bookings_bp.route('/api/bookings/check-availability', methods=['POST'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=50, time_window=60)
def check_availability():
    """
    Check room availability for given time slot.

    Returns:
        Availability status
    """
    data = request.get_json()
    
    validate_required_fields(data, ['room_id', 'start_time', 'end_time'])
    
    room_id = validate_positive_integer(data.get('room_id'), 'room_id')
    start_time = validate_datetime(data.get('start_time'))
    end_time = validate_datetime(data.get('end_time'))
    
    validate_booking_times(start_time, end_time)
    
    exclude_booking_id = data.get('exclude_booking_id')
    
    db_pool = current_app.config['DB_POOL']
    
    with db_pool.get_connection() as connection:
        is_available = dao.check_availability(
            connection, 
            room_id, 
            start_time, 
            end_time,
            exclude_booking_id=exclude_booking_id
        )
        
        conflicts = []
        if not is_available:
            conflicts = dao.get_conflicts(connection, room_id, start_time, end_time)
    
    return success_response({
        'available': is_available,
        'room_id': room_id,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'conflicts': conflicts
    })


@bookings_bp.route('/api/bookings/conflicts', methods=['GET'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=50, time_window=60)
def get_conflicts_endpoint():
    """
    Get conflicts for a room and time slot (Admin only).

    Returns:
        List of conflicts
    """
    claims = get_jwt()
    user_role = claims.get('role', 'user')
    
    if user_role != 'admin':
        return error_response('Admin access required', status_code=403)
    
    room_id = request.args.get('room_id', type=int)
    start_time = request.args.get('start_time', type=str)
    end_time = request.args.get('end_time', type=str)
    
    if not all([room_id, start_time, end_time]):
        return validation_error_response(['room_id, start_time, and end_time are required'])
    
    start_time_obj = validate_datetime(start_time)
    end_time_obj = validate_datetime(end_time)
    
    validate_booking_times(start_time_obj, end_time_obj)
    
    db_pool = current_app.config['DB_POOL']
    
    with db_pool.get_connection() as connection:
        conflicts = dao.get_conflicts(connection, room_id, start_time_obj, end_time_obj)
    
    return success_response({
        'room_id': room_id,
        'conflicts': conflicts,
        'conflict_count': len(conflicts)
    })


@bookings_bp.route('/api/bookings/recurring', methods=['POST'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=10, time_window=60)
def create_recurring_booking():
    """
    Create recurring bookings.

    Returns:
        List of created booking IDs
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    validate_required_fields(data, [
        'room_id', 'title', 'start_time', 'end_time', 
        'attendees', 'pattern', 'end_date'
    ])
    
    room_id = validate_positive_integer(data.get('room_id'), 'room_id')
    title = sanitize_string(data.get('title'))
    description = sanitize_html(data.get('description', ''))
    attendees = validate_positive_integer(data.get('attendees'), 'attendees')
    
    validate_string_length(title, 'title', min_length=3, max_length=200)
    validate_string_length(description, 'description', max_length=1000)
    
    start_time = validate_datetime(data.get('start_time'))
    end_time = validate_datetime(data.get('end_time'))
    end_date = validate_datetime(data.get('end_date'))
    
    validate_booking_times(start_time, end_time)
    
    pattern = data.get('pattern')
    if pattern not in ['daily', 'weekly', 'monthly']:
        raise ValidationError('Pattern must be daily, weekly, or monthly')
    
    if end_date <= start_time:
        raise ValidationError('End date must be after start time')
    
    db_pool = current_app.config['DB_POOL']
    
    with db_pool.get_connection() as connection:
        booking_ids = dao.create_recurring_bookings(
            connection,
            user_id=current_user_id,
            room_id=room_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            pattern=pattern,
            end_date=end_date
        )
    
    return success_response({
        'booking_ids': booking_ids,
        'created_count': len(booking_ids),
        'pattern': pattern
    }, message=f'Created {len(booking_ids)} recurring bookings', status_code=201)


@bookings_bp.route('/api/bookings/availability-matrix', methods=['GET'])
@jwt_required()
@handle_errors
@rate_limit(max_calls=50, time_window=60)
def get_availability_matrix():
    """
    Get hourly availability matrix for a room.

    Returns:
        Hourly availability slots
    """
    room_id = request.args.get('room_id', type=int)
    date_str = request.args.get('date', type=str)
    
    if not room_id or not date_str:
        return validation_error_response(['room_id and date are required'])
    
    date = validate_datetime(date_str)
    
    db_pool = current_app.config['DB_POOL']
    
    with db_pool.get_connection() as connection:
        availability = dao.get_availability_matrix(connection, room_id, date)
    
    return success_response({
        'room_id': room_id,
        'date': date.date().isoformat(),
        'availability': availability
    })
