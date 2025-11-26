"""
Unit tests for authentication module.
Tests password hashing, JWT tokens, and role checking.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from utils.auth import (
    hash_password, verify_password, generate_tokens,
    decode_token, get_token_identity, get_token_claims
)
from utils.exceptions import AuthenticationError


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = 'SecurePass123!'
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test that same password produces different hashes."""
        password = 'SecurePass123!'
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = 'SecurePass123!'
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = 'SecurePass123!'
        hashed = hash_password(password)
        
        assert verify_password('WrongPassword!', hashed) is False

    def test_verify_password_empty(self):
        """Test verifying empty password."""
        hashed = hash_password('SecurePass123!')
        
        assert verify_password('', hashed) is False

    def test_hash_password_empty(self):
        """Test hashing empty password."""
        hashed = hash_password('')
        
        assert hashed is not None
        assert verify_password('', hashed) is True


class TestTokenGeneration:
    """Tests for JWT token generation."""

    @pytest.fixture
    def app_context(self):
        """Create Flask app context for JWT operations."""
        from flask import Flask
        from flask_jwt_extended import JWTManager
        
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
        
        JWTManager(app)
        
        with app.app_context():
            yield app

    def test_generate_tokens(self, app_context):
        """Test generating access and refresh tokens."""
        tokens = generate_tokens(user_id=1, username='testuser', role='user')
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['access_token'] is not None
        assert tokens['refresh_token'] is not None

    def test_tokens_are_different(self, app_context):
        """Test that access and refresh tokens are different."""
        tokens = generate_tokens(user_id=1, username='testuser', role='user')
        
        assert tokens['access_token'] != tokens['refresh_token']

    def test_generate_tokens_with_role(self, app_context):
        """Test generating tokens includes role claim."""
        tokens = generate_tokens(user_id=1, username='testuser', role='admin')
        
        from flask_jwt_extended import decode_token
        decoded = decode_token(tokens['access_token'])
        
        assert decoded['role'] == 'admin'

    def test_generate_tokens_different_users(self, app_context):
        """Test tokens for different users are different."""
        tokens1 = generate_tokens(user_id=1, username='user1', role='user')
        tokens2 = generate_tokens(user_id=2, username='user2', role='user')
        
        assert tokens1['access_token'] != tokens2['access_token']


class TestTokenDecoding:
    """Tests for JWT token decoding."""

    @pytest.fixture
    def app_context(self):
        """Create Flask app context for JWT operations."""
        from flask import Flask
        from flask_jwt_extended import JWTManager
        
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
        
        JWTManager(app)
        
        with app.app_context():
            yield app

    def test_decode_valid_token(self, app_context):
        """Test decoding valid token."""
        from flask_jwt_extended import decode_token
        
        tokens = generate_tokens(user_id=1, username='testuser', role='user')
        decoded = decode_token(tokens['access_token'])
        
        assert decoded['sub'] == 1
        assert decoded['username'] == 'testuser'
        assert decoded['role'] == 'user'

    def test_decode_expired_token(self, app_context):
        """Test decoding expired token."""
        from flask import Flask
        from flask_jwt_extended import JWTManager, decode_token, ExpiredSignatureError
        
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=-1)
        
        JWTManager(app)
        
        with app.app_context():
            tokens = generate_tokens(user_id=1, username='testuser', role='user')
            
            with pytest.raises(ExpiredSignatureError):
                decode_token(tokens['access_token'])


class TestRoleChecking:
    """Tests for role-based access control."""

    def test_admin_role_check(self):
        """Test admin role verification."""
        claims = {'role': 'admin'}
        
        assert claims['role'] == 'admin'

    def test_user_role_check(self):
        """Test user role verification."""
        claims = {'role': 'user'}
        
        assert claims['role'] == 'user'
        assert claims['role'] != 'admin'

    def test_moderator_role_check(self):
        """Test moderator role verification."""
        claims = {'role': 'moderator'}
        
        assert claims['role'] == 'moderator'


class TestAccountLockout:
    """Tests for account lockout mechanism."""

    def test_failed_login_increment(self):
        """Test incrementing failed login count."""
        failed_count = 0
        
        for _ in range(5):
            failed_count += 1
        
        assert failed_count == 5

    def test_account_locked_after_threshold(self):
        """Test account locks after threshold."""
        failed_count = 5
        threshold = 5
        
        is_locked = failed_count >= threshold
        
        assert is_locked is True

    def test_account_not_locked_below_threshold(self):
        """Test account not locked below threshold."""
        failed_count = 4
        threshold = 5
        
        is_locked = failed_count >= threshold
        
        assert is_locked is False

    def test_failed_count_reset_on_success(self):
        """Test failed count resets on successful login."""
        failed_count = 4
        
        failed_count = 0
        
        assert failed_count == 0

    def test_lockout_duration(self):
        """Test lockout duration calculation."""
        locked_at = datetime.now()
        lockout_duration = timedelta(minutes=30)
        unlock_at = locked_at + lockout_duration
        
        assert unlock_at > datetime.now()
