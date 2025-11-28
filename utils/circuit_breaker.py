"""
Circuit Breaker pattern implementation for fault-tolerant service communication.
Provides protection against cascading failures in microservices architecture.

Author: Ahmad Yateem
"""

import threading
import time
from functools import wraps
from typing import Callable, Any, Optional
from enum import Enum

from .exceptions import ServiceUnavailableError


class CircuitState(Enum):
    """
    Circuit breaker states.

    Attributes:
        CLOSED: Normal operation, requests pass through
        OPEN: Circuit tripped, requests fail immediately
        HALF_OPEN: Testing if service recovered
    """
    CLOSED = 'CLOSED'
    OPEN = 'OPEN'
    HALF_OPEN = 'HALF_OPEN'


class CircuitBreakerOpenError(ServiceUnavailableError):
    """
    Exception raised when circuit breaker is open.

    Attributes:
        message: Error message
        circuit_name: Name of the circuit breaker
        retry_after: Seconds until circuit may close
    """

    def __init__(self, message: str, circuit_name: str = None, 
                 retry_after: float = None):
        """
        Initialize circuit breaker open error.

        Args:
            message: Error message
            circuit_name: Name of the circuit breaker
            retry_after: Seconds until retry
        """
        super().__init__(message)
        self.circuit_name = circuit_name
        self.retry_after = retry_after


class CircuitBreaker:
    """
    Circuit Breaker implementation with three states.

    Provides fault tolerance by failing fast when a service is unavailable,
    preventing cascading failures across microservices.

    Attributes:
        name: Circuit breaker identifier
        failure_threshold: Failures before opening circuit
        timeout: Seconds before attempting recovery
        success_threshold: Successes needed to close circuit
        excluded_exceptions: Exceptions that don't count as failures
    """

    def __init__(self, name: str = 'default', failure_threshold: int = 5,
                 timeout: int = 30, success_threshold: int = 2,
                 excluded_exceptions: tuple = None):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name for identification
            failure_threshold: Number of failures to open circuit
            timeout: Seconds in OPEN state before testing recovery
            success_threshold: Successes in HALF_OPEN to close circuit
            excluded_exceptions: Exception types that don't trigger failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.excluded_exceptions = excluded_exceptions or ()
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._lock = threading.Lock()
        
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._state_changes = []

    @property
    def state(self) -> CircuitState:
        """
        Get current circuit state.

        Returns:
            Current CircuitState
        """
        return self._state

    @property
    def failure_count(self) -> int:
        """
        Get current failure count.

        Returns:
            Number of consecutive failures
        """
        return self._failure_count

    @property
    def metrics(self) -> dict:
        """
        Get circuit breaker metrics.

        Returns:
            Dictionary with metrics data
        """
        with self._lock:
            return {
                'name': self.name,
                'state': self._state.value,
                'failure_count': self._failure_count,
                'success_count': self._success_count,
                'total_calls': self._total_calls,
                'total_failures': self._total_failures,
                'total_successes': self._total_successes,
                'state_changes': len(self._state_changes),
                'last_failure_time': self._last_failure_time,
                'failure_threshold': self.failure_threshold,
                'timeout': self.timeout,
                'success_threshold': self.success_threshold
            }

    def _change_state(self, new_state: CircuitState) -> None:
        """
        Change circuit state and record the transition.

        Args:
            new_state: New circuit state
        """
        if self._state != new_state:
            self._state_changes.append({
                'from': self._state.value,
                'to': new_state.value,
                'timestamp': time.time()
            })
            self._state = new_state

    def _on_success(self) -> None:
        """
        Handle successful call.
        
        Resets failure count in CLOSED state.
        Increments success count in HALF_OPEN and closes circuit if threshold met.
        """
        with self._lock:
            self._total_successes += 1
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._change_state(CircuitState.CLOSED)
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def _on_failure(self) -> None:
        """
        Handle failed call.
        
        Increments failure count and opens circuit if threshold exceeded.
        Returns to OPEN state if failure occurs in HALF_OPEN.
        """
        with self._lock:
            self._total_failures += 1
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._change_state(CircuitState.OPEN)
                self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._change_state(CircuitState.OPEN)

    def _should_allow_request(self) -> bool:
        """
        Check if request should be allowed through circuit.

        Returns:
            True if request allowed, False otherwise
        """
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                if self._last_failure_time is None:
                    return True
                
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.timeout:
                    self._change_state(CircuitState.HALF_OPEN)
                    self._success_count = 0
                    return True
                return False
            
            if self._state == CircuitState.HALF_OPEN:
                return True
            
            return False

    def _get_retry_after(self) -> Optional[float]:
        """
        Calculate seconds until circuit may allow requests.

        Returns:
            Seconds until retry or None if not applicable
        """
        if self._state != CircuitState.OPEN:
            return None
        
        if self._last_failure_time is None:
            return None
        
        elapsed = time.time() - self._last_failure_time
        remaining = self.timeout - elapsed
        return max(0, remaining)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function raises exception
        """
        with self._lock:
            self._total_calls += 1
        
        if not self._should_allow_request():
            retry_after = self._get_retry_after()
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN",
                circuit_name=self.name,
                retry_after=retry_after
            )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.excluded_exceptions:
            self._on_success()
            raise
        except Exception as e:
            self._on_failure()
            raise e

    def reset(self) -> None:
        """
        Reset circuit breaker to initial state.
        
        Clears all counters and sets state to CLOSED.
        """
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def force_open(self) -> None:
        """
        Force circuit to OPEN state.
        
        Useful for maintenance or testing.
        """
        with self._lock:
            self._change_state(CircuitState.OPEN)
            self._last_failure_time = time.time()

    def force_close(self) -> None:
        """
        Force circuit to CLOSED state.
        
        Useful for recovery after maintenance.
        """
        with self._lock:
            self._change_state(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Provides centralized access and management of circuit breakers
    across the application.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Singleton pattern implementation.

        Returns:
            Single registry instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers = {}
                    cls._instance._breakers_lock = threading.Lock()
        return cls._instance

    def get_or_create(self, name: str, **kwargs) -> CircuitBreaker:
        """
        Get existing or create new circuit breaker.

        Args:
            name: Circuit breaker name
            **kwargs: Configuration options for new breaker

        Returns:
            CircuitBreaker instance
        """
        with self._breakers_lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name=name, **kwargs)
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get circuit breaker by name.

        Args:
            name: Circuit breaker name

        Returns:
            CircuitBreaker or None if not found
        """
        with self._breakers_lock:
            return self._breakers.get(name)

    def get_all_metrics(self) -> dict:
        """
        Get metrics for all circuit breakers.

        Returns:
            Dictionary mapping names to metrics
        """
        with self._breakers_lock:
            return {
                name: breaker.metrics 
                for name, breaker in self._breakers.items()
            }

    def reset_all(self) -> None:
        """
        Reset all circuit breakers to CLOSED state.
        """
        with self._breakers_lock:
            for breaker in self._breakers.values():
                breaker.reset()


def circuit_breaker(name: str = 'default', failure_threshold: int = 5,
                    timeout: int = 30, success_threshold: int = 2,
                    excluded_exceptions: tuple = None):
    """
    Decorator for protecting functions with circuit breaker.

    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        timeout: Seconds before recovery attempt
        success_threshold: Successes to close circuit
        excluded_exceptions: Exceptions that don't trigger failures

    Returns:
        Decorated function

    Example:
        @circuit_breaker(name='users-service', failure_threshold=3)
        def get_user(user_id):
            return requests.get(f'/api/users/{user_id}')
    """
    registry = CircuitBreakerRegistry()
    
    def decorator(func: Callable) -> Callable:
        breaker = registry.get_or_create(
            name,
            failure_threshold=failure_threshold,
            timeout=timeout,
            success_threshold=success_threshold,
            excluded_exceptions=excluded_exceptions
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """
    Get circuit breaker by name from registry.

    Args:
        name: Circuit breaker name

    Returns:
        CircuitBreaker or None
    """
    registry = CircuitBreakerRegistry()
    return registry.get(name)


def get_all_circuit_breakers_metrics() -> dict:
    """
    Get metrics for all registered circuit breakers.

    Returns:
        Dictionary with all metrics
    """
    registry = CircuitBreakerRegistry()
    return registry.get_all_metrics()
