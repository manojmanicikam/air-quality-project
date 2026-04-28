## AirIQ Smart City AQI Monitor

Modern hackathon-ready frontend for hyperlocal air quality monitoring with Google Maps integration, dark neon styling, and responsive dashboard UX.

### Stack
- Next.js 14 (App Router)
- React + TypeScript
- Tailwind CSS
- `@react-google-maps/api`

### Setup

1. Install dependencies:

```bash
npm install
```

2. Create `.env.local` from the example:

```bash
cp .env.local.example .env.local
```

3. Add your Google Maps JavaScript API key in `.env.local`:

```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_key_here
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

4. Run local dev server:

```bash
npm run dev
```

App runs at [http://localhost:3000](http://localhost:3000).

### Pages
- `/` Home page with hero, tagline, CTAs, and AQI stats.
- `/dashboard` Split dashboard layout with AQI cards, health score, forecast placeholder, alerts, and large Google Map.
- `/route-optimization` Route form with map and mock outputs for fastest/cleanest route + pollution saved.
- `/alerts` AQI warning and event feed.

### Folder Structure

```text
src/
  app/
    alerts/page.tsx
    dashboard/page.tsx
    route-optimization/page.tsx
    page.tsx
    layout.tsx
    globals.css
  components/
    aqi-map.tsx
    route-map.tsx
    glass-card.tsx
    loading-skeleton.tsx
    navbar.tsx
    sidebar.tsx
    stat-card.tsx
  data/
    mockData.ts
  lib/
    api.ts
  types/
    aqi.ts
```

### Notes for FastAPI Integration
- Replace mock data in `src/data/mockData.ts` with API calls from `src/lib/api.ts`.
- Use `NEXT_PUBLIC_API_BASE_URL` for backend endpoint configuration.
- Keep UI components unchanged and swap only data sources for rapid iteration.

### Google Maps Integration
- Uses `@react-google-maps/api` with `useJsApiLoader`.
- Default center: Chennai, India.
- Dashboard map renders 5 sample AQI markers with color states:
  - Green = Good
  - Yellow = Moderate
  - Red = Poor
