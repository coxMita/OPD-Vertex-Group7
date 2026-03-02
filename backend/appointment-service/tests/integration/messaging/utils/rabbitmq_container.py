from typing import Generator

import pytest
from pydantic import Field
from testcontainers.rabbitmq import RabbitMqContainer

from src.models.msg.abstract_message import AbstractMessage

EXCHANGE_NAME = "test_exchange"
ROUTING_KEY = "test_routing_key"
QUEUE_NAME = "test_queue"


@pytest.fixture(scope="module")
def rabbitmq_container() -> Generator[RabbitMqContainer]:
    """Set up a RabbitMQ container for integration testing."""
    with RabbitMqContainer("rabbitmq:4.1.4-management-alpine") as rabbit:
        yield rabbit


def get_amqp_url(rabbitmq_container: RabbitMqContainer) -> str:
    """Construct the AMQP URL from the RabbitMQ container connection parameters."""
    connection_params = rabbitmq_container.get_connection_params()
    amqp_url = (
        f"amqp://{connection_params.credentials.username}:{connection_params.credentials.password}@"
        f"{connection_params.host}:{connection_params.port}{connection_params.virtual_host}"
    )
    return amqp_url


class DummyMessage(AbstractMessage):
    """A dummy message class for testing purposes."""

    content: str = Field(...)

    def to_bytes(self) -> bytes:
        """Serialize the message to bytes."""
        return self.content.encode()

    @classmethod
    def from_bytes(cls, body: bytes) -> "DummyMessage":
        """Deserialize bytes to an instance of DummyMessage."""
        return cls(content=body.decode())
