"""PCM preprocessing shared by local batch speech recognizers."""

from __future__ import annotations

import numpy as np


def trim_outer_silence(
    pcm_bytes: bytes,
    *,
    sample_rate: int,
    frame_ms: int = 20,
    silence_rms: float = 180.0,
    leading_context_ms: int = 160,
    trailing_context_ms: int = 200,
) -> bytes:
    """Trim transport/VAD silence while retaining phoneme context for batch STT."""
    if not pcm_bytes or len(pcm_bytes) % 2:
        return pcm_bytes

    pcm = np.frombuffer(pcm_bytes, dtype="<i2")
    frame_samples = max(1, sample_rate * frame_ms // 1000)
    active_frames: list[int] = []
    for frame_index, start in enumerate(range(0, pcm.size, frame_samples)):
        frame = pcm[start : start + frame_samples].astype(np.float32)
        if frame.size and float(np.sqrt(np.mean(frame * frame))) >= silence_rms:
            active_frames.append(frame_index)
    if not active_frames:
        return pcm_bytes

    first_sample = active_frames[0] * frame_samples
    last_sample = min(pcm.size, (active_frames[-1] + 1) * frame_samples)
    keep_start = max(0, first_sample - sample_rate * leading_context_ms // 1000)
    keep_end = min(pcm.size, last_sample + sample_rate * trailing_context_ms // 1000)
    return pcm[keep_start:keep_end].tobytes()
