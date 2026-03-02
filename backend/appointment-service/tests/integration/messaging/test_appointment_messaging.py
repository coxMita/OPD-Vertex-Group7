"""Integration tests for appointment service messaging."""

import asyncio
from asyncio import AbstractEventLoop
from datetime import date, time
from typing import Generator

import pytest

from src.messaging.pubsub_exchanges import (
    APPOINTMENT_CREATED,
    APPOINTMENT_STATUS_CHANGED,
)
from src.messaging.pubsub_facade import PubSubFacade
from src.models.db.appointment import AppointmentStatus, TimePreference
from src.models.msg.appointment_message import AppointmentMessage
from tests.integration.messaging.utils.rabbitmq_container import (
    RabbitMqContainer,
    get_amqp_url,
)
from tests.integration.messaging.utils.rabbitmq_container import (
    rabbitmq_container as _rabbitmq_container,  # noqa: F401
)


@pytest.fixture(scope="module")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    """Create an event loop for the module scope."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _make_appointment_message() -> AppointmentMessage:
    """Create a test appointment message."""
    return AppointmentMessage(
        appointment_id=1,
        patient_id=1,
        doctor_id=1,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.AM,
        assigned_time=time(8, 0),
        status=AppointmentStatus.SCHEDULED,
    )


# ── APPOINTMENT_CREATED


@pytest.mark.asyncio
async def test_publish_appointment_created(
    _rabbitmq_container: RabbitMqContainer,  # noqa: PT019, F811
) -> None:
    """Should successfully publish to appointment.created exchange."""
    amqp_url = get_amqp_url(_rabbitmq_container)
    facade = PubSubFacade(amqp_url, APPOINTMENT_CREATED)
    await facade.connect()
    assert facade.is_connected

    message = _make_appointment_message()
    await facade.publish(message)
    await facade.close()


@pytest.mark.asyncio
async def test_subscribe_and_receive_appointment_created(
    _rabbitmq_container: RabbitMqContainer,  # noqa: PT019, F811
) -> None:
    """Should receive published appointment.created message."""
    amqp_url = get_amqp_url(_rabbitmq_container)

    received_messages: list[AppointmentMessage] = []
    message_received_event = asyncio.Event()

    async def on_message(msg: AppointmentMessage) -> None:
        received_messages.append(msg)
        message_received_event.set()

    subscriber = PubSubFacade(amqp_url, APPOINTMENT_CREATED)
    await subscriber.connect()
    subscriber.subscribe(
        queue_name="test.appointment.created",
        on_message=on_message,
        message_class=AppointmentMessage,
    )

    await asyncio.sleep(1)

    publisher = PubSubFacade(amqp_url, APPOINTMENT_CREATED)
    await publisher.connect()
    message = _make_appointment_message()
    await publisher.publish(message)
    await publisher.close()

    try:
        await asyncio.wait_for(message_received_event.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        pytest.fail("Did not receive appointment.created message within timeout.")

    assert len(received_messages) == 1
    assert received_messages[0].appointment_id == message.appointment_id
    assert received_messages[0].status == AppointmentStatus.SCHEDULED

    await subscriber.close()


# ── APPOINTMENT_STATUS_CHANGED


@pytest.mark.asyncio
async def test_subscribe_and_receive_appointment_status_changed(
    _rabbitmq_container: RabbitMqContainer,  # noqa: PT019, F811
) -> None:
    """Should receive published appointment.status_changed message."""
    amqp_url = get_amqp_url(_rabbitmq_container)

    received_messages: list[AppointmentMessage] = []
    message_received_event = asyncio.Event()

    async def on_message(msg: AppointmentMessage) -> None:
        received_messages.append(msg)
        message_received_event.set()

    subscriber = PubSubFacade(amqp_url, APPOINTMENT_STATUS_CHANGED)
    await subscriber.connect()
    subscriber.subscribe(
        queue_name="test.appointment.status_changed",
        on_message=on_message,
        message_class=AppointmentMessage,
    )

    await asyncio.sleep(1)

    publisher = PubSubFacade(amqp_url, APPOINTMENT_STATUS_CHANGED)
    await publisher.connect()
    message = AppointmentMessage(
        appointment_id=1,
        patient_id=1,
        doctor_id=1,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.AM,
        assigned_time=time(8, 0),
        status=AppointmentStatus.IN_PROGRESS,
    )
    await publisher.publish(message)
    await publisher.close()

    try:
        await asyncio.wait_for(message_received_event.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        pytest.fail(
            "Did not receive appointment.status_changed message within timeout."
        )

    assert len(received_messages) == 1
    assert received_messages[0].status == AppointmentStatus.IN_PROGRESS

    await subscriber.close()
