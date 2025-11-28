"""
Unit tests for validators module.
Tests input validation functions.

Author: Ahmad Yateem
"""

import pytest
from datetime import datetime, timedelta

from utils.validators import (
    validate_email_format, validate_username, validate_password,
    validate_role, validate_rating, validate_booking_times,
    validate_room_capacity, validate_required_fields,
    validate_date_format, validate_pagination_params, ValidationError
)


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        valid_emails = [
            'user@gmail.com',
            'user.name@yahoo.com',
            'user@outlook.com',
        ]
        
        for email in valid_emails:
            result = validate_email_format(email)
            assert result is not None

    def test_invalid_email_format(self):
        """Test invalid email formats."""
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email_format(email)


class TestUsernameValidation:
    """Tests for username validation."""

    def test_valid_username(self):
        """Test valid usernames."""
        valid_usernames = [
            'user123',
            'john_doe',
            'testuser',
        ]
        
        for username in valid_usernames:
            validate_username(username)

    def test_username_too_short(self):
        """Test username below minimum length."""
        with pytest.raises(ValidationError):
            validate_username('ab')

    def test_username_too_long(self):
        """Test username exceeding maximum length."""
        long_username = 'a' * 51
        
        with pytest.raises(ValidationError):
            validate_username(long_username)


class TestPasswordValidation:
    """Tests for password validation."""

    def test_valid_password(self):
        """Test valid passwords."""
        valid_passwords = [
            'SecurePass123!',
            'MyP@ssw0rd',
            'Complex1ty!@#',
        ]
        
        for password in valid_passwords:
            validate_password(password)

    def test_password_too_short(self):
        """Test password below minimum length."""
        with pytest.raises(ValidationError):
            validate_password('Short1!')

    def test_password_no_uppercase(self):
        """Test password without uppercase."""
        with pytest.raises(ValidationError):
            validate_password('lowercase123!')

    def test_password_no_lowercase(self):
        """Test password without lowercase."""
        with pytest.raises(ValidationError):
            validate_password('UPPERCASE123!')


class TestRoleValidation:
    """Tests for role validation."""

    def test_valid_roles(self):
        """Test valid role values."""
        valid_roles = ['user', 'admin', 'moderator']
        
        for role in valid_roles:
            validate_role(role)

    def test_invalid_role(self):
        """Test invalid role value."""
        with pytest.raises(ValidationError):
            validate_role('superadmin')


class TestRatingValidation:
    """Tests for rating validation."""

    def test_valid_ratings(self):
        """Test valid rating values."""
        for rating in [1, 2, 3, 4, 5]:
            validate_rating(rating)

    def test_rating_below_minimum(self):
        """Test rating below 1."""
        with pytest.raises(ValidationError):
            validate_rating(0)

    def test_rating_above_maximum(self):
        """Test rating above 5."""
        with pytest.raises(ValidationError):
            validate_rating(6)


class TestBookingTimesValidation:
    """Tests for booking times validation."""

    def test_valid_booking_times(self):
        """Test valid booking times."""
        start = datetime.now() + timedelta(hours=1)
        end = datetime.now() + timedelta(hours=2)
        
        validate_booking_times(start, end)

    def test_end_before_start(self):
        """Test end time before start time."""
        start = datetime.now() + timedelta(hours=2)
        end = datetime.now() + timedelta(hours=1)
        
        with pytest.raises(ValidationError):
            validate_booking_times(start, end)


class TestCapacityValidation:
    """Tests for capacity validation."""

    def test_valid_capacity(self):
        """Test valid capacity values."""
        validate_room_capacity(1)
        validate_room_capacity(50)
        validate_room_capacity(500)

    def test_zero_capacity(self):
        """Test zero capacity."""
        with pytest.raises(ValidationError):
            validate_room_capacity(0)

    def test_negative_capacity(self):
        """Test negative capacity."""
        with pytest.raises(ValidationError):
            validate_room_capacity(-10)


class TestRequiredFieldsValidation:
    """Tests for required fields validation."""

    def test_all_fields_present(self):
        """Test all required fields present."""
        data = {'name': 'test', 'email': 'test@example.com', 'age': 25}
        required = ['name', 'email']
        
        validate_required_fields(data, required)

    def test_missing_field(self):
        """Test missing required field."""
        data = {'name': 'test'}
        required = ['name', 'email']
        
        with pytest.raises(ValidationError):
            validate_required_fields(data, required)


class TestDateFormatValidation:
    """Tests for date format validation."""

    def test_valid_date_string(self):
        """Test valid date string."""
        result = validate_date_format('2024-12-25')
        assert isinstance(result, datetime)

    def test_invalid_date_string(self):
        """Test invalid date string."""
        with pytest.raises(ValidationError):
            validate_date_format('not-a-date')


class TestPaginationValidation:
    """Tests for pagination validation."""

    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        validate_pagination_params(1, 10)
        validate_pagination_params(5, 50)

    def test_invalid_page(self):
        """Test invalid page number."""
        with pytest.raises(ValidationError):
            validate_pagination_params(0, 10)

    def test_invalid_per_page(self):
        """Test invalid per_page value."""
        with pytest.raises(ValidationError):
            validate_pagination_params(1, 0)

