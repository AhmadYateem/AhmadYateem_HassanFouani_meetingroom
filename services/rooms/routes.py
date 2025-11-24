"""
Flask routes for the Rooms service using raw MySQL DAO.
"""

from datetime import datetime
import json
from flask import Blueprint, jsonify, request

from database.connection import MySQLConnectionPool, get_connection
from services.rooms import dao


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
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        rooms = dao.get_all_rooms(conn, filters)
    return _success(rooms)


@bp.route("/api/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id: int):
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        room = dao.get_room_by_id(conn, room_id)
    if not room:
        return _error("Room not found", 404)
    return _success(room)


@bp.route("/api/rooms", methods=["POST"])
def create_room_route():
    data = request.get_json() or {}
    required = ["name", "capacity"]
    for key in required:
        if key not in data:
            return _error(f"Missing required field: {key}", 400)

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        room_id = dao.create_room(
            conn,
            name=data["name"],
            capacity=data["capacity"],
            floor=data.get("floor"),
            building=data.get("building"),
            equipment=data.get("equipment"),
            amenities=data.get("amenities"),
            hourly_rate=data.get("hourly_rate"),
            location=data.get("location"),
        )
    return _success({"id": room_id, "message": "Room created"}, 201)


@bp.route("/api/rooms/<int:room_id>", methods=["PUT"])
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
    update_data = {k: v for k, v in data.items() if k in allowed}
    if not update_data:
        return _error("No valid fields to update", 400)

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        updated = dao.update_room(conn, room_id, **update_data)
    if not updated:
        return _error("Room not found", 404)
    return _success({"id": room_id, "message": "Room updated"})


@bp.route("/api/rooms/<int:room_id>", methods=["DELETE"])
def delete_room_route(room_id: int):
    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
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

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
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

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
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
def update_status(room_id: int):
    data = request.get_json() or {}
    status = data.get("status")
    if not status:
        return _error("Missing status", 400)

    pool: MySQLConnectionPool = bp.pool  # type: ignore[attr-defined]
    with get_connection(pool) as conn:
        updated = dao.update_room_status(conn, room_id, status)
    if not updated:
        return _error("Room not found", 404)
    return _success({"id": room_id, "message": "Status updated"})
