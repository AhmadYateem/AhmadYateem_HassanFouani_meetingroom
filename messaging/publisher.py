"""
RabbitMQ publisher for event-driven messaging.
Handles publishing events to message queues.
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError


logger = logging.getLogger(__name__)


class QueueNames:
    """
    Queue name constants.

    Attributes:
        BOOKING_CONFIRMATIONS: Queue for booking confirmation events
        BOOKING_CANCELLATIONS: Queue for booking cancellation events
        REVIEW_NOTIFICATIONS: Queue for review notification events
        USER_EVENTS: Queue for user registration events
    """
    BOOKING_CONFIRMATIONS = 'booking_confirmations'
    BOOKING_CANCELLATIONS = 'booking_cancellations'
    REVIEW_NOTIFICATIONS = 'review_notifications'
    USER_EVENTS = 'user_events'


class ExchangeNames:
    """
    Exchange name constants.

    Attributes:
        EVENTS: Main events exchange
        NOTIFICATIONS: Notifications exchange
    """
    EVENTS = 'smartmeetingroom_events'
    NOTIFICATIONS = 'smartmeetingroom_notifications'


class RabbitMQPublisher:
    """
    RabbitMQ publisher for event messages.

    Provides methods for publishing different event types
    with connection management and retry logic.

    Attributes:
        host: RabbitMQ host
        port: RabbitMQ port
        username: Authentication username
        password: Authentication password
        virtual_host: RabbitMQ virtual host
    """

    def __init__(self, host: str = None, port: int = None,
                 username: str = None, password: str = None,
                 virtual_host: str = '/', max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize RabbitMQ publisher.

        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            username: Authentication username
            password: Authentication password
            virtual_host: RabbitMQ virtual host
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.host = host or os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = port or int(os.getenv('RABBITMQ_PORT', '5672'))
        self.username = username or os.getenv('RABBITMQ_USER', 'admin')
        self.password = password or os.getenv('RABBITMQ_PASSWORD', 'admin')
        self.virtual_host = virtual_host
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._connection = None
        self._channel = None

    def _get_connection_parameters(self) -> pika.ConnectionParameters:
        """
        Get connection parameters.

        Returns:
            Configured ConnectionParameters
        """
        credentials = pika.PlainCredentials(self.username, self.password)
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.virtual_host,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )

    def connect(self) -> None:
        """
        Establish connection to RabbitMQ.

        Raises:
            AMQPConnectionError: If connection fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                parameters = self._get_connection_parameters()
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                
                self._setup_exchanges()
                self._setup_queues()
                
                logger.info("Connected to RabbitMQ successfully")
                return
            except AMQPConnectionError as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

    def _setup_exchanges(self) -> None:
        """
        Declare exchanges.
        """
        self._channel.exchange_declare(
            exchange=ExchangeNames.EVENTS,
            exchange_type='topic',
            durable=True
        )
        
        self._channel.exchange_declare(
            exchange=ExchangeNames.NOTIFICATIONS,
            exchange_type='fanout',
            durable=True
        )

    def _setup_queues(self) -> None:
        """
        Declare queues and bindings.
        """
        queues = [
            QueueNames.BOOKING_CONFIRMATIONS,
            QueueNames.BOOKING_CANCELLATIONS,
            QueueNames.REVIEW_NOTIFICATIONS,
            QueueNames.USER_EVENTS
        ]
        
        for queue in queues:
            self._channel.queue_declare(queue=queue, durable=True)
            
            self._channel.queue_bind(
                exchange=ExchangeNames.EVENTS,
                queue=queue,
                routing_key=queue
            )

    def _ensure_connection(self) -> None:
        """
        Ensure connection is active, reconnect if needed.
        """
        if self._connection is None or self._connection.is_closed:
            self.connect()
        elif self._channel is None or self._channel.is_closed:
            self._channel = self._connection.channel()
            self._setup_exchanges()
            self._setup_queues()

    def _publish(self, queue_name: str, message: Dict[str, Any],
                 routing_key: str = None) -> bool:
        """
        Publish message to queue.

        Args:
            queue_name: Target queue name
            message: Message data
            routing_key: Optional routing key

        Returns:
            True if published successfully
        """
        try:
            self._ensure_connection()
            
            message['timestamp'] = datetime.utcnow().isoformat()
            message['queue'] = queue_name
            
            body = json.dumps(message, default=str)
            
            properties = pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                timestamp=int(time.time())
            )
            
            self._channel.basic_publish(
                exchange='',
                routing_key=routing_key or queue_name,
                body=body,
                properties=properties
            )
            
            logger.info(f"Published message to {queue_name}")
            return True
        except (AMQPConnectionError, AMQPChannelError) as e:
            logger.error(f"Failed to publish to {queue_name}: {e}")
            self._connection = None
            self._channel = None
            return False

    def publish_booking_confirmation(self, booking_data: Dict[str, Any]) -> bool:
        """
        Publish booking confirmation event.

        Args:
            booking_data: Booking information

        Returns:
            True if published successfully
        """
        message = {
            'event_type': 'booking_confirmation',
            'data': booking_data
        }
        return self._publish(QueueNames.BOOKING_CONFIRMATIONS, message)

    def publish_booking_cancellation(self, booking_data: Dict[str, Any],
                                     reason: str = None) -> bool:
        """
        Publish booking cancellation event.

        Args:
            booking_data: Booking information
            reason: Cancellation reason

        Returns:
            True if published successfully
        """
        message = {
            'event_type': 'booking_cancellation',
            'data': booking_data,
            'reason': reason
        }
        return self._publish(QueueNames.BOOKING_CANCELLATIONS, message)

    def publish_review_notification(self, review_data: Dict[str, Any]) -> bool:
        """
        Publish review notification event.

        Args:
            review_data: Review information

        Returns:
            True if published successfully
        """
        message = {
            'event_type': 'review_notification',
            'data': review_data
        }
        return self._publish(QueueNames.REVIEW_NOTIFICATIONS, message)

    def publish_user_registration(self, user_data: Dict[str, Any]) -> bool:
        """
        Publish user registration event.

        Args:
            user_data: User information

        Returns:
            True if published successfully
        """
        safe_user_data = {k: v for k, v in user_data.items() 
                         if k not in ['password', 'password_hash']}
        
        message = {
            'event_type': 'user_registration',
            'data': safe_user_data
        }
        return self._publish(QueueNames.USER_EVENTS, message)

    def publish_user_updated(self, user_data: Dict[str, Any]) -> bool:
        """
        Publish user update event.

        Args:
            user_data: User information

        Returns:
            True if published successfully
        """
        safe_user_data = {k: v for k, v in user_data.items() 
                         if k not in ['password', 'password_hash']}
        
        message = {
            'event_type': 'user_updated',
            'data': safe_user_data
        }
        return self._publish(QueueNames.USER_EVENTS, message)

    def publish_custom_event(self, queue_name: str, event_type: str,
                             data: Dict[str, Any]) -> bool:
        """
        Publish custom event.

        Args:
            queue_name: Target queue
            event_type: Event type identifier
            data: Event data

        Returns:
            True if published successfully
        """
        message = {
            'event_type': event_type,
            'data': data
        }
        return self._publish(queue_name, message)

    def close(self) -> None:
        """
        Close connection.
        """
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and self._connection.is_open:
                self._connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
        finally:
            self._channel = None
            self._connection = None

    def __enter__(self):
        """
        Context manager entry.

        Returns:
            Self
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self.close()


_publisher_instance: Optional[RabbitMQPublisher] = None


def get_publisher() -> RabbitMQPublisher:
    """
    Get singleton publisher instance.

    Returns:
        RabbitMQPublisher instance
    """
    global _publisher_instance
    if _publisher_instance is None:
        _publisher_instance = RabbitMQPublisher()
        _publisher_instance.connect()
    return _publisher_instance


def close_publisher() -> None:
    """
    Close singleton publisher instance.
    """
    global _publisher_instance
    if _publisher_instance is not None:
        _publisher_instance.close()
        _publisher_instance = None
