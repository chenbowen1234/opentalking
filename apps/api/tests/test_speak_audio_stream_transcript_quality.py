from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import apps.api.routes.sessions as sessions_routes
from opentalking.core.in_memory_redis import InMemoryRedis


class FinishedAudioWebSocket:
    def __init__(self) -> None:
        self.app = SimpleNamespace(state=SimpleNamespace(redis=InMemoryRedis()))
        self._messages = [
            {
                "type": "websocket.receive",
                "text": json.dumps({"type": "meta", "tts_provider": "edge"}),
            },
            {"type": "websocket.receive", "bytes": b"\x00\x00" * 1600},
            {"type": "websocket.receive", "text": json.dumps({"type": "end"})},
        ]
        self.sent: list[dict[str, str]] = []

    async def accept(self) -> None:
        return None

    async def receive(self) -> dict[str, object]:
        return self._messages.pop(0)

    async def send_json(self, payload: dict[str, str]) -> None:
        self.sent.append(payload)

    async def close(self, code: int = 1000) -> None:
        del code


def test_speak_audio_stream_rejects_punctuation_only_transcript(monkeypatch) -> None:
    queued: list[str] = []

    async def fake_get_session(_redis: InMemoryRedis, _session_id: str) -> dict[str, str]:
        return {"id": "sess_test"}

    def fake_transcribe(*_args, **_kwargs) -> tuple[str, float]:
        return ".。！？", 1.0

    async def fake_speak(_redis, _session_id: str, text: str, **_kwargs) -> None:
        queued.append(text)

    monkeypatch.setattr(sessions_routes.session_service, "get_session", fake_get_session)
    monkeypatch.setattr(sessions_routes.session_service, "speak", fake_speak)
    monkeypatch.setattr(sessions_routes, "transcribe_pcm_chunk_queue_sync", fake_transcribe)
    websocket = FinishedAudioWebSocket()

    asyncio.run(sessions_routes.speak_audio_stream_ws(websocket, "sess_test"))

    assert queued == []
    assert websocket.sent == [{"error": "未能识别有效语音，请重试。"}]
