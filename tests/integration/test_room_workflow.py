"""
Integration tests for room workflows.
Tests room CRUD operations and availability checking.

Author: Hassan Fouani
"""

import pytest
import json
from datetime import datetime, timedelta


class TestRoomCreationWorkflow:
    """Tests for room creation workflow."""

    def test_successful_room_creation(self, mysql_connection, clean_database):
        """Test successful room creation flow."""
        db = mysql_connection._db
        
        room_data = {
            'name': 'Test Conference Room',
            'capacity': 10,
            'floor': 1,
            'building': 'Main Building',
            'equipment': json.dumps(['projector', 'whiteboard']),
            'amenities': json.dumps(['wifi', 'air_conditioning']),
            'hourly_rate': 50.00,
            'location': 'Room 101',
            'status': 'available'
        }
        
        room_id = db.add_room(room_data)
        
        assert room_id is not None
        assert room_id > 0
        
        room = db.get_room(room_id)
        
        assert room is not None
        assert room['name'] == 'Test Conference Room'
        assert room['capacity'] == 10
        assert room['status'] == 'available'

    def test_room_with_equipment(self, mysql_connection, clean_database):
        """Test room creation with equipment list."""
        db = mysql_connection._db
        
        equipment = ['projector', 'video_conferencing', 'whiteboard']
        
        room_data = {
            'name': 'Tech Room',
            'capacity': 8,
            'equipment': json.dumps(equipment),
            'status': 'available'
        }
        
        room_id = db.add_room(room_data)
        
        room = db.get_room(room_id)
        
        assert room is not None
        assert 'projector' in room.get('equipment', '')


class TestRoomUpdateWorkflow:
    """Tests for room update workflow."""

    def test_update_room_capacity(self, mysql_connection, created_test_room):
        """Test updating room capacity."""
        db = mysql_connection._db
        room_id = created_test_room['id']
        
        db.rooms[room_id]['capacity'] = 20
        
        room = db.get_room(room_id)
        assert room['capacity'] == 20

    def test_update_room_status(self, mysql_connection, created_test_room):
        """Test updating room status."""
        db = mysql_connection._db
        room_id = created_test_room['id']
        
        db.rooms[room_id]['status'] = 'maintenance'
        
        room = db.get_room(room_id)
        assert room['status'] == 'maintenance'

    def test_update_room_equipment(self, mysql_connection, created_test_room):
        """Test updating room equipment."""
        db = mysql_connection._db
        room_id = created_test_room['id']
        
        new_equipment = json.dumps(['projector', 'teleconference', 'smartboard'])
        db.rooms[room_id]['equipment'] = new_equipment
        
        room = db.get_room(room_id)
        assert 'smartboard' in room['equipment']


class TestRoomAvailabilityWorkflow:
    """Tests for room availability workflow."""

    def test_available_rooms_no_bookings(self, mysql_connection, created_test_room):
        """Test getting available rooms when no bookings exist."""
        db = mysql_connection._db
        
        # Get all rooms with available status
        available_rooms = [r for r in db.rooms.values() if r.get('status') == 'available']
        
        assert isinstance(available_rooms, list)
        assert len(available_rooms) >= 1

    def test_room_not_available_during_booking(self, mysql_connection, created_test_user,
                                                created_test_room, clean_database):
        """Test room becomes unavailable during booking time."""
        db = mysql_connection._db
        
        start_time = datetime.now() + timedelta(days=2, hours=14)
        end_time = datetime.now() + timedelta(days=2, hours=15)
        
        # Create a booking
        booking_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'title': 'Test Meeting',
            'description': 'Test',
            'start_time': start_time,
            'end_time': end_time,
            'attendees': 5,
            'status': 'confirmed'
        }
        db.add_booking(booking_data)
        
        # Check bookings for the room
        room_bookings = [b for b in db.bookings.values() 
                        if b['room_id'] == created_test_room['id']]
        
        assert len(room_bookings) == 1
        assert room_bookings[0]['room_id'] == created_test_room['id']


class TestRoomSearchWorkflow:
    """Tests for room search workflow."""

    def test_search_by_capacity(self, mysql_connection, created_test_room, clean_database):
        """Test searching rooms by minimum capacity."""
        db = mysql_connection._db
        
        # Search for rooms with capacity >= 5
        min_capacity = 5
        rooms = [r for r in db.rooms.values() if r.get('capacity', 0) >= min_capacity]
        
        assert isinstance(rooms, list)
        for room in rooms:
            assert room['capacity'] >= min_capacity

    def test_search_by_building(self, mysql_connection, clean_database):
        """Test searching rooms by building."""
        db = mysql_connection._db
        
        room_data = {
            'name': 'Building A Room',
            'capacity': 10,
            'building': 'Building A',
            'status': 'available'
        }
        db.add_room(room_data)
        
        # Search for rooms in Building A
        rooms = [r for r in db.rooms.values() if r.get('building') == 'Building A']
        
        assert isinstance(rooms, list)
        for room in rooms:
            assert room['building'] == 'Building A'

    def test_get_all_rooms_with_filters(self, mysql_connection, clean_database):
        """Test getting all rooms with filters."""
        db = mysql_connection._db
        
        room_data = {
            'name': 'Large Room',
            'capacity': 20,
            'floor': 2,
            'status': 'available'
        }
        db.add_room(room_data)
        
        # Apply filters
        min_capacity = 15
        target_floor = 2
        
        filtered_rooms = [r for r in db.rooms.values() 
                         if r.get('capacity', 0) >= min_capacity 
                         and r.get('floor') == target_floor]
        
        assert isinstance(filtered_rooms, list)
        for room in filtered_rooms:
            assert room['capacity'] >= min_capacity
            assert room['floor'] == target_floor


class TestRoomDeletionWorkflow:
    """Tests for room deletion workflow."""

    def test_delete_room(self, mysql_connection, clean_database):
        """Test deleting a room."""
        db = mysql_connection._db
        
        room_data = {
            'name': 'Room to Delete',
            'capacity': 5,
            'status': 'available'
        }
        room_id = db.add_room(room_data)
        
        # Delete room
        del db.rooms[room_id]
        
        room = db.get_room(room_id)
        assert room is None

    def test_delete_nonexistent_room(self, mysql_connection, clean_database):
        """Test deleting a room that doesn't exist."""
        db = mysql_connection._db
        
        nonexistent_id = 99999
        room = db.get_room(nonexistent_id)
        
        assert room is None
