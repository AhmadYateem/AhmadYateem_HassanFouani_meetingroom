"""
Integration tests for booking workflows.
Tests complete booking creation, conflict detection, and cancellation flows.
"""

import pytest
import json
from datetime import datetime, timedelta


class TestBookingCreationWorkflow:
    """Tests for booking creation workflow."""

    def test_successful_booking_creation(self, mysql_connection, created_test_user, 
                                         created_test_room, sample_booking_data, clean_database):
        """Test successful booking creation flow."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        booking_id = dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Team Meeting',
            description='Weekly team sync',
            start_time=start_time,
            end_time=end_time,
            attendees=5
        )
        
        assert booking_id is not None
        assert booking_id > 0
        
        booking = dao.get_booking_by_id(mysql_connection, booking_id)
        
        assert booking is not None
        assert booking['title'] == 'Team Meeting'
        assert booking['status'] == 'confirmed'
        assert booking['user_id'] == created_test_user['id']
        assert booking['room_id'] == created_test_room['id']

    def test_booking_with_user_and_room_details(self, mysql_connection, created_test_user,
                                                 created_test_room, clean_database):
        """Test booking includes user and room details."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        booking_id = dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        booking = dao.get_booking_by_id(mysql_connection, booking_id)
        
        assert booking['username'] == created_test_user['username']
        assert booking['room_name'] == created_test_room['name']


class TestConflictDetectionWorkflow:
    """Tests for booking conflict detection workflow."""

    def test_detect_exact_overlap(self, mysql_connection, created_test_user,
                                  created_test_room, clean_database):
        """Test detecting exact time overlap conflict."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='First Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        is_available = dao.check_availability(
            mysql_connection,
            room_id=created_test_room['id'],
            start_time=start_time,
            end_time=end_time
        )
        
        assert is_available is False

    def test_detect_partial_overlap_start(self, mysql_connection, created_test_user,
                                          created_test_room, clean_database):
        """Test detecting partial overlap at start."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='First Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        new_start = start_time - timedelta(minutes=30)
        new_end = start_time + timedelta(minutes=30)
        
        is_available = dao.check_availability(
            mysql_connection,
            room_id=created_test_room['id'],
            start_time=new_start,
            end_time=new_end
        )
        
        assert is_available is False

    def test_detect_partial_overlap_end(self, mysql_connection, created_test_user,
                                        created_test_room, clean_database):
        """Test detecting partial overlap at end."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='First Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        new_start = end_time - timedelta(minutes=30)
        new_end = end_time + timedelta(minutes=30)
        
        is_available = dao.check_availability(
            mysql_connection,
            room_id=created_test_room['id'],
            start_time=new_start,
            end_time=new_end
        )
        
        assert is_available is False

    def test_detect_contained_booking(self, mysql_connection, created_test_user,
                                      created_test_room, clean_database):
        """Test detecting new booking contained in existing."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=11)
        
        dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Long Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        new_start = start_time + timedelta(minutes=30)
        new_end = end_time - timedelta(minutes=30)
        
        is_available = dao.check_availability(
            mysql_connection,
            room_id=created_test_room['id'],
            start_time=new_start,
            end_time=new_end
        )
        
        assert is_available is False

    def test_no_conflict_adjacent_bookings(self, mysql_connection, created_test_user,
                                           created_test_room, clean_database):
        """Test no conflict for adjacent time slots."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='First Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        is_available = dao.check_availability(
            mysql_connection,
            room_id=created_test_room['id'],
            start_time=end_time,
            end_time=end_time + timedelta(hours=1)
        )
        
        assert is_available is True

    def test_get_conflicts_returns_details(self, mysql_connection, created_test_user,
                                           created_test_room, clean_database):
        """Test getting conflict details."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Conflicting Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        conflicts = dao.get_conflicts(
            mysql_connection,
            room_id=created_test_room['id'],
            start_time=start_time,
            end_time=end_time
        )
        
        assert len(conflicts) == 1
        assert conflicts[0]['title'] == 'Conflicting Meeting'


class TestBookingCancellationWorkflow:
    """Tests for booking cancellation workflow."""

    def test_cancel_booking(self, mysql_connection, created_test_user,
                           created_test_room, clean_database):
        """Test cancelling a booking."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        booking_id = dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Meeting to Cancel',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        result = dao.cancel_booking(
            mysql_connection,
            booking_id=booking_id,
            cancelled_by=created_test_user['id'],
            cancellation_reason='Schedule conflict'
        )
        
        assert result is True
        
        booking = dao.get_booking_by_id(mysql_connection, booking_id)
        
        assert booking['status'] == 'cancelled'
        assert booking['cancellation_reason'] == 'Schedule conflict'
        assert booking['cancelled_by'] == created_test_user['id']

    def test_cancelled_booking_frees_slot(self, mysql_connection, created_test_user,
                                          created_test_room, clean_database):
        """Test cancelled booking frees time slot."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        
        booking_id = dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        dao.cancel_booking(
            mysql_connection,
            booking_id=booking_id,
            cancelled_by=created_test_user['id']
        )
        
        is_available = dao.check_availability(
            mysql_connection,
            room_id=created_test_room['id'],
            start_time=start_time,
            end_time=end_time
        )
        
        assert is_available is True


class TestRecurringBookingWorkflow:
    """Tests for recurring booking workflow."""

    def test_create_daily_recurring(self, mysql_connection, created_test_user,
                                    created_test_room, clean_database):
        """Test creating daily recurring booking."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        recurrence_end = datetime.now() + timedelta(days=5)
        
        booking_ids = dao.create_recurring_bookings(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Daily Standup',
            description='Daily team standup',
            start_time=start_time,
            end_time=end_time,
            attendees=5,
            pattern='daily',
            end_date=recurrence_end
        )
        
        assert len(booking_ids) >= 1

    def test_create_weekly_recurring(self, mysql_connection, created_test_user,
                                     created_test_room, clean_database):
        """Test creating weekly recurring booking."""
        from services.bookings import dao
        
        start_time = datetime.now() + timedelta(days=1, hours=9)
        end_time = datetime.now() + timedelta(days=1, hours=10)
        recurrence_end = datetime.now() + timedelta(weeks=4)
        
        booking_ids = dao.create_recurring_bookings(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Weekly Review',
            description='Weekly team review',
            start_time=start_time,
            end_time=end_time,
            attendees=10,
            pattern='weekly',
            end_date=recurrence_end
        )
        
        assert len(booking_ids) >= 1


class TestAvailabilityCheckingWorkflow:
    """Tests for availability checking workflow."""

    def test_get_availability_matrix(self, mysql_connection, created_test_user,
                                     created_test_room, clean_database):
        """Test getting hourly availability matrix."""
        from services.bookings import dao
        
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
        
        dao.create_booking(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            title='Morning Meeting',
            description='Test',
            start_time=start_time,
            end_time=end_time,
            attendees=3
        )
        
        availability = dao.get_availability_matrix(
            mysql_connection,
            room_id=created_test_room['id'],
            date=tomorrow
        )
        
        assert len(availability) == 24
        
        assert availability[9]['available'] is False
        assert availability[10]['available'] is False
        
        assert availability[8]['available'] is True
        assert availability[11]['available'] is True

    def test_get_user_bookings(self, mysql_connection, created_test_user,
                               created_test_room, clean_database):
        """Test getting user's bookings."""
        from services.bookings import dao
        
        for i in range(3):
            start_time = datetime.now() + timedelta(days=i+1, hours=9)
            end_time = datetime.now() + timedelta(days=i+1, hours=10)
            
            dao.create_booking(
                mysql_connection,
                user_id=created_test_user['id'],
                room_id=created_test_room['id'],
                title=f'Meeting {i+1}',
                description='Test',
                start_time=start_time,
                end_time=end_time,
                attendees=3
            )
        
        user_bookings = dao.get_user_bookings(
            mysql_connection,
            user_id=created_test_user['id']
        )
        
        assert len(user_bookings) == 3
