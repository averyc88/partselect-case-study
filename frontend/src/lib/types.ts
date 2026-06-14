// Types mirroring the backend's NDJSON contract and card payloads.
// The backend (tools.py) emits plain dicts; these are the TypeScript shapes the
// UI renders. Kept loose where the backend record is rich — we only type the
// fields the cards actually use.

export type Role = "user" | "assistant";

// ---- Card payloads (one per card_kind emitted by the backend) -------------

export interface Part {
  ps_number: string;
  manufacturer_number: string;
  name: string;
  brand: string;
  appliance: "refrigerator" | "dishwasher";
  category: string;
  price: number;
  in_stock: boolean;
  description: string;
  part_url: string;
}

export interface InstallGuidePayload {
  ps_number: string;
  name: string;
  part_url: string;
  difficulty: string;
  time: string;
  steps: string[];
}

export interface CompatibilityPayload {
  ps_number: string;
  model_number: string;
  part_known: boolean;
  model_known: boolean;
  compatible: boolean;
  part_name?: string;
  model_description?: string;
}

export interface RepairDoc {
  id: string;
  title: string;
  appliance: string;
  content: string;
  related_parts: string[];
  score: number;
}

export interface RepairPayload {
  doc: RepairDoc;
  suggested_parts: Part[];
}

export interface OrderItem {
  ps_number: string;
  name: string;
  quantity: number;
  price: number;
}

export interface Order {
  order_id: string;
  status: string;
  order_date: string;
  ship_date: string | null;
  delivered_date: string | null;
  estimated_delivery: string | null;
  tracking_number: string | null;
  carrier: string | null;
  shipping_address: string;
  items: OrderItem[];
  subtotal: number;
  shipping_cost: number;
  total: number;
  return_eligible: boolean;
  cancellable: boolean;
}

export type CardKind = "product" | "install" | "compatibility" | "repair" | "order";

// A discriminated union so components can switch on `kind` with full typing.
export type Card =
  | { kind: "product"; payload: Part }
  | { kind: "install"; payload: InstallGuidePayload }
  | { kind: "compatibility"; payload: CompatibilityPayload }
  | { kind: "repair"; payload: RepairPayload }
  | { kind: "order"; payload: Order };

// ---- Stream events (one per NDJSON line from POST /chat) -------------------

export type StreamEvent =
  | { type: "text"; delta: string }
  | { type: "card"; kind: CardKind; payload: unknown };

// ---- Chat model -----------------------------------------------------------

// A rendered turn. Assistant turns interleave streamed text with cards in the
// order the backend emitted them, so we keep an ordered list of blocks.
export type MessageBlock = { type: "text"; text: string } | { type: "card"; card: Card };

export interface ChatMessage {
  role: Role;
  blocks: MessageBlock[];
}

// What we POST to /chat: plain role+content history (matches the Pydantic model).
export interface WireMessage {
  role: Role;
  content: string;
}

// CTA target for part links. Our catalog mixes the brief's real PS11752778 with
// illustrative mock SKUs, and PartSelect's site blocks bots so we can't verify a
// deep-link or search-URL scheme. Rather than ship links that may 404, every CTA
// points at partselect.com — the part's own details (price, stock, PS#, steps)
// already live in the card, so the link just means "go to the store."
export const PARTSELECT_URL = "https://www.partselect.com";
