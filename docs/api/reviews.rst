Reviews Service API
===================

This document provides comprehensive documentation for the Reviews Service API. The Reviews Service manages user reviews and ratings for meeting rooms, enabling feedback collection and quality assessment.

**Service Owner:** Hassan Fouani

**Base URL:** ``http://localhost:5004``

.. contents:: Table of Contents
   :local:
   :depth: 3

Overview
--------

The Reviews Service enables users to provide feedback on meeting rooms they have used. This feedback helps other users make informed decisions when selecting rooms and helps facility managers identify areas for improvement. Reviews include both numerical ratings and text comments.

Key Features
~~~~~~~~~~~~

**Room Reviews**
    Users can submit reviews for rooms they have booked. Each review includes a rating (1 to 5 stars) and an optional comment describing their experience.

**Review Management**
    Users can view, update, and delete their own reviews. Administrators can moderate reviews across the entire system.

**Rating Aggregation**
    The service calculates and maintains average ratings for each room based on all submitted reviews.

**Booking Verification**
    The service can verify that a user has actually booked a room before allowing them to submit a review, ensuring authentic feedback.

**Content Moderation**
    Reviews are sanitized to prevent inappropriate content. Administrators can flag or remove reviews that violate guidelines.

Authentication
--------------

Most endpoints in this service require authentication. Include the JWT access token from the Users Service in the Authorization header::

    Authorization: Bearer <your_access_token>

Users can only modify their own reviews unless they have moderator or administrator privileges.

API Endpoints
-------------

Health Check
~~~~~~~~~~~~

Check if the Reviews Service is running and healthy.

**Endpoint:** ``GET /health``

**Authentication:** Not required

**Example Request:**

::

    GET http://localhost:5004/health

**Example Response (200 OK):**

::

    {
        "status": "healthy",
        "service": "reviews"
    }

Create Review
~~~~~~~~~~~~~

Submit a new review for a meeting room.

**Endpoint:** ``POST /api/reviews``

**Authentication:** Required

**Request Body:**

+---------------+--------+----------+-----------------------------------------------+
| Field         | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| room_id       | int    | Yes      | The ID of the room being reviewed             |
+---------------+--------+----------+-----------------------------------------------+
| rating        | int    | Yes      | Rating from 1 (lowest) to 5 (highest)         |
+---------------+--------+----------+-----------------------------------------------+
| comment       | string | No       | Detailed review comment, max 1000 characters  |
+---------------+--------+----------+-----------------------------------------------+
| booking_id    | int    | No       | Associated booking ID for verification        |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    POST http://localhost:5004/api/reviews
    Authorization: Bearer <access_token>
    Content-Type: application/json

    {
        "room_id": 1,
        "rating": 5,
        "comment": "Excellent room with great amenities. The video conferencing setup worked flawlessly and the room was very comfortable for our team meeting."
    }

**Example Response (201 Created):**

::

    {
        "success": true,
        "message": "Review created successfully",
        "data": {
            "id": 10,
            "room_id": 1,
            "user_id": 6,
            "rating": 5,
            "comment": "Excellent room with great amenities. The video conferencing setup worked flawlessly and the room was very comfortable for our team meeting.",
            "created_at": "2025-11-28T23:00:00",
            "user": {
                "id": 6,
                "username": "ahmadyateem",
                "full_name": "Ahmad Yateem"
            }
        }
    }

**Error Responses:**

* **400 Bad Request:** Invalid input data or missing required fields
* **404 Not Found:** Room does not exist
* **409 Conflict:** User has already reviewed this room

Get All Reviews
~~~~~~~~~~~~~~~

Retrieve a paginated list of all reviews with optional filtering.

**Endpoint:** ``GET /api/reviews``

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
| user_id       | int    | No       | Filter by user ID (admin only)                |
+---------------+--------+----------+-----------------------------------------------+
| min_rating    | int    | No       | Minimum rating filter                         |
+---------------+--------+----------+-----------------------------------------------+
| max_rating    | int    | No       | Maximum rating filter                         |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5004/api/reviews?room_id=1&page=1
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "id": 10,
                "room_id": 1,
                "user_id": 6,
                "rating": 5,
                "comment": "Excellent room with great amenities.",
                "created_at": "2025-11-28T23:00:00",
                "user": {
                    "username": "ahmadyateem",
                    "full_name": "Ahmad Yateem"
                }
            },
            {
                "id": 8,
                "room_id": 1,
                "user_id": 7,
                "rating": 4,
                "comment": "Good room, but the projector was a bit dim.",
                "created_at": "2025-11-27T15:30:00",
                "user": {
                    "username": "hassanfouani",
                    "full_name": "Hassan Fouani"
                }
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

Get Review by ID
~~~~~~~~~~~~~~~~

Retrieve detailed information about a specific review.

**Endpoint:** ``GET /api/reviews/<review_id>``

**Authentication:** Required

**Path Parameters:**

+---------------+--------+-----------------------------------------------+
| Parameter     | Type   | Description                                   |
+===============+========+===============================================+
| review_id     | int    | The ID of the review to retrieve              |
+---------------+--------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5004/api/reviews/10
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "id": 10,
            "room_id": 1,
            "user_id": 6,
            "rating": 5,
            "comment": "Excellent room with great amenities. The video conferencing setup worked flawlessly and the room was very comfortable for our team meeting.",
            "created_at": "2025-11-28T23:00:00",
            "updated_at": "2025-11-28T23:00:00",
            "user": {
                "id": 6,
                "username": "ahmadyateem",
                "full_name": "Ahmad Yateem"
            },
            "room": {
                "id": 1,
                "name": "Conference Room A",
                "building": "Main Building"
            }
        }
    }

**Error Responses:**

* **404 Not Found:** Review does not exist

Update Review
~~~~~~~~~~~~~

Update an existing review. Users can only update their own reviews unless they have moderator or administrator privileges.

**Endpoint:** ``PUT /api/reviews/<review_id>``

**Authentication:** Required

**Path Parameters:**

+---------------+--------+-----------------------------------------------+
| Parameter     | Type   | Description                                   |
+===============+========+===============================================+
| review_id     | int    | The ID of the review to update                |
+---------------+--------+-----------------------------------------------+

**Request Body:**

+---------------+--------+----------+-----------------------------------------------+
| Field         | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| rating        | int    | No       | Updated rating (1 to 5)                       |
+---------------+--------+----------+-----------------------------------------------+
| comment       | string | No       | Updated review comment                        |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    PUT http://localhost:5004/api/reviews/10
    Authorization: Bearer <access_token>
    Content-Type: application/json

    {
        "rating": 4,
        "comment": "Great room overall, but the air conditioning was a bit cold during our meeting."
    }

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Review updated successfully",
        "data": {
            "id": 10,
            "room_id": 1,
            "rating": 4,
            "comment": "Great room overall, but the air conditioning was a bit cold during our meeting.",
            "updated_at": "2025-11-28T23:30:00"
        }
    }

**Error Responses:**

* **400 Bad Request:** Invalid input data
* **403 Forbidden:** Cannot update other users' reviews
* **404 Not Found:** Review does not exist

Delete Review
~~~~~~~~~~~~~

Delete an existing review. Users can only delete their own reviews unless they have moderator or administrator privileges.

**Endpoint:** ``DELETE /api/reviews/<review_id>``

**Authentication:** Required

**Path Parameters:**

+---------------+--------+-----------------------------------------------+
| Parameter     | Type   | Description                                   |
+===============+========+===============================================+
| review_id     | int    | The ID of the review to delete                |
+---------------+--------+-----------------------------------------------+

**Example Request:**

::

    DELETE http://localhost:5004/api/reviews/10
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "message": "Review deleted successfully"
    }

**Error Responses:**

* **403 Forbidden:** Cannot delete other users' reviews
* **404 Not Found:** Review does not exist

Get Room Reviews
~~~~~~~~~~~~~~~~

Retrieve all reviews for a specific room.

**Endpoint:** ``GET /api/reviews/room/<room_id>``

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
| page          | int    | No       | Page number, defaults to 1                    |
+---------------+--------+----------+-----------------------------------------------+
| per_page      | int    | No       | Items per page, defaults to 20                |
+---------------+--------+----------+-----------------------------------------------+
| sort_by       | string | No       | Sort field: rating, created_at                |
+---------------+--------+----------+-----------------------------------------------+
| sort_order    | string | No       | Sort order: asc or desc                       |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5004/api/reviews/room/1?sort_by=rating&sort_order=desc
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "room": {
                "id": 1,
                "name": "Conference Room A",
                "average_rating": 4.5,
                "total_reviews": 10
            },
            "reviews": [
                {
                    "id": 10,
                    "rating": 5,
                    "comment": "Excellent room with great amenities.",
                    "created_at": "2025-11-28T23:00:00",
                    "user": {
                        "username": "ahmadyateem",
                        "full_name": "Ahmad Yateem"
                    }
                },
                {
                    "id": 8,
                    "rating": 4,
                    "comment": "Good room, but the projector was a bit dim.",
                    "created_at": "2025-11-27T15:30:00",
                    "user": {
                        "username": "hassanfouani",
                        "full_name": "Hassan Fouani"
                    }
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total_items": 10,
                "total_pages": 1
            }
        }
    }

Get My Reviews
~~~~~~~~~~~~~~

Retrieve all reviews submitted by the currently authenticated user.

**Endpoint:** ``GET /api/reviews/my``

**Authentication:** Required

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| page          | int    | No       | Page number, defaults to 1                    |
+---------------+--------+----------+-----------------------------------------------+
| per_page      | int    | No       | Items per page, defaults to 20                |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5004/api/reviews/my
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "id": 10,
                "room_id": 1,
                "rating": 5,
                "comment": "Excellent room with great amenities.",
                "created_at": "2025-11-28T23:00:00",
                "room": {
                    "id": 1,
                    "name": "Conference Room A"
                }
            },
            {
                "id": 5,
                "room_id": 2,
                "rating": 3,
                "comment": "Average room, needs better lighting.",
                "created_at": "2025-11-25T11:00:00",
                "room": {
                    "id": 2,
                    "name": "Meeting Room B"
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

Get Room Rating Summary
~~~~~~~~~~~~~~~~~~~~~~~

Get a summary of ratings for a specific room including average rating, rating distribution, and total review count.

**Endpoint:** ``GET /api/reviews/room/<room_id>/summary``

**Authentication:** Required

**Path Parameters:**

+---------------+--------+-----------------------------------------------+
| Parameter     | Type   | Description                                   |
+===============+========+===============================================+
| room_id       | int    | The ID of the room                            |
+---------------+--------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5004/api/reviews/room/1/summary
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "room_id": 1,
            "room_name": "Conference Room A",
            "average_rating": 4.5,
            "total_reviews": 20,
            "rating_distribution": {
                "5": 10,
                "4": 6,
                "3": 3,
                "2": 1,
                "1": 0
            },
            "recent_trend": "positive",
            "last_review_date": "2025-11-28T23:00:00"
        }
    }

Get All Room Ratings
~~~~~~~~~~~~~~~~~~~~

Get rating summaries for all rooms in the system. Useful for comparing rooms or displaying on a dashboard.

**Endpoint:** ``GET /api/reviews/ratings``

**Authentication:** Required

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| building      | string | No       | Filter by building name                       |
+---------------+--------+----------+-----------------------------------------------+
| min_reviews   | int    | No       | Minimum number of reviews required            |
+---------------+--------+----------+-----------------------------------------------+
| sort_by       | string | No       | Sort field: average_rating, total_reviews     |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5004/api/reviews/ratings?sort_by=average_rating
    Authorization: Bearer <access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": [
            {
                "room_id": 1,
                "room_name": "Conference Room A",
                "building": "Main Building",
                "average_rating": 4.5,
                "total_reviews": 20
            },
            {
                "room_id": 3,
                "room_name": "Board Room",
                "building": "Main Building",
                "average_rating": 4.3,
                "total_reviews": 15
            },
            {
                "room_id": 2,
                "room_name": "Meeting Room B",
                "building": "Main Building",
                "average_rating": 3.8,
                "total_reviews": 12
            }
        ]
    }

Review Statistics
~~~~~~~~~~~~~~~~~

Get overall review statistics for administrators and facility managers.

**Endpoint:** ``GET /api/reviews/stats``

**Authentication:** Required (admin or facility_manager role)

**Query Parameters:**

+---------------+--------+----------+-----------------------------------------------+
| Parameter     | Type   | Required | Description                                   |
+===============+========+==========+===============================================+
| start_date    | string | No       | Start of reporting period                     |
+---------------+--------+----------+-----------------------------------------------+
| end_date      | string | No       | End of reporting period                       |
+---------------+--------+----------+-----------------------------------------------+

**Example Request:**

::

    GET http://localhost:5004/api/reviews/stats?start_date=2025-11-01&end_date=2025-11-30
    Authorization: Bearer <admin_access_token>

**Example Response (200 OK):**

::

    {
        "success": true,
        "data": {
            "period": {
                "start": "2025-11-01",
                "end": "2025-11-30"
            },
            "total_reviews": 45,
            "average_rating": 4.2,
            "rating_distribution": {
                "5": 18,
                "4": 15,
                "3": 8,
                "2": 3,
                "1": 1
            },
            "reviews_by_day": [
                {"date": "2025-11-28", "count": 5},
                {"date": "2025-11-27", "count": 3},
                {"date": "2025-11-26", "count": 4}
            ],
            "top_rated_rooms": [
                {"room_id": 1, "room_name": "Conference Room A", "average": 4.5},
                {"room_id": 3, "room_name": "Board Room", "average": 4.3}
            ],
            "lowest_rated_rooms": [
                {"room_id": 5, "room_name": "Huddle Space", "average": 3.2}
            ]
        }
    }

Rating System
-------------

The review system uses a 5 star rating scale:

**5 Stars (Excellent)**
    The room exceeded expectations. Amenities worked perfectly, the space was comfortable, and it was ideal for the meeting type.

**4 Stars (Good)**
    The room met expectations with minor issues. Overall a positive experience with room for small improvements.

**3 Stars (Average)**
    The room was adequate but had noticeable issues. It served its purpose but could be improved in several areas.

**2 Stars (Below Average)**
    The room had significant issues that impacted the meeting. Major improvements needed.

**1 Star (Poor)**
    The room failed to meet basic requirements. Serious issues that made it unsuitable for meetings.

Error Codes
-----------

The Reviews Service returns the following error codes:

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
| 404  | Not Found               | The requested review or room does not exist   |
+------+-------------------------+-----------------------------------------------+
| 409  | Conflict                | User has already reviewed this room           |
+------+-------------------------+-----------------------------------------------+
| 422  | Unprocessable Entity    | The request data failed validation            |
+------+-------------------------+-----------------------------------------------+
| 429  | Too Many Requests       | Rate limit exceeded                           |
+------+-------------------------+-----------------------------------------------+
| 500  | Internal Server Error   | An unexpected error occurred                  |
+------+-------------------------+-----------------------------------------------+

Business Rules
--------------

The Reviews Service enforces the following business rules:

**One Review Per Room**
    A user can only submit one review per room. Users must update their existing review if they want to change their feedback.

**Rating Range**
    Ratings must be integers between 1 and 5, inclusive.

**Comment Length**
    Comments are optional but when provided must not exceed 1000 characters.

**Content Sanitization**
    All review content is sanitized to prevent XSS attacks and remove inappropriate content.

**Edit Window**
    Users can edit their reviews at any time. There is no time limit on review modifications.

**Deletion Rights**
    Users can delete their own reviews. Moderators and administrators can delete any review.

Testing with Postman
--------------------

The ``postman/`` directory contains a ready to use Postman collection for testing the Reviews Service. Import ``Reviews_Service_FIXED.postman_collection.json`` into Postman to get started.

**Testing Workflow:**

1. Ensure the Users Service (port 5001) and Rooms Service (port 5002) are running
2. Run the "Login User" request first to obtain an access token
3. The token is automatically saved to collection variables
4. Test review creation, retrieval, and management endpoints

**Default Test Credentials:**

::

    Admin User:
        Username: adminuser
        Password: SecurePass@123

    Regular User:
        Username: hassanfouani
        Password: SecurePass@123

**Note:** The Reviews Service validates tokens with the Users Service and may validate room existence with the Rooms Service, so ensure dependent services are running before testing.
