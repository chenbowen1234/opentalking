from __future__ import annotations

import asyncio
import json
import queue
from types import SimpleNamespace

import apps.api.routes.sessions as sessions_routes
from opentalking.core.in_memory_redis import InMemoryRedis


class DisconnectingWebSocket:
    def __init__(self) -> None:
        self.app = SimpleNamespace(state=SimpleNamespace(redis=InMemoryRedis()))
        self._messages = [
            {
                "type": "websocket.receive",
                "text": json.dumps({"type": "meta", "tts_provider": "edge"}),
            },
            {"type": "websocket.disconnect", "code": 1000},
        ]
        self.sent: list[dict[str, str]] = []

    async def accept(self) -> None:
        return None

    async def receive(self) -> dict[str, object]:
        if not self._messages:
            raise RuntimeError('Cannot call "receive" once a disconnect message has been received.')
        return self._messages.pop(0)

    async def send_json(self, payload: dict[str, str]) -> None:
        self.sent.append(payload)

    async def close(self, code: int = 1000) -> None:
        del code


def test_speak_audio_stream_stops_receiving_after_disconnect(monkeypatch) -> None:
    async def fake_get_session(_redis: InMemoryRedis, _session_id: str) -> dict[str, str]:
        return {"id": "sess_test"}

    def fake_transcribe(
        chunk_queue: "queue.Queue[bytes | None]",
        *,
        provider: str | None = None,
    ) -> tuple[str, float]:
        del provider
        while chunk_queue.get() is not None:
            pass
        return "", 0.0

    monkeypatch.setattr(sessions_routes.session_service, "get_session", fake_get_session)
    monkeypatch.setattr(sessions_routes, "transcribe_pcm_chunk_queue_sync", fake_transcribe)
    websocket = DisconnectingWebSocket()

    asyncio.run(sessions_routes.speak_audio_stream_ws(websocket, "sess_test"))

    assert websocket._messages == []
