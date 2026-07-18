# ApplyMind — Frontend

Next.js (App Router) frontend for ApplyMind AI. See the [repo root README](../README.md) for the full project overview, architecture, and live demo link.

## Development

```bash
npm install
cp .env.local.example .env.local   # fill in Firebase web config + NEXT_PUBLIC_API_URL
npm run dev
```

Runs on `http://localhost:3000`.

## Structure

- `app/` — pages (dashboard, login, portal-admin, legal pages)
- `components/` — UI components
- `lib/` — Firebase client init and auth context

## Scripts

- `npm run dev` — start the dev server
- `npm run build` — production build
- `npm run start` — serve the production build
- `npm run lint` — lint the codebase
