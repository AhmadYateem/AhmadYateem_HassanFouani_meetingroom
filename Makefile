.PHONY: help install build up down logs test clean health backup-db test-unit test-integration lint format docs

help:
	@echo "Smart Meeting Room Management System - Makefile Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make build          - Build Docker images"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - Show logs from all services"
	@echo "  make restart        - Restart all services"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests with coverage"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Clean up containers and volumes"
	@echo "  make health         - Check service health"
	@echo "  make backup-db      - Backup MySQL database"
	@echo ""
	@echo "Development:"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code with black"
	@echo "  make docs           - Generate documentation"

install:
	pip install -r requirements.txt

build:
	docker-compose build

build-no-cache:
	docker-compose build --no-cache

up:
	docker-compose up -d

up-logs:
	docker-compose up

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-users:
	docker-compose logs -f users-service

logs-rooms:
	docker-compose logs -f rooms-service

logs-bookings:
	docker-compose logs -f bookings-service

logs-reviews:
	docker-compose logs -f reviews-service

test:
	pytest tests/ -v --cov=services --cov=utils --cov-report=html --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v --cov=utils --cov-report=term-missing

test-integration:
	pytest tests/integration/ -v --cov=services --cov-report=term-missing

test-fast:
	pytest tests/unit/ -v -x --tb=short

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

clean-docker:
	docker-compose down -v --rmi local

health:
	@echo "Checking service health..."
	@echo ""
	@echo "Users Service (5001):"
	@curl -s http://localhost:5001/health || echo "  Status: DOWN"
	@echo ""
	@echo "Rooms Service (5002):"
	@curl -s http://localhost:5002/health || echo "  Status: DOWN"
	@echo ""
	@echo "Bookings Service (5003):"
	@curl -s http://localhost:5003/health || echo "  Status: DOWN"
	@echo ""
	@echo "Reviews Service (5004):"
	@curl -s http://localhost:5004/health || echo "  Status: DOWN"
	@echo ""

backup-db:
	@echo "Creating database backup..."
	docker exec smr_mysql mysqldump -uadmin -psecure_password smartmeetingroom > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created successfully"

restore-db:
	@echo "Restoring database from $(FILE)..."
	docker exec -i smr_mysql mysql -uadmin -psecure_password smartmeetingroom < $(FILE)
	@echo "Database restored successfully"

lint:
	flake8 services/ utils/ tests/ --max-line-length=100 --exclude=__pycache__
	pylint services/ utils/ --disable=C0114,C0115,C0116

format:
	black services/ utils/ tests/ --line-length=100
	isort services/ utils/ tests/

docs:
	cd docs && make html

shell-mysql:
	docker exec -it smr_mysql mysql -uadmin -psecure_password smartmeetingroom

shell-redis:
	docker exec -it smr_redis redis-cli

status:
	docker-compose ps

migrate:
	@echo "Running database migrations..."
	docker exec -i smr_mysql mysql -uadmin -psecure_password smartmeetingroom < database/schema.sql
	@echo "Migrations complete"

seed:
	@echo "Seeding database with test data..."
	docker exec -i smr_mysql mysql -uadmin -psecure_password smartmeetingroom < database/seed.sql
	@echo "Seeding complete"

dev-users:
	FLASK_ENV=development python -m services.users.app

dev-rooms:
	FLASK_ENV=development python -m services.rooms.app

dev-bookings:
	FLASK_ENV=development python -m services.bookings.app

dev-reviews:
	FLASK_ENV=development python -m services.reviews.app
