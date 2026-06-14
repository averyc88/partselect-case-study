import ChatWindow from "@/components/ChatWindow";
import Header from "@/components/Header";

export default function Home() {
  // Full-height column: fixed header on top, chat fills the rest. The chat's
  // own transcript scrolls while the composer stays pinned to the bottom.
  return (
    <div className="flex h-screen flex-col bg-canvas">
      <Header />
      <ChatWindow />
    </div>
  );
}
