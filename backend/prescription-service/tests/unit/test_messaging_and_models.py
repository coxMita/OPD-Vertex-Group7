"""Unit tests for messaging layer — subscriber, models, abstract message."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_facade import PubSubFacade
from src.messaging.subscriber import on_ai_completed_message
from src.models.db.prescription import PrescriptionStatus
from src.models.msg.abstract_message import AbstractMessage
from src.models.msg.ai_completed_message import AICompletedMessage

# ── AbstractMessage ───────────────────────────────────────────────────────────


class _ConcreteMsg(AbstractMessage):
    """Minimal concrete subclass for testing."""

    text: str


class TestAbstractMessage:
    """Unit tests for AbstractMessage serialisation."""

    def test_to_bytes_produces_valid_json(self) -> None:
        """to_bytes() should return UTF-8-encoded JSON."""
        msg = _ConcreteMsg(text="hello")
        data = json.loads(msg.to_bytes())
        assert data["text"] == "hello"

    def test_from_bytes_reconstructs_message(self) -> None:
        """from_bytes() should deserialise back to original."""
        msg = _ConcreteMsg(text="world")
        restored = _ConcreteMsg.from_bytes(msg.to_bytes())
        assert restored.text == "world"

    def test_roundtrip_preserves_all_fields(self) -> None:
        """Serialise → deserialise should be lossless."""
        msg = _ConcreteMsg(text="roundtrip")
        assert _ConcreteMsg.from_bytes(msg.to_bytes()) == msg

    def test_str_contains_class_name(self) -> None:
        """__str__ should include the class name."""
        assert "_ConcreteMsg" in str(_ConcreteMsg(text="x"))

    def test_str_contains_field_value(self) -> None:
        """__str__ should include field values."""
        assert "visible" in str(_ConcreteMsg(text="visible"))


# ── AICompletedMessage ────────────────────────────────────────────────────────


class TestAICompletedMessage:
    """Unit tests for AICompletedMessage."""

    def _make(self) -> AICompletedMessage:
        return AICompletedMessage(
            filename="audio.wav",
            summary="Patient has fever.",
            prescription={"medication_name": "Paracetamol"},
            processed_at=datetime(2026, 4, 4, 12, 0, 0, tzinfo=timezone.utc),
            consultation_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        )

    def test_serialises_to_bytes(self) -> None:
        """Should serialise without error."""
        msg = self._make()
        assert isinstance(msg.to_bytes(), bytes)

    def test_roundtrip_preserves_consultation_id(self) -> None:
        """consultation_id must survive serialise → deserialise."""
        msg = self._make()
        restored = AICompletedMessage.from_bytes(msg.to_bytes())
        assert restored.consultation_id == msg.consultation_id

    def test_roundtrip_preserves_prescription_dict(self) -> None:
        """Prescription dict must survive serialise → deserialise."""
        msg = self._make()
        restored = AICompletedMessage.from_bytes(msg.to_bytes())
        assert restored.prescription == msg.prescription

    def test_roundtrip_preserves_summary(self) -> None:
        """Summary must survive serialise → deserialise."""
        msg = self._make()
        restored = AICompletedMessage.from_bytes(msg.to_bytes())
        assert restored.summary == msg.summary

    def test_prescription_accepts_null_fields(self) -> None:
        """Prescription dict should accept None values."""
        msg = AICompletedMessage(
            filename="f.wav",
            summary="None prescribed.",
            prescription={"medication_name": None, "notes": "No prescription."},
            processed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            consultation_id=uuid.uuid4(),
        )
        assert msg.prescription["medication_name"] is None


# ── MessagingManager ──────────────────────────────────────────────────────────


def _make_facade(exchange: str) -> MagicMock:
    facade = MagicMock(spec=PubSubFacade)
    facade.exchange_name = exchange
    facade.connect = AsyncMock()
    facade.close = AsyncMock()
    return facade


class TestMessagingManager:
    """Unit tests for MessagingManager."""

    def test_add_pubsub_stores_facade(self) -> None:
        """add_pubsub() should allow retrieval afterwards."""
        mgr = MessagingManager()
        facade = _make_facade("test.exchange")
        mgr.add_pubsub(facade)
        assert mgr.get_pubsub("test.exchange") is facade

    def test_add_duplicate_raises_value_error(self) -> None:
        """Adding same exchange twice should raise ValueError."""
        mgr = MessagingManager()
        mgr.add_pubsub(_make_facade("dup.exchange"))
        with pytest.raises(ValueError, match="already exists"):
            mgr.add_pubsub(_make_facade("dup.exchange"))

    def test_get_unknown_exchange_raises_value_error(self) -> None:
        """Getting unregistered exchange should raise ValueError."""
        mgr = MessagingManager()
        with pytest.raises(ValueError, match="No PubSubFacade found"):
            mgr.get_pubsub("ghost.exchange")

    def test_add_pubsubs_registers_all(self) -> None:
        """add_pubsubs() should register every facade in the list."""
        mgr = MessagingManager()
        f1 = _make_facade("ex.one")
        f2 = _make_facade("ex.two")
        mgr.add_pubsubs([f1, f2])
        assert mgr.get_pubsub("ex.one") is f1
        assert mgr.get_pubsub("ex.two") is f2

    def test_get_correct_facade_among_multiple(self) -> None:
        """Should return the correct facade when several are registered."""
        mgr = MessagingManager()
        f1 = _make_facade("alpha")
        f2 = _make_facade("beta")
        mgr.add_pubsubs([f1, f2])
        assert mgr.get_pubsub("beta") is f2

    @pytest.mark.asyncio
    async def test_start_all_connects_all_facades(self) -> None:
        """start_all() should call connect() on every facade."""
        mgr = MessagingManager()
        f1 = _make_facade("e1")
        f2 = _make_facade("e2")
        mgr.add_pubsubs([f1, f2])
        await mgr.start_all()
        f1.connect.assert_awaited_once()
        f2.connect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_all_closes_all_facades(self) -> None:
        """stop_all() should call close() on every facade."""
        mgr = MessagingManager()
        f1 = _make_facade("e1")
        f2 = _make_facade("e2")
        mgr.add_pubsubs([f1, f2])
        await mgr.stop_all()
        f1.close.assert_awaited_once()
        f2.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_all_empty_does_not_raise(self) -> None:
        """start_all() on empty manager should complete without error."""
        await MessagingManager().start_all()

    @pytest.mark.asyncio
    async def test_stop_all_empty_does_not_raise(self) -> None:
        """stop_all() on empty manager should complete without error."""
        await MessagingManager().stop_all()


# ── PubSubFacade unit tests ───────────────────────────────────────────────────


class TestPubSubFacadeUnit:
    """Unit tests for PubSubFacade (without real AMQP)."""

    def test_exchange_name_property(self) -> None:
        """exchange_name should return the value passed to __init__."""
        facade = PubSubFacade("amqp://localhost", "my.exchange")
        assert facade.exchange_name == "my.exchange"

    def test_is_connected_false_before_connect(self) -> None:
        """is_connected should be False before connect() is called."""
        facade = PubSubFacade("amqp://localhost", "test.exchange")
        assert facade.is_connected is False

    @pytest.mark.asyncio
    async def test_publish_raises_without_connect(self) -> None:
        """publish() should raise RuntimeError if not connected."""
        facade = PubSubFacade("amqp://localhost", "test.exchange")
        msg = AICompletedMessage(
            filename="f.wav",
            summary="s",
            prescription={},
            processed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            consultation_id=uuid.uuid4(),
        )
        with pytest.raises(RuntimeError, match="connect"):
            await facade.publish(msg)

    def test_subscribe_raises_without_connect(self) -> None:
        """subscribe() should raise RuntimeError if not connected."""
        facade = PubSubFacade("amqp://localhost", "test.exchange")
        with pytest.raises(RuntimeError, match="connect"):
            facade.subscribe("queue", AsyncMock(), AICompletedMessage)


# ── Subscriber ────────────────────────────────────────────────────────────────


class TestSubscriber:
    """Unit tests for on_ai_completed_message subscriber."""

    def _make_payload(
        self,
        consultation_id: uuid.UUID | None = None,
        summary: str = "Clinical summary.",
        prescription: dict | None = None,
        filename: str = "audio.wav",
    ) -> AICompletedMessage:
        return AICompletedMessage(
            filename=filename,
            summary=summary,
            prescription=prescription or {"medication_name": "Paracetamol"},
            processed_at=datetime(2026, 4, 4, tzinfo=timezone.utc),
            consultation_id=consultation_id or uuid.uuid4(),
        )

    @pytest.mark.asyncio
    async def test_happy_path_saves_prescription(self) -> None:
        """Valid message should create a prescription in the DB."""
        msg = self._make_payload()
        mock_repo = MagicMock()
        mock_repo.get_by_consultation_id.return_value = None

        def fake_thread(fn: object) -> None:
            fn()

        with (
            patch(
                "src.messaging.subscriber.asyncio.to_thread", side_effect=fake_thread
            ),
            patch(
                "src.messaging.subscriber.PrescriptionRepository",
                return_value=mock_repo,
            ),
            patch("src.messaging.subscriber.engine"),
        ):
            await on_ai_completed_message(msg)

        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_idempotency_skips_existing_prescription(self) -> None:
        """If prescription already exists for consultation, should not create again."""
        msg = self._make_payload()
        existing = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_by_consultation_id.return_value = existing

        def fake_thread(fn: object) -> None:
            fn()

        with (
            patch(
                "src.messaging.subscriber.asyncio.to_thread", side_effect=fake_thread
            ),
            patch(
                "src.messaging.subscriber.PrescriptionRepository",
                return_value=mock_repo,
            ),
            patch("src.messaging.subscriber.engine"),
        ):
            await on_ai_completed_message(msg)

        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_exception_in_save_does_not_propagate(self) -> None:
        """DB failure should be caught and logged, not re-raised."""
        msg = self._make_payload()

        async def raising_thread(fn: object) -> None:
            raise RuntimeError("DB connection lost")

        with patch(
            "src.messaging.subscriber.asyncio.to_thread", side_effect=raising_thread
        ):
            # Should not raise
            await on_ai_completed_message(msg)

    @pytest.mark.asyncio
    async def test_saved_prescription_has_correct_consultation_id(self) -> None:
        """Saved prescription must carry the consultation_id from the message."""
        consultation_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        msg = self._make_payload(consultation_id=consultation_id)
        mock_repo = MagicMock()
        mock_repo.get_by_consultation_id.return_value = None

        def fake_thread(fn: object) -> None:
            fn()

        with (
            patch(
                "src.messaging.subscriber.asyncio.to_thread", side_effect=fake_thread
            ),
            patch(
                "src.messaging.subscriber.PrescriptionRepository",
                return_value=mock_repo,
            ),
            patch("src.messaging.subscriber.engine"),
        ):
            await on_ai_completed_message(msg)

        created: object = mock_repo.create.call_args[0][0]
        assert created.consultation_id == consultation_id

    @pytest.mark.asyncio
    async def test_saved_prescription_has_draft_status(self) -> None:
        """Saved prescription must be in DRAFT status."""
        msg = self._make_payload()
        mock_repo = MagicMock()
        mock_repo.get_by_consultation_id.return_value = None

        def fake_thread(fn: object) -> None:
            fn()

        with (
            patch(
                "src.messaging.subscriber.asyncio.to_thread", side_effect=fake_thread
            ),
            patch(
                "src.messaging.subscriber.PrescriptionRepository",
                return_value=mock_repo,
            ),
            patch("src.messaging.subscriber.engine"),
        ):
            await on_ai_completed_message(msg)

        created: object = mock_repo.create.call_args[0][0]
        assert created.status == PrescriptionStatus.DRAFT

    @pytest.mark.asyncio
    async def test_saved_prescription_stores_summary_json(self) -> None:
        """Saved prescription must wrap summary in summary_json dict."""
        summary = "Patient has chest pain."
        msg = self._make_payload(summary=summary)
        mock_repo = MagicMock()
        mock_repo.get_by_consultation_id.return_value = None

        def fake_thread(fn: object) -> None:
            fn()

        with (
            patch(
                "src.messaging.subscriber.asyncio.to_thread", side_effect=fake_thread
            ),
            patch(
                "src.messaging.subscriber.PrescriptionRepository",
                return_value=mock_repo,
            ),
            patch("src.messaging.subscriber.engine"),
        ):
            await on_ai_completed_message(msg)

        created: object = mock_repo.create.call_args[0][0]
        assert created.summary_json == {"summary": summary}
