// Streaming chat client — the browser mirror of the backend's NDJSON contract.
//
// POST the message history to /chat, read the response body as a stream, split
// it on newlines, and JSON.parse each line into a typed StreamEvent. This is the
// client side of the same protocol you can see with `curl -N` against /chat.

import type { StreamEvent, WireMessage } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/**
 * Stream a chat turn. Yields each {type:'text'|'card'} event as it arrives, so
 * the caller can render tokens and cards live. Throws on a non-OK response or a
 * network error (the caller surfaces a friendly message).
 *
 * `signal` lets the caller abort an in-flight turn (e.g. user navigates away).
 */
export async function* streamChat(
  messages: WireMessage[],
  signal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new Error(`Chat request failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // NDJSON: complete lines end in "\n". Keep the trailing partial in `buffer`.
    let newlineIdx: number;
    while ((newlineIdx = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, newlineIdx).trim();
      buffer = buffer.slice(newlineIdx + 1);
      if (line) yield JSON.parse(line) as StreamEvent;
    }
  }

  // Flush any final line without a trailing newline.
  const tail = buffer.trim();
  if (tail) yield JSON.parse(tail) as StreamEvent;
}
