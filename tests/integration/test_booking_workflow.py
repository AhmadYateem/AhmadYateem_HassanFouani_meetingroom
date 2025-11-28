"""
Integration tests for booking workflows.
Tests booking creation, conflict detection, and cancellation.

Author: Ahmad Yateem
"""

import pytest
from datetime import datetime, timedelta


class TestBookingCreationWorkflow:
    """Tests for booking creation workflow."""

    def test_successful_booking_creation(self, mysql_connection, created_test_user, 
                                         created_test_room):
        """Test successful booking creation flow."""
        db = mysql_connection._db
        
        start_time = datetime.now() + timedelta(days=1, hours=10)
        end_time = datetime.now() + timedelta(days=1, hours=11)
        
        booking_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Team Standup',
            'description': 'Daily standup meeting',
            'start_time': start_time,
            'end_time': end_time,
            'attendees': 5,
            'status': 'confirmed'
        }
        
        booking_id = db.add_booking(booking_data)
        
        assert booking_id is not None
        assert booking_id > 0
        
        booking = db.bookings[booking_id]
        
        assert booking is not None
        assert booking['user_id'] == created_test_user['id']
        assert booking['room_id'] == created_test_room['id']
        assert booking['title'] == 'Team Standup'

    def test_booking_with_user_and_room_details(self, mysql_connection, created_test_user,
                                                 created_test_room):
        """Test booking includes user and room details."""
        db = mysql_connection._db
        
        start_time = datetime.now() + timedelta(days=2, hours=14)
        end_time = datetime.now() + timedelta(days=2, hours=15)
        
        booking_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Project Review',
            'description': 'Quarterly review',
            'start_time': start_time,
            'end_time': end_time,
            'attendees': 8,
            'status': 'confirmed'
        }
        
        booking_id = db.add_booking(booking_data)
        booking = db.bookings[booking_id]
        
        # Verify booking is linked to user and room
        user = db.get_user(booking['user_id'])
        room = db.get_room(booking['room_id'])
        
        assert user is not None
        assert room is not None
        assert user['id'] == created_test_user['id']
        assert room['id'] == created_test_room['id']


class TestConflictDetectionWorkflow:
    """Tests for booking conflict detection."""

    def test_detect_exact_overlap(self, mysql_connection, created_test_user,
                                   created_test_room):
        """Test detection of exact time overlap."""
        db = mysql_connection._db
        
        start_time = datetime.now() + timedelta(days=3, hours=10)
        end_time = datetime.now() + timedelta(days=3, hours=11)
        
        # Create first booking
        booking1_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Meeting 1',
            'start_time': start_time,
            'end_time': end_time,
            'status': 'confirmed'
        }
        db.add_booking(booking1_data)
        
        # Check for conflicts (same time, same room)
        conflicts = [b for b in db.bookings.values()
                    if b['room_id'] == created_test_room['id']
                    and b['start_time'] == start_time
                    and b['end_time'] == end_time]
        
        assert len(conflicts) == 1

    def test_detect_partial_overlap_start(self, mysql_connection, created_test_user,
                                          created_test_room):
        """Test detection of partial overlap at start."""
        db = mysql_connection._db
        
        base_start = datetime.now() + timedelta(days=4, hours=10)
        base_end = datetime.now() + timedelta(days=4, hours=12)
        
        # Create first booking 10:00 - 12:00
        booking1_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Meeting 1',
            'start_time': base_start,
            'end_time': base_end,
            'status': 'confirmed'
        }
        db.add_booking(booking1_data)
        
        # Check for overlap with 11:00 - 13:00
        new_start = base_start + timedelta(hours=1)
        new_end = base_end + timedelta(hours=1)
        
        # Find overlapping bookings
        overlaps = []
        for b in db.bookings.values():
            if b['room_id'] == created_test_room['id']:
                if not (b['end_time'] <= new_start or b['start_time'] >= new_end):
                    overlaps.append(b)
        
        assert len(overlaps) == 1

    def test_detect_partial_overlap_end(self, mysql_connection, created_test_user,
                                        created_test_room):
        """Test detection of partial overlap at end."""
        db = mysql_connection._db
        
        base_start = datetime.now() + timedelta(days=5, hours=14)
        base_end = datetime.now() + timedelta(days=5, hours=16)
        
        # Create first booking 14:00 - 16:00
        booking1_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Meeting 1',
            'start_time': base_start,
            'end_time': base_end,
            'status': 'confirmed'
        }
        db.add_booking(booking1_data)
        
        # Check for overlap with 13:00 - 15:00
        new_start = base_start - timedelta(hours=1)
        new_end = base_end - timedelta(hours=1)
        
        # Find overlapping bookings
        overlaps = []
        for b in db.bookings.values():
            if b['room_id'] == created_test_room['id']:
                if not (b['end_time'] <= new_start or b['start_time'] >= new_end):
                    overlaps.append(b)
        
        assert len(overlaps) == 1

    def test_detect_contained_booking(self, mysql_connection, created_test_user,
                                      created_test_room):
        """Test detection of booking contained within another."""
        db = mysql_connection._db
        
        # Create booking 10:00 - 14:00
        outer_start = datetime.now() + timedelta(days=6, hours=10)
        outer_end = datetime.now() + timedelta(days=6, hours=14)
        
        booking_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Long Meeting',
            'start_time': outer_start,
            'end_time': outer_end,
            'status': 'confirmed'
        }
        db.add_booking(booking_data)
        
        # Check for contained booking 11:00 - 13:00
        inner_start = outer_start + timedelta(hours=1)
        inner_end = outer_end - timedelta(hours=1)
        
        # Find overlapping bookings
        overlaps = []
        for b in db.bookings.values():
            if b['room_id'] == created_test_room['id']:
                if not (b['end_time'] <= inner_start or b['start_time'] >= inner_end):
                    overlaps.append(b)
        
        assert len(overlaps) == 1

    def test_no_conflict_adjacent_bookings(self, mysql_connection, created_test_user,
                                           created_test_room):
        """Test no conflict for adjacent bookings."""
        db = mysql_connection._db
        
        first_start = datetime.now() + timedelta(days=7, hours=10)
        first_end = datetime.now() + timedelta(days=7, hours=11)
        
        # Create first booking 10:00 - 11:00
        booking1_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Meeting 1',
            'start_time': first_start,
            'end_time': first_end,
            'status': 'confirmed'
        }
        db.add_booking(booking1_data)
        
        # Check for adjacent booking 11:00 - 12:00 (no overlap)
        adjacent_start = first_end
        adjacent_end = first_end + timedelta(hours=1)
        
        # Find overlapping bookings
        overlaps = []
        for b in db.bookings.values():
            if b['room_id'] == created_test_room['id']:
                if not (b['end_time'] <= adjacent_start or b['start_time'] >= adjacent_end):
                    overlaps.append(b)
        
        assert len(overlaps) == 0

    def test_get_conflicts_returns_details(self, mysql_connection, created_test_user,
                                           created_test_room):
        """Test conflict detection returns booking details."""
        db = mysql_connection._db
        
        start_time = datetime.now() + timedelta(days=8, hours=10)
        end_time = datetime.now() + timedelta(days=8, hours=12)
        
        booking_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Original Meeting',
            'start_time': start_time,
            'end_time': end_time,
            'status': 'confirmed'
        }
        db.add_booking(booking_data)
        
        # Get conflicts with booking details
        conflicts = []
        for b in db.bookings.values():
            if b['room_id'] == created_test_room['id']:
                if not (b['end_time'] <= start_time or b['start_time'] >= end_time):
                    conflicts.append(b)
        
        assert len(conflicts) == 1
        assert 'title' in conflicts[0]
        assert 'start_time' in conflicts[0]
        assert 'end_time' in conflicts[0]


class TestBookingCancellationWorkflow:
    """Tests for booking cancellation."""

    def test_cancel_booking(self, mysql_connection, created_test_booking):
        """Test cancelling a booking."""
        db = mysql_connection._db
        booking_id = created_test_booking['id']
        
        # Cancel the booking
        db.bookings[booking_id]['status'] = 'cancelled'
        
        booking = db.bookings[booking_id]
        
        assert booking['status'] == 'cancelled'

    def test_cancelled_booking_frees_slot(self, mysql_connection, created_test_user,
                                          created_test_room):
        """Test cancelling booking frees the time slot."""
        db = mysql_connection._db
        
        start_time = datetime.now() + timedelta(days=9, hours=10)
        end_time = datetime.now() + timedelta(days=9, hours=11)
        
        # Create and then cancel booking
        booking_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Meeting to Cancel',
            'start_time': start_time,
            'end_time': end_time,
            'status': 'confirmed'
        }
        booking_id = db.add_booking(booking_data)
        
        # Cancel the booking
        db.bookings[booking_id]['status'] = 'cancelled'
        
        # Check that slot is now free (no active bookings)
        active_bookings = [b for b in db.bookings.values()
                         if b['room_id'] == created_test_room['id']
                         and b['status'] != 'cancelled'
                         and not (b['end_time'] <= start_time or b['start_time'] >= end_time)]
        
        assert len(active_bookings) == 0


class TestRecurringBookingWorkflow:
    """Tests for recurring bookings."""

    def test_create_daily_recurring(self, mysql_connection, created_test_user,
                                    created_test_room):
        """Test creating daily recurring bookings."""
        db = mysql_connection._db
        
        base_start = datetime.now() + timedelta(days=10, hours=9)
        base_end = datetime.now() + timedelta(days=10, hours=10)
        
        # Create 5 daily recurring bookings
        for i in range(5):
            booking_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'title': f'Daily Standup Day {i+1}',
                'start_time': base_start + timedelta(days=i),
                'end_time': base_end + timedelta(days=i),
                'status': 'confirmed',
                'recurrence': 'daily'
            }
            db.add_booking(booking_data)
        
        user_bookings = [b for b in db.bookings.values()
                        if b['user_id'] == created_test_user['id']]
        
        assert len(user_bookings) == 5

    def test_create_weekly_recurring(self, mysql_connection, created_test_user,
                                     created_test_room):
        """Test creating weekly recurring bookings."""
        db = mysql_connection._db
        
        base_start = datetime.now() + timedelta(days=15, hours=14)
        base_end = datetime.now() + timedelta(days=15, hours=15)
        
        # Create 4 weekly recurring bookings
        for i in range(4):
            booking_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'title': f'Weekly Review Week {i+1}',
                'start_time': base_start + timedelta(weeks=i),
                'end_time': base_end + timedelta(weeks=i),
                'status': 'confirmed',
                'recurrence': 'weekly'
            }
            db.add_booking(booking_data)
        
        user_bookings = [b for b in db.bookings.values()
                        if b['user_id'] == created_test_user['id']]
        
        assert len(user_bookings) == 4


class TestAvailabilityCheckingWorkflow:
    """Tests for room availability checking."""

    def test_get_availability_matrix(self, mysql_connection, created_test_room):
        """Test getting room availability matrix."""
        db = mysql_connection._db
        
        # Room should be available when no bookings
        room = db.get_room(created_test_room['id'])
        
        assert room is not None
        assert room['status'] == 'available'

    def test_get_user_bookings(self, mysql_connection, created_test_user,
                               created_test_room):
        """Test getting all bookings for a user."""
        db = mysql_connection._db
        
        # Create multiple bookings for user
        for i in range(3):
            booking_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'title': f'User Meeting {i+1}',
                'start_time': datetime.now() + timedelta(days=20+i, hours=10),
                'end_time': datetime.now() + timedelta(days=20+i, hours=11),
                'status': 'confirmed'
            }
            db.add_booking(booking_data)
        
        user_bookings = [b for b in db.bookings.values()
                        if b['user_id'] == created_test_user['id']]
        
        assert len(user_bookings) == 3
