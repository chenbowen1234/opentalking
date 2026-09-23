import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { createServer } from "vite";

test("continuous voice pauses automatic capture while the avatar is speaking by default", async () => {
  const vite = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    server: { middlewareMode: true },
  });

  try {
    const module = await vite.ssrLoadModule("/src/config/voiceVad.ts");
    const config = module.getVoiceVadConfig() as { captureDuringPlayback?: boolean };

    assert.equal(config.captureDuringPlayback, false);
  } finally {
    await vite.close();
  }
});
