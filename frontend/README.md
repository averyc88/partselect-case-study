# PartSelect Chat Agent — Frontend

Next.js + TypeScript + Tailwind v4 chat UI for the PartSelect parts assistant.
Streams the assistant's reply (text + structured cards) from the backend over
NDJSON. See the root [`README.md`](../README.md) for the full setup.

## Run

```bash
npm install
npm run dev      # http://localhost:3000
```

Requires the backend running on `http://localhost:8000` (override with
`NEXT_PUBLIC_API_BASE`).

## Layout

```
src/
  app/            layout, page, Tailwind theme (PartSelect branding)
  components/     Header, ChatWindow, Composer, Message, EmptyState
    cards/        product / install / compatibility / repair / order cards
  lib/            NDJSON streaming client (api.ts) + shared types
```
