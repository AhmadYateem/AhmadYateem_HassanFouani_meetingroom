"""
Routes for Users Service.
Handles user authentication and management endpoints.
"""

from flask import Blueprint, request
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.connection import get_connection
from services.users import dao
from utils.auth import hash_password, verify_password, generate_tokens, get_current_user, admin_required
from utils.validators import (
    validate_required_fields,
    validate_email_format,
    validate_username,
    validate_password,
    validate_role,
    validate_pagination_params,
    ValidationError
)
from utils.sanitizers import sanitize_username, sanitize_email, sanitize_string
from utils.responses import *
from utils.decorators import handle_errors, audit_log, rate_limit, validate_json
from utils.logger import setup_logger
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

logger = setup_logger('users-routes')

users_bp = Blueprint('users', __name__)


@users_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        200: Service is healthy
    """
    return success_response({'status': 'healthy', 'service': 'users'})


@users_bp.route('/api/auth/register', methods=['POST'])
@handle_errors
@validate_json
@rate_limit(limit=10, window=3600)
@audit_log('user_register', 'user')
def register():
    """
    Register a new user.

    Request Body:
        username: Unique username
        email: Valid email address
        password: Strong password
        full_name: User's full name
        role: Optional role (default: 'user')

    Returns:
        201: User created successfully with JWT tokens
    """
    from flask import current_app
    data = request.get_json()
    
    validate_required_fields(data, ['username', 'email', 'password', 'full_name'])
    
    username = sanitize_username(data['username'])
    email = sanitize_email(data['email'])
    full_name = sanitize_string(data['full_name'], max_length=100)
    role = data.get('role', 'user')
    
    validate_username(username)
    email = validate_email_format(email)
    validate_password(data['password'])
    validate_role(role)
    
    db_pool = current_app.config['DB_POOL']
    
    with get_connection(db_pool) as conn:
        if dao.get_user_by_username(conn, username):
            return conflict_response(f"Username '{username}' is already taken")
        
        if dao.get_user_by_email(conn, email):
            return conflict_response(f"Email '{email}' is already registered")
        
        password_hash = hash_password(data['password'])
        
        user_id = dao.create_user(conn, username, email, password_hash, full_name, role)
        
        user = dao.get_user_by_id(conn, user_id)
    
    tokens = generate_tokens(user['id'], user['username'], user['role'])
    
    logger.info(f"User registered: {username} (ID: {user_id})")
    
    return created_response({
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role']
        },
        'tokens': tokens
    }, message="User registered successfully")


@users_bp.route('/api/auth/login', methods=['POST'])
@handle_errors
@validate_json
@rate_limit(limit=20, window=300)
def login():
    """
    User login.

    Request Body:
        username: Username or email
        password: User password

    Returns:
        200: Login successful with JWT tokens
    """
    from flask import current_app
    data = request.get_json()
    
    validate_required_fields(data, ['username', 'password'])
    
    username_or_email = sanitize_string(data['username'])
    
    db_pool = current_app.config['DB_POOL']
    
    with get_connection(db_pool) as conn:
        user = dao.get_user_by_username_or_email(conn, username_or_email)
        
        if not user:
            return unauthorized_response("Invalid username or password")
        
        if user['locked_until'] and user['locked_until'] > datetime.now():
            time_remaining = int((user['locked_until'] - datetime.now()).total_seconds() / 60)
            return unauthorized_response(
                f"Account is locked. Try again in {time_remaining} minutes."
            )
        
        if not verify_password(data['password'], user['password_hash']):
            dao.increment_failed_login(conn, user['id'])
            
            max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
            if user['failed_login_attempts'] + 1 >= max_attempts:
                lock_duration = current_app.config.get('ACCOUNT_LOCK_DURATION', 1800)
                locked_until = datetime.now() + timedelta(seconds=lock_duration)
                dao.lock_account(conn, user['id'], locked_until)
                logger.warning(f"Account locked: {user['username']}")
            
            return unauthorized_response("Invalid username or password")
        
        if not user['is_active']:
            return unauthorized_response("Account is disabled")
        
        dao.reset_failed_login(conn, user['id'])
        
        user = dao.get_user_by_id(conn, user['id'])
    
    tokens = generate_tokens(user['id'], user['username'], user['role'])
    
    logger.info(f"User logged in: {user['username']}")
    
    return success_response({
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role']
        },
        'tokens': tokens
    }, message="Login successful")


@users_bp.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
@handle_errors
def refresh_token():
    """
    Refresh access token.

    Returns:
        200: New access token
    """
    from flask import current_app
    current_user_id = get_jwt_identity()
    
    db_pool = current_app.config['DB_POOL']
    
    with get_connection(db_pool) as conn:
        user = dao.get_user_by_id(conn, current_user_id)
        
        if not user or not user['is_active']:
            return unauthorized_response("User not found or inactive")
    
    tokens = generate_tokens(user['id'], user['username'], user['role'])
    
    return success_response({'tokens': tokens}, message="Token refreshed successfully")


@users_bp.route('/api/users', methods=['GET'])
@jwt_required()
@admin_required
@handle_errors
@rate_limit(limit=100, window=60)
def get_all_users():
    """
    Get all users (Admin only).

    Query Parameters:
        page: Page number
        per_page: Items per page
        role: Filter by role
        is_active: Filter by active status

    Returns:
        200: List of users with pagination
    """
    from flask import current_app
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    role_filter = request.args.get('role')
    is_active_str = request.args.get('is_active')
    
    validate_pagination_params(page, per_page)
    
    is_active = None
    if is_active_str is not None:
        is_active = is_active_str.lower() == 'true'
    
    offset = (page - 1) * per_page
    
    db_pool = current_app.config['DB_POOL']
    
    with get_connection(db_pool) as conn:
        users = dao.get_all_users(conn, limit=per_page, offset=offset, 
                                  role=role_filter, is_active=is_active)
        total = dao.count_users(conn, role=role_filter, is_active=is_active)
    
    users_data = [{
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'full_name': user['full_name'],
        'role': user['role'],
        'is_active': user['is_active'],
        'created_at': user['created_at'].isoformat() if user['created_at'] else None,
        'last_login': user['last_login'].isoformat() if user.get('last_login') else None
    } for user in users]
    
    return paginated_response(users_data, page, per_page, total)


@users_bp.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_user(user_id):
    """
    Get user by ID.

    Returns:
        200: User details
    """
    from flask import current_app
    current_user = get_current_user()
    
    if current_user['user_id'] != user_id and current_user['role'] != 'admin':
        return forbidden_response("You can only view your own profile")
    
    db_pool = current_app.config['DB_POOL']
    
    with get_connection(db_pool) as conn:
        user = dao.get_user_by_id(conn, user_id)
    
    if not user:
        return not_found_response("User not found")
    
    return success_response({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'full_name': user['full_name'],
        'role': user['role'],
        'is_active': user['is_active'],
        'created_at': user['created_at'].isoformat() if user['created_at'] else None,
        'last_login': user['last_login'].isoformat() if user.get('last_login') else None
    })


@users_bp.route('/api/users/profile', methods=['GET'])
@jwt_required()
@handle_errors
def get_profile():
    """
    Get current user's profile.

    Returns:
        200: User profile
    """
    from flask import current_app
    current_user = get_current_user()
    
    db_pool = current_app.config['DB_POOL']
    
    with get_connection(db_pool) as conn:
        user = dao.get_user_by_id(conn, current_user['user_id'])
    
    if not user:
        return not_found_response("User not found")
    
    return success_response({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'full_name': user['full_name'],
        'role': user['role'],
        'is_active': user['is_active'],
        'created_at': user['created_at'].isoformat() if user['created_at'] else None,
        'last_login': user['last_login'].isoformat() if user.get('last_login') else None
    })


@users_bp.route('/api/users/profile', methods=['PUT'])
@jwt_required()
@handle_errors
@validate_json
@audit_log('update_profile', 'user')
def update_profile():
    """
    Update current user's profile.

    Request Body:
        email: New email (optional)
        full_name: New full name (optional)
        password: New password (optional)

    Returns:
        200: Profile updated successfully
    """
    from flask import current_app
    current_user = get_current_user()
    data = request.get_json()
    
    db_pool = current_app.config['DB_POOL']
    
    updates = {}
    
    if 'email' in data:
        new_email = sanitize_email(data['email'])
        new_email = validate_email_format(new_email)
        
        with get_connection(db_pool) as conn:
            existing_user = dao.get_user_by_email(conn, new_email)
            if existing_user and existing_user['id'] != current_user['user_id']:
                return conflict_response("Email is already in use")
        
        updates['email'] = new_email
    
    if 'full_name' in data:
        updates['full_name'] = sanitize_string(data['full_name'], max_length=100)
    
    if 'password' in data:
        validate_password(data['password'])
        updates['password_hash'] = hash_password(data['password'])
    
    with get_connection(db_pool) as conn:
        dao.update_user(conn, current_user['user_id'], **updates)
        user = dao.get_user_by_id(conn, current_user['user_id'])
    
    logger.info(f"Profile updated: {user['username']}")
    
    return success_response({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'full_name': user['full_name'],
        'role': user['role']
    }, message="Profile updated successfully")


@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@handle_errors
@audit_log('delete_user', 'user')
def delete_user(user_id):
    """
    Delete a user (Admin only).

    Returns:
        200: User deleted successfully
    """
    from flask import current_app
    current_user = get_current_user()
    
    if current_user['user_id'] == user_id:
        return forbidden_response("You cannot delete your own account")
    
    db_pool = current_app.config['DB_POOL']
    
    with get_connection(db_pool) as conn:
        user = dao.get_user_by_id(conn, user_id)
        
        if not user:
            return not_found_response("User not found")
        
        username = user['username']
        dao.delete_user(conn, user_id)
    
    logger.info(f"User deleted: {username}")
    
    return success_response(message=f"User '{username}' deleted successfully")


@users_bp.route('/api/users/<int:user_id>/bookings', methods=['GET'])
@jwt_required()
@handle_errors
def get_user_bookings(user_id):
    """
    Get user's booking history.

    Query Parameters:
        page: Page number
        per_page: Items per page

    Returns:
        200: List of bookings with pagination
    """
    from flask import current_app
    current_user = get_current_user()
    
    if current_user['user_id'] != user_id and current_user['role'] != 'admin':
        return forbidden_response("You can only view your own bookings")
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    validate_pagination_params(page, per_page)
    
    offset = (page - 1) * per_page
    
    db_pool = current_app.config['DB_POOL']
    
    with get_connection(db_pool) as conn:
        bookings = dao.get_user_bookings(conn, user_id, limit=per_page, offset=offset)
        total = dao.count_user_bookings(conn, user_id)
    
    bookings_data = [{
        'id': booking['id'],
        'title': booking['title'],
        'description': booking['description'],
        'start_time': booking['start_time'].isoformat() if booking['start_time'] else None,
        'end_time': booking['end_time'].isoformat() if booking['end_time'] else None,
        'status': booking['status'],
        'attendees': booking['attendees'],
        'room': {
            'id': booking['room_id'],
            'name': booking['room_name'],
            'capacity': booking['room_capacity'],
            'floor': booking['room_floor'],
            'building': booking['room_building']
        },
        'created_at': booking['created_at'].isoformat() if booking['created_at'] else None
    } for booking in bookings]
    
    return paginated_response(bookings_data, page, per_page, total)
