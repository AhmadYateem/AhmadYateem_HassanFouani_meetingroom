"""
RabbitMQ consumer for event-driven messaging.
Handles consuming and processing events from message queues.

Author: Ahmad Yateem
"""

import json
import logging
import os
import threading
import time
from typing import Callable, Dict, Any, Optional, List
from functools import wraps

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


class EventHandlers:
    """
    Default event handlers for different event types.

    Provides placeholder implementations for event processing.
    """

    @staticmethod
    def handle_booking_confirmation(data: Dict[str, Any]) -> bool:
        """
        Handle booking confirmation event.

        Args:
            data: Booking data

        Returns:
            True if handled successfully
        """
        logger.info(f"Processing booking confirmation: {data.get('data', {}).get('id')}")
        
        booking = data.get('data', {})
        user_email = booking.get('email')
        title = booking.get('title')
        start_time = booking.get('start_time')
        room_name = booking.get('room_name')
        
        logger.info(
            f"Sending confirmation email to {user_email} for booking '{title}' "
            f"at {room_name} on {start_time}"
        )
        
        return True

    @staticmethod
    def handle_booking_cancellation(data: Dict[str, Any]) -> bool:
        """
        Handle booking cancellation event.

        Args:
            data: Cancellation data with reason

        Returns:
            True if handled successfully
        """
        logger.info(f"Processing booking cancellation: {data.get('data', {}).get('id')}")
        
        booking = data.get('data', {})
        reason = data.get('reason', 'No reason provided')
        user_email = booking.get('email')
        title = booking.get('title')
        
        logger.info(
            f"Sending cancellation email to {user_email} for booking '{title}'. "
            f"Reason: {reason}"
        )
        
        return True

    @staticmethod
    def handle_review_notification(data: Dict[str, Any]) -> bool:
        """
        Handle review notification event.

        Args:
            data: Review data

        Returns:
            True if handled successfully
        """
        logger.info(f"Processing review notification: {data.get('data', {}).get('id')}")
        
        review = data.get('data', {})
        room_id = review.get('room_id')
        rating = review.get('rating')
        reviewer = review.get('username')
        
        logger.info(
            f"Notifying room manager about new review for room {room_id}. "
            f"Rating: {rating}/5 by {reviewer}"
        )
        
        return True

    @staticmethod
    def handle_user_registration(data: Dict[str, Any]) -> bool:
        """
        Handle user registration event.

        Args:
            data: User data

        Returns:
            True if handled successfully
        """
        logger.info(f"Processing user registration: {data.get('data', {}).get('id')}")
        
        user = data.get('data', {})
        email = user.get('email')
        username = user.get('username')
        full_name = user.get('full_name')
        
        logger.info(
            f"Sending welcome email to {email} ({full_name or username})"
        )
        
        return True


class RabbitMQConsumer:
    """
    RabbitMQ consumer for processing event messages.

    Provides methods for consuming messages from queues
    with acknowledgment and error handling.

    Attributes:
        host: RabbitMQ host
        port: RabbitMQ port
        username: Authentication username
        password: Authentication password
        virtual_host: RabbitMQ virtual host
    """

    def __init__(self, host: str = None, port: int = None,
                 username: str = None, password: str = None,
                 virtual_host: str = '/', prefetch_count: int = 1,
                 max_retries: int = 3, retry_delay: float = 5.0):
        """
        Initialize RabbitMQ consumer.

        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            username: Authentication username
            password: Authentication password
            virtual_host: RabbitMQ virtual host
            prefetch_count: Number of messages to prefetch
            max_retries: Maximum message processing retries
            retry_delay: Delay between retries in seconds
        """
        self.host = host or os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = port or int(os.getenv('RABBITMQ_PORT', '5672'))
        self.username = username or os.getenv('RABBITMQ_USER', 'admin')
        self.password = password or os.getenv('RABBITMQ_PASSWORD', 'admin')
        self.virtual_host = virtual_host
        self.prefetch_count = prefetch_count
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._connection = None
        self._channel = None
        self._handlers: Dict[str, Callable] = {}
        self._consuming = False
        self._consumer_threads: List[threading.Thread] = []

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
            AMQPConnectionError: If connection fails
        """
        try:
            parameters = self._get_connection_parameters()
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            self._channel.basic_qos(prefetch_count=self.prefetch_count)
            
            logger.info("Consumer connected to RabbitMQ successfully")
        except AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def register_handler(self, queue_name: str, handler: Callable) -> None:
        """
        Register handler for queue.

        Args:
            queue_name: Queue to handle
            handler: Handler function
        """
        self._handlers[queue_name] = handler
        logger.info(f"Registered handler for queue: {queue_name}")

    def register_default_handlers(self) -> None:
        """
        Register default event handlers.
        """
        self.register_handler(
            QueueNames.BOOKING_CONFIRMATIONS,
            EventHandlers.handle_booking_confirmation
        )
        self.register_handler(
            QueueNames.BOOKING_CANCELLATIONS,
            EventHandlers.handle_booking_cancellation
        )
        self.register_handler(
            QueueNames.REVIEW_NOTIFICATIONS,
            EventHandlers.handle_review_notification
        )
        self.register_handler(
            QueueNames.USER_EVENTS,
            EventHandlers.handle_user_registration
        )

    def _process_message(self, channel, method, properties, body,
                         handler: Callable) -> None:
        """
        Process received message.

        Args:
            channel: AMQP channel
            method: Delivery method
            properties: Message properties
            body: Message body
            handler: Handler function
        """
        try:
            message = json.loads(body.decode('utf-8'))
            logger.info(f"Received message from {method.routing_key}: {message.get('event_type')}")
            
            success = handler(message)
            
            if success:
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Message processed successfully: {method.delivery_tag}")
            else:
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                logger.warning(f"Message processing failed, requeued: {method.delivery_tag}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _create_callback(self, handler: Callable) -> Callable:
        """
        Create callback wrapper for handler.

        Args:
            handler: Handler function

        Returns:
            Callback function
        """
        def callback(channel, method, properties, body):
            self._process_message(channel, method, properties, body, handler)
        return callback

    def consume(self, queue_name: str, handler: Callable = None) -> None:
        """
        Start consuming from queue.

        Args:
            queue_name: Queue to consume from
            handler: Optional handler override
        """
        if self._connection is None or self._connection.is_closed:
            self.connect()
        
        handler = handler or self._handlers.get(queue_name)
        if handler is None:
            raise ValueError(f"No handler registered for queue: {queue_name}")
        
        self._channel.queue_declare(queue=queue_name, durable=True)
        
        callback = self._create_callback(handler)
        
        self._channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        
        logger.info(f"Started consuming from queue: {queue_name}")

    def start_consuming(self, blocking: bool = True) -> None:
        """
        Start consuming messages.

        Args:
            blocking: Whether to block current thread
        """
        if self._connection is None or self._connection.is_closed:
            self.connect()
        
        self._consuming = True
        
        if blocking:
            logger.info("Starting message consumption (blocking)")
            try:
                self._channel.start_consuming()
            except KeyboardInterrupt:
                self.stop_consuming()
        else:
            thread = threading.Thread(target=self._consume_in_thread)
            thread.daemon = True
            thread.start()
            self._consumer_threads.append(thread)
            logger.info("Started message consumption in background thread")

    def _consume_in_thread(self) -> None:
        """
        Consume messages in thread.
        """
        try:
            while self._consuming:
                self._connection.process_data_events(time_limit=1)
        except Exception as e:
            logger.error(f"Consumer thread error: {e}")
            self._consuming = False

    def stop_consuming(self) -> None:
        """
        Stop consuming messages.
        """
        self._consuming = False
        
        if self._channel and self._channel.is_open:
            try:
                self._channel.stop_consuming()
            except Exception as e:
                logger.warning(f"Error stopping consumption: {e}")
        
        for thread in self._consumer_threads:
            thread.join(timeout=5)
        
        self._consumer_threads.clear()
        logger.info("Stopped consuming messages")

    def consume_all_queues(self) -> None:
        """
        Start consuming from all registered queues.
        """
        for queue_name, handler in self._handlers.items():
            self.consume(queue_name, handler)

    def close(self) -> None:
        """
        Close connection.
        """
        self.stop_consuming()
        
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and self._connection.is_open:
                self._connection.close()
            logger.info("Consumer connection closed")
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


class MultiThreadedConsumer:
    """
    Multi-threaded consumer for parallel message processing.

    Creates multiple consumer threads for high-throughput scenarios.
    """

    def __init__(self, num_threads: int = 4, **kwargs):
        """
        Initialize multi-threaded consumer.

        Args:
            num_threads: Number of consumer threads
            **kwargs: RabbitMQConsumer configuration
        """
        self.num_threads = num_threads
        self._consumer_config = kwargs
        self._consumers: List[RabbitMQConsumer] = []
        self._threads: List[threading.Thread] = []
        self._running = False

    def register_handler(self, queue_name: str, handler: Callable) -> None:
        """
        Register handler for all consumers.

        Args:
            queue_name: Queue to handle
            handler: Handler function
        """
        for consumer in self._consumers:
            consumer.register_handler(queue_name, handler)

    def start(self, queues: List[str] = None) -> None:
        """
        Start all consumer threads.

        Args:
            queues: List of queues to consume from
        """
        self._running = True
        
        for i in range(self.num_threads):
            consumer = RabbitMQConsumer(**self._consumer_config)
            consumer.register_default_handlers()
            
            thread = threading.Thread(
                target=self._run_consumer,
                args=(consumer, queues),
                name=f"consumer-{i}"
            )
            thread.daemon = True
            thread.start()
            
            self._consumers.append(consumer)
            self._threads.append(thread)
        
        logger.info(f"Started {self.num_threads} consumer threads")

    def _run_consumer(self, consumer: RabbitMQConsumer, 
                      queues: List[str] = None) -> None:
        """
        Run consumer in thread.

        Args:
            consumer: Consumer instance
            queues: Queues to consume from
        """
        try:
            consumer.connect()
            
            if queues:
                for queue in queues:
                    consumer.consume(queue)
            else:
                consumer.consume_all_queues()
            
            consumer.start_consuming(blocking=True)
        except Exception as e:
            logger.error(f"Consumer thread error: {e}")
        finally:
            consumer.close()

    def stop(self) -> None:
        """
        Stop all consumer threads.
        """
        self._running = False
        
        for consumer in self._consumers:
            consumer.stop_consuming()
        
        for thread in self._threads:
            thread.join(timeout=5)
        
        for consumer in self._consumers:
            consumer.close()
        
        self._consumers.clear()
        self._threads.clear()
        
        logger.info("Stopped all consumer threads")


def start_consumer(queues: List[str] = None, blocking: bool = True) -> RabbitMQConsumer:
    """
    Start a consumer with default handlers.

    Args:
        queues: List of queues to consume from
        blocking: Whether to block current thread

    Returns:
        RabbitMQConsumer instance
    """
    consumer = RabbitMQConsumer()
    consumer.connect()
    consumer.register_default_handlers()
    
    if queues:
        for queue in queues:
            consumer.consume(queue)
    else:
        consumer.consume_all_queues()
    
    consumer.start_consuming(blocking=blocking)
    
    return consumer


def event_handler(queue_name: str):
    """
    Decorator for registering event handlers.

    Args:
        queue_name: Queue to handle

    Returns:
        Decorator function

    Example:
        @event_handler(QueueNames.BOOKING_CONFIRMATIONS)
        def handle_booking(data):
            process_booking(data)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper._queue_name = queue_name
        return wrapper
    
    return decorator
