// Minimal PartSelect-branded header. Just enough chrome to frame the chat as
// part of the PartSelect site — the wordmark and a thin teal accent strip — with
// no fake navigation or dead links.

export default function Header() {
  return (
    <header className="sticky top-0 z-20 shadow-sm">
      <div className="bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-5 py-3">
          <div className="leading-tight">
            <div className="text-[22px] font-extrabold tracking-tight text-ink">
              Part<span className="text-teal">Select</span>
            </div>
            <div className="text-[11px] font-medium text-muted">Here to help since 1999</div>
          </div>
          <span className="hidden items-center gap-1.5 text-[13px] font-semibold text-body sm:flex">
            <span className="inline-block h-2 w-2 rounded-full bg-teal" />
            Parts Assistant
          </span>
        </div>
      </div>
      <div className="h-1 bg-teal" />
    </header>
  );
}
