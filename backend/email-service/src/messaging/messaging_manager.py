"""Messaging manager for email-service (durable work queue consumer)."""

import logging

import aio_pika

from src.messaging.email_queue_facade import EmailQueueFacade

logger = logging.getLogger(__name__)


class MessagingManager:
    """Manages one or more email queue facades (typically a single inbound queue)."""

    def __init__(self) -> None:
        """Initialise with empty facade list and no active connection."""
        self._queues: list[EmailQueueFacade] = []
        self._connection: aio_pika.RobustConnection | None = None

    async def start_all(self) -> None:
        """Start each registered queue facade and retain the broker connection."""
        for facade in self._queues:
            logger.info("Connecting EmailQueueFacade for queue '%s'", facade.queue_name)
            self._connection = await facade.connect_and_consume()
        logger.info("All messaging facades started.")

    async def stop_all(self) -> None:
        """Close all queue facades, clear connection, and drop registrations."""
        for facade in list(self._queues):
            logger.info("Closing EmailQueueFacade for queue '%s'", facade.queue_name)
            await facade.close()
        self._connection = None
        self._queues.clear()
        logger.info("All messaging facades stopped.")

    def add_email_queue(self, facade: EmailQueueFacade) -> None:
        """Register an EmailQueueFacade.

        Raises:
            ValueError: If a facade for the same queue name already exists.

        """
        if facade.queue_name in [q.queue_name for q in self._queues]:
            raise ValueError(
                f"EmailQueueFacade for queue '{facade.queue_name}' already exists."
            )
        self._queues.append(facade)

    def add_email_queues(self, facades: list[EmailQueueFacade]) -> None:
        """Register multiple EmailQueueFacade instances."""
        for facade in facades:
            self.add_email_queue(facade)

    def get_email_queue(self, queue_name: str) -> EmailQueueFacade:
        """Return a registered facade by queue name."""
        if queue_name not in [q.queue_name for q in self._queues]:
            raise ValueError(f"No EmailQueueFacade found for queue '{queue_name}'.")
        return next(q for q in self._queues if q.queue_name == queue_name)

    @property
    def rabbitmq_connection(self) -> aio_pika.RobustConnection:
        """Broker connection after ``start_all`` (used by HTTP publish helper)."""
        if self._connection is None or self._connection.is_closed:
            msg = "RabbitMQ is not connected; call start_all() first."
            raise RuntimeError(msg)
        return self._connection


messaging_manager = MessagingManager()
