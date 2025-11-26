"""
Unit tests for validators module.
Tests input validation functions.
"""

import pytest
from datetime import datetime, timedelta

from utils.validators import (
    validate_email, validate_username, validate_password,
    validate_role, validate_rating, validate_positive_integer,
    validate_string_length, validate_booking_times, validate_datetime,
    validate_capacity, validate_required_fields
)
from utils.exceptions import ValidationError


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        valid_emails = [
            'user@example.com',
            'user.name@example.com',
            'user+tag@example.com',
            'user@subdomain.example.com',
            'user123@example.co.uk'
        ]
        
        for email in valid_emails:
            assert validate_email(email) == email.lower()

    def test_invalid_email_format(self):
        """Test invalid email formats."""
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user@.com',
            'user space@example.com'
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email(email)

    def test_email_too_long(self):
        """Test email exceeding maximum length."""
        long_email = 'a' * 250 + '@example.com'
        
        with pytest.raises(ValidationError):
            validate_email(long_email)

    def test_email_none(self):
        """Test None email value."""
        with pytest.raises(ValidationError):
            validate_email(None)


class TestUsernameValidation:
    """Tests for username validation."""

    def test_valid_username(self):
        """Test valid usernames."""
        valid_usernames = [
            'user123',
            'john_doe',
            'testuser',
            'User_Name_123'
        ]
        
        for username in valid_usernames:
            assert validate_username(username) == username

    def test_username_too_short(self):
        """Test username below minimum length."""
        with pytest.raises(ValidationError):
            validate_username('ab')

    def test_username_too_long(self):
        """Test username exceeding maximum length."""
        long_username = 'a' * 51
        
        with pytest.raises(ValidationError):
            validate_username(long_username)

    def test_username_invalid_characters(self):
        """Test username with invalid characters."""
        invalid_usernames = [
            'user@name',
            'user name',
            'user!name',
            'user#name'
        ]
        
        for username in invalid_usernames:
            with pytest.raises(ValidationError):
                validate_username(username)


class TestPasswordValidation:
    """Tests for password validation."""

    def test_valid_password(self):
        """Test valid passwords."""
        valid_passwords = [
            'SecurePass123!',
            'MyP@ssw0rd',
            'Complex1ty!@#',
            'Str0ng_P@ss!'
        ]
        
        for password in valid_passwords:
            assert validate_password(password) == password

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

    def test_password_no_digit(self):
        """Test password without digit."""
        with pytest.raises(ValidationError):
            validate_password('NoDigitsHere!')

    def test_password_no_special(self):
        """Test password without special character."""
        with pytest.raises(ValidationError):
            validate_password('NoSpecial123')


class TestRoleValidation:
    """Tests for role validation."""

    def test_valid_roles(self):
        """Test valid role values."""
        valid_roles = ['user', 'admin', 'moderator']
        
        for role in valid_roles:
            assert validate_role(role) == role

    def test_invalid_role(self):
        """Test invalid role value."""
        with pytest.raises(ValidationError):
            validate_role('superadmin')

    def test_role_case_sensitivity(self):
        """Test role case sensitivity."""
        with pytest.raises(ValidationError):
            validate_role('ADMIN')


class TestRatingValidation:
    """Tests for rating validation."""

    def test_valid_ratings(self):
        """Test valid rating values."""
        for rating in [1, 2, 3, 4, 5]:
            assert validate_rating(rating) == rating

    def test_rating_below_minimum(self):
        """Test rating below 1."""
        with pytest.raises(ValidationError):
            validate_rating(0)

    def test_rating_above_maximum(self):
        """Test rating above 5."""
        with pytest.raises(ValidationError):
            validate_rating(6)

    def test_rating_non_integer(self):
        """Test non-integer rating."""
        with pytest.raises(ValidationError):
            validate_rating(3.5)

    def test_rating_string(self):
        """Test string rating."""
        with pytest.raises(ValidationError):
            validate_rating('5')


class TestPositiveIntegerValidation:
    """Tests for positive integer validation."""

    def test_valid_positive_integer(self):
        """Test valid positive integers."""
        assert validate_positive_integer(1, 'field') == 1
        assert validate_positive_integer(100, 'field') == 100
        assert validate_positive_integer(999999, 'field') == 999999

    def test_zero_not_allowed(self):
        """Test zero value."""
        with pytest.raises(ValidationError):
            validate_positive_integer(0, 'field')

    def test_negative_not_allowed(self):
        """Test negative value."""
        with pytest.raises(ValidationError):
            validate_positive_integer(-1, 'field')

    def test_string_conversion(self):
        """Test string to integer conversion."""
        assert validate_positive_integer('42', 'field') == 42

    def test_invalid_string(self):
        """Test invalid string value."""
        with pytest.raises(ValidationError):
            validate_positive_integer('abc', 'field')


class TestStringLengthValidation:
    """Tests for string length validation."""

    def test_valid_string_length(self):
        """Test string within length limits."""
        result = validate_string_length('test', 'field', min_length=1, max_length=10)
        assert result == 'test'

    def test_string_too_short(self):
        """Test string below minimum length."""
        with pytest.raises(ValidationError):
            validate_string_length('ab', 'field', min_length=3)

    def test_string_too_long(self):
        """Test string exceeding maximum length."""
        with pytest.raises(ValidationError):
            validate_string_length('a' * 101, 'field', max_length=100)

    def test_empty_string(self):
        """Test empty string with minimum length."""
        with pytest.raises(ValidationError):
            validate_string_length('', 'field', min_length=1)


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

    def test_same_start_and_end(self):
        """Test same start and end time."""
        time = datetime.now() + timedelta(hours=1)
        
        with pytest.raises(ValidationError):
            validate_booking_times(time, time)

    def test_past_start_time(self):
        """Test start time in the past."""
        start = datetime.now() - timedelta(hours=1)
        end = datetime.now() + timedelta(hours=1)
        
        with pytest.raises(ValidationError):
            validate_booking_times(start, end)


class TestDatetimeValidation:
    """Tests for datetime validation."""

    def test_valid_datetime_string(self):
        """Test valid ISO datetime string."""
        dt_string = '2024-12-25T10:00:00'
        result = validate_datetime(dt_string)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25

    def test_valid_datetime_object(self):
        """Test datetime object input."""
        dt = datetime(2024, 12, 25, 10, 0, 0)
        result = validate_datetime(dt)
        
        assert result == dt

    def test_invalid_datetime_string(self):
        """Test invalid datetime string."""
        with pytest.raises(ValidationError):
            validate_datetime('not-a-datetime')

    def test_none_datetime(self):
        """Test None datetime value."""
        with pytest.raises(ValidationError):
            validate_datetime(None)


class TestCapacityValidation:
    """Tests for capacity validation."""

    def test_valid_capacity(self):
        """Test valid capacity values."""
        assert validate_capacity(1) == 1
        assert validate_capacity(50) == 50
        assert validate_capacity(500) == 500

    def test_zero_capacity(self):
        """Test zero capacity."""
        with pytest.raises(ValidationError):
            validate_capacity(0)

    def test_negative_capacity(self):
        """Test negative capacity."""
        with pytest.raises(ValidationError):
            validate_capacity(-10)

    def test_capacity_too_large(self):
        """Test capacity exceeding maximum."""
        with pytest.raises(ValidationError):
            validate_capacity(10001)


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

    def test_empty_field_value(self):
        """Test empty required field value."""
        data = {'name': '', 'email': 'test@example.com'}
        required = ['name', 'email']
        
        with pytest.raises(ValidationError):
            validate_required_fields(data, required)

    def test_none_field_value(self):
        """Test None required field value."""
        data = {'name': None, 'email': 'test@example.com'}
        required = ['name', 'email']
        
        with pytest.raises(ValidationError):
            validate_required_fields(data, required)
