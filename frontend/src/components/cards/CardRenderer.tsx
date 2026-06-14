import type { Card } from "@/lib/types";

import CompatibilityCard from "./CompatibilityCard";
import InstallGuide from "./InstallGuide";
import OrderCard from "./OrderCard";
import ProductCard from "./ProductCard";
import RepairCard from "./RepairCard";

// Dispatches a card payload to its component by `kind`. Mirrors the backend's
// card_kind registry — adding a card is one case here + one component.

export default function CardRenderer({ card }: { card: Card }) {
  switch (card.kind) {
    case "product":
      return <ProductCard part={card.payload} />;
    case "install":
      return <InstallGuide guide={card.payload} />;
    case "compatibility":
      return <CompatibilityCard result={card.payload} />;
    case "repair":
      return <RepairCard repair={card.payload} />;
    case "order":
      return <OrderCard order={card.payload} />;
    default:
      return null;
  }
}
