Users Service API
=================

This document provides comprehensive documentation for the Users Service API. The Users Service handles all authentication, user management, and profile operations for the Smart Meeting Room Management System.

**Service Owner:** Ahmad Yateem

**Base URL:** ``http://localhost:5001``

.. contents:: Table of Contents
   :local:
   :depth: 3

Overview
--------

The Users Service is the authentication hub for the entire system. It manages user accounts, handles login and registration, issues JWT tokens, and maintains user profiles. All other services rely on the Users Service for authentication validation.

Key Features
~~~~~~~~~~~~

**User Registration**
    New users can create accounts by providing a username, email, password, and full name. The service validates all input data and checks for duplicate usernames and emails.

**Authentication**
    Users authenticate using their username (or email) and password. Upon successful authentication, the service issues JWT access and refresh tokens.

**Profile Management**
    Users can view and update their profile information, including email and full name. Password changes are also supported.

**Role Based Access**
    The service supports multiple user roles including user, facility_manager, moderator, and admin. Each role has different permissions throughout the system.

Authentication
--------------

Most endpoints in this service require authentication. To authenticate requests, include the JWT access token in the Authorization header::

    Authorization: Bearer <your_access_token>

Tokens are obtained through the login or registration endpoints. Access tokens expire after 1 hour by default, while refresh tokens are valid for 30 days.

API Endpoints
-------------

Health Check
~~~~~~~~~~~~

Check if the Users Service is running and healthy.

**Endpoint:** ``GET /health``

**Authentication:** Not required

**Example Request:**

::

    GET http://localhost:5001/health

**Example Response (200 OK):**

::

    {
        "status": "healthy",
        "service": "users"
    }

Register User
~~~~~~~~~~~~~

Create a new user account in the system.

**Endpoint:** ``POST /api/auth/register``

**Authentication:** Not required

**Request Body:**

+------------+--------+----------+-----------------------------------------------+
| Field      | Type   | Required | Description                                   |
+============+========+==========+===============================================+
| username   | string | Yes      | Unique username, 3 to 50 characters           |
+------------+--------+----------+-----------------------------------------------+
| email      | string | Yes      | Valid email address, must be unique           |
+------------+--------+----------+-----------------------------------------------+
| password   | string | Yes      | Password with at least 8 characters,          |
|            |        |          | including uppercase, lowercase, and number    |
+------------+--------+----------+-----------------------------------------------+
| full_name  | string | Yes      | User's full name, 2 to 100 characters         |
+------------+--------+----------+-----------------------------------------------+
| role       | string | No       | User role, defaults to "user"                 |
+------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    POST http://localhost:5001/api/auth/register
    Content-Type: application/json

    {
        "username": "ahmadyateem",
        "email": "aay123@mail.aub.edu",
        "password": "SecurePass@123",
        "full_name": "Ahmad Yateem",
        "role": "user"
    }

**Example Response (201 Created):**

::

    {
        "success": true,
        "message": "User registered successfully",
        "data": {
            "user": {
                "id": 1,
                "username": "ahmadyateem",
                "email": "aay123@mail.aub.edu",
                "full_name": "Ahmad Yateem",
                "role": "user"
            },
            "tokens": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }

**Error Responses:**

* **400 Bad Request:** Invalid input data or missing required fields
* **409 Conflict:** Username or email already exists

Login
~~~~~

Authenticate a user and receive JWT tokens.

**Endpoint:** ``POST /api/auth/login``

**Authentication:** Not required

**Request Body:**

+------------+--------+----------+-----------------------------------------------+
| Field      | Type   | Required | Description                                   |
+============+========+==========+===============================================+
| username   | string | Yes      | Username or email address                     |
+------------+--------+----------+-----------------------------------------------+
| password   | string | Yes      | User's password                               |
+------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    POST http://localhost:5001/api/auth/login
    Content-Type: application/json

    {
        "username": "adminuser",
        "password": "SecurePass@123"
    }

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Login successful",
        "data": {
            "user": {
                "id": 9,
                "username": "adminuser",
                "email": "admin@mail.aub.edu",
                "full_name": "Admin User",
                "role": "admin"
            },
            "tokens": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }

**Error Responses:**

* **401 Unauthorized:** Invalid username or password
* **401 Unauthorized:** Account is locked due to too many failed attempts

**Security Notes:**

The service implements account lockout after 5 failed login attempts. The account will be locked for 30 minutes. During this time, login attempts will be rejected even with correct credentials.

Refresh Token
~~~~~~~~~~~~~

Obtain a new access token using a valid refresh token.

**Endpoint:** ``POST /api/auth/refresh``

**Authentication:** Requires refresh token in Authorization header

**Example Request:**

::

    POST http://localhost:5001/api/auth/refresh
    Authorization: Bearer <refresh_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Token refreshed successfully",
        "data": {
            "tokens": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }

Get All Users
~~~~~~~~~~~~~

Retrieve a paginated list of all users. This endpoint is restricted to administrators only.

**Endpoint:** ``GET /api/users``

**Authentication:** Required (Admin role)

**Query Parameters:**

+------------+--------+----------+-----------------------------------------------+
| Parameter  | Type   | Required | Description                                   |
+============+========+==========+===============================================+
| page       | int    | No       | Page number, defaults to 1                    |
+------------+--------+----------+-----------------------------------------------+
| per_page   | int    | No       | Items per page, defaults to 20, max 100       |
+------------+--------+----------+-----------------------------------------------+
| role       | string | No       | Filter by role                                |
+------------+--------+----------+-----------------------------------------------+
| is_active  | bool   | No       | Filter by active status                       |
+------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5001/api/users?page=1&per_page=20
    Authorization: Bearer <admin_access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "id": 1,
                "username": "ahmadyateem",
                "email": "aay123@mail.aub.edu",
                "full_name": "Ahmad Yateem",
                "role": "user",
                "is_active": true,
                "created_at": "2025-11-28T19:34:55",
                "last_login": "2025-11-28T20:21:18"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total_items": 9,
            "total_pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }

**Error Responses:**

* **401 Unauthorized:** Missing or invalid token
* **403 Forbidden:** User does not have admin role

Get Current User Profile
~~~~~~~~~~~~~~~~~~~~~~~~

Retrieve the profile of the currently authenticated user.

**Endpoint:** ``GET /api/users/profile``

**Authentication:** Required

**Example Request:**

::

    GET http://localhost:5001/api/users/profile
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "id": 6,
            "username": "ahmadyateem",
            "email": "aay123@mail.aub.edu",
            "full_name": "Ahmad Yateem",
            "role": "user",
            "is_active": true,
            "created_at": "2025-11-28T19:34:55",
            "last_login": "2025-11-28T20:21:18"
        }
    }

Get User by ID
~~~~~~~~~~~~~~

Retrieve a specific user's information. Users can only view their own profile unless they have admin privileges.

**Endpoint:** ``GET /api/users/<user_id>``

**Authentication:** Required

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| user_id    | int    | The ID of the user to retrieve                |
+------------+--------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5001/api/users/6
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "id": 6,
            "username": "ahmadyateem",
            "email": "aay123@mail.aub.edu",
            "full_name": "Ahmad Yateem",
            "role": "user",
            "is_active": true,
            "created_at": "2025-11-28T19:34:55",
            "last_login": "2025-11-28T20:21:18"
        }
    }

**Error Responses:**

* **403 Forbidden:** Cannot view other users' profiles without admin role
* **404 Not Found:** User does not exist

Update User Profile
~~~~~~~~~~~~~~~~~~~

Update the current user's profile information.

**Endpoint:** ``PUT /api/users/profile``

**Authentication:** Required

**Request Body:**

+------------+--------+----------+-----------------------------------------------+
| Field      | Type   | Required | Description                                   |
+============+========+==========+===============================================+
| email      | string | No       | New email address                             |
+------------+--------+----------+-----------------------------------------------+
| full_name  | string | No       | New full name                                 |
+------------+--------+----------+-----------------------------------------------+
| password   | string | No       | New password                                  |
+------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    PUT http://localhost:5001/api/users/profile
    Authorization: Bearer <access_token>
    Content-Type: application/json

    {
        "full_name": "Ahmad Yateem Updated"
    }

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Profile updated successfully",
        "data": {
            "id": 6,
            "username": "ahmadyateem",
            "email": "aay123@mail.aub.edu",
            "full_name": "Ahmad Yateem Updated",
            "role": "user"
        }
    }

**Error Responses:**

* **400 Bad Request:** Invalid input data
* **409 Conflict:** Email already in use by another user

Delete User
~~~~~~~~~~~

Delete a user account. This endpoint is restricted to administrators only. Administrators cannot delete their own account.

**Endpoint:** ``DELETE /api/users/<user_id>``

**Authentication:** Required (Admin role)

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| user_id    | int    | The ID of the user to delete                  |
+------------+--------+-----------------------------------------------+

**Example Request:**

::

    DELETE http://localhost:5001/api/users/5
    Authorization: Bearer <admin_access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "User 'testuser' deleted successfully"
    }

**Error Responses:**

* **403 Forbidden:** Cannot delete your own account
* **404 Not Found:** User does not exist

Get User Booking History
~~~~~~~~~~~~~~~~~~~~~~~~

Retrieve the booking history for a specific user. Users can only view their own bookings unless they have admin privileges.

**Endpoint:** ``GET /api/users/<user_id>/bookings``

**Authentication:** Required

**Path Parameters:**

+------------+--------+-----------------------------------------------+
| Parameter  | Type   | Description                                   |
+============+========+===============================================+
| user_id    | int    | The ID of the user                            |
+------------+--------+-----------------------------------------------+

**Query Parameters:**

+------------+--------+----------+-----------------------------------------------+
| Parameter  | Type   | Required | Description                                   |
+============+========+==========+===============================================+
| page       | int    | No       | Page number, defaults to 1                    |
+------------+--------+----------+-----------------------------------------------+
| per_page   | int    | No       | Items per page, defaults to 20                |
+------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5001/api/users/6/bookings?page=1&per_page=10
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "id": 1,
                "title": "Team Meeting",
                "description": "Weekly team sync",
                "start_time": "2025-12-01T10:00:00",
                "end_time": "2025-12-01T11:00:00",
                "status": "confirmed",
                "attendees": 5,
                "room": {
                    "id": 1,
                    "name": "Conference Room A",
                    "capacity": 20,
                    "floor": 3,
                    "building": "Main Building"
                },
                "created_at": "2025-11-28T15:30:00"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 10,
            "total_items": 1,
            "total_pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }

Error Codes
-----------

The Users Service returns the following error codes:

+------+-------------------------+-----------------------------------------------+
| Code | Name                    | Description                                   |
+======+=========================+===============================================+
| 400  | Bad Request             | The request body is malformed or missing      |
|      |                         | required fields                               |
+------+-------------------------+-----------------------------------------------+
| 401  | Unauthorized            | Authentication is required or the provided    |
|      |                         | credentials are invalid                       |
+------+-------------------------+-----------------------------------------------+
| 403  | Forbidden               | The authenticated user does not have          |
|      |                         | permission to perform this action             |
+------+-------------------------+-----------------------------------------------+
| 404  | Not Found               | The requested user does not exist             |
+------+-------------------------+-----------------------------------------------+
| 409  | Conflict                | The username or email is already registered   |
+------+-------------------------+-----------------------------------------------+
| 422  | Unprocessable Entity    | The request data failed validation            |
+------+-------------------------+-----------------------------------------------+
| 429  | Too Many Requests       | Rate limit exceeded                           |
+------+-------------------------+-----------------------------------------------+
| 500  | Internal Server Error   | An unexpected error occurred                  |
+------+-------------------------+-----------------------------------------------+

Testing with Postman
--------------------

The ``postman/`` directory contains a ready to use Postman collection for testing the Users Service. Import ``Users_Service_FIXED.postman_collection.json`` into Postman to get started.

**Testing Workflow:**

1. Run the "Login User" request first to obtain an access token
2. The token is automatically saved to collection variables
3. All subsequent requests will use this token for authentication
4. For admin only endpoints, login with an admin account first

**Default Test Credentials:**

::

    Admin User:
        Username: adminuser
        Password: SecurePass@123

    Regular User:
        Username: ahmadyateem
        Password: SecurePass@123
