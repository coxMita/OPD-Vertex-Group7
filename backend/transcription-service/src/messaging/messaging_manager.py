import logging

from src.messaging.pubsub_facade import PubSubFacade

logger = logging.getLogger(__name__)


class MessagingManager:
    """Manager for handling multiple PubSub messaging facades."""

    def __init__(self) -> None:
        """Initialize the MessagingManager with an empty list of facades."""
        self._pubsubs: list[PubSubFacade] = []

    async def start_all(self) -> None:
        """Start all messaging facades by establishing their connections."""
        for facade in self._pubsubs:
            logger.info(
                "Connecting PubSubFacade for exchange '%s'", facade.exchange_name
            )
            await facade.connect()
        logger.info("All messaging facades started.")

    async def stop_all(self) -> None:
        """Stop all messaging facades by closing their connections."""
        for facade in self._pubsubs:
            logger.info("Closing PubSubFacade for exchange '%s'", facade.exchange_name)
            await facade.close()
        logger.info("All messaging facades stopped.")

    def add_pubsub(self, facade: PubSubFacade) -> None:
        """Add a PubSubFacade to the manager.

        Args:
            facade (PubSubFacade): The PubSubFacade instance to add.

        Raises:
            ValueError: If a PubSubFacade with the same exchange already exists.

        """
        if facade.exchange_name in [pubsub.exchange_name for pubsub in self._pubsubs]:
            raise ValueError(
                f"PubSubFacade with exchange '{facade.exchange_name}' already exists."
            )
        self._pubsubs.append(facade)

    def add_pubsubs(self, facades: list[PubSubFacade]) -> None:
        """Add multiple PubSubFacade instances to the manager.

        Args:
            facades (list[PubSubFacade]): The list of PubSubFacade instances to add.

        Raises:
            ValueError: If any PubSubFacade with the same exchange already exists.

        """
        for facade in facades:
            self.add_pubsub(facade)

    def get_pubsub(self, exchange: str) -> PubSubFacade:
        """Retrieve a PubSubFacade by exchange name.

        Args:
            exchange (str): The exchange name.

        Returns:
            PubSubFacade: The requested PubSubFacade instance.

        Raises:
            ValueError: If no PubSubFacade with the given exchange exists.

        """
        if exchange not in [pubsub.exchange_name for pubsub in self._pubsubs]:
            raise ValueError(f"No PubSubFacade found with exchange '{exchange}'.")
        return next(
            pubsub for pubsub in self._pubsubs if pubsub.exchange_name == exchange
        )


messaging_manager = MessagingManager()
