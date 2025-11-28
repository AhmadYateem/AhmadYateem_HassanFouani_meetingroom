Rooms Service API
=================

This document provides comprehensive documentation for the Rooms Service API. The Rooms Service manages all meeting room operations, including room creation, availability checking, amenity management, and room scheduling.

**Service Owner:** Hassan Fouani

**Base URL:** ``http://localhost:5002``

.. contents:: Table of Contents
   :local:
   :depth: 3

Overview
--------

The Rooms Service is responsible for managing the physical meeting room inventory. It tracks room details, capacity, amenities, location information, and availability status. Other services, particularly the Bookings Service, communicate with this service to validate room availability before creating reservations.

Key Features
~~~~~~~~~~~~

**Room Management**
    Create, update, and delete meeting rooms. Each room has a name, capacity, floor number, building designation, and detailed description.

**Amenity Tracking**
    Rooms can have multiple amenities such as projectors, whiteboards, video conferencing equipment, and more. These amenities help users find the right room for their needs.

**Availability Checking**
    The service provides endpoints to check room availability for specific time periods. This helps prevent double bookings and scheduling conflicts.

**Capacity Planning**
    Users can search for rooms based on required capacity, ensuring the selected room can accommodate all meeting attendees.

**Location Organization**
    Rooms are organized by building and floor, making it easy to find meeting spaces in specific locations.

Authentication
--------------

Most endpoints in this service require authentication. To authenticate requests, include the JWT access token from the Users Service in the Authorization header::

    Authorization: Bearer <your_access_token>

Certain operations, such as creating or deleting rooms, require administrative privileges.

API Endpoints
-------------

Health Check
~~~~~~~~~~~~

Check if the Rooms Service is running and healthy.

**Endpoint:** ``GET /health``

**Authentication:** Not required

**Example Request:**

::

    GET http://localhost:5002/health

**Example Response (200 OK):**

::

    {
        "status": "healthy",
        "service": "rooms"
    }

Create Room
~~~~~~~~~~~

Create a new meeting room in the system. This endpoint is restricted to facility managers and administrators.

**Endpoint:** ``POST /api/rooms``

**Authentication:** Required (facility_manager or admin role)

**Request Body:**

+---------------+--------+----------+-----------------------------------------------+
| Field         | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| name          | string | Yes      | Room name, unique within building and floor   |
+---------------+--------+----------+-----------------------------------------------+
| capacity      | int    | Yes      | Maximum number of people, 1 to 500            |
+---------------+--------+----------+-----------------------------------------------+
| floor         | int    | Yes      | Floor number where the room is located        |
+---------------+--------+----------+-----------------------------------------------+
| building      | string | Yes      | Building name or identifier                   |
+---------------+--------+----------+-----------------------------------------------+
| description   | string | No       | Detailed description of the room              |
+---------------+--------+----------+-----------------------------------------------+
| amenities     | array  | No       | List of amenity names available in the room   |
+---------------+--------+----------+-----------------------------------------------+
| is_active     | bool   | No       | Whether the room is available for booking     |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    POST http://localhost:5002/api/rooms
    Authorization: Bearer <admin_access_token>
    Content-Type: application/json

    {
        "name": "Innovation Lab",
        "capacity": 15,
        "floor": 2,
        "building": "Engineering Building",
        "description": "Creative space with modular furniture",
        "amenities": ["projector", "whiteboard", "video_conferencing"],
        "is_active": true
    }

**Example Response (201 Created):**

::

    {
        "success": true,
        "message": "Room created successfully",
        "data": {
            "id": 5,
            "name": "Innovation Lab",
            "capacity": 15,
            "floor": 2,
            "building": "Engineering Building",
            "description": "Creative space with modular furniture",
            "amenities": ["projector", "whiteboard", "video_conferencing"],
            "is_active": true,
            "created_at": "2025-11-28T21:30:00"
        }
    }

**Error Responses:**

* **400 Bad Request:** Invalid input data or missing required fields
* **403 Forbidden:** User does not have permission to create rooms
* **409 Conflict:** Room with same name already exists on this floor and building

Get All Rooms
~~~~~~~~~~~~~

Retrieve a paginated list of all meeting rooms with optional filtering.

**Endpoint:** ``GET /api/rooms``

**Authentication:** Required

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| page          | int    | No       | Page number, defaults to 1                    |
+---------------+--------+----------+-----------------------------------------------+
| per_page      | int    | No       | Items per page, defaults to 20, max 100       |
+---------------+--------+----------+-----------------------------------------------+
| building      | string | No       | Filter by building name                       |
+---------------+--------+----------+-----------------------------------------------+
| floor         | int    | No       | Filter by floor number                        |
+---------------+--------+----------+-----------------------------------------------+
| min_capacity  | int    | No       | Minimum capacity required                     |
+---------------+--------+----------+-----------------------------------------------+
| is_active     | bool   | No       | Filter by active status                       |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5002/api/rooms?building=Main%20Building&min_capacity=10
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "id": 1,
                "name": "Conference Room A",
                "capacity": 20,
                "floor": 3,
                "building": "Main Building",
                "description": "Large conference room with panoramic views",
                "amenities": ["projector", "whiteboard", "video_conferencing", "phone"],
                "is_active": true,
                "created_at": "2025-11-27T10:00:00"
            },
            {
                "id": 2,
                "name": "Meeting Room B",
                "capacity": 10,
                "floor": 2,
                "building": "Main Building",
                "description": "Medium sized meeting room",
                "amenities": ["whiteboard", "display"],
                "is_active": true,
                "created_at": "2025-11-27T10:15:00"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total_items": 2,
            "total_pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }

Get Room by ID
~~~~~~~~~~~~~~

Retrieve detailed information about a specific room.

**Endpoint:** ``GET /api/rooms/<room_id>``

**Authentication:** Required

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| room_id    | int    | The ID of the room to retrieve                |
+------------+--------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5002/api/rooms/1
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "id": 1,
            "name": "Conference Room A",
            "capacity": 20,
            "floor": 3,
            "building": "Main Building",
            "description": "Large conference room with panoramic views",
            "amenities": ["projector", "whiteboard", "video_conferencing", "phone"],
            "is_active": true,
            "created_at": "2025-11-27T10:00:00",
            "updated_at": "2025-11-27T10:00:00"
        }
    }

**Error Responses:**

* **404 Not Found:** Room does not exist

Update Room
~~~~~~~~~~~

Update an existing room's information. This endpoint is restricted to facility managers and administrators.

**Endpoint:** ``PUT /api/rooms/<room_id>``

**Authentication:** Required (facility_manager or admin role)

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| room_id    | int    | The ID of the room to update                  |
+------------+--------+-----------------------------------------------+

**Request Body:**

+---------------+--------+----------+-----------------------------------------------+
| Field         | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| name          | string | No       | New room name                                 |
+---------------+--------+----------+-----------------------------------------------+
| capacity      | int    | No       | New capacity                                  |
+---------------+--------+----------+-----------------------------------------------+
| floor         | int    | No       | New floor number                              |
+---------------+--------+----------+-----------------------------------------------+
| building      | string | No       | New building name                             |
+---------------+--------+----------+-----------------------------------------------+
| description   | string | No       | New description                               |
+---------------+--------+----------+-----------------------------------------------+
| amenities     | array  | No       | Updated list of amenities                     |
+---------------+--------+----------+-----------------------------------------------+
| is_active     | bool   | No       | Updated active status                         |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    PUT http://localhost:5002/api/rooms/1
    Authorization: Bearer <admin_access_token>
    Content-Type: application/json

    {
        "capacity": 25,
        "amenities": ["projector", "whiteboard", "video_conferencing", "phone", "display"]
    }

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Room updated successfully",
        "data": {
            "id": 1,
            "name": "Conference Room A",
            "capacity": 25,
            "floor": 3,
            "building": "Main Building",
            "description": "Large conference room with panoramic views",
            "amenities": ["projector", "whiteboard", "video_conferencing", "phone", "display"],
            "is_active": true,
            "updated_at": "2025-11-28T21:45:00"
        }
    }

**Error Responses:**

* **400 Bad Request:** Invalid input data
* **403 Forbidden:** User does not have permission to update rooms
* **404 Not Found:** Room does not exist
* **409 Conflict:** New name conflicts with existing room

Delete Room
~~~~~~~~~~~

Delete a meeting room from the system. This endpoint is restricted to administrators only. Rooms with active bookings cannot be deleted.

**Endpoint:** ``DELETE /api/rooms/<room_id>``

**Authentication:** Required (admin role)

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| room_id    | int    | The ID of the room to delete                  |
+------------+--------+-----------------------------------------------+

**Example Request:**

::

    DELETE http://localhost:5002/api/rooms/5
    Authorization: Bearer <admin_access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Room 'Innovation Lab' deleted successfully"
    }

**Error Responses:**

* **403 Forbidden:** User does not have permission to delete rooms
* **404 Not Found:** Room does not exist
* **409 Conflict:** Room has active bookings and cannot be deleted

Check Room Availability
~~~~~~~~~~~~~~~~~~~~~~~

Check if a specific room is available during a given time period.

**Endpoint:** ``GET /api/rooms/<room_id>/availability``

**Authentication:** Required

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| room_id    | int    | The ID of the room to check                   |
+------------+--------+-----------------------------------------------+

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| start_time    | string | Yes      | Start time in ISO 8601 format                 |
+---------------+--------+----------+-----------------------------------------------+
| end_time      | string | Yes      | End time in ISO 8601 format                   |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5002/api/rooms/1/availability?start_time=2025-12-01T10:00:00&end_time=2025-12-01T11:00:00
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "room_id": 1,
            "room_name": "Conference Room A",
            "is_available": true,
            "requested_start": "2025-12-01T10:00:00",
            "requested_end": "2025-12-01T11:00:00",
            "conflicts": []
        }
    }

**Example Response (Room Not Available):**

::

    {
        "success": true,
        "data": {
            "room_id": 1,
            "room_name": "Conference Room A",
            "is_available": false,
            "requested_start": "2025-12-01T10:00:00",
            "requested_end": "2025-12-01T11:00:00",
            "conflicts": [
                {
                    "booking_id": 15,
                    "title": "Team Standup",
                    "start_time": "2025-12-01T09:30:00",
                    "end_time": "2025-12-01T10:30:00"
                }
            ]
        }
    }

Get Room Schedule
~~~~~~~~~~~~~~~~~

Retrieve the booking schedule for a specific room over a date range.

**Endpoint:** ``GET /api/rooms/<room_id>/schedule``

**Authentication:** Required

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| room_id    | int    | The ID of the room                            |
+------------+--------+-----------------------------------------------+

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| date          | string | No       | Specific date in YYYY-MM-DD format            |
+---------------+--------+----------+-----------------------------------------------+
| start_date    | string | No       | Start of date range                           |
+---------------+--------+----------+-----------------------------------------------+
| end_date      | string | No       | End of date range                             |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5002/api/rooms/1/schedule?date=2025-12-01
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "room_id": 1,
            "room_name": "Conference Room A",
            "date": "2025-12-01",
            "bookings": [
                {
                    "id": 10,
                    "title": "Morning Standup",
                    "start_time": "2025-12-01T09:00:00",
                    "end_time": "2025-12-01T09:30:00",
                    "organizer": "Ahmad Yateem"
                },
                {
                    "id": 11,
                    "title": "Project Review",
                    "start_time": "2025-12-01T14:00:00",
                    "end_time": "2025-12-01T15:30:00",
                    "organizer": "Hassan Fouani"
                }
            ],
            "available_slots": [
                {
                    "start": "2025-12-01T09:30:00",
                    "end": "2025-12-01T14:00:00"
                },
                {
                    "start": "2025-12-01T15:30:00",
                    "end": "2025-12-01T18:00:00"
                }
            ]
        }
    }

Search Available Rooms
~~~~~~~~~~~~~~~~~~~~~~

Find rooms that are available during a specific time period and meet capacity requirements.

**Endpoint:** ``GET /api/rooms/search/available``

**Authentication:** Required

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| start_time    | string | Yes      | Start time in ISO 8601 format                 |
+---------------+--------+----------+-----------------------------------------------+
| end_time      | string | Yes      | End time in ISO 8601 format                   |
+---------------+--------+----------+-----------------------------------------------+
| capacity      | int    | No       | Minimum required capacity                     |
+---------------+--------+----------+-----------------------------------------------+
| building      | string | No       | Preferred building                            |
+---------------+--------+----------+-----------------------------------------------+
| floor         | int    | No       | Preferred floor                               |
+---------------+--------+----------+-----------------------------------------------+
| amenities     | string | No       | Comma separated list of required amenities    |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5002/api/rooms/search/available?start_time=2025-12-01T10:00:00&end_time=2025-12-01T11:00:00&capacity=10&amenities=projector,whiteboard
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "id": 1,
                "name": "Conference Room A",
                "capacity": 20,
                "floor": 3,
                "building": "Main Building",
                "amenities": ["projector", "whiteboard", "video_conferencing"],
                "is_available": true
            },
            {
                "id": 3,
                "name": "Board Room",
                "capacity": 15,
                "floor": 4,
                "building": "Main Building",
                "amenities": ["projector", "whiteboard", "display", "phone"],
                "is_available": true
            }
        ],
        "search_criteria": {
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T11:00:00",
            "min_capacity": 10,
            "required_amenities": ["projector", "whiteboard"]
        }
    }

Manage Room Amenities
~~~~~~~~~~~~~~~~~~~~~

Add or remove amenities from a room. This endpoint is restricted to facility managers and administrators.

**Endpoint:** ``PATCH /api/rooms/<room_id>/amenities``

**Authentication:** Required (facility_manager or admin role)

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| room_id    | int    | The ID of the room                            |
+------------+--------+-----------------------------------------------+

**Request Body:**

+---------------+--------+----------+-----------------------------------------------+
| Field         | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| add           | array  | No       | List of amenities to add                      |
+---------------+--------+----------+-----------------------------------------------+
| remove        | array  | No       | List of amenities to remove                   |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    PATCH http://localhost:5002/api/rooms/1/amenities
    Authorization: Bearer <admin_access_token>
    Content-Type: application/json

    {
        "add": ["air_conditioning", "natural_light"],
        "remove": ["phone"]
    }

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Room amenities updated",
        "data": {
            "id": 1,
            "name": "Conference Room A",
            "amenities": ["projector", "whiteboard", "video_conferencing", "air_conditioning", "natural_light"]
        }
    }

Available Amenities
~~~~~~~~~~~~~~~~~~~

Get a list of all available amenities that can be assigned to rooms.

**Endpoint:** ``GET /api/rooms/amenities``

**Authentication:** Required

**Example Request:**

::

    GET http://localhost:5002/api/rooms/amenities
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            "projector",
            "whiteboard",
            "video_conferencing",
            "phone",
            "display",
            "air_conditioning",
            "natural_light",
            "wheelchair_accessible",
            "standing_desks",
            "kitchen_access"
        ]
    }

Get Buildings
~~~~~~~~~~~~~

Retrieve a list of all buildings that have meeting rooms.

**Endpoint:** ``GET /api/rooms/buildings``

**Authentication:** Required

**Example Request:**

::

    GET http://localhost:5002/api/rooms/buildings
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "name": "Main Building",
                "total_rooms": 5,
                "floors": [1, 2, 3, 4]
            },
            {
                "name": "Engineering Building",
                "total_rooms": 3,
                "floors": [1, 2]
            }
        ]
    }

Error Codes
-----------

The Rooms Service returns the following error codes:

+------+-------------------------+-----------------------------------------------+
| Code | Name                    | Description                                   |
+======+=========================+===============================================+
| 400  | Bad Request             | The request body is malformed or missing      |
|      |                         | required fields                               |
+------+-------------------------+-----------------------------------------------+
| 401  | Unauthorized            | Authentication is required or the token       |
|      |                         | is invalid or expired                         |
+------+-------------------------+-----------------------------------------------+
| 403  | Forbidden               | The authenticated user does not have          |
|      |                         | permission to perform this action             |
+------+-------------------------+-----------------------------------------------+
| 404  | Not Found               | The requested room does not exist             |
+------+-------------------------+-----------------------------------------------+
| 409  | Conflict                | Room name conflict or room has active         |
|      |                         | bookings and cannot be deleted                |
+------+-------------------------+-----------------------------------------------+
| 422  | Unprocessable Entity    | The request data failed validation            |
+------+-------------------------+-----------------------------------------------+
| 429  | Too Many Requests       | Rate limit exceeded                           |
+------+-------------------------+-----------------------------------------------+
| 500  | Internal Server Error   | An unexpected error occurred                  |
+------+-------------------------+-----------------------------------------------+

Room Status Values
------------------

Rooms can have the following status values:

**Active (is_active: true)**
    The room is available for booking. Users can see and reserve this room.

**Inactive (is_active: false)**
    The room is not available for booking. This might be due to maintenance, renovation, or other temporary unavailability. Existing bookings remain valid, but new bookings cannot be created.

Testing with Postman
--------------------

The ``postman/`` directory contains a ready to use Postman collection for testing the Rooms Service. Import ``Rooms_Service_FIXED.postman_collection.json`` into Postman to get started.

**Testing Workflow:**

1. Ensure the Users Service is running on port 5001
2. Run the "Login User" request first to obtain an access token
3. The token is automatically saved to collection variables
4. All subsequent requests will use this token for authentication
5. For admin only endpoints, login with an admin account first

**Default Test Credentials:**

::

    Admin User:
        Username: adminuser
        Password: SecurePass@123

**Note:** The Rooms Service validates tokens with the Users Service, so ensure the Users Service is running before testing.
