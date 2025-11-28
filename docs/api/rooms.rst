Rooms Service API
=================

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Base URL: ``http://localhost:5002``

Responsibilities:

- Room catalog CRUD operations
- Availability lookups
- Amenities and equipment tracking
- Advanced search and filtering

Authentication
--------------

All endpoints require ``Authorization: Bearer <access_token>`` unless stated otherwise. Facility Manager or Admin roles are required for write operations.

Endpoints
---------

List Rooms
~~~~~~~~~~

- **Method/Path**: ``GET /api/rooms``
- **Auth**: Bearer token
- **Query Params** (optional): ``page``, ``per_page``, ``capacity``, ``amenities``

Get Room Details
~~~~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/rooms/<room_id>``
- **Auth**: Bearer token

Create Room
~~~~~~~~~~~

- **Method/Path**: ``POST /api/rooms``
- **Auth**: Facility Manager or Admin

Request::

   {
     "name": "Board Room A",
     "capacity": 12,
     "floor": 5,
     "building": "HQ",
     "amenities": ["projector", "whiteboard", "speakerphone"],
     "hourly_rate": 35.0
   }

Update Room
~~~~~~~~~~~

- **Method/Path**: ``PUT /api/rooms/<room_id>``
- **Auth**: Facility Manager or Admin

Delete Room
~~~~~~~~~~~

- **Method/Path**: ``DELETE /api/rooms/<room_id>``
- **Auth**: Admin

Available Rooms
~~~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/rooms/available``
- **Auth**: Bearer token
- **Query Params**: ``start_time``, ``end_time``, ``capacity`` (optional)

Advanced Search
~~~~~~~~~~~~~~~

- **Method/Path**: ``POST /api/rooms/search``
- **Auth**: Bearer token

Request::

   {
     "capacity_min": 8,
     "capacity_max": 30,
     "amenities": ["whiteboard", "camera"],
     "building": "HQ"
   }

Error Codes
-----------

- ``400``: Invalid payload or search filters.
- ``401``: Missing/invalid token.
- ``403``: Role not allowed to perform operation.
- ``404``: Room not found.
- ``409``: Duplicate room name.
