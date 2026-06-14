"use client";

import ReactMarkdown from "react-markdown";

import type { ChatMessage } from "@/lib/types";

import CardRenderer from "./cards/CardRenderer";

// A single chat turn. User turns are compact teal bubbles on the right.
// Assistant turns are open (no bubble chrome) on the left and render their
// interleaved blocks in order — markdown text now, cards added next step.
// `streaming` shows a blinking caret on the assistant's trailing text.

export default function Message({
  message,
  streaming = false,
}: {
  message: ChatMessage;
  streaming?: boolean;
}) {
  if (message.role === "user") {
    const text = message.blocks.map((b) => (b.type === "text" ? b.text : "")).join("");
    return (
      <div className="ps-rise flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-md bg-teal px-4 py-2.5 text-[15px] leading-relaxed text-white shadow-sm">
          {text}
        </div>
      </div>
    );
  }

  return (
    <div className="ps-rise flex gap-3">
      <Avatar />
      <div className="min-w-0 flex-1 space-y-3 pt-0.5">
        {message.blocks.map((block, i) => {
          const isLastText =
            block.type === "text" &&
            i === message.blocks.map((b) => b.type).lastIndexOf("text");
          if (block.type === "text") {
            if (!block.text && streaming) return <Thinking key={i} />;
            return (
              <div
                key={i}
                className={`prose-ps text-[15px] leading-relaxed text-body ${
                  streaming && isLastText ? "ps-caret" : ""
                }`}
              >
                <ReactMarkdown>{block.text}</ReactMarkdown>
              </div>
            );
          }
          return <CardRenderer key={i} card={block.card} />;
        })}
      </div>
    </div>
  );
}

function Avatar() {
  return (
    <div className="mt-0.5 flex h-8 w-8 flex-none items-center justify-center rounded-full bg-teal text-[13px] font-bold text-white">
      PS
    </div>
  );
}

// Three-dot indicator shown before the first token of a reply arrives.
function Thinking() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="ps-dot h-2 w-2 rounded-full bg-muted"
          style={{ animationDelay: `${i * 0.16}s` }}
        />
      ))}
    </div>
  );
}
