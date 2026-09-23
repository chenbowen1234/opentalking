import assert from "node:assert/strict";
import test from "node:test";

import { connectSse } from "../src/lib/sse";

class FakeEventSource {
  static last: FakeEventSource | null = null;
  listeners = new Map<string, Array<(event: unknown) => void>>();
  onmessage: ((event: unknown) => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(_url: string) {
    FakeEventSource.last = this;
  }

  addEventListener(name: string, listener: (event: unknown) => void) {
    const listeners = this.listeners.get(name) ?? [];
    listeners.push(listener);
    this.listeners.set(name, listeners);
  }

  emit(name: string, event: unknown) {
    for (const listener of this.listeners.get(name) ?? []) listener(event);
  }

  close() {}
}

test("SSE transport errors do not become application error messages", () => {
  const original = globalThis.EventSource;
  globalThis.EventSource = FakeEventSource as unknown as typeof EventSource;
  const received: Array<[string, unknown]> = [];

  try {
    const stop = connectSse("http://local.test/events", (event, data) => {
      received.push([event, data]);
    });
    FakeEventSource.last?.emit("error", { type: "error" });
    stop();
  } finally {
    globalThis.EventSource = original;
  }

  assert.deepEqual(received, []);
});

test("SSE application error events still reach the application", () => {
  const original = globalThis.EventSource;
  globalThis.EventSource = FakeEventSource as unknown as typeof EventSource;
  const received: Array<[string, unknown]> = [];

  try {
    const stop = connectSse("http://local.test/events", (event, data) => {
      received.push([event, data]);
    });
    FakeEventSource.last?.emit("error", {
      type: "error",
      data: JSON.stringify({ message: "real pipeline failure" }),
    });
    stop();
  } finally {
    globalThis.EventSource = original;
  }

  assert.deepEqual(received, [["error", { message: "real pipeline failure" }]]);
});
