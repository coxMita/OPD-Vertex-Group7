"""Root conftest - sets AMQP_URL so main.py does not raise on import."""

import os
import sys
import types

os.environ.setdefault("AMQP_URL", "amqp://guest:guest@localhost/")

if "faster_whisper" not in sys.modules:
    fake_faster_whisper = types.ModuleType("faster_whisper")

    class DummyWhisperModel:
        """Test stub for faster_whisper.WhisperModel."""

    fake_faster_whisper.WhisperModel = DummyWhisperModel
    sys.modules["faster_whisper"] = fake_faster_whisper
