import { PARTSELECT_URL, type Part } from "@/lib/types";

import { ApplianceTag, CardShell, StockBadge } from "./shared";

// Product card — the part's identity, price, stock, and a CTA to the live
// PartSelect page. The visual anchor of most answers.

export default function ProductCard({ part }: { part: Part }) {
  return (
    <CardShell>
      <div className="flex items-start justify-between gap-3 p-4">
        <div className="min-w-0">
          <div className="mb-1 flex flex-wrap items-center gap-1.5">
            <ApplianceTag appliance={part.appliance} />
            <span className="text-[11px] font-semibold uppercase tracking-wide text-muted">
              {part.brand}
            </span>
          </div>
          <h3 className="text-[15px] font-bold leading-snug text-ink">{part.name}</h3>
          <p className="mt-0.5 text-[12px] text-muted">
            PS# {part.ps_number} · Mfr# {part.manufacturer_number}
          </p>
        </div>
        <div className="flex flex-none flex-col items-end gap-1.5">
          <span className="text-[18px] font-extrabold text-ink">${part.price.toFixed(2)}</span>
          <StockBadge inStock={part.in_stock} />
        </div>
      </div>

      <p className="px-4 pb-3 text-[13px] leading-relaxed text-body line-clamp-2">
        {part.description}
      </p>

      <div className="flex items-center justify-between border-t border-line px-4 py-2.5">
        <span className="text-[12px] text-muted">{part.category}</span>
        <a
          href={PARTSELECT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 rounded-lg bg-gold px-3 py-1.5 text-[13px] font-bold text-ink transition-colors hover:bg-gold-dark"
        >
          Shop on PartSelect
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M7 17 17 7M9 7h8v8"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </a>
      </div>
    </CardShell>
  );
}
