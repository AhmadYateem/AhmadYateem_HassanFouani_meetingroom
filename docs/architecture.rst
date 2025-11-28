System Architecture
===================

This document provides a detailed overview of the Smart Meeting Room Management System architecture, explaining how the various components interact and the design decisions behind the system.

.. contents:: Table of Contents
   :local:
   :depth: 3

Architectural Overview
----------------------

The Smart Meeting Room Management System follows a microservices architecture pattern, where the application is decomposed into four independent services that communicate over HTTP. Each service is responsible for a specific domain of functionality and maintains its own data.

This architectural approach provides several benefits:

**Independent Deployability**
    Each service can be updated, scaled, or redeployed without affecting the other services. This allows for faster iteration and reduced risk during deployments.

**Technology Flexibility**
    While all services currently use Flask and Python, the architecture allows for different services to use different technologies if needed in the future.

**Scalability**
    Services that receive more traffic can be scaled independently. For example, during peak booking times, additional instances of the Bookings Service can be deployed.

**Fault Isolation**
    If one service experiences issues, the other services can continue operating. This improves overall system resilience.

Service Architecture
--------------------

Users Service (Port 5001)
~~~~~~~~~~~~~~~~~~~~~~~~~

The Users Service is the authentication and identity management hub for the entire system. It is developed and maintained by Ahmad Yateem.

**Primary Responsibilities:**

The Users Service handles user registration, allowing new users to create accounts with validated credentials. It manages the authentication process, issuing JWT access tokens and refresh tokens upon successful login. The service also maintains user profiles, storing personal information and preferences. Additionally, it implements role based access control (RBAC), ensuring users can only access resources appropriate to their role.

**Key Components:**

The service consists of several modules working together:

1. The ``routes.py`` module defines all HTTP endpoints and handles request validation
2. The ``dao.py`` module contains data access functions for user operations
3. The authentication utilities in ``utils/auth.py`` handle password hashing and JWT operations

**Security Features:**

The service implements several security measures including bcrypt password hashing with configurable rounds, account lockout after failed login attempts, token refresh mechanism for extended sessions, and input sanitization to prevent injection attacks.

Rooms Service (Port 5002)
~~~~~~~~~~~~~~~~~~~~~~~~~

The Rooms Service manages the catalog of available meeting rooms and their properties. It is developed and maintained by Hassan Fouani.

**Primary Responsibilities:**

This service maintains the room inventory, including details such as capacity, location, and available amenities. It handles availability checking, determining which rooms are free during specific time periods. The service also manages room status, tracking whether rooms are available, under maintenance, or temporarily unavailable.

**Key Components:**

1. The ``routes.py`` module exposes endpoints for room CRUD operations and availability queries
2. The ``dao.py`` module handles database interactions for room data
3. Filtering and search functionality allows users to find rooms matching their requirements

**Room Properties:**

Each room in the system has the following attributes:

* Name: A human readable identifier for the room
* Capacity: The maximum number of people the room can accommodate
* Floor: The floor number where the room is located
* Building: The building name or identifier
* Amenities: A list of available features such as projector, whiteboard, or video conferencing equipment
* Status: The current availability status of the room

Bookings Service (Port 5003)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Bookings Service manages the complete lifecycle of room reservations. It is developed and maintained by Ahmad Yateem.

**Primary Responsibilities:**

This service handles booking creation with automatic conflict detection, ensuring no double bookings occur. It manages booking modifications, allowing users to update reservation details. The service also handles cancellations and maintains a complete history of all bookings for reporting purposes.

**Key Components:**

1. The ``routes.py`` module defines booking endpoints with comprehensive validation
2. The ``dao.py`` module handles database operations including conflict checking
3. Integration with the Rooms Service validates room existence before accepting bookings

**Conflict Detection:**

The service implements sophisticated conflict detection to prevent overlapping bookings. When a new booking is requested, the system checks for any existing bookings that overlap with the requested time period. If a conflict is detected, the booking is rejected with a clear error message explaining the conflict.

**Booking States:**

Bookings progress through several states during their lifecycle:

* Pending: The initial state when a booking is created
* Confirmed: The booking has been verified and is active
* Cancelled: The booking has been cancelled by the user or an administrator
* Completed: The meeting time has passed

Reviews Service (Port 5004)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Reviews Service enables users to provide feedback on rooms they have used. It is developed and maintained by Hassan Fouani.

**Primary Responsibilities:**

This service manages review submission, allowing users to rate rooms and provide written feedback. It handles review moderation, enabling administrators to flag or remove inappropriate content. The service also calculates and provides rating statistics for each room.

**Key Components:**

1. The ``routes.py`` module exposes endpoints for review CRUD operations and moderation
2. The ``dao.py`` module handles database operations for review data
3. Rating aggregation functions calculate average ratings and distributions

**Review Properties:**

Each review contains the following information:

* Rating: A numeric score from 1 to 5 stars
* Comment: Optional written feedback about the room
* Title: A brief summary of the review
* Pros: Positive aspects noted by the reviewer
* Cons: Negative aspects noted by the reviewer
* Helpful Count: The number of users who found this review useful

Infrastructure Components
-------------------------

Database Layer
~~~~~~~~~~~~~~

The system uses MySQL as its primary data store. Each service connects to the database using a connection pool to efficiently manage database connections and improve performance under load.

**Connection Pooling:**

Connection pooling reduces the overhead of establishing new database connections for each request. The system maintains a pool of reusable connections that are allocated to requests as needed and returned to the pool when the request completes.

**Data Organization:**

While all services share a single database instance for simplicity, the tables are organized by service domain. This approach makes it easier to separate the data into individual databases if needed for scaling in the future.

Caching with Redis
~~~~~~~~~~~~~~~~~~

Redis provides fast, in memory caching for frequently accessed data. The system caches user session information, room availability snapshots, and aggregated review statistics.

**Cache Strategy:**

The system uses a cache aside pattern where the application first checks the cache for requested data. If the data is not in the cache (a cache miss), it is retrieved from the database and stored in the cache for future requests.

**Cache Invalidation:**

When data is modified, the corresponding cache entries are invalidated to ensure users always see current information. This is particularly important for booking availability where stale data could lead to conflicts.

Message Queue with RabbitMQ
~~~~~~~~~~~~~~~~~~~~~~~~~~~

RabbitMQ provides asynchronous messaging capabilities for operations that do not require immediate responses. This includes sending booking confirmation emails, processing review moderation alerts, and generating reports.

**Event Types:**

The system publishes several types of events:

* Booking Created: Triggered when a new booking is confirmed
* Booking Cancelled: Triggered when a booking is cancelled
* Review Flagged: Triggered when a review is flagged for moderation
* User Registered: Triggered when a new user account is created

Authentication Flow
-------------------

The system uses JSON Web Tokens (JWT) for authentication. Here is how the authentication process works:

**Step 1: User Login**

The user sends their credentials (username and password) to the Users Service login endpoint. The service validates the credentials against the stored password hash.

**Step 2: Token Issuance**

Upon successful authentication, the Users Service generates two tokens:

* An access token with a short expiration time (typically 1 hour) used for API requests
* A refresh token with a longer expiration time (typically 30 days) used to obtain new access tokens

**Step 3: Authenticated Requests**

For subsequent API requests, the client includes the access token in the Authorization header using the Bearer scheme::

    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

**Step 4: Token Refresh**

When the access token expires, the client can use the refresh token to obtain a new access token without requiring the user to log in again.

**Step 5: Token Validation**

Each service validates incoming tokens by checking the signature and expiration time. The token payload contains the user ID and role, which are used for authorization decisions.

Role Based Access Control
-------------------------

The system implements role based access control to restrict certain operations to authorized users. The following roles are defined:

**User Role**
    Standard users can create bookings, submit reviews, and manage their own profile. They can view room information and check availability.

**Facility Manager Role**
    Facility managers have all user permissions plus the ability to create, update, and delete rooms. They can also manage room status and availability.

**Moderator Role**
    Moderators have all user permissions plus the ability to review and moderate user submitted reviews. They can approve, reject, or remove flagged content.

**Admin Role**
    Administrators have full access to all system functions. They can manage users, assign roles, and perform any operation in the system.

Deployment Architecture
-----------------------

The system is containerized using Docker, with each service running in its own container. Docker Compose orchestrates the containers for local development and testing.

**Container Organization:**

* Each microservice runs in its own container
* MySQL runs in a dedicated database container
* Redis runs in a caching container
* RabbitMQ runs in a messaging container
* Prometheus and Grafana run in monitoring containers

**Network Configuration:**

All containers are connected to a shared Docker network, allowing them to communicate using service names as hostnames. External access is provided through exposed ports mapped to the host machine.

Monitoring and Observability
----------------------------

The system includes comprehensive monitoring capabilities:

**Health Checks**

Each service exposes a ``/health`` endpoint that returns the current service status. These endpoints are used by Docker for container health checks and by load balancers for routing decisions.

**Metrics Collection**

Prometheus scrapes metrics from each service, collecting information about request counts, response times, error rates, and resource utilization.

**Visualization**

Grafana provides dashboards for visualizing the collected metrics, enabling operators to monitor system health and identify performance issues.

**Logging**

All services use structured JSON logging, making it easy to aggregate and search logs across services. Log messages include correlation IDs for tracing requests across service boundaries.

Error Handling
--------------

The system implements consistent error handling across all services:

**Error Response Format**

All error responses follow a standard JSON format::

    {
        "error": "Error Type",
        "message": "A human readable description of what went wrong"
    }

**HTTP Status Codes**

The system uses standard HTTP status codes to indicate the type of error:

* 400 Bad Request: The request was malformed or contained invalid data
* 401 Unauthorized: Authentication is required but was not provided or is invalid
* 403 Forbidden: The authenticated user does not have permission for this operation
* 404 Not Found: The requested resource does not exist
* 409 Conflict: The request conflicts with existing data (such as duplicate usernames)
* 422 Unprocessable Entity: The request was valid but contained semantic errors
* 500 Internal Server Error: An unexpected error occurred on the server

Future Considerations
---------------------

The architecture is designed to accommodate future enhancements:

**Database Separation**
    If scaling requirements increase, each service can be migrated to its own database instance.

**Service Mesh**
    A service mesh like Istio could be added for advanced traffic management and security.

**Event Sourcing**
    Critical operations could be migrated to an event sourcing pattern for improved auditability.

**API Gateway**
    An API gateway could be added to provide a single entry point, rate limiting, and request routing.
