"""
Performance profiling for the Smart Meeting Room Management System.

Author: Hassan Fouani

Includes:
- Database benchmarks
- Input validation throughput
- Cache latency checks
- Service response time sampling
- Memory profiling (via memory_profiler)
- CPU profiling (cProfile with a py-spy hint)
"""

import cProfile
import io
import os
import pstats
import sys
import time
import statistics
from typing import List
from datetime import datetime, timedelta

import requests
from memory_profiler import profile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

SERVICE_ENDPOINTS = {
    'users': os.getenv('USERS_SERVICE_URL', 'http://localhost:5001'),
    'rooms': os.getenv('ROOMS_SERVICE_URL', 'http://localhost:5002'),
    'bookings': os.getenv('BOOKINGS_SERVICE_URL', 'http://localhost:5003'),
    'reviews': os.getenv('REVIEWS_SERVICE_URL', 'http://localhost:5004'),
}


def percentile(data: List[float], percent: float) -> float:
    """Return a percentile value for a list of floats."""
    if not data:
        return 0.0
    data_sorted = sorted(data)
    k = (len(data_sorted) - 1) * (percent / 100)
    f = int(k)
    c = min(f + 1, len(data_sorted) - 1)
    if f == c:
        return data_sorted[int(k)]
    return data_sorted[f] + (k - f) * (data_sorted[c] - data_sorted[f])


def profile_function(func, *args, **kwargs):
    """Run cProfile on a function and print the top cumulative entries."""
    pr = cProfile.Profile()
    pr.enable()

    result = func(*args, **kwargs)

    pr.disable()

    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats('cumulative').print_stats(20)
    print(s.getvalue())

    return result


@profile
def test_database_operations():
    """Test database operation performance (counts, timing, memory)."""
    print("\n" + "=" * 80)
    print("DATABASE OPERATIONS PERFORMANCE TEST")
    print("=" * 80 + "\n")

    from flask import Flask
    from database.models import db, User, Room, Booking
    from configs.config import TestingConfig
    from utils.auth import hash_password

    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    db.init_app(app)

    with app.app_context():
        db.create_all()

        start = time.perf_counter()
        for i in range(100):
            user = User(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                password_hash=hash_password('TestPass123!'),
                full_name=f'Test User {i}',
                role='user',
            )
            db.session.add(user)
        db.session.commit()
        duration = time.perf_counter() - start
        print(f"Created 100 users in {duration:.4f}s | avg {duration / 100:.4f}s/user")

        start = time.perf_counter()
        for i in range(50):
            room = Room(
                name=f'Room {i}',
                capacity=10 + i,
                status='available',
            )
            db.session.add(room)
        db.session.commit()
        duration = time.perf_counter() - start
        print(f"Created 50 rooms in {duration:.4f}s | avg {duration / 50:.4f}s/room")

        start = time.perf_counter()
        for i in range(25):
            slot_start = datetime.utcnow() + timedelta(hours=i)
            booking = Booking(
                user_id=1,
                room_id=i % 5 + 1,
                title=f'Meeting {i}',
                start_time=slot_start,
                end_time=slot_start + timedelta(hours=1),
                status='confirmed',
            )
            db.session.add(booking)
        db.session.commit()
        duration = time.perf_counter() - start
        print(f"Created 25 bookings in {duration:.4f}s | avg {duration / 25:.4f}s/booking")

        start = time.perf_counter()
        users = User.query.filter_by(role='user').all()
        duration = time.perf_counter() - start
        print(f"Queried {len(users)} users in {duration:.4f}s")

        db.drop_all()


def test_validation_performance():
    """Test input validation throughput."""
    print("\n" + "=" * 80)
    print("INPUT VALIDATION PERFORMANCE TEST")
    print("=" * 80 + "\n")

    from utils.validators import validate_email_format, validate_username, validate_password

    iterations = 10000

    start = time.perf_counter()
    for i in range(iterations):
        try:
            validate_email_format(f'user{i}@example.com')
        except Exception:
            pass
    duration = time.perf_counter() - start
    print(f"Validated {iterations} emails in {duration:.4f}s | {duration / iterations * 1000:.4f} ms/op")

    start = time.perf_counter()
    for i in range(iterations):
        try:
            validate_username(f'username{i}')
        except Exception:
            pass
    duration = time.perf_counter() - start
    print(f"Validated {iterations} usernames in {duration:.4f}s | {duration / iterations * 1000:.4f} ms/op")

    start = time.perf_counter()
    for _ in range(iterations):
        try:
            validate_password('StrongPass123!')
        except Exception:
            pass
    duration = time.perf_counter() - start
    print(f"Validated {iterations} passwords in {duration:.4f}s | {duration / iterations * 1000:.4f} ms/op")


def test_cache_performance():
    """Test Redis cache performance."""
    print("\n" + "=" * 80)
    print("CACHE PERFORMANCE TEST")
    print("=" * 80 + "\n")

    from utils.cache import cache

    if not cache.enabled:
        print("Cache is disabled. Skipping cache performance tests.\n")
        return

    iterations = 1000

    start = time.perf_counter()
    for i in range(iterations):
        cache.set(f'test_key_{i}', {'data': f'value_{i}'}, ttl=60)
    duration = time.perf_counter() - start
    print(f"Set {iterations} cache entries in {duration:.4f}s | {duration / iterations * 1000:.4f} ms/set")

    start = time.perf_counter()
    for i in range(iterations):
        cache.get(f'test_key_{i}')
    duration = time.perf_counter() - start
    print(f"Retrieved {iterations} cache entries in {duration:.4f}s | {duration / iterations * 1000:.4f} ms/get")

    for i in range(iterations):
        cache.delete(f'test_key_{i}')


def test_service_response_times():
    """Sample response times for service health endpoints."""
    print("\n" + "=" * 80)
    print("SERVICE RESPONSE TIME SAMPLING")
    print("=" * 80 + "\n")

    session = requests.Session()
    endpoints = {
        'users_health': f"{SERVICE_ENDPOINTS['users']}/api/health",
        'rooms_health': f"{SERVICE_ENDPOINTS['rooms']}/api/health",
        'bookings_health': f"{SERVICE_ENDPOINTS['bookings']}/api/health",
        'reviews_health': f"{SERVICE_ENDPOINTS['reviews']}/api/health",
    }

    latencies: List[float] = []

    for name, url in endpoints.items():
        start = time.perf_counter()
        try:
            response = session.get(url, timeout=3)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)
            print(f"{name}: {response.status_code} in {elapsed_ms:.2f} ms")
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"{name}: error after {elapsed_ms:.2f} ms -> {exc}")

    if latencies:
        avg = statistics.mean(latencies)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)
        print(f"\nLatency summary -> avg: {avg:.2f} ms | p95: {p95:.2f} ms | p99: {p99:.2f} ms")
    else:
        print("\nNo latency samples collected. Ensure services are running.")


def cpu_profiling_hint():
    """Print guidance for running external CPU profiling with py-spy."""
    print("\n" + "=" * 80)
    print("CPU PROFILING (py-spy)")
    print("=" * 80 + "\n")
    print("For deeper CPU insights run:")
    print("  py-spy record -o profiling/pyspy.svg -- python profiling/performance_tests.py")
    print("Then open profiling/pyspy.svg to inspect flame graphs.")


def main():
    """Run all performance tests."""
    print("\n" + "=" * 80)
    print("SMART MEETING ROOM MANAGEMENT SYSTEM - PERFORMANCE PROFILING")
    print("=" * 80)

    try:
        profile_function(test_database_operations)
        test_validation_performance()
        test_cache_performance()
        test_service_response_times()
        cpu_profiling_hint()

        print("\n" + "=" * 80)
        print("PROFILING COMPLETED")
        print("=" * 80 + "\n")

    except Exception as exc:
        print(f"\nError during profiling: {exc}\n")


if __name__ == '__main__':
    main()
