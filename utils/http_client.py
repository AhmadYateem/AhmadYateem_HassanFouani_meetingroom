"""
HTTP client wrapper with circuit breaker integration.
Provides fault-tolerant inter-service communication.

Author: Ahmad Yateem
"""

import time
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .circuit_breaker import circuit_breaker, CircuitBreakerOpenError
from .exceptions import ServiceUnavailableError, ExternalServiceError


logger = logging.getLogger(__name__)


class ServiceConfig:
    """
    Service URL configuration.

    Attributes:
        USERS_SERVICE: Users service base URL
        ROOMS_SERVICE: Rooms service base URL
        BOOKINGS_SERVICE: Bookings service base URL
        REVIEWS_SERVICE: Reviews service base URL
    """
    USERS_SERVICE = 'http://users-service:5001'
    ROOMS_SERVICE = 'http://rooms-service:5002'
    BOOKINGS_SERVICE = 'http://bookings-service:5003'
    REVIEWS_SERVICE = 'http://reviews-service:5004'

    @classmethod
    def get_service_url(cls, service_name: str) -> str:
        """
        Get service URL by name.

        Args:
            service_name: Service name (users, rooms, bookings, reviews)

        Returns:
            Service base URL

        Raises:
            ValueError: If service name is unknown
        """
        services = {
            'users': cls.USERS_SERVICE,
            'rooms': cls.ROOMS_SERVICE,
            'bookings': cls.BOOKINGS_SERVICE,
            'reviews': cls.REVIEWS_SERVICE
        }
        
        if service_name not in services:
            raise ValueError(f"Unknown service: {service_name}")
        
        return services[service_name]


class HTTPClient:
    """
    HTTP client with circuit breaker and retry logic.

    Provides fault-tolerant HTTP requests to microservices with:
    - Circuit breaker pattern for fail-fast behavior
    - Exponential backoff retry logic
    - Connection pooling
    - Configurable timeouts

    Attributes:
        base_url: Base URL for requests
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        backoff_factor: Exponential backoff multiplier
    """

    def __init__(self, base_url: str = None, timeout: int = 10,
                 max_retries: int = 3, backoff_factor: float = 0.5,
                 pool_connections: int = 10, pool_maxsize: int = 20):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            backoff_factor: Exponential backoff factor
            pool_connections: Number of connection pools
            pool_maxsize: Maximum connections per pool
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        self._session = self._create_session(
            pool_connections, 
            pool_maxsize
        )

    def _create_session(self, pool_connections: int, 
                        pool_maxsize: int) -> requests.Session:
        """
        Create requests session with retry adapter.

        Args:
            pool_connections: Number of connection pools
            pool_maxsize: Maximum connections per pool

        Returns:
            Configured requests Session
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session

    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Full URL
        """
        if self.base_url:
            return urljoin(self.base_url, endpoint)
        return endpoint

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            Response object

        Raises:
            ServiceUnavailableError: If service is unavailable
            ExternalServiceError: If request fails
        """
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {url}")
            raise ServiceUnavailableError(f"Service timeout: {url}") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {url}")
            raise ServiceUnavailableError(f"Service unavailable: {url}") from e
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {url}")
            raise ExternalServiceError(
                f"Service error: {e.response.status_code}",
                status_code=e.response.status_code
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {url} - {str(e)}")
            raise ExternalServiceError(f"Request failed: {str(e)}") from e

    def get(self, endpoint: str, params: Dict = None, 
            headers: Dict = None) -> requests.Response:
        """
        Make GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers

        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        return self._make_request('GET', url, params=params, headers=headers)

    def post(self, endpoint: str, data: Dict = None, json: Dict = None,
             headers: Dict = None) -> requests.Response:
        """
        Make POST request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data
            headers: Request headers

        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        return self._make_request('POST', url, data=data, json=json, headers=headers)

    def put(self, endpoint: str, data: Dict = None, json: Dict = None,
            headers: Dict = None) -> requests.Response:
        """
        Make PUT request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data
            headers: Request headers

        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        return self._make_request('PUT', url, data=data, json=json, headers=headers)

    def delete(self, endpoint: str, headers: Dict = None) -> requests.Response:
        """
        Make DELETE request.

        Args:
            endpoint: API endpoint
            headers: Request headers

        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        return self._make_request('DELETE', url, headers=headers)

    def patch(self, endpoint: str, data: Dict = None, json: Dict = None,
              headers: Dict = None) -> requests.Response:
        """
        Make PATCH request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data
            headers: Request headers

        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        return self._make_request('PATCH', url, data=data, json=json, headers=headers)

    def close(self) -> None:
        """
        Close the session and release connections.
        """
        self._session.close()


class ServiceClient:
    """
    Service client with circuit breaker protection.

    Provides methods for calling other microservices with
    automatic circuit breaker integration.

    Attributes:
        service_name: Target service name
        http_client: Underlying HTTP client
    """

    def __init__(self, service_name: str, failure_threshold: int = 5,
                 timeout: int = 30, success_threshold: int = 2,
                 request_timeout: int = 10):
        """
        Initialize service client.

        Args:
            service_name: Service name (users, rooms, bookings, reviews)
            failure_threshold: Circuit breaker failure threshold
            timeout: Circuit breaker timeout
            success_threshold: Circuit breaker success threshold
            request_timeout: HTTP request timeout
        """
        self.service_name = service_name
        self._base_url = ServiceConfig.get_service_url(service_name)
        self._http_client = HTTPClient(
            base_url=self._base_url,
            timeout=request_timeout
        )
        
        self._failure_threshold = failure_threshold
        self._timeout = timeout
        self._success_threshold = success_threshold

    def _get_circuit_breaker_decorator(self):
        """
        Get circuit breaker decorator for this service.

        Returns:
            Circuit breaker decorator
        """
        return circuit_breaker(
            name=f"{self.service_name}-service",
            failure_threshold=self._failure_threshold,
            timeout=self._timeout,
            success_threshold=self._success_threshold
        )

    def get(self, endpoint: str, params: Dict = None,
            headers: Dict = None) -> Dict[str, Any]:
        """
        Make protected GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers

        Returns:
            JSON response data

        Raises:
            CircuitBreakerOpenError: If circuit is open
            ServiceUnavailableError: If service unavailable
        """
        @self._get_circuit_breaker_decorator()
        def _request():
            response = self._http_client.get(endpoint, params=params, headers=headers)
            return response.json()
        
        return _request()

    def post(self, endpoint: str, data: Dict = None, json: Dict = None,
             headers: Dict = None) -> Dict[str, Any]:
        """
        Make protected POST request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data
            headers: Request headers

        Returns:
            JSON response data

        Raises:
            CircuitBreakerOpenError: If circuit is open
            ServiceUnavailableError: If service unavailable
        """
        @self._get_circuit_breaker_decorator()
        def _request():
            response = self._http_client.post(endpoint, data=data, json=json, headers=headers)
            return response.json()
        
        return _request()

    def put(self, endpoint: str, data: Dict = None, json: Dict = None,
            headers: Dict = None) -> Dict[str, Any]:
        """
        Make protected PUT request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data
            headers: Request headers

        Returns:
            JSON response data

        Raises:
            CircuitBreakerOpenError: If circuit is open
            ServiceUnavailableError: If service unavailable
        """
        @self._get_circuit_breaker_decorator()
        def _request():
            response = self._http_client.put(endpoint, data=data, json=json, headers=headers)
            return response.json()
        
        return _request()

    def delete(self, endpoint: str, headers: Dict = None) -> Dict[str, Any]:
        """
        Make protected DELETE request.

        Args:
            endpoint: API endpoint
            headers: Request headers

        Returns:
            JSON response data

        Raises:
            CircuitBreakerOpenError: If circuit is open
            ServiceUnavailableError: If service unavailable
        """
        @self._get_circuit_breaker_decorator()
        def _request():
            response = self._http_client.delete(endpoint, headers=headers)
            return response.json()
        
        return _request()

    def close(self) -> None:
        """
        Close the HTTP client.
        """
        self._http_client.close()


class UsersServiceClient(ServiceClient):
    """
    Client for Users Service.

    Provides typed methods for common user operations.
    """

    def __init__(self, **kwargs):
        """
        Initialize users service client.

        Args:
            **kwargs: ServiceClient configuration
        """
        super().__init__('users', **kwargs)

    def get_user(self, user_id: int, token: str) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID
            token: JWT authorization token

        Returns:
            User data
        """
        headers = {'Authorization': f'Bearer {token}'}
        return self.get(f'/api/users/{user_id}', headers=headers)

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token.

        Args:
            token: JWT token to validate

        Returns:
            Token validation result
        """
        headers = {'Authorization': f'Bearer {token}'}
        return self.get('/api/auth/validate', headers=headers)


class RoomsServiceClient(ServiceClient):
    """
    Client for Rooms Service.

    Provides typed methods for common room operations.
    """

    def __init__(self, **kwargs):
        """
        Initialize rooms service client.

        Args:
            **kwargs: ServiceClient configuration
        """
        super().__init__('rooms', **kwargs)

    def get_room(self, room_id: int, token: str) -> Dict[str, Any]:
        """
        Get room by ID.

        Args:
            room_id: Room ID
            token: JWT authorization token

        Returns:
            Room data
        """
        headers = {'Authorization': f'Bearer {token}'}
        return self.get(f'/api/rooms/{room_id}', headers=headers)

    def check_room_exists(self, room_id: int, token: str) -> bool:
        """
        Check if room exists.

        Args:
            room_id: Room ID
            token: JWT authorization token

        Returns:
            True if room exists
        """
        try:
            self.get_room(room_id, token)
            return True
        except ExternalServiceError as e:
            if e.status_code == 404:
                return False
            raise


class BookingsServiceClient(ServiceClient):
    """
    Client for Bookings Service.

    Provides typed methods for common booking operations.
    """

    def __init__(self, **kwargs):
        """
        Initialize bookings service client.

        Args:
            **kwargs: ServiceClient configuration
        """
        super().__init__('bookings', **kwargs)

    def get_booking(self, booking_id: int, token: str) -> Dict[str, Any]:
        """
        Get booking by ID.

        Args:
            booking_id: Booking ID
            token: JWT authorization token

        Returns:
            Booking data
        """
        headers = {'Authorization': f'Bearer {token}'}
        return self.get(f'/api/bookings/{booking_id}', headers=headers)

    def check_availability(self, room_id: int, start_time: str, 
                          end_time: str, token: str) -> Dict[str, Any]:
        """
        Check room availability.

        Args:
            room_id: Room ID
            start_time: Start time ISO format
            end_time: End time ISO format
            token: JWT authorization token

        Returns:
            Availability check result
        """
        headers = {'Authorization': f'Bearer {token}'}
        return self.post(
            '/api/bookings/check-availability',
            json={
                'room_id': room_id,
                'start_time': start_time,
                'end_time': end_time
            },
            headers=headers
        )


class ReviewsServiceClient(ServiceClient):
    """
    Client for Reviews Service.

    Provides typed methods for common review operations.
    """

    def __init__(self, **kwargs):
        """
        Initialize reviews service client.

        Args:
            **kwargs: ServiceClient configuration
        """
        super().__init__('reviews', **kwargs)

    def get_room_reviews(self, room_id: int, token: str) -> Dict[str, Any]:
        """
        Get reviews for a room.

        Args:
            room_id: Room ID
            token: JWT authorization token

        Returns:
            Room reviews data
        """
        headers = {'Authorization': f'Bearer {token}'}
        return self.get(f'/api/reviews/room/{room_id}', headers=headers)

    def get_room_rating(self, room_id: int, token: str) -> Dict[str, Any]:
        """
        Get average rating for a room.

        Args:
            room_id: Room ID
            token: JWT authorization token

        Returns:
            Room rating data
        """
        headers = {'Authorization': f'Bearer {token}'}
        return self.get(f'/api/reviews/room/{room_id}/rating', headers=headers)


def create_service_client(service_name: str, **kwargs) -> ServiceClient:
    """
    Factory function to create service client.

    Args:
        service_name: Service name
        **kwargs: Client configuration

    Returns:
        Appropriate service client instance
    """
    clients = {
        'users': UsersServiceClient,
        'rooms': RoomsServiceClient,
        'bookings': BookingsServiceClient,
        'reviews': ReviewsServiceClient
    }
    
    client_class = clients.get(service_name, ServiceClient)
    
    if client_class == ServiceClient:
        return ServiceClient(service_name, **kwargs)
    
    return client_class(**kwargs)
