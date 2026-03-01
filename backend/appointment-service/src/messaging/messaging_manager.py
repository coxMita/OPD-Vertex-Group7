import logging

from .direct_message_facade import DirectMessageFacade
from .pubsub_facade import PubSubFacade

logger = logging.getLogger(__name__)


class MessagingManager:
    """Manager for handling multiple messaging facades (PubSub and DirectMessage)."""

    def __init__(self) -> None:
        """Initialize the MessagingManager with empty lists for facades."""
        self._pubsubs: list[PubSubFacade] = []
        self._directs: list[DirectMessageFacade] = []

    async def start_all(self) -> None:
        """Start all messaging facades by establishing their connections."""
        for facade in self._pubsubs:
            logger.info(
                "Connecting PubSubFacade for exchange '%s'", facade.exchange_name
            )
            await facade.connect()
        for facade in self._directs:
            logger.info(
                "Connecting DirectMessageFacade for exchange '%s'", facade.exchange_name
            )
            await facade.connect()
        logger.info("All messaging facades started.")

    async def stop_all(self) -> None:
        """Stop all messaging facades by closing their connections."""
        for facade in self._pubsubs:
            logger.info("Closing PubSubFacade for exchange '%s'", facade.exchange_name)
            await facade.close()
        for facade in self._directs:
            logger.info(
                "Closing DirectMessageFacade for exchange '%s'", facade.exchange_name
            )
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

    def add_direct(self, facade: DirectMessageFacade) -> None:
        """Add a DirectMessageFacade to the manager.

        Args:
            facade (DirectMessageFacade): The DirectMessageFacade instance to add.

        Raises:
            ValueError: If a DirectMessageFacade with the same exchange already exists.

        """
        if facade.exchange_name in [direct.exchange_name for direct in self._directs]:
            raise ValueError(
                f"DirectMessageFacade with exchange '{facade.exchange_name}' already exists."  # noqa: E501
            )
        self._directs.append(facade)

    def add_directs(self, facades: list[DirectMessageFacade]) -> None:
        """Add multiple DirectMessageFacade instances to the manager.

        Args:
            facades (list[DirectMessageFacade]): The list of DirectMessageFacade instances to add.

        Raises:
            ValueError: If any DirectMessageFacade with the same exchange already exists.

        """  # noqa: E501
        for facade in facades:
            self.add_direct(facade)

    def get_pubsub(self, exchange: str) -> PubSubFacade:
        """Retrieve a PubSubFacade by the name of the exchange.

        Args:
            exchange (str): The exchange of the PubSubFacade.

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

    def get_direct(self, exchange: str) -> DirectMessageFacade:
        """Retrieve a DirectMessageFacade by its name.

        Args:
            exchange (str): The exchange of the DirectMessageFacade.

        Returns:
            DirectMessageFacade: The requested DirectMessageFacade instance.

        Raises:
            ValueError: If no DirectMessageFacade with the given exchange exists.

        """
        if exchange not in [direct.exchange_name for direct in self._directs]:
            raise ValueError(
                f"No DirectMessageFacade found with exchange '{exchange}'."
            )
        return next(
            direct for direct in self._directs if direct.exchange_name == exchange
        )


messaging_manager = MessagingManager()
