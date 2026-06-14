"use client";

import { useEffect, useRef, useState } from "react";

import { streamChat } from "@/lib/api";
import type { Card, CardKind, ChatMessage, WireMessage } from "@/lib/types";

import Composer from "./Composer";
import EmptyState from "./EmptyState";
import Message from "./Message";

// Orchestrates the conversation: holds the message list, runs the streaming
// turn, and appends text deltas / card blocks to the in-flight assistant
// message as they arrive. The wire history we POST is just role+content text;
// cards are presentational and don't need to round-trip back to the model.

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Keep the latest turn in view as content streams in.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, streaming]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || streaming) return;
    setError(null);

    // Build the wire history (prior turns flattened to text) + the new user turn.
    const history: WireMessage[] = messages.map((m) => ({
      role: m.role,
      content: m.blocks.map((b) => (b.type === "text" ? b.text : "")).join(""),
    }));
    history.push({ role: "user", content: trimmed });

    // Optimistically render the user turn and an empty assistant turn.
    setMessages((prev) => [
      ...prev,
      { role: "user", blocks: [{ type: "text", text: trimmed }] },
      { role: "assistant", blocks: [{ type: "text", text: "" }] },
    ]);
    setStreaming(true);

    try {
      for await (const event of streamChat(history)) {
        if (event.type === "text") {
          appendText(event.delta);
        } else if (event.type === "card") {
          appendCard(event.kind, event.payload);
        }
      }
    } catch {
      setError("Sorry — something went wrong reaching the assistant. Please try again.");
      // Drop the empty assistant turn we optimistically added.
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        const empty =
          last?.role === "assistant" && last.blocks.every((b) => b.type !== "card" && !("text" in b && b.text));
        return empty ? prev.slice(0, -1) : prev;
      });
    } finally {
      setStreaming(false);
    }
  }

  // Append a text delta to the assistant's trailing text block, opening a new
  // one if the last block was a card (so text after a card renders separately).
  function appendText(delta: string) {
    setMessages((prev) => {
      const next = [...prev];
      const msg = { ...next[next.length - 1] };
      const blocks = [...msg.blocks];
      const last = blocks[blocks.length - 1];
      if (last?.type === "text") {
        blocks[blocks.length - 1] = { type: "text", text: last.text + delta };
      } else {
        blocks.push({ type: "text", text: delta });
      }
      msg.blocks = blocks;
      next[next.length - 1] = msg;
      return next;
    });
  }

  function appendCard(kind: CardKind, payload: unknown) {
    const card = { kind, payload } as Card;
    setMessages((prev) => {
      const next = [...prev];
      const msg = { ...next[next.length - 1] };
      msg.blocks = [...msg.blocks, { type: "card", card }];
      next[next.length - 1] = msg;
      return next;
    });
  }

  const empty = messages.length === 0;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div ref={scrollRef} className="ps-scroll min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6">
          {empty ? (
            <EmptyState onPick={send} />
          ) : (
            <div className="space-y-6">
              {messages.map((m, i) => (
                <Message
                  key={i}
                  message={m}
                  streaming={streaming && i === messages.length - 1 && m.role === "assistant"}
                />
              ))}
              {error && (
                <div className="rounded-card border border-nostock/30 bg-nostock/5 px-4 py-3 text-sm text-nostock">
                  {error}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <Composer onSend={send} disabled={streaming} />
    </div>
  );
}
