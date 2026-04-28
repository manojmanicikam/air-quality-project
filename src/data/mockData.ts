import { AlertItem, AqiMarker } from "@/types/aqi";

export const cityCenter = {
  lat: 13.0827,
  lng: 80.2707,
};

export const aqiMarkers: AqiMarker[] = [
  { id: "1", name: "T. Nagar", lat: 13.0418, lng: 80.2341, aqi: 62, level: "Moderate" },
  { id: "2", name: "Anna Nagar", lat: 13.0849, lng: 80.2101, aqi: 48, level: "Good" },
  { id: "3", name: "Adyar", lat: 13.0067, lng: 80.2573, aqi: 89, level: "Moderate" },
  { id: "4", name: "Perungudi", lat: 12.9647, lng: 80.2446, aqi: 132, level: "Poor" },
  { id: "5", name: "Guindy", lat: 13.0069, lng: 80.2206, aqi: 154, level: "Poor" },
];

export const alertsData: AlertItem[] = [
  {
    id: "a1",
    title: "AQI Warning - North Chennai",
    message: "AQI has crossed 150 near industrial corridors. Avoid outdoor activity.",
    severity: "high",
    time: "5 min ago",
  },
  {
    id: "a2",
    title: "Dust Storm Advisory",
    message: "Dry winds expected after 7 PM. Wear masks and close windows when possible.",
    severity: "medium",
    time: "28 min ago",
  },
  {
    id: "a3",
    title: "Smoke/Fire Nearby",
    message: "Localized smoke plume detected near Guindy. Route diversions enabled.",
    severity: "high",
    time: "42 min ago",
  },
];

export const dashboardStats = [
  { label: "City AQI", value: "87", delta: "+6% today" },
  { label: "Sensors Active", value: "128", delta: "98.4% uptime" },
  { label: "Hotspots", value: "11", delta: "-2 from yesterday" },
];
