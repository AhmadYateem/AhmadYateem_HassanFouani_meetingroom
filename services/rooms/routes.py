"""
Flask routes for the Rooms service using raw MySQL DAO.

Author: Hassan Fouani
"""

from datetime import datetime
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from database.connection import MySQLConnectionPool, get_connection
from services.rooms import dao
from utils.validators import validate_required_fields, validate_positive_integer, validate_string_length
from utils.sanitizers import sanitize_string
from utils.auth import get_current_user, facility_manager_required, admin_required


bp = Blueprint("rooms", __name__)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _error(message: str, code: int = 400):
    return jsonify({"error": message}), code


def _success(payload, code: int = 200):
    return jsonify(payload), code


@bp.route("/health", methods=["GET"])
def health():
    return _success({"status": "healthy", "service": "rooms"})


@bp.route("/api/rooms", methods=["GET"])
def list_rooms():
    filters = {
        "capacity_min": request.args.get("capacity_min", type=int),
        "capacity_max": request.args.get("capacity_max", type=int),
        "floor": request.args.get("floor", type=int),
        "building": request.args.get("building"),
        "status": request.args.get("status"),
    }
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        rooms = dao.get_all_rooms(conn, filters)
    return _success(rooms)


@bp.route("/api/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id: int):
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        room = dao.get_room_by_id(conn, room_id)
    if not room:
        return _error("Room not found", 404)
    return _success(room)


@bp.route("/api/rooms", methods=["POST"])
@jwt_required()
@facility_manager_required
def create_room_route():
    data = request.get_json() or {}
    required = ["name", "capacity"]
    for key in required:
        if key not in data:
            return _error(f"Missing required field: {key}", 400)
    
    name = sanitize_string(data["name"])
    if not name or len(name) < 2:
        return _error("Room name must be at least 2 characters", 400)
    
    capacity = data["capacity"]
    if not isinstance(capacity, int) or capacity < 1:
        return _error("Capacity must be a positive integer", 400)

    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        room_id = dao.create_room(
            conn,
            name=name,
            capacity=capacity,
            floor=data.get("floor"),
            building=sanitize_string(data.get("building", "")) if data.get("building") else None,
            equipment=data.get("equipment"),
            amenities=data.get("amenities"),
            hourly_rate=data.get("hourly_rate"),
            location=sanitize_string(data.get("location", "")) if data.get("location") else None,
        )
    return _success({"id": room_id, "message": "Room created"}, 201)


@bp.route("/api/rooms/<int:room_id>", methods=["PUT"])
@jwt_required()
@facility_manager_required
def update_room_route(room_id: int):
    data = request.get_json() or {}
    allowed = {
        "name",
        "capacity",
        "floor",
        "building",
        "location",
        "equipment",
        "amenities",
        "status",
        "hourly_rate",
    }
    update_data = {}
    
    for key in allowed:
        if key in data:
            if key in ["name", "building", "location"]:
                update_data[key] = sanitize_string(data[key]) if data[key] else None
            elif key == "capacity":
                if not isinstance(data[key], int) or data[key] < 1:
                    return _error("Capacity must be a positive integer", 400)
                update_data[key] = data[key]
            else:
                update_data[key] = data[key]
    
    if not update_data:
        return _error("No valid fields to update", 400)

    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        updated = dao.update_room(conn, room_id, **update_data)
    if not updated:
        return _error("Room not found", 404)
    return _success({"id": room_id, "message": "Room updated"})


@bp.route("/api/rooms/<int:room_id>", methods=["DELETE"])
@jwt_required()
@facility_manager_required
def delete_room_route(room_id: int):
    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        deleted = dao.delete_room(conn, room_id)
    if not deleted:
        return _error("Room not found", 404)
    return _success({"id": room_id, "message": "Room deleted"})


@bp.route("/api/rooms/available", methods=["GET"])
def available_rooms():
    start_time_str = request.args.get("start_time")
    end_time_str = request.args.get("end_time")
    if not start_time_str or not end_time_str:
        return _error("start_time and end_time are required", 400)

    try:
        start_time = _parse_iso(start_time_str)
        end_time = _parse_iso(end_time_str)
    except ValueError:
        return _error("Invalid datetime format. Use ISO 8601.", 400)

    capacity_min = request.args.get("capacity_min", type=int)
    equipment_raw = request.args.get("equipment")
    equipment = [e.strip() for e in equipment_raw.split(",")] if equipment_raw else None

    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        rooms = dao.get_available_rooms(
            conn,
            start_time=start_time,
            end_time=end_time,
            capacity_min=capacity_min,
            equipment=equipment,
        )
    return _success(rooms)


@bp.route("/api/rooms/search", methods=["POST"])
def search_rooms_route():
    data = request.get_json() or {}
    capacity = data.get("capacity")
    floor = data.get("floor")
    building = data.get("building")
    equipment = data.get("equipment")
    amenities = data.get("amenities")
    query_text = data.get("query")

    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        rooms = dao.search_rooms(
            conn,
            capacity=capacity,
            equipment=equipment,
            amenities=amenities,
            floor=floor,
            building=building,
            query_text=query_text,
        )
    return _success(rooms)


@bp.route("/api/rooms/status/<int:room_id>", methods=["PUT"])
@jwt_required()
@facility_manager_required
def update_status(room_id: int):
    data = request.get_json() or {}
    status = data.get("status")
    if not status:
        return _error("Missing status", 400)
    
    valid_statuses = ["available", "booked", "maintenance", "out_of_service"]
    if status not in valid_statuses:
        return _error(f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 400)

    pool: MySQLConnectionPool = bp.pool
    with get_connection(pool) as conn:
        updated = dao.update_room_status(conn, room_id, status)
    if not updated:
        return _error("Room not found", 404)
    return _success({"id": room_id, "message": "Status updated"})
