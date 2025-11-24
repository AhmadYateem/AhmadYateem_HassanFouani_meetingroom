"""
Rooms DAO with raw MySQL queries.
"""

import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

from mysql.connector.connection import MySQLConnection


def _json_or_empty(value: Optional[Sequence[str]]) -> str:
    return json.dumps(value or [])


def create_room(
    connection: MySQLConnection,
    name: str,
    capacity: int,
    floor: Optional[int],
    building: Optional[str],
    equipment: Optional[Sequence[str]],
    amenities: Optional[Sequence[str]],
    hourly_rate: Optional[float],
    location: Optional[str] = None,
) -> int:
    cursor = connection.cursor()
    query = """
        INSERT INTO rooms (name, capacity, floor, building, location, equipment, amenities, status, hourly_rate)
        VALUES (%s, %s, %s, %s, %s, CAST(%s AS JSON), CAST(%s AS JSON), %s, %s)
    """
    cursor.execute(
        query,
        (
            name,
            capacity,
            floor,
            building,
            location,
            _json_or_empty(equipment),
            _json_or_empty(amenities),
            "available",
            hourly_rate,
        ),
    )
    room_id = cursor.lastrowid
    cursor.close()
    return room_id


def get_room_by_id(connection: MySQLConnection, room_id: int) -> Optional[Dict[str, Any]]:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
    row = cursor.fetchone()
    cursor.close()
    return row


def get_all_rooms(
    connection: MySQLConnection,
    filters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    clauses = []
    params: List[Any] = []

    if filters.get("capacity_min") is not None:
        clauses.append("capacity >= %s")
        params.append(filters["capacity_min"])

    if filters.get("capacity_max") is not None:
        clauses.append("capacity <= %s")
        params.append(filters["capacity_max"])

    if filters.get("floor") is not None:
        clauses.append("floor = %s")
        params.append(filters["floor"])

    if filters.get("building"):
        clauses.append("building = %s")
        params.append(filters["building"])

    if filters.get("status"):
        clauses.append("status = %s")
        params.append(filters["status"])

    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)

    sql = f"SELECT * FROM rooms {where_sql} ORDER BY name"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def update_room(connection: MySQLConnection, room_id: int, **kwargs) -> bool:
    if not kwargs:
        return False

    fields = []
    params: List[Any] = []
    for key, value in kwargs.items():
        if key in {"equipment", "amenities"}:
            fields.append(f"{key} = CAST(%s AS JSON)")
            params.append(_json_or_empty(value))
        else:
            fields.append(f"{key} = %s")
            params.append(value)

    params.append(room_id)

    sql = f"UPDATE rooms SET {', '.join(fields)} WHERE id = %s"
    cursor = connection.cursor()
    cursor.execute(sql, tuple(params))
    updated = cursor.rowcount > 0
    cursor.close()
    return updated


def delete_room(connection: MySQLConnection, room_id: int) -> bool:
    cursor = connection.cursor()
    cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
    deleted = cursor.rowcount > 0
    cursor.close()
    return deleted


def search_rooms(
    connection: MySQLConnection,
    capacity: Optional[int],
    equipment: Optional[Sequence[str]],
    amenities: Optional[Sequence[str]],
    floor: Optional[int],
    building: Optional[str],
    query_text: Optional[str] = None,
) -> List[Dict[str, Any]]:
    clauses = []
    params: List[Any] = []

    if capacity is not None:
        clauses.append("capacity >= %s")
        params.append(capacity)

    if floor is not None:
        clauses.append("floor = %s")
        params.append(floor)

    if building:
        clauses.append("building = %s")
        params.append(building)

    if equipment:
        for item in equipment:
            clauses.append("JSON_CONTAINS(equipment, %s)")
            params.append(json.dumps([item]))

    if amenities:
        for item in amenities:
            clauses.append("JSON_CONTAINS(amenities, %s)")
            params.append(json.dumps([item]))

    if query_text:
        clauses.append("(name LIKE %s OR location LIKE %s OR building LIKE %s)")
        like_pattern = f"%{query_text}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)

    sql = f"SELECT * FROM rooms {where_sql} ORDER BY name"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_available_rooms(
    connection: MySQLConnection,
    start_time,
    end_time,
    capacity_min: Optional[int] = None,
    equipment: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    clauses = ["r.status = 'available'"]
    params: List[Any] = []

    if capacity_min is not None:
        clauses.append("r.capacity >= %s")
        params.append(capacity_min)

    if equipment:
        for item in equipment:
            clauses.append("JSON_CONTAINS(r.equipment, %s)")
            params.append(json.dumps([item]))

    clauses.append(
        """NOT EXISTS (
            SELECT 1 FROM bookings b
            WHERE b.room_id = r.id
              AND b.status IN ('pending', 'confirmed')
              AND (
                   (b.start_time <= %s AND b.end_time > %s)
                OR (b.start_time < %s AND b.end_time >= %s)
                OR (b.start_time >= %s AND b.end_time <= %s)
              )
        )"""
    )
    params.extend([start_time, start_time, end_time, end_time, start_time, end_time])

    where_sql = " AND ".join(clauses)
    sql = f"SELECT r.* FROM rooms r WHERE {where_sql} ORDER BY r.name"

    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def update_room_status(connection: MySQLConnection, room_id: int, status: str) -> bool:
    cursor = connection.cursor()
    cursor.execute("UPDATE rooms SET status = %s WHERE id = %s", (status, room_id))
    updated = cursor.rowcount > 0
    cursor.close()
    return updated
