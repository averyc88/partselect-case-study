"use client";

import { useRef, useState } from "react";

// The message input bar. Auto-growing textarea, Enter to send (Shift+Enter for a
// newline), teal send button that disables while a reply streams.

export default function Composer({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");
  const taRef = useRef<HTMLTextAreaElement>(null);

  function submit() {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
    if (taRef.current) taRef.current.style.height = "auto";
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function grow(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }

  return (
    <div className="border-t border-line bg-surface">
      <div className="mx-auto w-full max-w-3xl px-4 py-3">
        <div className="flex items-end gap-2 rounded-2xl border border-line bg-canvas px-3 py-2 transition-colors focus-within:border-teal">
          <textarea
            ref={taRef}
            value={value}
            onChange={grow}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Ask about a part, model, repair, or order…"
            className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-[15px] leading-relaxed text-ink outline-none placeholder:text-muted"
          />
          <button
            onClick={submit}
            disabled={!value.trim() || disabled}
            aria-label="Send message"
            className="mb-0.5 flex h-9 w-9 flex-none items-center justify-center rounded-xl bg-teal text-white transition-colors hover:bg-teal-dark disabled:cursor-not-allowed disabled:opacity-40"
          >
            <SendIcon />
          </button>
        </div>
        <p className="mt-1.5 text-center text-[11px] text-muted">
          PartSelect Assistant helps with refrigerator &amp; dishwasher parts.
        </p>
      </div>
    </div>
  );
}

function SendIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M5 12h13M13 6l6 6-6 6"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
