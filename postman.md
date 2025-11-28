# Postman Trial Guide

This document captures all API trials required for the Smart Meeting Room Management System. Every trial must show **input**, **process**, and **output** in a single screenshot to comply with the project rubric.

---

## Prerequisites

1. Start Docker Desktop.
2. Run the services:
   ```powershell
   docker-compose up -d
   ```
3. Wait ~30 seconds until all containers are healthy.
4. Open Postman.

---

## Screenshot Requirements

- Each screenshot must clearly display:
  - **Input**: URL, method, headers, and request body (Postman top and Body tab).
  - **Process**: The endpoint being called (visible in Postman request bar).
  - **Output**: Full response body and HTTP status code (Postman Response pane).
- Add captions in the report: `Figure X: [API name] – [short description] ([Student Name])`.

---

## Ahmad Yateem – Users & Bookings Services (Ports 5001, 5003)

### Users Service Trials

| # | Scenario | Method & URL | Request Body (JSON) | Expected Output | Status |
|---|----------|--------------|---------------------|-----------------|--------|
| 1 | Register success | `POST http://localhost:5001/api/users/register` | ```json
{
  "username": "ahmad_demo",
  "email": "ahmad.demo@example.com",
  "password": "SecurePass@123",
  "name": "Ahmad Yateem Demo",
  "role": "user"
}
``` | ```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "ahmad_demo",
    "email": "ahmad.demo@example.com",
    "name": "Ahmad Yateem Demo",
    "role": "user"
  }
}
``` | 201 |
| 2 | Register invalid email | `POST /api/users/register` | same as above but `"email": "not-a-valid-email"` | ```json
{"error": "Invalid email format"}
``` | 400 |
| 3 | Register weak password | `POST /api/users/register` | same as above but `"password": "123"` | ```json
{"error": "Password must be at least 8 characters with uppercase, lowercase, digit, and special character"}
``` | 400 |
| 4 | Login success | `POST http://localhost:5001/api/users/login` | ```json
{
  "username": "ahmad_demo",
  "password": "SecurePass@123"
}
``` | ```json
{
  "message": "Login successful",
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "user": {"id": 1, "username": "ahmad_demo", "role": "user"}
}
``` | 200 |
| 5 | Login wrong password | `POST /api/users/login` | password = `WrongPassword123` | ```json
{"error": "Invalid username or password"}
``` | 401 |
| 6 | Get all users (authorized) | `GET http://localhost:5001/api/users/` | Headers: `Authorization: Bearer <access_token>` | ```json
{
  "users": [ { "id": 1, ... } ],
  "total": 1,
  "page": 1
}
``` | 200 |
| 7 | Get all users (no token) | `GET /api/users/` | No headers | ```json
{"msg": "Missing Authorization Header"}
``` | 401 |
| 8 | Get user by username | `GET /api/users/ahmad_demo` | Auth header required | User object | 200 |
| 9 | Update user profile | `PUT /api/users/1` | ```json
{
  "name": "Ahmad Yateem Updated",
  "email": "ahmad.updated@example.com"
}
``` | ```json
{
  "message": "User updated successfully",
  "user": { ... }
}
``` | 200 |
|10 | Booking history | `GET /api/users/1/bookings` | Auth header | ```json
{"user_id": 1, "bookings": [], "total": 0}
``` | 200 |
|11 | Delete user | `DELETE /api/users/2` (create user first) | Auth header | ```json
{"message": "User deleted successfully"}
``` | 200 |

> **Reminder:** Copy the `access_token` from the login response and use it in the `Authorization` header for protected endpoints: `Bearer <token>`.

### Bookings Service Trials

| # | Scenario | Method & URL | Request Body (JSON) | Expected Output | Status |
|---|----------|--------------|---------------------|-----------------|--------|
|12 | Create booking success | `POST http://localhost:5003/api/bookings/` | ```json
{
  "room_id": 1,
  "start_time": "2025-11-29T09:00:00",
  "end_time": "2025-11-29T10:00:00",
  "title": "Team Standup Meeting",
  "description": "Daily sync with development team"
}
``` | ```json
{
  "message": "Booking created successfully",
  "booking": {"id": 1, ...}
}
``` | 201 |
|13 | Create booking conflict | same endpoint | same times as above | ```json
{"error": "Room is not available for the selected time slot"}
``` | 409 |
|14 | Get all bookings | `GET http://localhost:5003/api/bookings/` | Auth header | bookings list with pagination | 200 |
|15 | Get booking by ID | `GET /api/bookings/1` | Auth header | booking object | 200 |
|16 | Update booking | `PUT /api/bookings/1` | ```json
{
  "start_time": "2025-11-29T14:00:00",
  "end_time": "2025-11-29T15:00:00",
  "title": "Team Standup Meeting - Rescheduled"
}
``` | ```json
{"message": "Booking updated successfully", "booking": { ... }}
``` | 200 |
|17 | Check availability | `GET http://localhost:5003/api/bookings/availability?room_id=1&date=2025-11-29` | Auth header | ```json
{
  "room_id": 1,
  "available_slots": [...],
  "booked_slots": [...]
}
``` | 200 |
|18 | Cancel booking | `DELETE /api/bookings/1` | Auth header | ```json
{"message": "Booking cancelled successfully"}
``` | 200 |

---

## Hassan Fouani – Rooms & Reviews Services (Ports 5002, 5004)

### Rooms Service Trials

| # | Scenario | Method & URL | Request Body (JSON) | Expected Output | Status |
|---|----------|--------------|---------------------|-----------------|--------|
|19 | Add room A | `POST http://localhost:5002/api/rooms/` | ```json
{
  "name": "Conference Room A",
  "capacity": 20,
  "location": "Building 1, Floor 2",
  "equipment": ["projector", "whiteboard", "video_conferencing"],
  "description": "Large conference room with modern amenities"
}
``` | ```json
{"message": "Room created successfully", "room": {"id": 1, ...}}
``` | 201 |
|20 | Add room B | same endpoint, body: `name`="Meeting Room B", `capacity`=8, equipment `"tv_screen", "whiteboard"` | Created room payload | 201 |
|21 | Get all rooms | `GET http://localhost:5002/api/rooms/` | Auth header | list of rooms + total | 200 |
|22 | Filter rooms (capacity) | `GET /api/rooms/?min_capacity=10` | Auth header | filtered list | 200 |
|23 | Filter rooms (equipment) | `GET /api/rooms/?equipment=projector` | same | filtered list | 200 |
|24 | Get room by ID | `GET /api/rooms/1` | same | room object | 200 |
|25 | Update room | `PUT /api/rooms/1` | ```json
{
  "capacity": 25,
  "equipment": ["projector", "whiteboard", "video_conferencing", "speaker_system"]
}
``` | ```json
{"message": "Room updated successfully", "room": { ... }}
``` | 200 |
|26 | Room status | `GET /api/rooms/1/status` | same | ```json
{"room_id": 1, "status": "available", "current_booking": null}
``` | 200 |
|27 | Delete room | `DELETE /api/rooms/2` | same | ```json
{"message": "Room deleted successfully"}
``` | 200 |

### Reviews Service Trials

| # | Scenario | Method & URL | Request Body (JSON) | Expected Output | Status |
|---|----------|--------------|---------------------|-----------------|--------|
|28 | Submit review success | `POST http://localhost:5004/api/reviews/` | ```json
{
  "room_id": 1,
  "rating": 5,
  "comment": "Excellent conference room! Great equipment and spacious layout."
}
``` | ```json
{"message": "Review submitted successfully", "review": {"id": 1, ...}}
``` | 201 |
|29 | Submit review invalid rating | same endpoint, `"rating": 6` | ```json
{"error": "Rating must be between 1 and 5"}
``` | 400 |
|30 | Submit second review | rating 3, comment "Room was okay..." | review object | 201 |
|31 | Get reviews for room | `GET http://localhost:5004/api/reviews/room/1` | Auth header | ```json
{"room_id": 1, "reviews": [...], "average_rating": 4.0}
``` | 200 |
|32 | Update review | `PUT /api/reviews/2` | ```json
{
  "rating": 4,
  "comment": "Room was good after maintenance fixed the projector."
}
``` | ```json
{"message": "Review updated successfully", "review": { ... }}
``` | 200 |
|33 | Flag review | `POST /api/reviews/2/flag` | ```json
{"reason": "Inappropriate language"}
``` | ```json
{"message": "Review flagged for moderation", "review": {"flagged": true}}
``` | 200 |
|34 | Get flagged reviews | `GET /api/reviews/flagged` | Auth header | list of flagged reviews | 200 |
|35 | Unflag review | `POST /api/reviews/2/unflag` | no body needed | ```json
{"message": "Review unflagged", "review": {"flagged": false}}
``` | 200 |
|36 | Delete review | `DELETE /api/reviews/2` | Auth header | ```json
{"message": "Review deleted successfully"}
``` | 200 |

---

## Captions for Report

Use this template under each screenshot:

```
Figure X: <API Name> Trial – Input: <brief input>, Process: <HTTP method + endpoint>, Output: <response summary> (Student Name)
```

Example:
```
Figure 3: User Registration API Trial – Input: username/email/password payload, Process: POST /api/users/register, Output: 201 Created with new user object (Ahmad Yateem)
```

---

## Verification Steps After Testing

1. Confirm every required screenshot exists (approx. 18 per student).
2. Ensure JWT tokens are visible only partially (crop if needed) for security.
3. Insert screenshots directly into the corresponding report section (no appendix).
4. Double-check captions list the correct student name.

---

Happy documenting! Be sure to keep Docker running while capturing Postman trials.
