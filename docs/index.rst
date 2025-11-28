Smart Meeting Room Management System
=====================================

Welcome to the comprehensive documentation for the Smart Meeting Room Management System. This documentation provides complete guidance for understanding, deploying, and using the microservices that power room booking, user management, and review functionality.

About This Project
------------------

The Smart Meeting Room Management System is a modern, microservices based application designed to streamline the process of booking meeting rooms in corporate environments. Built with Flask and Python, the system provides a robust API for managing users, rooms, bookings, and reviews.

This project was developed as part of EECE 435L at the American University of Beirut during the Fall 2024 semester.

Development Team
----------------

**Ahmad Yateem**
    Responsible for the Users Service and Bookings Service. Ahmad designed and implemented the authentication system, user profile management, JWT token handling, and the complete booking lifecycle including conflict detection and calendar integration.

**Hassan Fouani**
    Responsible for the Rooms Service and Reviews Service. Hassan designed and implemented the room catalog management, availability checking, amenities tracking, and the review system including moderation workflows and rating aggregation.

System Overview
---------------

The system consists of four independent microservices that communicate through HTTP APIs and share a common authentication mechanism:

1. **Users Service** runs on port 5001 and handles all authentication and user management operations
2. **Rooms Service** runs on port 5002 and manages the catalog of available meeting rooms
3. **Bookings Service** runs on port 5003 and handles the complete booking lifecycle
4. **Reviews Service** runs on port 5004 and manages user reviews and ratings for rooms

Each service is designed to be independently deployable and scalable, following modern microservices best practices.

Quick Start Guide
-----------------

To get the system running on your local machine, follow these steps:

**Step 1: Install Dependencies**

Open your terminal and navigate to the project directory. Run the following command to install all required Python packages::

    pip install -r requirements.txt

**Step 2: Configure Environment Variables**

Copy the environment template file and update it with your specific configuration::

    cp configs/.env.template configs/.env

Open the newly created ``.env`` file and update the database credentials, JWT secret key, and other configuration values as needed for your environment.

**Step 3: Start the Services**

You can start all services using Docker Compose::

    docker-compose up -d

Alternatively, if you have Make installed, you can use::

    make up

**Step 4: Verify the Installation**

Check that all services are running correctly by testing their health endpoints::

    make health

You can also import the Postman collections from the ``postman/`` directory to test the APIs interactively.

Technology Stack
----------------

The system is built using the following technologies:

**Backend Framework**
    Flask 3.0 with Blueprints for modular route organization

**Database**
    MySQL for persistent data storage with connection pooling

**Caching**
    Redis for session caching and frequently accessed data

**Message Queue**
    RabbitMQ for asynchronous event processing

**Authentication**
    JSON Web Tokens (JWT) using the Flask JWT Extended library

**Monitoring**
    Prometheus for metrics collection and Grafana for visualization

**Containerization**
    Docker and Docker Compose for development and deployment

**Documentation**
    Sphinx with the Read the Docs theme for API documentation

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Architecture and Design

   architecture

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/users
   api/rooms
   api/bookings
   api/reviews

Getting Help
------------

If you encounter any issues or have questions about the system:

1. Check the API documentation for endpoint specifications and examples
2. Review the Postman collections for working request examples
3. Examine the service logs using ``docker logs <service_name>``
4. Contact the development team for additional support

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
