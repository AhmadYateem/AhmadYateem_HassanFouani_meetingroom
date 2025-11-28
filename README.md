# Smart Meeting Room Management System

A backend system for managing meeting room bookings, built with Flask microservices.

## What This Project Does

This system allows users to:
- Register accounts and log in
- Browse available meeting rooms
- Book rooms for specific time slots
- Leave reviews and ratings for rooms
- Manage their bookings (update, cancel)

Administrators can:
- Manage users and their roles
- Add, update, or remove rooms
- Moderate reviews
- View all bookings across the system

---

## Architecture

The project uses four independent microservices:

| Service | Port | Description |
|---------|------|-------------|
| Users | 5001 | User registration, login, authentication |
| Rooms | 5002 | Room management (add, update, delete, search) |
| Bookings | 5003 | Booking creation, updates, cancellations |
| Reviews | 5004 | Room reviews and ratings |

Supporting infrastructure:
- MySQL 8.0 - Database (port 33306)
- Redis - Caching (port 6379)
- RabbitMQ - Message queue (ports 5672, 15672)
- Prometheus - Metrics (port 9090)
- Grafana - Dashboards (port 3000)

---

## Requirements

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

---

## Quick Start

### 1. Clone and Start

```bash
cd AhmadYateem_HassanFouani_meetingroom
docker-compose up -d
```

This starts all services. Wait about 30 seconds for MySQL to initialize.

### 2. Verify Services Are Running

```bash
docker ps
```

You should see containers for mysql, redis, rabbitmq, and all four services.

### 3. Test the APIs

Health checks:
```
http://localhost:5001/health  (Users)
http://localhost:5002/health  (Rooms)
http://localhost:5003/health  (Bookings)
http://localhost:5004/health  (Reviews)
```

---

## API Endpoints

### Users Service (port 5001)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/auth/register | Register new user | No |
| POST | /api/auth/login | Login, get JWT token | No |
| POST | /api/auth/refresh | Refresh JWT token | Yes |
| GET | /api/users | List all users | Yes (Admin) |
| GET | /api/users/{id} | Get user by ID | Yes |
| GET | /api/users/profile | Get current user profile | Yes |
| PUT | /api/users/profile | Update profile | Yes |
| DELETE | /api/users/{id} | Delete user | Yes (Admin) |
| GET | /api/users/{id}/bookings | Get user bookings | Yes |

### Rooms Service (port 5002)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/rooms | List rooms (with filters) | No |
| GET | /api/rooms/{id} | Get room details | No |
| POST | /api/rooms | Create room | Yes (Facility Manager) |
| PUT | /api/rooms/{id} | Update room | Yes (Facility Manager) |
| DELETE | /api/rooms/{id} | Delete room | Yes (Admin) |

Query parameters for listing: capacity_min, capacity_max, floor, building, status

### Bookings Service (port 5003)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/bookings | List bookings | Yes |
| GET | /api/bookings/{id} | Get booking details | Yes |
| POST | /api/bookings | Create booking | Yes |
| PUT | /api/bookings/{id} | Update booking | Yes |
| DELETE | /api/bookings/{id} | Cancel booking | Yes |
| POST | /api/bookings/check-availability | Check room availability | Yes |
| GET | /api/bookings/availability | Get availability matrix | Yes |
| POST | /api/bookings/recurring | Create recurring booking | Yes |

### Reviews Service (port 5004)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/reviews | List reviews | Yes |
| GET | /api/reviews/{id} | Get review details | Yes |
| POST | /api/reviews | Create review | Yes |
| PUT | /api/reviews/{id} | Update review | Yes |
| DELETE | /api/reviews/{id} | Delete review | Yes |
| GET | /api/rooms/{id}/reviews | Get reviews for room | Yes |

---

## Authentication

The system uses JWT (JSON Web Tokens).

1. Register or login to get tokens
2. Include the access token in requests:
   ```
   Authorization: Bearer <your_token>
   ```
3. Tokens expire after 1 hour; use refresh token to get new ones

### User Roles

- user: Can book rooms, leave reviews
- facility_manager: Can manage rooms
- moderator: Can moderate reviews
- admin: Full access

---

## Database Schema

Four main tables:

**users**: id, username, email, password_hash, full_name, role, is_active, created_at

**rooms**: id, name, capacity, floor, building, location, equipment (JSON), status, hourly_rate

**bookings**: id, user_id, room_id, title, start_time, end_time, status, attendees

**reviews**: id, user_id, room_id, rating (1-5), comment, is_hidden, created_at

---

## Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker logs smr_users_service

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Run tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/
```

---

## Configuration

Environment variables are set in docker-compose.yml. Key settings:

```
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=smartmeetingroom
MYSQL_USER=admin
MYSQL_PASSWORD=secure_password

REDIS_HOST=redis
REDIS_PORT=6379

JWT_SECRET_KEY=your-secret-key
```

For local development, copy these to a .env file.

---

## Monitoring

- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- RabbitMQ Management: http://localhost:15672 (admin/admin)

---

## Project Structure

```
AhmadYateem_HassanFouani_meetingroom/
    configs/          - Configuration settings
    database/         - DB connection, schema, models
    docker/           - Dockerfiles for each service
    docs/             - Sphinx documentation
    messaging/        - RabbitMQ publisher/consumer
    profiling/        - Load testing scripts
    services/         - The four microservices
        users/        - User management
        rooms/        - Room management
        bookings/     - Booking management
        reviews/      - Review management
    tests/            - Unit and integration tests
    utils/            - Shared utilities (auth, cache, validators)
```

---

## Troubleshooting

**Services not starting**: Wait for MySQL to fully initialize (check with `docker logs smr_mysql`)

**Connection refused**: Ensure all containers are running with `docker ps`

**Authentication errors**: Check that JWT_SECRET_KEY is consistent across services

**Database errors**: Verify MySQL is healthy and schema was loaded from schema.sql

---

## Authors

- Ahmad Yateem - Users Service, Bookings Service
- Hassan Fouani - Rooms Service, Reviews Service
