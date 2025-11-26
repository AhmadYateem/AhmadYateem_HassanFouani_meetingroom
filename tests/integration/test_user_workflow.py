"""
Integration tests for user workflows.
Tests complete user registration, login, and profile management flows.
"""

import pytest
import json
from datetime import datetime

from utils.auth import hash_password, verify_password, generate_tokens


class TestUserRegistrationWorkflow:
    """Tests for user registration workflow."""

    def test_successful_registration(self, mysql_connection, clean_database, sample_user_data):
        """Test successful user registration flow."""
        from services.users import dao
        
        password_hash = hash_password(sample_user_data['password'])
        
        user_id = dao.create_user(
            mysql_connection,
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            password_hash=password_hash,
            full_name=sample_user_data['full_name'],
            role=sample_user_data['role']
        )
        
        assert user_id is not None
        assert user_id > 0
        
        user = dao.get_user_by_id(mysql_connection, user_id)
        
        assert user is not None
        assert user['username'] == sample_user_data['username']
        assert user['email'] == sample_user_data['email']
        assert user['full_name'] == sample_user_data['full_name']
        assert user['role'] == sample_user_data['role']
        assert user['is_active'] == 1

    def test_duplicate_username_rejected(self, mysql_connection, clean_database, sample_user_data):
        """Test duplicate username is rejected."""
        from services.users import dao
        import mysql.connector
        
        password_hash = hash_password(sample_user_data['password'])
        
        dao.create_user(
            mysql_connection,
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            password_hash=password_hash,
            full_name=sample_user_data['full_name'],
            role=sample_user_data['role']
        )
        
        with pytest.raises(mysql.connector.Error):
            dao.create_user(
                mysql_connection,
                username=sample_user_data['username'],
                email='different@example.com',
                password_hash=password_hash,
                full_name='Different User',
                role='user'
            )

    def test_duplicate_email_rejected(self, mysql_connection, clean_database, sample_user_data):
        """Test duplicate email is rejected."""
        from services.users import dao
        import mysql.connector
        
        password_hash = hash_password(sample_user_data['password'])
        
        dao.create_user(
            mysql_connection,
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            password_hash=password_hash,
            full_name=sample_user_data['full_name'],
            role=sample_user_data['role']
        )
        
        with pytest.raises(mysql.connector.Error):
            dao.create_user(
                mysql_connection,
                username='differentuser',
                email=sample_user_data['email'],
                password_hash=password_hash,
                full_name='Different User',
                role='user'
            )


class TestUserLoginWorkflow:
    """Tests for user login workflow."""

    def test_successful_login(self, mysql_connection, created_test_user, sample_user_data):
        """Test successful login flow."""
        from services.users import dao
        
        user = dao.get_user_by_username(mysql_connection, sample_user_data['username'])
        
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
        from services.users import dao
        
        user = dao.get_user_by_username(mysql_connection, 'nonexistent')
        
        assert user is None

    def test_failed_login_increments_counter(self, mysql_connection, created_test_user):
        """Test failed login increments failure counter."""
        from services.users import dao
        
        dao.increment_failed_login(mysql_connection, created_test_user['id'])
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user['failed_login_attempts'] == 1

    def test_account_lockout(self, mysql_connection, created_test_user):
        """Test account lockout after multiple failures."""
        from services.users import dao
        
        for _ in range(5):
            dao.increment_failed_login(mysql_connection, created_test_user['id'])
        
        dao.lock_account(mysql_connection, created_test_user['id'])
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user['is_locked'] == 1

    def test_successful_login_resets_counter(self, mysql_connection, created_test_user):
        """Test successful login resets failure counter."""
        from services.users import dao
        
        dao.increment_failed_login(mysql_connection, created_test_user['id'])
        dao.increment_failed_login(mysql_connection, created_test_user['id'])
        
        dao.reset_failed_login(mysql_connection, created_test_user['id'])
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user['failed_login_attempts'] == 0


class TestProfileUpdateWorkflow:
    """Tests for profile update workflow."""

    def test_update_full_name(self, mysql_connection, created_test_user):
        """Test updating user full name."""
        from services.users import dao
        
        dao.update_user(
            mysql_connection, 
            created_test_user['id'],
            full_name='Updated Name'
        )
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user['full_name'] == 'Updated Name'

    def test_update_email(self, mysql_connection, created_test_user):
        """Test updating user email."""
        from services.users import dao
        
        new_email = 'updated@example.com'
        dao.update_user(
            mysql_connection, 
            created_test_user['id'],
            email=new_email
        )
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user['email'] == new_email

    def test_update_multiple_fields(self, mysql_connection, created_test_user):
        """Test updating multiple fields at once."""
        from services.users import dao
        
        dao.update_user(
            mysql_connection, 
            created_test_user['id'],
            full_name='New Name',
            email='new@example.com'
        )
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user['full_name'] == 'New Name'
        assert user['email'] == 'new@example.com'


class TestUserDeletionWorkflow:
    """Tests for user deletion workflow."""

    def test_delete_user(self, mysql_connection, created_test_user):
        """Test deleting a user."""
        from services.users import dao
        
        result = dao.delete_user(mysql_connection, created_test_user['id'])
        
        assert result is True
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user is None

    def test_delete_nonexistent_user(self, mysql_connection, clean_database):
        """Test deleting nonexistent user."""
        from services.users import dao
        
        result = dao.delete_user(mysql_connection, 99999)
        
        assert result is False


class TestAdminOperationsWorkflow:
    """Tests for admin operations workflow."""

    def test_admin_can_list_all_users(self, mysql_connection, clean_database, sample_user_data):
        """Test admin can list all users."""
        from services.users import dao
        
        password_hash = hash_password(sample_user_data['password'])
        
        for i in range(3):
            dao.create_user(
                mysql_connection,
                username=f'user{i}',
                email=f'user{i}@example.com',
                password_hash=password_hash,
                full_name=f'User {i}',
                role='user'
            )
        
        users = dao.get_all_users(mysql_connection)
        
        assert len(users) == 3

    def test_admin_can_change_user_role(self, mysql_connection, created_test_user):
        """Test admin can change user role."""
        from services.users import dao
        
        dao.update_user(
            mysql_connection, 
            created_test_user['id'],
            role='admin'
        )
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user['role'] == 'admin'

    def test_admin_can_deactivate_user(self, mysql_connection, created_test_user):
        """Test admin can deactivate user."""
        from services.users import dao
        
        dao.update_user(
            mysql_connection, 
            created_test_user['id'],
            is_active=False
        )
        
        user = dao.get_user_by_id(mysql_connection, created_test_user['id'])
        
        assert user['is_active'] == 0

    def test_user_pagination(self, mysql_connection, clean_database, sample_user_data):
        """Test user listing pagination."""
        from services.users import dao
        
        password_hash = hash_password(sample_user_data['password'])
        
        for i in range(10):
            dao.create_user(
                mysql_connection,
                username=f'user{i}',
                email=f'user{i}@example.com',
                password_hash=password_hash,
                full_name=f'User {i}',
                role='user'
            )
        
        page1 = dao.get_all_users(mysql_connection, limit=5, offset=0)
        page2 = dao.get_all_users(mysql_connection, limit=5, offset=5)
        
        assert len(page1) == 5
        assert len(page2) == 5
        
        total = dao.count_users(mysql_connection)
        assert total == 10
