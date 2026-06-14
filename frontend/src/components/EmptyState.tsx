"use client";

// The first-run welcome. A branded intro plus tappable suggestion chips drawn
// from the brief's own example queries, so the demo path is one click away.

const SUGGESTIONS = [
  "How can I install part PS11752778?",
  "Is PS11746337 compatible with my WDT780SAEM1?",
  "My Whirlpool fridge ice maker isn't working",
  "What's the status of order PS-100234?",
];

export default function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex flex-col items-center py-16 text-center">
      <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-tint text-2xl">
        🧊
      </div>
      <h1 className="text-2xl font-extrabold tracking-tight text-ink">
        How can I help with your appliance?
      </h1>
      <p className="mt-2 max-w-md text-[15px] leading-relaxed text-body">
        Find parts, check if they fit your model, troubleshoot a problem, or look up an order — for
        your refrigerator or dishwasher.
      </p>

      <div className="mt-8 grid w-full max-w-xl grid-cols-1 gap-2.5 sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="group rounded-card border border-line bg-surface px-4 py-3 text-left text-[14px] font-medium text-body shadow-sm transition-all hover:-translate-y-0.5 hover:border-teal hover:shadow-md"
          >
            <span className="text-teal transition-colors group-hover:text-teal-dark">›</span>{" "}
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
