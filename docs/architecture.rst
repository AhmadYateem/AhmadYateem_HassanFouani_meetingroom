Architecture
============

Overview
--------

The Smart Meeting Room Management System follows a microservices architecture built with Flask. Each service owns its domain, exposes a RESTful API secured with JWT, and communicates through shared infrastructure components where needed.

Core Services
-------------

- **Users Service** (port 5001): authentication, JWT issuance/refresh, profile management, RBAC.
- **Rooms Service** (port 5002): room catalog, amenities and equipment tracking, availability checks.
- **Bookings Service** (port 5003): booking lifecycle, conflict detection, recurring bookings, calendar views.
- **Reviews Service** (port 5004): review submission, moderation, helpful/unhelpful votes, rating aggregation.

Supporting Infrastructure
-------------------------

- **PostgreSQL**: primary data store for all services.
- **Redis**: caching for session data, room availability, and aggregated review metrics.
- **RabbitMQ**: async events for booking confirmations, cancellation notifications, and moderation alerts.
- **Prometheus + Grafana**: metrics scraping and visualization dashboards.
- **Docker Compose**: local orchestration for services and infrastructure.

Technology Stack
----------------

- **Framework**: Flask 3.0 with blueprints per service
- **ORM**: SQLAlchemy 2.x and migrations
- **Auth**: Flask-JWT-Extended for access and refresh tokens
- **Observability**: Prometheus client metrics, structured JSON logging, Grafana dashboards
- **Dev Tooling**: Pytest + coverage, Make targets, Postman collections, Sphinx documentation

Interaction Model
-----------------

- Clients authenticate via Users Service and pass ``Authorization: Bearer <token>`` to other services.
- Bookings Service queries Rooms Service availability and writes booking records to PostgreSQL.
- Reviews Service validates bookings before accepting reviews and publishes moderation events to RabbitMQ.
- Redis reduces load on PostgreSQL for frequent lookups (availability snapshots, user profile cache).

Operational Notes
-----------------

- Use ``make up`` to start the full stack locally, or ``docker-compose up -d`` if Make is unavailable.
- Health checks expose basic service readiness; see Postman collections for smoke tests.
- Metrics are scraped by Prometheus on the configured ports; dashboards are pre-wired in Grafana.
