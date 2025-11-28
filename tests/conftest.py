"""
Pytest configuration and fixtures for tests.

Author: Ahmad Yateem & Hassan Fouani
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth import hash_password


class TestDatabase:
    """Simple test database for integration tests."""
    
    def __init__(self):
        self.users = {}
        self.rooms = {}
        self.bookings = {}
        self.reviews = {}
        self._user_id = 0
        self._room_id = 0
        self._booking_id = 0
        self._review_id = 0
    
    def clear(self):
        self.users.clear()
        self.rooms.clear()
        self.bookings.clear()
        self.reviews.clear()
        self._user_id = 0
        self._room_id = 0
        self._booking_id = 0
        self._review_id = 0
    
    def add_user(self, data):
        self._user_id += 1
        data['id'] = self._user_id
        self.users[self._user_id] = data
        return self._user_id
    
    def get_user(self, user_id):
        return self.users.get(user_id)
    
    def get_user_by_username(self, username):
        for user in self.users.values():
            if user.get('username') == username:
                return user
        return None
    
    def add_room(self, data):
        self._room_id += 1
        data['id'] = self._room_id
        self.rooms[self._room_id] = data
        return self._room_id
    
    def get_room(self, room_id):
        return self.rooms.get(room_id)
    
    def add_booking(self, data):
        self._booking_id += 1
        data['id'] = self._booking_id
        self.bookings[self._booking_id] = data
        return self._booking_id
    
    def add_review(self, data):
        self._review_id += 1
        data['id'] = self._review_id
        self.reviews[self._review_id] = data
        return self._review_id


_db = TestDatabase()


@pytest.fixture(scope='function')
def mysql_connection():
    """Provides test database connection."""
    _db.clear()
    
    class Connection:
        def __init__(self):
            self._db = _db
    
    return Connection()


@pytest.fixture(scope='function')
def clean_database(mysql_connection):
    """Ensures clean database state."""
    yield


@pytest.fixture
def sample_user_data():
    """Sample user data for tests."""
    return {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'SecurePass123!',
        'full_name': 'Test User',
        'role': 'user'
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin user data."""
    return {
        'username': 'adminuser',
        'email': 'admin@example.com',
        'password': 'AdminPass123!',
        'full_name': 'Admin User',
        'role': 'admin'
    }


@pytest.fixture
def sample_room_data():
    """Sample room data for tests."""
    return {
        'name': 'Conference Room A',
        'capacity': 10,
        'floor': 1,
        'building': 'Main Building',
        'equipment': ['projector', 'whiteboard'],
        'amenities': ['wifi', 'air_conditioning'],
        'hourly_rate': 50.00,
        'status': 'available'
    }


@pytest.fixture
def sample_booking_data():
    """Sample booking data for tests."""
    return {
        'title': 'Test Meeting',
        'description': 'A test meeting',
        'start_time': datetime.now() + timedelta(days=1, hours=9),
        'end_time': datetime.now() + timedelta(days=1, hours=10),
        'attendees': 5,
        'status': 'confirmed'
    }


@pytest.fixture
def sample_review_data():
    """Sample review data for tests."""
    return {
        'rating': 4,
        'comment': 'Great meeting room.',
        'is_flagged': False,
        'helpful_votes': 0,
        'unhelpful_votes': 0
    }


@pytest.fixture
def created_test_user(mysql_connection, sample_user_data):
    """Creates a test user in database."""
    user = {
        'username': sample_user_data['username'],
        'email': sample_user_data['email'],
        'password_hash': hash_password(sample_user_data['password']),
        'full_name': sample_user_data['full_name'],
        'role': sample_user_data['role'],
        'is_active': True,
        'is_locked': False,
        'failed_login_attempts': 0,
        'created_at': datetime.now()
    }
    user_id = _db.add_user(user)
    return _db.get_user(user_id)


@pytest.fixture
def created_admin_user(mysql_connection, sample_admin_data):
    """Creates an admin user in database."""
    user = {
        'username': sample_admin_data['username'],
        'email': sample_admin_data['email'],
        'password_hash': hash_password(sample_admin_data['password']),
        'full_name': sample_admin_data['full_name'],
        'role': sample_admin_data['role'],
        'is_active': True,
        'is_locked': False,
        'failed_login_attempts': 0,
        'created_at': datetime.now()
    }
    user_id = _db.add_user(user)
    return _db.get_user(user_id)


@pytest.fixture
def created_test_room(mysql_connection, sample_room_data):
    """Creates a test room in database."""
    room = {
        'name': sample_room_data['name'],
        'capacity': sample_room_data['capacity'],
        'floor': sample_room_data.get('floor', 1),
        'building': sample_room_data.get('building', 'Main Building'),
        'equipment': sample_room_data.get('equipment', []),
        'amenities': sample_room_data.get('amenities', []),
        'hourly_rate': sample_room_data.get('hourly_rate', 0.0),
        'status': 'available',
        'created_at': datetime.now()
    }
    room_id = _db.add_room(room)
    return _db.get_room(room_id)


@pytest.fixture
def created_test_booking(mysql_connection, created_test_user, created_test_room, sample_booking_data):
    """Creates a test booking in database."""
    booking = {
        'user_id': created_test_user['id'],
        'room_id': created_test_room['id'],
        'title': sample_booking_data['title'],
        'description': sample_booking_data['description'],
        'start_time': sample_booking_data['start_time'],
        'end_time': sample_booking_data['end_time'],
        'attendees': sample_booking_data['attendees'],
        'status': sample_booking_data['status'],
        'created_at': datetime.now()
    }
    booking_id = _db.add_booking(booking)
    return _db.bookings[booking_id]


@pytest.fixture
def created_test_review(mysql_connection, created_test_user, created_test_room, sample_review_data):
    """Creates a test review in database."""
    review = {
        'user_id': created_test_user['id'],
        'room_id': created_test_room['id'],
        'rating': sample_review_data['rating'],
        'comment': sample_review_data['comment'],
        'is_flagged': sample_review_data['is_flagged'],
        'is_approved': True,
        'helpful_votes': sample_review_data['helpful_votes'],
        'unhelpful_votes': sample_review_data['unhelpful_votes'],
        'created_at': datetime.now()
    }
    review_id = _db.add_review(review)
    return _db.reviews[review_id]


@pytest.fixture
def auth_token(created_test_user):
    """Provides authentication token for test user."""
    from utils.auth import generate_tokens
    tokens = generate_tokens(
        user_id=created_test_user['id'],
        username=created_test_user['username'],
        role=created_test_user['role']
    )
    return tokens['access_token']


@pytest.fixture
def admin_auth_token(created_admin_user):
    """Provides authentication token for admin user."""
    from utils.auth import generate_tokens
    tokens = generate_tokens(
        user_id=created_admin_user['id'],
        username=created_admin_user['username'],
        role=created_admin_user['role']
    )
    return tokens['access_token']
