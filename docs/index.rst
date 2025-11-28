Smart Meeting Room Management System
====================================

Welcome to the Smart Meeting Room Management System documentation. This guide covers the architecture, APIs, and supporting tools for the microservices powering authentication, room inventory, bookings, and reviews.

Team
----

* **Ahmad Yateem** — Users Service & Bookings Service
* **Hassan Fouani** — Rooms Service & Reviews Service

Quick Start
-----------

1. Install dependencies: ``pip install -r requirements.txt``
2. Copy environment template: ``cp configs/.env.template configs/.env`` and update secrets.
3. Start the stack: ``docker-compose up -d`` or ``make up``
4. Verify health: ``make health`` then open the Postman collections in ``postman/``.

Architecture at a Glance
------------------------

- Flask microservices exposed on ports 5001–5004 with JWT authentication
- PostgreSQL for persistence, Redis for caching, RabbitMQ for async messaging
- Prometheus + Grafana for metrics and dashboards
- Docker Compose for local orchestration and Make targets for common tasks

Documentation Map
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Contents

   architecture
   api/users
   api/rooms
   api/bookings
   api/reviews

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
