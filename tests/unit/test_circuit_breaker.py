"""
Unit tests for circuit breaker module.
Tests circuit breaker states, thresholds, and recovery.
"""

import pytest
import time
from unittest.mock import MagicMock

from utils.circuit_breaker import (
    CircuitBreaker, CircuitState, CircuitBreakerOpenError,
    CircuitBreakerRegistry, circuit_breaker,
    get_circuit_breaker, get_all_circuit_breakers_metrics
)


class TestCircuitBreakerStates:
    """Tests for circuit breaker state transitions."""

    def test_initial_state_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker(name='test')
        
        assert cb.state == CircuitState.CLOSED

    def test_state_opens_after_failures(self):
        """Test circuit opens after reaching failure threshold."""
        cb = CircuitBreaker(name='test', failure_threshold=3)
        
        def failing_func():
            raise Exception('Service error')
        
        for _ in range(3):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN

    def test_state_half_open_after_timeout(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        cb = CircuitBreaker(name='test', failure_threshold=1, timeout=0.1)
        
        def failing_func():
            raise Exception('Service error')
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        assert cb.state == CircuitState.OPEN
        
        time.sleep(0.15)
        
        try:
            cb.call(failing_func)
        except CircuitBreakerOpenError:
            pass
        except Exception:
            pass
        
        assert cb.state in [CircuitState.HALF_OPEN, CircuitState.OPEN]

    def test_state_closes_after_success_in_half_open(self):
        """Test circuit closes after successes in HALF_OPEN."""
        cb = CircuitBreaker(name='test', failure_threshold=1, 
                          timeout=0.1, success_threshold=1)
        
        def failing_func():
            raise Exception('Service error')
        
        def success_func():
            return 'success'
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        time.sleep(0.15)
        
        result = cb.call(success_func)
        
        assert result == 'success'
        assert cb.state == CircuitState.CLOSED


class TestFailureThreshold:
    """Tests for failure threshold behavior."""

    def test_no_open_below_threshold(self):
        """Test circuit doesn't open below threshold."""
        cb = CircuitBreaker(name='test', failure_threshold=5)
        
        def failing_func():
            raise Exception('Service error')
        
        for _ in range(4):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.CLOSED

    def test_open_at_threshold(self):
        """Test circuit opens at exact threshold."""
        cb = CircuitBreaker(name='test', failure_threshold=3)
        
        def failing_func():
            raise Exception('Service error')
        
        for _ in range(3):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN

    def test_failure_count_resets_on_success(self):
        """Test failure count resets after successful call."""
        cb = CircuitBreaker(name='test', failure_threshold=3)
        
        def failing_func():
            raise Exception('Service error')
        
        def success_func():
            return 'success'
        
        for _ in range(2):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        cb.call(success_func)
        
        assert cb.failure_count == 0


class TestTimeoutAndRecovery:
    """Tests for timeout and recovery behavior."""

    def test_open_circuit_rejects_calls(self):
        """Test open circuit rejects calls immediately."""
        cb = CircuitBreaker(name='test', failure_threshold=1, timeout=60)
        
        def failing_func():
            raise Exception('Service error')
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: 'test')

    def test_half_open_allows_test_call(self):
        """Test HALF_OPEN state allows test call."""
        cb = CircuitBreaker(name='test', failure_threshold=1, timeout=0.1)
        
        def failing_func():
            raise Exception('Service error')
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        time.sleep(0.15)
        
        def success_func():
            return 'success'
        
        result = cb.call(success_func)
        assert result == 'success'

    def test_half_open_reopens_on_failure(self):
        """Test HALF_OPEN reopens on failure."""
        cb = CircuitBreaker(name='test', failure_threshold=1, timeout=0.1)
        
        def failing_func():
            raise Exception('Service error')
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        time.sleep(0.15)
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        assert cb.state == CircuitState.OPEN


class TestSuccessThreshold:
    """Tests for success threshold in HALF_OPEN state."""

    def test_requires_multiple_successes(self):
        """Test requiring multiple successes to close."""
        cb = CircuitBreaker(name='test', failure_threshold=1, 
                          timeout=0.1, success_threshold=3)
        
        def failing_func():
            raise Exception('Service error')
        
        def success_func():
            return 'success'
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        time.sleep(0.15)
        
        cb.call(success_func)
        cb.call(success_func)
        
        assert cb.state == CircuitState.HALF_OPEN
        
        cb.call(success_func)
        
        assert cb.state == CircuitState.CLOSED


class TestMetrics:
    """Tests for circuit breaker metrics."""

    def test_metrics_tracking(self):
        """Test metrics are tracked correctly."""
        cb = CircuitBreaker(name='test', failure_threshold=5)
        
        def success_func():
            return 'success'
        
        def failing_func():
            raise Exception('error')
        
        cb.call(success_func)
        cb.call(success_func)
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        metrics = cb.metrics
        
        assert metrics['total_calls'] == 3
        assert metrics['total_successes'] == 2
        assert metrics['total_failures'] == 1

    def test_state_changes_recorded(self):
        """Test state changes are recorded."""
        cb = CircuitBreaker(name='test', failure_threshold=1)
        
        def failing_func():
            raise Exception('error')
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        metrics = cb.metrics
        
        assert metrics['state_changes'] >= 1


class TestCircuitBreakerRegistry:
    """Tests for circuit breaker registry."""

    def test_get_or_create(self):
        """Test get or create circuit breaker."""
        registry = CircuitBreakerRegistry()
        
        cb1 = registry.get_or_create('service1')
        cb2 = registry.get_or_create('service1')
        
        assert cb1 is cb2

    def test_different_names_different_breakers(self):
        """Test different names create different breakers."""
        registry = CircuitBreakerRegistry()
        
        cb1 = registry.get_or_create('service1')
        cb2 = registry.get_or_create('service2')
        
        assert cb1 is not cb2

    def test_get_all_metrics(self):
        """Test getting all metrics."""
        registry = CircuitBreakerRegistry()
        
        registry.get_or_create('service1')
        registry.get_or_create('service2')
        
        metrics = registry.get_all_metrics()
        
        assert 'service1' in metrics
        assert 'service2' in metrics


class TestCircuitBreakerDecorator:
    """Tests for circuit breaker decorator."""

    def test_decorator_protects_function(self):
        """Test decorator protects function with circuit breaker."""
        @circuit_breaker(name='test-decorator', failure_threshold=2)
        def protected_func():
            return 'success'
        
        result = protected_func()
        
        assert result == 'success'

    def test_decorator_opens_on_failures(self):
        """Test decorator opens circuit on failures."""
        call_count = 0
        
        @circuit_breaker(name='test-decorator-fail', failure_threshold=2, timeout=60)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception('error')
        
        for _ in range(2):
            try:
                failing_func()
            except Exception:
                pass
        
        with pytest.raises(CircuitBreakerOpenError):
            failing_func()


class TestForceStateChanges:
    """Tests for force state change methods."""

    def test_force_open(self):
        """Test force opening circuit."""
        cb = CircuitBreaker(name='test')
        
        cb.force_open()
        
        assert cb.state == CircuitState.OPEN

    def test_force_close(self):
        """Test force closing circuit."""
        cb = CircuitBreaker(name='test', failure_threshold=1)
        
        def failing_func():
            raise Exception('error')
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        cb.force_close()
        
        assert cb.state == CircuitState.CLOSED

    def test_reset(self):
        """Test reset circuit breaker."""
        cb = CircuitBreaker(name='test', failure_threshold=1)
        
        def failing_func():
            raise Exception('error')
        
        try:
            cb.call(failing_func)
        except Exception:
            pass
        
        cb.reset()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
