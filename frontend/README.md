# AI Music Recommender — Frontend

React + Vite + TypeScript client for the AI Music Recommender. Connects to Spotify,
lets the user pick a playlist, and displays the ten GPT-ranked recommendations with
plain-language explanations.

## Design direction

The product is framed as an analog audio console rather than a generic SaaS
dashboard: a deep ink-blue body (`--ink-950`, never pure black), a warm VU-meter
amber as the primary signal color, and a cooler oscilloscope teal as the secondary
trace. Fraunces (serif) carries headline weight like a hi-fi nameplate; IBM Plex
Mono renders every piece of data — confidence scores, dates, track counts — like a
channel-strip readout. The signature element is a pulsing **waveform/equalizer**
motif (`components/Waveform.tsx`), used for every loading and "thinking" state
instead of a generic spinner. Design tokens live in `src/index.css`.

Navigation is a vertical rail (`components/Navbar.tsx`) styled like a mixing
console's channel strip rather than a top navbar, since this is an authenticated
app, not a marketing site.

## Pages → spec mapping

| Spec page | Implementation |
|---|---|
| Login | `pages/LoginPage.tsx` (login + registration in one view) |
| Dashboard | `pages/Dashboard.tsx` |
| Connect Music Account | `components/AccountCard.tsx`, embedded in Dashboard |
| Playlist Selection | `components/PlaylistSelector.tsx`, embedded in Dashboard |
| Recommendation Results | `pages/RecommendationPage.tsx` |
| Recommendation History | `pages/HistoryPage.tsx` |

Component tree matches the spec: `Navbar`, `LoginPage`, `Dashboard` (→
`AccountCard`, `PlaylistSelector`, `GenerateButton`), `RecommendationPage` (→
`SongCard`, `ExplanationModal`, `SaveButton`), `HistoryPage`.

## Structure

```
src/
├── api/            # typed fetch wrappers, one file per backend router
│   ├── client.ts    # base request fn: JWT header, JSON, typed ApiRequestError
│   ├── auth.ts
│   ├── spotify.ts
│   └── recommendations.ts
├── context/
│   └── AuthContext.tsx   # current user + login/logout, backed by localStorage JWT
├── routes/
│   ├── ProtectedRoute.tsx   # redirects to /login when unauthenticated
│   └── AppShellLayout.tsx   # wraps authenticated pages with the nav rail
├── components/      # AccountCard, PlaylistSelector, GenerateButton, SongCard,
│                     # ExplanationModal, SaveButton, Navbar, Waveform
├── pages/            # LoginPage, Dashboard, RecommendationPage, HistoryPage
└── types/index.ts    # mirrors backend Pydantic schemas
```

## Running locally

```bash
cp .env.example .env    # set VITE_API_BASE_URL to the running backend
npm install
npm run dev
```

Requires the backend running (see `../backend/README.md`) with a Spotify app
registered so `/spotify/connect` returns a working authorization URL.

## Building

```bash
npm run build      # tsc -b && vite build, outputs to dist/
npm run preview     # serve the production build locally
```

`dist/` is what gets deployed to S3 + CloudFront in production (see
`../terraform/`). The included `Dockerfile` (nginx-based) is for local/container
preview only — it is not the production deployment path.

> **Note:** this project was scaffolded in a sandboxed environment with no
> network access, so `npm install` could not be run here and the build has not
> been executed end to end. Every file was checked with `tsc --noEmit` against
> the project's own `tsconfig.json`; the only errors reported were "cannot find
> module" for not-yet-installed packages (react, react-router-dom, css side-effect
> imports) — no structural/logic type errors. Run `npm install && npm run build`
> locally to confirm before deploying.

## Notes on API contract

- `GET /spotify/connect` returns `{ authorization_url }`; the frontend does a full
  redirect (`window.location.href`) rather than an XHR, since this has to leave
  the SPA for Spotify's consent screen.
- `POST /recommendations/generate` returns the full `RecommendationHistoryEntry`
  (including nested track data per item), which is handed to `RecommendationPage`
  via React Router's navigation `state` to avoid an extra round-trip. Reloading
  that page requires clicking through from History or Dashboard again, since
  route `state` doesn't survive a hard refresh — that's a deliberate MVP
  trade-off, not an oversight.
