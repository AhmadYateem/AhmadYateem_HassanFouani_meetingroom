"""
RabbitMQ messaging module for event-driven architecture.
Provides publishers and consumers for asynchronous communication.
"""

from .publisher import RabbitMQPublisher, get_publisher
from .consumer import RabbitMQConsumer, start_consumer


__all__ = [
    'RabbitMQPublisher',
    'RabbitMQConsumer',
    'get_publisher',
    'start_consumer'
]
