Reviews Service API
===================

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Base URL: ``http://localhost:5004``

Responsibilities:

- Review submission and updates
- Moderation and flagging workflow
- Helpful/unhelpful voting
- Rating aggregation per room

Authentication
--------------

All endpoints require ``Authorization: Bearer <access_token>``. Moderation-specific endpoints require Moderator or Admin roles.

Endpoints
---------

Create Review
~~~~~~~~~~~~~

- **Method/Path**: ``POST /api/reviews``
- **Auth**: Bearer token

Request::

   {
     "room_id": "{{room_id}}",
     "booking_id": "{{booking_id}}",
     "rating": 5,
     "title": "Excellent space",
     "comment": "Plenty of light and great A/V setup.",
     "pros": ["projector", "whiteboard"],
     "cons": []
   }

Get Review
~~~~~~~~~~

- **Method/Path**: ``GET /api/reviews/<review_id>``
- **Auth**: Bearer token

Update Review
~~~~~~~~~~~~~

- **Method/Path**: ``PUT /api/reviews/<review_id>``
- **Auth**: Bearer token (author only)

Delete Review
~~~~~~~~~~~~~

- **Method/Path**: ``DELETE /api/reviews/<review_id>``
- **Auth**: Bearer token (author or Admin)

List Room Reviews
~~~~~~~~~~~~~~~~~

- **Method/Path**: ``GET /api/reviews/room/<room_id>``
- **Auth**: Bearer token
- **Query Params**: ``page``, ``per_page``, ``min_rating`` (optional)

Flag Review
~~~~~~~~~~~

- **Method/Path**: ``POST /api/reviews/<review_id>/flag``
- **Auth**: Bearer token
- **Description**: Flags a review for moderation with a reason field in the payload.

Moderate Review
~~~~~~~~~~~~~~~

- **Method/Path**: ``PUT /api/reviews/<review_id>/moderate``
- **Auth**: Moderator or Admin
- **Description**: Approve, hide, or reject flagged content.

Helpful/Unhelpful Vote
~~~~~~~~~~~~~~~~~~~~~~

- **Method/Path**: ``POST /api/reviews/<review_id>/helpful`` or ``/unhelpful``
- **Auth**: Bearer token
- **Description**: Records user feedback to influence review ranking.

Error Codes
-----------

- ``400``: Invalid rating or payload.
- ``401``: Missing/invalid token.
- ``403``: Not allowed to edit/moderate.
- ``404``: Review or room not found.
- ``409``: Duplicate vote detected.
