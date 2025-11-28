"""
Lightweight load testing helpers for the Smart Meeting Room Management System.

Author: Hassan Fouani

Features:
- Concurrent request generation
- Throughput and latency percentile reporting
- Simple stress testing harness for peak-load checks
"""

import concurrent.futures
import os
import statistics
import time
from typing import Dict, List, Optional

import requests

SERVICE_TARGETS = {
    'users': os.getenv('USERS_SERVICE_URL', 'http://localhost:5001/api/health'),
    'rooms': os.getenv('ROOMS_SERVICE_URL', 'http://localhost:5002/api/health'),
    'bookings': os.getenv('BOOKINGS_SERVICE_URL', 'http://localhost:5003/api/health'),
    'reviews': os.getenv('REVIEWS_SERVICE_URL', 'http://localhost:5004/api/health'),
}


def percentile(data: List[float], percent: float) -> float:
    if not data:
        return 0.0
    data_sorted = sorted(data)
    k = (len(data_sorted) - 1) * (percent / 100)
    f = int(k)
    c = min(f + 1, len(data_sorted) - 1)
    if f == c:
        return data_sorted[int(k)]
    return data_sorted[f] + (k - f) * (data_sorted[c] - data_sorted[f])


def _issue_request(session: requests.Session, method: str, url: str, payload: Optional[dict], headers: Dict[str, str]) -> Dict:
    start = time.perf_counter()
    response = session.request(method, url, json=payload, headers=headers, timeout=5)
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        'status': response.status_code,
        'latency_ms': latency_ms,
    }


def run_load_test(url: str, concurrency: int = 10, iterations: int = 50, method: str = 'GET', payload: Optional[dict] = None, headers: Optional[Dict[str, str]] = None) -> Dict:
    """Run a load test against a single endpoint and return aggregated metrics."""
    headers = headers or {}
    latencies: List[float] = []
    statuses: List[int] = []

    started_at = time.perf_counter()
    with requests.Session() as session:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(_issue_request, session, method, url, payload, headers)
                for _ in range(iterations)
            ]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                latencies.append(result['latency_ms'])
                statuses.append(result['status'])
    duration = time.perf_counter() - started_at

    success_count = len([code for code in statuses if 200 <= code < 400])
    throughput = iterations / duration if duration else 0

    metrics = {
        'iterations': iterations,
        'concurrency': concurrency,
        'duration_s': round(duration, 4),
        'throughput_rps': round(throughput, 2),
        'success_rate': round((success_count / iterations) * 100, 2) if iterations else 0,
        'latency_ms': {
            'avg': round(statistics.mean(latencies), 2) if latencies else 0,
            'p50': round(percentile(latencies, 50), 2) if latencies else 0,
            'p95': round(percentile(latencies, 95), 2) if latencies else 0,
            'p99': round(percentile(latencies, 99), 2) if latencies else 0,
        },
        'status_codes': {code: statuses.count(code) for code in set(statuses)},
    }
    return metrics


def stress_test(steps: List[int], target_url: str) -> None:
    """Run a stepped stress test to observe behavior as concurrency increases."""
    print(f"Stress testing {target_url}")
    for level in steps:
        metrics = run_load_test(target_url, concurrency=level, iterations=max(level * 5, 25))
        print(f"Concurrency {level}: "
              f"throughput={metrics['throughput_rps']} rps, "
              f"p95={metrics['latency_ms']['p95']} ms, "
              f"success={metrics['success_rate']}%")


if __name__ == '__main__':
    print("Running smoke load tests against service health endpoints...\n")
    for name, url in SERVICE_TARGETS.items():
        metrics = run_load_test(url, concurrency=5, iterations=25)
        print(f"{name}: {metrics}")

    print("\nFor peak testing, call stress_test with your own concurrency steps, e.g.:")
    print("  stress_test([5, 10, 20, 40], SERVICE_TARGETS['bookings'])")
