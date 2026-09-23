from __future__ import annotations

import pytest

from opentalking.providers.tts.edge import adapter


@pytest.mark.asyncio
async def test_edge_audio_stream_survives_four_transient_connection_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    class FakeCommunicate:
        async def stream(self):
            nonlocal attempts
            attempts += 1
            if attempts < 5:
                raise ConnectionResetError("temporary network reset")
            yield {"type": "audio", "data": b"audio"}

    monkeypatch.setattr(adapter.edge_tts, "Communicate", lambda *_args: FakeCommunicate())

    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(adapter.asyncio, "sleep", no_sleep)

    audio = []
    try:
        async for chunk in adapter._edge_audio_stream("你好", "zh-CN-XiaoxiaoNeural"):
            audio.append(chunk)
    except ConnectionResetError:
        pass

    assert attempts == 5
    assert audio == [b"audio"]
