import asyncio
from asyncio import AbstractEventLoop
from typing import Any, Awaitable, Callable, Generator

import pytest

from src.messaging.pubsub_facade import MessageType, PubSubFacade
from tests.integration.messaging.utils.rabbitmq_container import (
    EXCHANGE_NAME,
    QUEUE_NAME,
    DummyMessage,
    RabbitMqContainer,
    get_amqp_url,
)
from tests.integration.messaging.utils.rabbitmq_container import (
    rabbitmq_container as _rabbitmq_container,  # noqa: F401
)


@pytest.fixture(scope="module")
def event_loop() -> Generator[AbstractEventLoop]:
    """Create an instance of the event loop for the module scope."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_is_connected_property(
    _rabbitmq_container: RabbitMqContainer,  # noqa: F811, PT019
) -> None:
    """Integration test for the is_connected property of PubSubFacade."""
    amqp_url = get_amqp_url(_rabbitmq_container)
    facade = PubSubFacade(amqp_url, EXCHANGE_NAME)

    assert not facade.is_connected
    await facade.connect()
    assert facade.is_connected


@pytest.mark.asyncio
async def test_subscribe_without_connect_raises(
    _rabbitmq_container: RabbitMqContainer,  # noqa: F811, PT019
) -> None:
    """Integration test to ensure subscribing without connecting raises an error."""
    amqp_url = get_amqp_url(_rabbitmq_container)
    facade = PubSubFacade(amqp_url, EXCHANGE_NAME)

    async def dummy_callback(_: DummyMessage) -> None:
        pass

    with pytest.raises(RuntimeError):
        facade.subscribe(QUEUE_NAME, dummy_callback, DummyMessage)


@pytest.mark.asyncio
async def test_integration_publish_and_subscribe(
    _rabbitmq_container: RabbitMqContainer,  # noqa:  F811, PT019
) -> None:
    """Integration test for publishing a message using PubSubFacade."""
    received_messages = []
    message_received_event = asyncio.Event()

    async def on_message(message: DummyMessage) -> None:
        received_messages.append(message)
        message_received_event.set()

    subscriber_facade = await _subscribe_to_exchange(_rabbitmq_container, on_message)

    await _publish_message(_rabbitmq_container)

    try:
        await asyncio.wait_for(message_received_event.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        pytest.fail("Did not receive message within timeout period.")

    assert len(received_messages) == 1
    assert received_messages[0].content == "test"

    await subscriber_facade.close()


async def _publish_message(
    _rabbitmq_container: RabbitMqContainer,  # noqa: F811
) -> None:
    """Send and receive a message using DirectMessageFacade."""
    amqp_url = get_amqp_url(_rabbitmq_container)
    facade = PubSubFacade(amqp_url, EXCHANGE_NAME)
    await facade.connect()
    await facade.publish(DummyMessage(content="test"))
    await asyncio.sleep(1)
    await facade.close()


async def _subscribe_to_exchange(
    _rabbitmq_container: RabbitMqContainer,  # noqa: F811
    on_message_callback: Callable[[MessageType], Awaitable[Any]],
) -> PubSubFacade:
    """Subscribe to a fanout exchange and set up a message handler."""
    amqp_url = get_amqp_url(_rabbitmq_container)
    facade = PubSubFacade(amqp_url, EXCHANGE_NAME)
    await facade.connect()
    facade.subscribe(QUEUE_NAME, on_message_callback, DummyMessage)
    return facade
