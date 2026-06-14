// Shared primitives for the structured cards — one consistent shell, badges,
// and tags so every card reads as part of the same system.

export function CardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="ps-rise overflow-hidden rounded-card border border-line bg-surface shadow-sm">
      {children}
    </div>
  );
}

export function StockBadge({ inStock }: { inStock: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold ${
        inStock ? "bg-stock/10 text-stock" : "bg-nostock/10 text-nostock"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${inStock ? "bg-stock" : "bg-nostock"}`} />
      {inStock ? "In Stock" : "Out of Stock"}
    </span>
  );
}

export function ApplianceTag({ appliance }: { appliance: string }) {
  const label = appliance === "refrigerator" ? "Refrigerator" : "Dishwasher";
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-teal-tint px-2 py-0.5 text-[11px] font-semibold text-teal-darker">
      {appliance === "refrigerator" ? "❄️" : "🍽️"} {label}
    </span>
  );
}

// A small difficulty pill for install guides (Easy / Medium / Hard).
export function DifficultyPill({ difficulty }: { difficulty: string }) {
  const color =
    difficulty === "Easy"
      ? "bg-stock/10 text-stock"
      : difficulty === "Hard"
        ? "bg-nostock/10 text-nostock"
        : "bg-gold/20 text-gold-dark";
  return (
    <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${color}`}>{difficulty}</span>
  );
}

// Section header used inside cards (e.g. "Installation Guide", "Troubleshooting").
export function CardHeader({
  title,
  accent = "teal",
}: {
  title: string;
  accent?: "teal" | "gold";
}) {
  return (
    <div
      className={`px-4 py-2.5 text-[12px] font-bold uppercase tracking-wide ${
        accent === "gold" ? "bg-gold/15 text-gold-dark" : "bg-teal-tint text-teal-darker"
      }`}
    >
      {title}
    </div>
  );
}
