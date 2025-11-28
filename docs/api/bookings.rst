Bookings Service API
====================

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Base URL: ``http://localhost:5003``

Responsibilities:

- Booking creation and lifecycle management
- Conflict detection and availability checks
- Recurring bookings and cancellations
- Audit-friendly status tracking

Authentication
--------------

All endpoints require ``Authorization: Bearer <access_token>``. Administrative operations note the required role.

Endpoints
---------

Create Booking
~~~~~~~~~~~~~~

- **Method/Path**: ``POST /api/bookings``
- **Auth**: Bearer token

Request::

   {
     "room_id": "{{room_id}}",
     "title": "Quarterly Planning",
     "start_time": "2025-12-01T10:00:00Z",
     "end_time": "2025-12-01T11:00:00Z",
     "attendees": 12,
     "is_recurring": false
   }

List Bookings
~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/bookings``
- **Auth**: Bearer token
- **Query Params** (optional): ``status``, ``user_id``, ``room_id``, ``page``, ``per_page``

Get Booking Details
~~~~~~~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/bookings/<booking_id>``
- **Auth**: Bearer token

Update Booking
~~~~~~~~~~~~~~

- **Method/Path**: ``PUT /api/bookings/<booking_id>``
- **Auth**: Bearer token

Cancel Booking
~~~~~~~~~~~~~~

- **Method/Path**: ``DELETE /api/bookings/<booking_id>``
- **Auth**: Bearer token (Admin can cancel any booking, users can cancel their own)

Check Availability
~~~~~~~~~~~~~~~~~~

- **Method/Path**: ``POST /api/bookings/check-availability``
- **Auth**: Bearer token

Request::

   {
     "room_id": "{{room_id}}",
     "start_time": "2025-12-01T13:00:00Z",
     "end_time": "2025-12-01T14:00:00Z"
   }

Conflict Inspection (Admin)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/bookings/conflicts``
- **Auth**: Admin
- **Description**: Lists bookings that overlap for investigation or forced overrides.

Error Codes
-----------

- ``400``: Validation error or time conflict.
- ``401``: Missing/invalid token.
- ``403``: Not allowed to update/cancel the booking.
- ``404``: Booking not found.
- ``409``: Schedule conflict detected.
