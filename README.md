## AirIQ Smart City AQI Monitor

Modern hackathon-ready frontend for hyperlocal air quality monitoring with OpenStreetMap integration, dark neon styling, and responsive dashboard UX.

### Stack
- Next.js 14 (App Router)
- React + TypeScript
- Tailwind CSS
- `react-leaflet` + `leaflet` (OpenStreetMap tiles)

### Setup

1. Install dependencies:

```bash
npm install
```

2. Create `.env.local` from the example:

```bash
cp .env.local.example .env.local
```

3. Configure `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

4. Run local dev server:

```bash
npm run dev
```

App runs at [http://localhost:3000](http://localhost:3000).

### Pages
- `/` Home page with hero, tagline, CTAs, and AQI stats.
- `/dashboard` Split dashboard layout with AQI cards, health score, forecast placeholder, alerts, and large city map.
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

### OpenStreetMap Integration
- Uses `react-leaflet` with OpenStreetMap tile layers.
- Default center: Bengaluru, India.
- Dashboard map renders 5 sample AQI markers with color states:
  - Green = Good
  - Yellow = Moderate
  - Red = Poor

## Python Sensor Backend (FastAPI)

Backend lives in `backend/` and is designed for Python sensor ingestion + database storage.

### Run backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Available API endpoints

- `GET /health`
- `POST /sensor/readings` (ingest sensor reading)
- `GET /sensor/readings/latest`
- `GET /aqi/hotspots`
- `GET /alerts`
- `POST /route/score`

### Example sensor ingest payload

```json
{
  "sensor_id": "blr-201",
  "location_name": "KR Puram",
  "lat": 13.0146,
  "lng": 77.6983,
  "gas_ppm": 136,
  "temperature_c": 32.4,
  "humidity_percent": 61.5,
  "pm25": 41,
  "pm10": 68,
  "no2": 19,
  "o3": 15
}
```

Frontend already defaults to `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.

### Hardware mapping guide
- Gas sensor -> `gas_ppm`
- Temperature sensor -> `temperature_c`
- Humidity sensor -> `humidity_percent`
- GPS module -> `lat` and `lng`
