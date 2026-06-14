import { PARTSELECT_URL, type InstallGuidePayload } from "@/lib/types";

import { CardHeader, CardShell, DifficultyPill } from "./shared";

// Install guide — difficulty + time at a glance, then ordered steps with
// teal numbered markers.

export default function InstallGuide({ guide }: { guide: InstallGuidePayload }) {
  return (
    <CardShell>
      <CardHeader title="Installation Guide" />

      <div className="p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h3 className="text-[15px] font-bold leading-snug text-ink">{guide.name}</h3>
          <span className="flex-none text-[12px] text-muted">PS# {guide.ps_number}</span>
        </div>

        <div className="mb-4 flex items-center gap-2">
          <DifficultyPill difficulty={guide.difficulty} />
          <span className="rounded-full bg-canvas px-2 py-0.5 text-[11px] font-semibold text-body">
            ~{guide.time}
          </span>
        </div>

        <ol className="space-y-2.5">
          {guide.steps.map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-teal text-[12px] font-bold text-white">
                {i + 1}
              </span>
              <span className="pt-0.5 text-[14px] leading-relaxed text-body">{step}</span>
            </li>
          ))}
        </ol>
      </div>

      <a
        href={PARTSELECT_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="block border-t border-line px-4 py-2.5 text-center text-[13px] font-semibold text-teal transition-colors hover:bg-teal-tint"
      >
        Shop parts on PartSelect →
      </a>
    </CardShell>
  );
}
