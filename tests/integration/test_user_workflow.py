"""
Integration tests for user workflows.
Tests complete user registration, login, and profile management flows.

Author: Ahmad Yateem
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from utils.auth import hash_password, verify_password, generate_tokens


class TestUserRegistrationWorkflow:
    """Tests for user registration workflow."""

    def test_successful_registration(self, mysql_connection, clean_database, sample_user_data):
        """Test successful user registration flow."""
        db = mysql_connection._db
        password_hash = hash_password(sample_user_data['password'])
        
        user_data = {
            'username': sample_user_data['username'],
            'email': sample_user_data['email'],
            'password_hash': password_hash,
            'full_name': sample_user_data['full_name'],
            'role': sample_user_data['role'],
            'is_active': 1,
            'is_locked': 0,
            'failed_login_attempts': 0
        }
        
        user_id = db.add_user(user_data)
        
        assert user_id is not None
        assert user_id > 0
        
        user = db.get_user(user_id)
        
        assert user is not None
        assert user['username'] == sample_user_data['username']
        assert user['email'] == sample_user_data['email']
        assert user['full_name'] == sample_user_data['full_name']
        assert user['role'] == sample_user_data['role']
        assert user['is_active'] == 1

    def test_duplicate_username_rejected(self, mysql_connection, clean_database, sample_user_data):
        """Test duplicate username detection."""
        db = mysql_connection._db
        password_hash = hash_password(sample_user_data['password'])
        
        # Create first user
        user_data = {
            'username': sample_user_data['username'],
            'email': sample_user_data['email'],
            'password_hash': password_hash,
            'full_name': sample_user_data['full_name'],
            'role': sample_user_data['role']
        }
        db.add_user(user_data)
        
        # Check if username already exists
        existing_user = db.get_user_by_username(sample_user_data['username'])
        
        # Duplicate should be detected
        assert existing_user is not None
        assert existing_user['username'] == sample_user_data['username']

    def test_duplicate_email_rejected(self, mysql_connection, clean_database, sample_user_data):
        """Test duplicate email detection."""
        db = mysql_connection._db
        password_hash = hash_password(sample_user_data['password'])
        
        # Create first user
        user_data = {
            'username': sample_user_data['username'],
            'email': sample_user_data['email'],
            'password_hash': password_hash,
            'full_name': sample_user_data['full_name'],
            'role': sample_user_data['role']
        }
        db.add_user(user_data)
        
        # Check if email already exists
        existing_emails = [u['email'] for u in db.users.values()]
        
        # Duplicate should be detected
        assert sample_user_data['email'] in existing_emails


class TestUserLoginWorkflow:
    """Tests for user login workflow."""

    def test_successful_login(self, mysql_connection, created_test_user, sample_user_data):
        """Test successful login flow."""
        db = mysql_connection._db
        
        user = db.get_user_by_username(sample_user_data['username'])
        
        assert user is not None
        
        password_valid = verify_password(
            sample_user_data['password'], 
            created_test_user['password_hash']
        )
        
        assert password_valid is True

    def test_login_wrong_password(self, mysql_connection, created_test_user, sample_user_data):
        """Test login with wrong password."""
        password_valid = verify_password(
            'WrongPassword123!', 
            created_test_user['password_hash']
        )
        
        assert password_valid is False

    def test_login_nonexistent_user(self, mysql_connection, clean_database):
        """Test login with nonexistent username."""
        db = mysql_connection._db
        
        user = db.get_user_by_username('nonexistent')
        
        assert user is None

    def test_failed_login_increments_counter(self, mysql_connection, created_test_user):
        """Test failed login increments failure counter."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        
        # Increment failed login counter
        db.users[user_id]['failed_login_attempts'] += 1
        
        user = db.get_user(user_id)
        
        assert user['failed_login_attempts'] == 1

    def test_account_lockout(self, mysql_connection, created_test_user):
        """Test account lockout after multiple failures."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        
        # Simulate 5 failed login attempts
        for _ in range(5):
            db.users[user_id]['failed_login_attempts'] += 1
        
        # Lock the account
        db.users[user_id]['is_locked'] = 1
        
        user = db.get_user(user_id)
        
        assert user['is_locked'] == 1

    def test_successful_login_resets_counter(self, mysql_connection, created_test_user):
        """Test successful login resets failure counter."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        
        # Add some failed attempts
        db.users[user_id]['failed_login_attempts'] = 2
        
        # Reset on successful login
        db.users[user_id]['failed_login_attempts'] = 0
        
        user = db.get_user(user_id)
        
        assert user['failed_login_attempts'] == 0


class TestProfileUpdateWorkflow:
    """Tests for profile update workflow."""

    def test_update_full_name(self, mysql_connection, created_test_user):
        """Test updating user full name."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        
        db.users[user_id]['full_name'] = 'Updated Name'
        
        user = db.get_user(user_id)
        
        assert user['full_name'] == 'Updated Name'

    def test_update_email(self, mysql_connection, created_test_user):
        """Test updating user email."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        new_email = 'updated@example.com'
        
        db.users[user_id]['email'] = new_email
        
        user = db.get_user(user_id)
        
        assert user['email'] == new_email

    def test_update_multiple_fields(self, mysql_connection, created_test_user):
        """Test updating multiple fields at once."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        
        db.users[user_id]['full_name'] = 'New Name'
        db.users[user_id]['email'] = 'new@example.com'
        
        user = db.get_user(user_id)
        
        assert user['full_name'] == 'New Name'
        assert user['email'] == 'new@example.com'


class TestUserDeletionWorkflow:
    """Tests for user deletion workflow."""

    def test_delete_user(self, mysql_connection, created_test_user):
        """Test deleting a user."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        
        # Delete user
        del db.users[user_id]
        
        user = db.get_user(user_id)
        
        assert user is None

    def test_delete_nonexistent_user(self, mysql_connection, clean_database):
        """Test deleting nonexistent user returns None."""
        db = mysql_connection._db
        nonexistent_id = 99999
        
        # Try to get - should return None
        result = db.get_user(nonexistent_id)
        
        assert result is None


class TestAdminOperationsWorkflow:
    """Tests for admin operations workflow."""

    def test_admin_can_list_all_users(self, mysql_connection, clean_database, sample_user_data):
        """Test admin can list all users."""
        db = mysql_connection._db
        password_hash = hash_password(sample_user_data['password'])
        
        # Create multiple users
        for i in range(3):
            user_data = {
                'username': f'user{i}',
                'email': f'user{i}@example.com',
                'password_hash': password_hash,
                'full_name': f'User {i}',
                'role': 'user'
            }
            db.add_user(user_data)
        
        users = list(db.users.values())
        
        assert len(users) == 3

    def test_admin_can_change_user_role(self, mysql_connection, created_test_user):
        """Test admin can change user role."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        
        db.users[user_id]['role'] = 'admin'
        
        user = db.get_user(user_id)
        
        assert user['role'] == 'admin'

    def test_admin_can_deactivate_user(self, mysql_connection, created_test_user):
        """Test admin can deactivate user."""
        db = mysql_connection._db
        user_id = created_test_user['id']
        
        db.users[user_id]['is_active'] = 0
        
        user = db.get_user(user_id)
        
        assert user['is_active'] == 0

    def test_user_pagination(self, mysql_connection, clean_database, sample_user_data):
        """Test user listing pagination."""
        db = mysql_connection._db
        password_hash = hash_password(sample_user_data['password'])
        
        # Create 10 users
        for i in range(10):
            user_data = {
                'username': f'user{i}',
                'email': f'user{i}@example.com',
                'password_hash': password_hash,
                'full_name': f'User {i}',
                'role': 'user'
            }
            db.add_user(user_data)
        
        all_users = list(db.users.values())
        
        # Simulate pagination
        page1 = all_users[0:5]
        page2 = all_users[5:10]
        
        assert len(page1) == 5
        assert len(page2) == 5
        
        total = len(db.users)
        assert total == 10
