Users Service API
=================

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Base URL: ``http://localhost:5001``

Responsibilities:

- User registration and authentication
- JWT access and refresh token issuance
- Profile management and RBAC
- Booking history lookup

Authentication
--------------

All protected endpoints require the ``Authorization: Bearer <access_token>`` header. Tokens are obtained through the ``/api/auth/login`` or ``/api/auth/register`` endpoints.

Endpoints
---------

Register User
~~~~~~~~~~~~~

- **Method/Path**: ``POST /api/auth/register``
- **Auth**: Public

Request::

   {
     "username": "johndoe",
     "email": "john@example.com",
     "password": "SecurePass123!",
     "full_name": "John Doe",
     "role": "user"
   }

Success (201)::

   {
     "success": true,
     "message": "User registered successfully",
     "data": {
       "user": {
         "id": 1,
         "username": "johndoe",
         "email": "john@example.com",
         "role": "user"
       },
       "tokens": {
         "access_token": "eyJ...",
         "refresh_token": "eyJ..."
       }
     }
   }

Login
~~~~~

- **Method/Path**: ``POST /api/auth/login``
- **Auth**: Public

Request::

   {
     "username": "johndoe",
     "password": "SecurePass123!"
   }

Notes:

- Returns new access and refresh tokens.
- Postman tests set ``access_token`` and ``user_id`` environment variables.

Refresh Token
~~~~~~~~~~~~~

- **Method/Path**: ``POST /api/auth/refresh``
- **Auth**: Requires valid refresh token
- **Behavior**: Issues a new access token.

Get Current Profile
~~~~~~~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/users/profile``
- **Auth**: Bearer token
- **Description**: Returns the authenticated user's profile.

Update Profile
~~~~~~~~~~~~~~

- **Method/Path**: ``PUT /api/users/profile``
- **Auth**: Bearer token
- **Description**: Update full name or email.

Request::

   {
     "full_name": "John D. Doe",
     "email": "newemail@example.com"
   }

List Users (Admin)
~~~~~~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/users``
- **Auth**: Admin
- **Query Params**: ``page`` (default 1), ``per_page`` (default 20)

Get User Booking History
~~~~~~~~~~~~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/users/<user_id>/bookings``
- **Auth**: Bearer token
- **Description**: Returns bookings associated with the user.

Error Codes
-----------

- ``400``: Validation error (invalid email, password strength, or payload).
- ``401``: Missing/invalid token.
- ``403``: Insufficient role (non-admin access to admin endpoints).
- ``404``: User not found.
- ``409``: Username or email already exists.
