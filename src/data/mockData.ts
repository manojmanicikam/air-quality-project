import { AlertItem, AqiMarker } from "@/types/aqi";

export const cityCenter = {
  lat: 12.9716,
  lng: 77.5946,
};

export const aqiMarkers: AqiMarker[] = [
  { id: "1", name: "Indiranagar", lat: 12.9784, lng: 77.6408, aqi: 64, level: "Moderate" },
  { id: "2", name: "Malleshwaram", lat: 13.0035, lng: 77.5706, aqi: 46, level: "Good" },
  { id: "3", name: "Whitefield", lat: 12.9698, lng: 77.7499, aqi: 91, level: "Moderate" },
  { id: "4", name: "Electronic City", lat: 12.8456, lng: 77.6603, aqi: 138, level: "Poor" },
  { id: "5", name: "Yeshwanthpur", lat: 13.0285, lng: 77.5400, aqi: 152, level: "Poor" },
];

export const alertsData: AlertItem[] = [
  {
    id: "a1",
    title: "AQI Warning - North Bengaluru",
    message: "AQI has crossed 150 near industrial corridors. Avoid prolonged outdoor activity.",
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
    message: "Localized smoke plume detected near Electronic City. Route diversions enabled.",
    severity: "high",
    time: "42 min ago",
  },
];

export const dashboardStats = [
  { label: "City AQI", value: "87", delta: "+6% today" },
  { label: "Sensors Active", value: "128", delta: "98.4% uptime" },
  { label: "Hotspots", value: "11", delta: "-2 from yesterday" },
];
