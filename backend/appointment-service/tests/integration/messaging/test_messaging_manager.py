import pytest
from testcontainers.rabbitmq import RabbitMqContainer

from src.messaging.direct_message_facade import DirectMessageFacade
from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_facade import PubSubFacade
from tests.integration.messaging.utils.rabbitmq_container import (
    get_amqp_url,
)
from tests.integration.messaging.utils.rabbitmq_container import (
    rabbitmq_container as _rabbitmq_container,  # noqa: F401
)


def _get_list_of_pubsub_facades(amqp_url: str) -> list[PubSubFacade]:
    """Return list of PubSubFacade instances for testing."""
    return [
        PubSubFacade(amqp_url, "exchange_1"),
        PubSubFacade(amqp_url, "exchange_2"),
    ]


def _get_list_of_direct_facades(amqp_url: str) -> list[DirectMessageFacade]:
    """Return list of DirectMessageFacade instances for testing."""
    return [
        DirectMessageFacade(amqp_url, "direct_exchange_1"),
        DirectMessageFacade(amqp_url, "direct_exchange_2"),
    ]


@pytest.mark.asyncio
async def test_start_all(
    _rabbitmq_container: RabbitMqContainer,  # noqa: F811, PT019
) -> None:
    """Integration test for starting all messaging components."""
    messaging_manager = MessagingManager()
    pubsub_facades = _get_list_of_pubsub_facades(get_amqp_url(_rabbitmq_container))
    messaging_manager.add_pubsubs(pubsub_facades)
    direct_facades = _get_list_of_direct_facades(get_amqp_url(_rabbitmq_container))
    messaging_manager.add_directs(direct_facades)
    await messaging_manager.start_all()
    for pubsub in pubsub_facades:
        assert pubsub.is_connected
    for direct in direct_facades:
        assert direct.is_connected


@pytest.mark.asyncio
async def test_stop_all(
    _rabbitmq_container: RabbitMqContainer,  # noqa: F811, PT019
) -> None:
    """Integration test for stopping all messaging components."""
    messaging_manager = MessagingManager()
    pubsub_facades = _get_list_of_pubsub_facades(get_amqp_url(_rabbitmq_container))
    messaging_manager.add_pubsubs(pubsub_facades)
    direct_facades = _get_list_of_direct_facades(get_amqp_url(_rabbitmq_container))
    messaging_manager.add_directs(direct_facades)
    await messaging_manager.start_all()
    await messaging_manager.stop_all()
    for pubsub in pubsub_facades:
        assert not pubsub.is_connected
    for direct in direct_facades:
        assert not direct.is_connected
