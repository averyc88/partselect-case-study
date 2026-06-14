import type { CompatibilityPayload } from "@/lib/types";

import { CardShell } from "./shared";

// Compatibility verdict — a big ✓/✗ for the part↔model check. When the part or
// model is unknown we can't assert a fit, so we show a neutral "couldn't verify"
// state rather than a false negative.

export default function CompatibilityCard({ result }: { result: CompatibilityPayload }) {
  const known = result.part_known && result.model_known;
  const compatible = known && result.compatible;

  const tone = !known
    ? { bg: "bg-canvas", ring: "border-line", fg: "text-muted", icon: "?" }
    : compatible
      ? { bg: "bg-stock/8", ring: "border-stock/30", fg: "text-stock", icon: "✓" }
      : { bg: "bg-nostock/8", ring: "border-nostock/30", fg: "text-nostock", icon: "✕" };

  const headline = !known
    ? "Couldn't verify compatibility"
    : compatible
      ? "Compatible"
      : "Not compatible";

  return (
    <CardShell>
      <div className={`flex items-center gap-3 border-b ${tone.ring} ${tone.bg} px-4 py-3`}>
        <span
          className={`flex h-9 w-9 flex-none items-center justify-center rounded-full text-[18px] font-black ${tone.fg} ${tone.bg} ring-2 ${tone.ring}`}
        >
          {tone.icon}
        </span>
        <div>
          <div className={`text-[15px] font-extrabold ${tone.fg}`}>{headline}</div>
          <div className="text-[12px] text-muted">
            {result.part_name ?? `Part ${result.ps_number}`} ·{" "}
            {result.model_number}
          </div>
        </div>
      </div>

      <div className="space-y-2 p-4 text-[13px]">
        <Row label="Part" value={result.part_name ? `${result.part_name} (${result.ps_number})` : result.ps_number} known={result.part_known} unknownNote="not in our catalog" />
        <Row label="Model" value={result.model_number} known={result.model_known} unknownNote="model not found" />
      </div>
    </CardShell>
  );
}

function Row({
  label,
  value,
  known,
  unknownNote,
}: {
  label: string;
  value: string;
  known: boolean;
  unknownNote: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-[12px] font-semibold uppercase tracking-wide text-muted">{label}</span>
      <span className={`text-right font-medium ${known ? "text-ink" : "text-nostock"}`}>
        {value}
        {!known && <span className="ml-1 text-[11px] font-normal text-muted">({unknownNote})</span>}
      </span>
    </div>
  );
}
