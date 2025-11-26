"""
Pytest fixtures for Smart Meeting Room Management System tests.
Provides database connections, test clients, and mock objects.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import mysql.connector
from mysql.connector import pooling


os.environ['MYSQL_HOST'] = os.getenv('TEST_MYSQL_HOST', 'localhost')
os.environ['MYSQL_PORT'] = os.getenv('TEST_MYSQL_PORT', '3306')
os.environ['MYSQL_USER'] = os.getenv('TEST_MYSQL_USER', 'admin')
os.environ['MYSQL_PASSWORD'] = os.getenv('TEST_MYSQL_PASSWORD', 'secure_password')
os.environ['MYSQL_DATABASE'] = os.getenv('TEST_MYSQL_DATABASE', 'smartmeetingroom_test')
os.environ['REDIS_HOST'] = os.getenv('TEST_REDIS_HOST', 'localhost')
os.environ['REDIS_PORT'] = os.getenv('TEST_REDIS_PORT', '6379')
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-jwt-tokens'


@pytest.fixture(scope='session')
def mysql_config():
    """
    Get MySQL configuration for tests.

    Returns:
        Dictionary with MySQL connection parameters
    """
    return {
        'host': os.environ['MYSQL_HOST'],
        'port': int(os.environ['MYSQL_PORT']),
        'user': os.environ['MYSQL_USER'],
        'password': os.environ['MYSQL_PASSWORD'],
        'database': os.environ['MYSQL_DATABASE']
    }


@pytest.fixture(scope='session')
def mysql_connection_pool(mysql_config):
    """
    Create MySQL connection pool for tests.

    Args:
        mysql_config: MySQL configuration

    Yields:
        MySQLConnectionPool instance
    """
    try:
        pool = pooling.MySQLConnectionPool(
            pool_name='test_pool',
            pool_size=5,
            **mysql_config
        )
        yield pool
    except mysql.connector.Error:
        pytest.skip('MySQL not available for testing')


@pytest.fixture
def mysql_connection(mysql_connection_pool):
    """
    Get MySQL connection from pool.

    Args:
        mysql_connection_pool: Connection pool

    Yields:
        MySQL connection
    """
    connection = mysql_connection_pool.get_connection()
    yield connection
    connection.rollback()
    connection.close()


@pytest.fixture
def clean_database(mysql_connection):
    """
    Clean database tables before test.

    Args:
        mysql_connection: MySQL connection
    """
    cursor = mysql_connection.cursor()
    
    tables = ['review_votes', 'reviews', 'bookings', 'rooms', 'users']
    
    cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
    for table in tables:
        try:
            cursor.execute(f'TRUNCATE TABLE {table}')
        except mysql.connector.Error:
            pass
    cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
    
    mysql_connection.commit()
    cursor.close()
    
    yield
    
    cursor = mysql_connection.cursor()
    cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
    for table in tables:
        try:
            cursor.execute(f'TRUNCATE TABLE {table}')
        except mysql.connector.Error:
            pass
    cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
    mysql_connection.commit()
    cursor.close()


@pytest.fixture
def mock_db_pool():
    """
    Create mock database pool.

    Returns:
        MagicMock database pool
    """
    pool = MagicMock()
    connection = MagicMock()
    cursor = MagicMock()
    
    pool.get_connection.return_value.__enter__ = MagicMock(return_value=connection)
    pool.get_connection.return_value.__exit__ = MagicMock(return_value=False)
    
    connection.cursor.return_value = cursor
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    cursor.lastrowid = 1
    
    return pool


@pytest.fixture
def mock_redis():
    """
    Create mock Redis client.

    Returns:
        MagicMock Redis client
    """
    redis_client = MagicMock()
    redis_client.get.return_value = None
    redis_client.set.return_value = True
    redis_client.delete.return_value = 1
    redis_client.exists.return_value = False
    redis_client.expire.return_value = True
    
    return redis_client


@pytest.fixture
def mock_rabbitmq_publisher():
    """
    Create mock RabbitMQ publisher.

    Returns:
        MagicMock publisher
    """
    publisher = MagicMock()
    publisher.publish_booking_confirmation.return_value = True
    publisher.publish_booking_cancellation.return_value = True
    publisher.publish_review_notification.return_value = True
    publisher.publish_user_registration.return_value = True
    
    return publisher


@pytest.fixture
def sample_user_data():
    """
    Get sample user data for tests.

    Returns:
        Dictionary with user data
    """
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'full_name': 'Test User',
        'role': 'user'
    }


@pytest.fixture
def sample_admin_data():
    """
    Get sample admin user data.

    Returns:
        Dictionary with admin data
    """
    return {
        'username': 'adminuser',
        'email': 'admin@example.com',
        'password': 'AdminPass123!',
        'full_name': 'Admin User',
        'role': 'admin'
    }


@pytest.fixture
def sample_room_data():
    """
    Get sample room data for tests.

    Returns:
        Dictionary with room data
    """
    return {
        'name': 'Conference Room A',
        'capacity': 10,
        'floor': 1,
        'building': 'Main Building',
        'equipment': ['projector', 'whiteboard', 'video_conferencing'],
        'description': 'Large conference room with AV equipment',
        'hourly_rate': 50.00
    }


@pytest.fixture
def sample_booking_data():
    """
    Get sample booking data for tests.

    Returns:
        Dictionary with booking data
    """
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    return {
        'title': 'Team Meeting',
        'description': 'Weekly team sync',
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'attendees': 5
    }


@pytest.fixture
def sample_review_data():
    """
    Get sample review data for tests.

    Returns:
        Dictionary with review data
    """
    return {
        'rating': 4,
        'title': 'Great room',
        'comment': 'Excellent facilities and clean environment.',
        'cleanliness_rating': 5,
        'equipment_rating': 4,
        'comfort_rating': 4
    }


@pytest.fixture
def users_app(mock_db_pool, mock_redis, mock_rabbitmq_publisher):
    """
    Create Users service test app.

    Args:
        mock_db_pool: Mock database pool
        mock_redis: Mock Redis client
        mock_rabbitmq_publisher: Mock publisher

    Returns:
        Flask test client
    """
    from services.users.app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['DB_POOL'] = mock_db_pool
    app.config['REDIS_CLIENT'] = mock_redis
    app.config['RABBITMQ_PUBLISHER'] = mock_rabbitmq_publisher
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def rooms_app(mock_db_pool, mock_redis):
    """
    Create Rooms service test app.

    Args:
        mock_db_pool: Mock database pool
        mock_redis: Mock Redis client

    Returns:
        Flask test client
    """
    from services.rooms.app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['DB_POOL'] = mock_db_pool
    app.config['REDIS_CLIENT'] = mock_redis
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def bookings_app(mock_db_pool, mock_redis, mock_rabbitmq_publisher):
    """
    Create Bookings service test app.

    Args:
        mock_db_pool: Mock database pool
        mock_redis: Mock Redis client
        mock_rabbitmq_publisher: Mock publisher

    Returns:
        Flask test client
    """
    from services.bookings.app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['DB_POOL'] = mock_db_pool
    app.config['REDIS_CLIENT'] = mock_redis
    app.config['RABBITMQ_PUBLISHER'] = mock_rabbitmq_publisher
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def reviews_app(mock_db_pool, mock_redis):
    """
    Create Reviews service test app.

    Args:
        mock_db_pool: Mock database pool
        mock_redis: Mock Redis client

    Returns:
        Flask test client
    """
    from services.reviews.app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['DB_POOL'] = mock_db_pool
    app.config['REDIS_CLIENT'] = mock_redis
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    """
    Get authorization headers with test token.

    Returns:
        Dictionary with Authorization header
    """
    from utils.auth import generate_tokens
    
    tokens = generate_tokens(user_id=1, username='testuser', role='user')
    
    return {
        'Authorization': f"Bearer {tokens['access_token']}",
        'Content-Type': 'application/json'
    }


@pytest.fixture
def admin_auth_headers():
    """
    Get authorization headers with admin token.

    Returns:
        Dictionary with Authorization header
    """
    from utils.auth import generate_tokens
    
    tokens = generate_tokens(user_id=1, username='adminuser', role='admin')
    
    return {
        'Authorization': f"Bearer {tokens['access_token']}",
        'Content-Type': 'application/json'
    }


@pytest.fixture
def created_test_user(mysql_connection, sample_user_data, clean_database):
    """
    Create a test user in database.

    Args:
        mysql_connection: MySQL connection
        sample_user_data: User data
        clean_database: Database cleanup fixture

    Returns:
        Created user data with ID
    """
    from utils.auth import hash_password
    
    cursor = mysql_connection.cursor(dictionary=True)
    
    password_hash = hash_password(sample_user_data['password'])
    
    query = """
        INSERT INTO users (username, email, password_hash, full_name, role, 
                          is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, TRUE, NOW(), NOW())
    """
    cursor.execute(query, (
        sample_user_data['username'],
        sample_user_data['email'],
        password_hash,
        sample_user_data['full_name'],
        sample_user_data['role']
    ))
    mysql_connection.commit()
    
    user_id = cursor.lastrowid
    cursor.close()
    
    return {**sample_user_data, 'id': user_id, 'password_hash': password_hash}


@pytest.fixture
def created_test_room(mysql_connection, sample_room_data, clean_database):
    """
    Create a test room in database.

    Args:
        mysql_connection: MySQL connection
        sample_room_data: Room data
        clean_database: Database cleanup fixture

    Returns:
        Created room data with ID
    """
    import json
    
    cursor = mysql_connection.cursor(dictionary=True)
    
    query = """
        INSERT INTO rooms (name, capacity, floor, building, equipment, 
                          description, hourly_rate, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())
    """
    cursor.execute(query, (
        sample_room_data['name'],
        sample_room_data['capacity'],
        sample_room_data['floor'],
        sample_room_data['building'],
        json.dumps(sample_room_data['equipment']),
        sample_room_data['description'],
        sample_room_data['hourly_rate']
    ))
    mysql_connection.commit()
    
    room_id = cursor.lastrowid
    cursor.close()
    
    return {**sample_room_data, 'id': room_id}
