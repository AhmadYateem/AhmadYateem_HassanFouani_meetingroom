Bookings Service API
====================

This document provides comprehensive documentation for the Bookings Service API. The Bookings Service manages all meeting room reservations, scheduling operations, and booking lifecycle management.

**Service Owner:** Ahmad Yateem

**Base URL:** ``http://localhost:5003``

.. contents:: Table of Contents
   :local:
   :depth: 3

Overview
--------

The Bookings Service is the core scheduling component of the Smart Meeting Room Management System. It handles the complete booking lifecycle from creation to completion, manages time conflict detection, integrates with the Rooms Service for availability validation, and sends notifications through the messaging system.

Key Features
~~~~~~~~~~~~

**Booking Creation**
    Users can create bookings by specifying the room, time slot, title, and optional attendee count. The service validates room availability and prevents double bookings.

**Conflict Detection**
    The service automatically detects scheduling conflicts when a booking request overlaps with existing reservations for the same room.

**Booking Lifecycle**
    Bookings progress through several states: pending, confirmed, cancelled, and completed. The service manages state transitions and enforces business rules.

**Time Validation**
    The service enforces time rules such as minimum notice periods, maximum booking duration, and business hours restrictions.

**Inter Service Communication**
    The Bookings Service communicates with the Rooms Service to validate room existence and availability, and with the Users Service to validate user permissions.

Authentication
--------------

All endpoints in this service require authentication. Include the JWT access token from the Users Service in the Authorization header::

    Authorization: Bearer <your_access_token>

Users can only manage their own bookings unless they have administrative privileges.

API Endpoints
-------------

Health Check
~~~~~~~~~~~~

Check if the Bookings Service is running and healthy.

**Endpoint:** ``GET /health``

**Authentication:** Not required

**Example Request:**

::

    GET http://localhost:5003/health

**Example Response (200 OK):**

::

    {
        "status": "healthy",
        "service": "bookings"
    }

Create Booking
~~~~~~~~~~~~~~

Create a new room booking. The service validates room availability before creating the reservation.

**Endpoint:** ``POST /api/bookings``

**Authentication:** Required

**Request Body:**

+---------------+--------+----------+-----------------------------------------------+
| Field         | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| room_id       | int    | Yes      | The ID of the room to book                    |
+---------------+--------+----------+-----------------------------------------------+
| title         | string | Yes      | Title of the meeting, 3 to 200 characters     |
+---------------+--------+----------+-----------------------------------------------+
| description   | string | No       | Detailed description of the meeting           |
+---------------+--------+----------+-----------------------------------------------+
| start_time    | string | Yes      | Start time in ISO 8601 format                 |
+---------------+--------+----------+-----------------------------------------------+
| end_time      | string | Yes      | End time in ISO 8601 format                   |
+---------------+--------+----------+-----------------------------------------------+
| attendees     | int    | No       | Expected number of attendees                  |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    POST http://localhost:5003/api/bookings
    Authorization: Bearer <access_token>
    Content-Type: application/json

    {
        "room_id": 1,
        "title": "Weekly Team Sync",
        "description": "Regular weekly meeting to discuss project progress",
        "start_time": "2025-12-01T10:00:00",
        "end_time": "2025-12-01T11:00:00",
        "attendees": 8
    }

**Example Response (201 Created):**

::

    {
        "success": true,
        "message": "Booking created successfully",
        "data": {
            "id": 25,
            "room_id": 1,
            "user_id": 6,
            "title": "Weekly Team Sync",
            "description": "Regular weekly meeting to discuss project progress",
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T11:00:00",
            "attendees": 8,
            "status": "confirmed",
            "created_at": "2025-11-28T22:00:00",
            "room": {
                "id": 1,
                "name": "Conference Room A",
                "capacity": 20,
                "building": "Main Building"
            }
        }
    }

**Error Responses:**

* **400 Bad Request:** Invalid input data or missing required fields
* **404 Not Found:** Room does not exist
* **409 Conflict:** Room is not available during the requested time
* **422 Unprocessable Entity:** Attendees exceed room capacity

Get All Bookings
~~~~~~~~~~~~~~~~

Retrieve a paginated list of bookings. Regular users see only their own bookings, while administrators can see all bookings.

**Endpoint:** ``GET /api/bookings``

**Authentication:** Required

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| page          | int    | No       | Page number, defaults to 1                    |
+---------------+--------+----------+-----------------------------------------------+
| per_page      | int    | No       | Items per page, defaults to 20, max 100       |
+---------------+--------+----------+-----------------------------------------------+
| room_id       | int    | No       | Filter by room ID                             |
+---------------+--------+----------+-----------------------------------------------+
| status        | string | No       | Filter by status                              |
+---------------+--------+----------+-----------------------------------------------+
| start_date    | string | No       | Filter bookings from this date                |
+---------------+--------+----------+-----------------------------------------------+
| end_date      | string | No       | Filter bookings until this date               |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5003/api/bookings?status=confirmed&page=1
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "id": 25,
                "room_id": 1,
                "user_id": 6,
                "title": "Weekly Team Sync",
                "start_time": "2025-12-01T10:00:00",
                "end_time": "2025-12-01T11:00:00",
                "status": "confirmed",
                "attendees": 8,
                "room": {
                    "id": 1,
                    "name": "Conference Room A",
                    "capacity": 20
                },
                "created_at": "2025-11-28T22:00:00"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total_items": 1,
            "total_pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }

Get Booking by ID
~~~~~~~~~~~~~~~~~

Retrieve detailed information about a specific booking.

**Endpoint:** ``GET /api/bookings/<booking_id>``

**Authentication:** Required

**Path Parameters:**

+---------------+--------+-----------------------------------------------+
| Parameter     | Type   | Description                                   |
+===============+========+===============================================+
| booking_id    | int    | The ID of the booking to retrieve             |
+---------------+--------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5003/api/bookings/25
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "id": 25,
            "room_id": 1,
            "user_id": 6,
            "title": "Weekly Team Sync",
            "description": "Regular weekly meeting to discuss project progress",
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T11:00:00",
            "attendees": 8,
            "status": "confirmed",
            "created_at": "2025-11-28T22:00:00",
            "updated_at": "2025-11-28T22:00:00",
            "room": {
                "id": 1,
                "name": "Conference Room A",
                "capacity": 20,
                "floor": 3,
                "building": "Main Building",
                "amenities": ["projector", "whiteboard", "video_conferencing"]
            },
            "organizer": {
                "id": 6,
                "username": "ahmadyateem",
                "full_name": "Ahmad Yateem"
            }
        }
    }

**Error Responses:**

* **403 Forbidden:** Cannot view other users' bookings without admin role
* **404 Not Found:** Booking does not exist

Update Booking
~~~~~~~~~~~~~~

Update an existing booking. Users can only update their own bookings unless they have administrative privileges.

**Endpoint:** ``PUT /api/bookings/<booking_id>``

**Authentication:** Required

**Path Parameters:**

+---------------+--------+-----------------------------------------------+
| Parameter     | Type   | Description                                   |
+===============+========+===============================================+
| booking_id    | int    | The ID of the booking to update               |
+---------------+--------+-----------------------------------------------+

**Request Body:**

+---------------+--------+----------+-----------------------------------------------+
| Field         | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| title         | string | No       | Updated meeting title                         |
+---------------+--------+----------+-----------------------------------------------+
| description   | string | No       | Updated description                           |
+---------------+--------+----------+-----------------------------------------------+
| start_time    | string | No       | Updated start time                            |
+---------------+--------+----------+-----------------------------------------------+
| end_time      | string | No       | Updated end time                              |
+---------------+--------+----------+-----------------------------------------------+
| attendees     | int    | No       | Updated attendee count                        |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    PUT http://localhost:5003/api/bookings/25
    Authorization: Bearer <access_token>
    Content-Type: application/json

    {
        "title": "Weekly Team Sync (Extended)",
        "end_time": "2025-12-01T11:30:00",
        "attendees": 10
    }

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Booking updated successfully",
        "data": {
            "id": 25,
            "title": "Weekly Team Sync (Extended)",
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T11:30:00",
            "attendees": 10,
            "status": "confirmed",
            "updated_at": "2025-11-28T22:30:00"
        }
    }

**Error Responses:**

* **400 Bad Request:** Invalid input data
* **403 Forbidden:** Cannot update other users' bookings
* **404 Not Found:** Booking does not exist
* **409 Conflict:** New time slot is not available

Cancel Booking
~~~~~~~~~~~~~~

Cancel an existing booking. Users can only cancel their own bookings unless they have administrative privileges.

**Endpoint:** ``DELETE /api/bookings/<booking_id>``

**Authentication:** Required

**Path Parameters:**

+---------------+--------+-----------------------------------------------+
| Parameter     | Type   | Description                                   |
+===============+========+===============================================+
| booking_id    | int    | The ID of the booking to cancel               |
+---------------+--------+-----------------------------------------------+

**Example Request:**

::

    DELETE http://localhost:5003/api/bookings/25
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Booking cancelled successfully"
    }

**Error Responses:**

* **403 Forbidden:** Cannot cancel other users' bookings
* **404 Not Found:** Booking does not exist
* **409 Conflict:** Booking is already cancelled or completed

Get My Bookings
~~~~~~~~~~~~~~~

Retrieve all bookings for the currently authenticated user.

**Endpoint:** ``GET /api/bookings/my``

**Authentication:** Required

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| page          | int    | No       | Page number, defaults to 1                    |
+---------------+--------+----------+-----------------------------------------------+
| per_page      | int    | No       | Items per page, defaults to 20                |
+---------------+--------+----------+-----------------------------------------------+
| status        | string | No       | Filter by status                              |
+---------------+--------+----------+-----------------------------------------------+
| upcoming      | bool   | No       | Only show future bookings                     |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5003/api/bookings/my?upcoming=true
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "id": 25,
                "title": "Weekly Team Sync",
                "start_time": "2025-12-01T10:00:00",
                "end_time": "2025-12-01T11:00:00",
                "status": "confirmed",
                "room": {
                    "id": 1,
                    "name": "Conference Room A"
                }
            },
            {
                "id": 28,
                "title": "Project Kickoff",
                "start_time": "2025-12-02T14:00:00",
                "end_time": "2025-12-02T15:30:00",
                "status": "confirmed",
                "room": {
                    "id": 3,
                    "name": "Board Room"
                }
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total_items": 2,
            "total_pages": 1
        }
    }

Get Room Bookings
~~~~~~~~~~~~~~~~~

Retrieve all bookings for a specific room.

**Endpoint:** ``GET /api/bookings/room/<room_id>``

**Authentication:** Required

**Path Parameters:**

+---------------+--------+-----------------------------------------------+
| Parameter     | Type   | Description                                   |
+===============+========+===============================================+
| room_id       | int    | The ID of the room                            |
+---------------+--------+-----------------------------------------------+

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| date          | string | No       | Filter by specific date                       |
+---------------+--------+----------+-----------------------------------------------+
| start_date    | string | No       | Start of date range                           |
+---------------+--------+----------+-----------------------------------------------+
| end_date      | string | No       | End of date range                             |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5003/api/bookings/room/1?date=2025-12-01
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "room": {
                "id": 1,
                "name": "Conference Room A"
            },
            "date": "2025-12-01",
            "bookings": [
                {
                    "id": 25,
                    "title": "Weekly Team Sync",
                    "start_time": "2025-12-01T10:00:00",
                    "end_time": "2025-12-01T11:00:00",
                    "organizer": "Ahmad Yateem"
                },
                {
                    "id": 26,
                    "title": "Client Presentation",
                    "start_time": "2025-12-01T14:00:00",
                    "end_time": "2025-12-01T16:00:00",
                    "organizer": "Hassan Fouani"
                }
            ]
        }
    }

Check Availability
~~~~~~~~~~~~~~~~~~

Check if a specific time slot is available for booking.

**Endpoint:** ``POST /api/bookings/check-availability``

**Authentication:** Required

**Request Body:**

+---------------+--------+----------+-----------------------------------------------+
| Field         | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| room_id       | int    | Yes      | The ID of the room to check                   |
+---------------+--------+----------+-----------------------------------------------+
| start_time    | string | Yes      | Start time in ISO 8601 format                 |
+---------------+--------+----------+-----------------------------------------------+
| end_time      | string | Yes      | End time in ISO 8601 format                   |
+---------------+--------+----------+-----------------------------------------------+
| exclude_id    | int    | No       | Booking ID to exclude from conflict check     |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    POST http://localhost:5003/api/bookings/check-availability
    Authorization: Bearer <access_token>
    Content-Type: application/json

    {
        "room_id": 1,
        "start_time": "2025-12-01T10:00:00",
        "end_time": "2025-12-01T11:00:00"
    }

**Example Response (Available):**

::

    {
        "success": true,
        "data": {
            "is_available": true,
            "room_id": 1,
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T11:00:00"
        }
    }

**Example Response (Not Available):**

::

    {
        "success": true,
        "data": {
            "is_available": false,
            "room_id": 1,
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T11:00:00",
            "conflicts": [
                {
                    "id": 25,
                    "title": "Weekly Team Sync",
                    "start_time": "2025-12-01T09:30:00",
                    "end_time": "2025-12-01T10:30:00"
                }
            ]
        }
    }

Booking Statistics
~~~~~~~~~~~~~~~~~~

Get booking statistics for administrators and facility managers.

**Endpoint:** ``GET /api/bookings/stats``

**Authentication:** Required (admin or facility_manager role)

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| start_date    | string | No       | Start of reporting period                     |
+---------------+--------+----------+-----------------------------------------------+
| end_date      | string | No       | End of reporting period                       |
+---------------+--------+----------+-----------------------------------------------+
| room_id       | int    | No       | Filter by specific room                       |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5003/api/bookings/stats?start_date=2025-12-01&end_date=2025-12-31
    Authorization: Bearer <admin_access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "period": {
                "start": "2025-12-01",
                "end": "2025-12-31"
            },
            "total_bookings": 150,
            "by_status": {
                "confirmed": 120,
                "cancelled": 25,
                "completed": 5,
                "pending": 0
            },
            "by_room": [
                {
                    "room_id": 1,
                    "room_name": "Conference Room A",
                    "booking_count": 45,
                    "total_hours": 67.5
                },
                {
                    "room_id": 2,
                    "room_name": "Meeting Room B",
                    "booking_count": 38,
                    "total_hours": 52.0
                }
            ],
            "peak_hours": [
                {"hour": 10, "booking_count": 35},
                {"hour": 14, "booking_count": 32},
                {"hour": 9, "booking_count": 28}
            ],
            "utilization_rate": 0.45
        }
    }

Booking Status Values
---------------------

Bookings progress through the following status values:

**pending**
    The booking has been created but is waiting for confirmation. This status may be used when approval workflows are enabled.

**confirmed**
    The booking is confirmed and the room is reserved. This is the default status for new bookings when no approval is required.

**cancelled**
    The booking has been cancelled by the user or an administrator. The room is released and available for other bookings.

**completed**
    The booking time has passed. Bookings are automatically marked as completed after their end time.

Error Codes
-----------

The Bookings Service returns the following error codes:

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
| 404  | Not Found               | The requested booking or room does not exist  |
+------+-------------------------+-----------------------------------------------+
| 409  | Conflict                | The room is not available during the          |
|      |                         | requested time period                         |
+------+-------------------------+-----------------------------------------------+
| 422  | Unprocessable Entity    | The request data failed validation            |
+------+-------------------------+-----------------------------------------------+
| 429  | Too Many Requests       | Rate limit exceeded                           |
+------+-------------------------+-----------------------------------------------+
| 500  | Internal Server Error   | An unexpected error occurred                  |
+------+-------------------------+-----------------------------------------------+

Business Rules
--------------

The Bookings Service enforces the following business rules:

**Booking Duration**
    Bookings must have a minimum duration of 15 minutes and a maximum duration of 8 hours.

**Advance Notice**
    Bookings must be created at least 15 minutes in advance. Bookings cannot be created for past times.

**Capacity Check**
    The number of attendees cannot exceed the room capacity. The service validates this against the Rooms Service.

**Business Hours**
    By default, bookings are allowed between 7:00 AM and 10:00 PM. This can be configured per room or globally.

**Cancellation Policy**
    Bookings can be cancelled up until their start time. Past bookings cannot be cancelled.

**Modification Restrictions**
    Confirmed bookings can be modified up until 30 minutes before start time. After that, only cancellation is allowed.

Testing with Postman
--------------------

The ``postman/`` directory contains Postman collections for testing the Bookings Service. Import ``SmartMeetingRoom_Bookings.postman_collection.json`` into Postman to get started.

**Testing Workflow:**

1. Ensure the Users Service (port 5001) and Rooms Service (port 5002) are running
2. Run the "Login User" request first to obtain an access token
3. The token is automatically saved to collection variables
4. Test booking creation, retrieval, and management endpoints

**Default Test Credentials:**

::

    Admin User:
        Username: adminuser
        Password: SecurePass@123

    Regular User:
        Username: ahmadyateem
        Password: SecurePass@123

**Note:** The Bookings Service communicates with both the Users Service and Rooms Service, so ensure all dependent services are running before testing.
