import type { Order } from "@/lib/types";

import { CardShell } from "./shared";

// Order card — status, line items, totals, and a clear read on whether the
// order can be returned or cancelled (the backend's hardcoded eligibility
// flags). Status pill color tracks the lifecycle.

const STATUS_TONE: Record<string, string> = {
  Delivered: "bg-stock/12 text-stock",
  Shipped: "bg-teal-tint text-teal-darker",
  Processing: "bg-gold/20 text-gold-dark",
  Cancelled: "bg-nostock/12 text-nostock",
  "Return Initiated": "bg-teal-tint text-teal-darker",
};

export default function OrderCard({ order }: { order: Order }) {
  const tone = STATUS_TONE[order.status] ?? "bg-canvas text-body";

  return (
    <CardShell>
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">Order</div>
          <div className="text-[15px] font-bold text-ink">{order.order_id}</div>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-[12px] font-bold ${tone}`}>
          {order.status}
        </span>
      </div>

      {/* Items */}
      <div className="divide-y divide-line">
        {order.items.map((item) => (
          <div key={item.ps_number} className="flex items-center justify-between gap-3 px-4 py-2.5">
            <div className="min-w-0">
              <div className="truncate text-[13px] font-semibold text-ink">{item.name}</div>
              <div className="text-[11px] text-muted">
                PS# {item.ps_number} · Qty {item.quantity}
              </div>
            </div>
            <span className="flex-none text-[13px] font-bold text-ink">
              ${(item.price * item.quantity).toFixed(2)}
            </span>
          </div>
        ))}
      </div>

      {/* Totals */}
      <div className="space-y-1 border-t border-line px-4 py-3 text-[13px]">
        <Line label="Subtotal" value={order.subtotal} />
        <Line label="Shipping" value={order.shipping_cost} free={order.shipping_cost === 0} />
        <div className="flex items-center justify-between pt-1 text-[14px] font-extrabold text-ink">
          <span>Total</span>
          <span>${order.total.toFixed(2)}</span>
        </div>
      </div>

      {/* Tracking / delivery facts */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 border-t border-line px-4 py-3 text-[12px]">
        <Fact label="Ordered" value={order.order_date} />
        {order.estimated_delivery && <Fact label="Est. delivery" value={order.estimated_delivery} />}
        {order.delivered_date && <Fact label="Delivered" value={order.delivered_date} />}
        {order.carrier && order.tracking_number && (
          <Fact label={order.carrier} value={order.tracking_number} mono />
        )}
      </div>

      {/* Eligibility */}
      <div className="flex gap-2 border-t border-line bg-canvas/60 px-4 py-2.5">
        <Eligibility ok={order.return_eligible} label="Returnable" />
        <Eligibility ok={order.cancellable} label="Cancellable" />
      </div>
    </CardShell>
  );
}

function Line({ label, value, free }: { label: string; value: number; free?: boolean }) {
  return (
    <div className="flex items-center justify-between text-body">
      <span>{label}</span>
      <span>{free ? "FREE" : `$${value.toFixed(2)}`}</span>
    </div>
  );
}

function Fact({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted">{label}</div>
      <div className={`truncate text-[12px] text-ink ${mono ? "font-mono" : "font-medium"}`}>
        {value}
      </div>
    </div>
  );
}

function Eligibility({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-bold ${
        ok ? "bg-stock/10 text-stock" : "bg-canvas text-muted"
      }`}
    >
      {ok ? "✓" : "—"} {label}
    </span>
  );
}
