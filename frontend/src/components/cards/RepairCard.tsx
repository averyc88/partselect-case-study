import ReactMarkdown from "react-markdown";

import type { RepairPayload } from "@/lib/types";

import { CardHeader, CardShell, StockBadge } from "./shared";

// Repair card — the matched troubleshooting guide (title + polished content)
// plus the parts that commonly fix it, as compact rows.

export default function RepairCard({ repair }: { repair: RepairPayload }) {
  const { doc, suggested_parts } = repair;
  return (
    <CardShell>
      <CardHeader title="Troubleshooting" accent="gold" />

      <div className="p-4">
        <h3 className="mb-2 text-[15px] font-bold leading-snug text-ink">{doc.title}</h3>
        <div className="prose-ps text-[13.5px] leading-relaxed text-body">
          <ReactMarkdown>{doc.content}</ReactMarkdown>
        </div>
      </div>

      {suggested_parts.length > 0 && (
        <div className="border-t border-line bg-canvas/60 p-4">
          <div className="mb-2 text-[12px] font-bold uppercase tracking-wide text-muted">
            Parts that may fix this
          </div>
          <div className="space-y-2">
            {suggested_parts.map((p) => (
              <div
                key={p.ps_number}
                className="flex items-center justify-between gap-3 rounded-lg border border-line bg-surface px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="truncate text-[13px] font-semibold text-ink">{p.name}</div>
                  <div className="text-[11px] text-muted">
                    {p.brand} · PS# {p.ps_number}
                  </div>
                </div>
                <div className="flex flex-none items-center gap-2">
                  <StockBadge inStock={p.in_stock} />
                  <span className="text-[14px] font-extrabold text-ink">${p.price.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </CardShell>
  );
}
