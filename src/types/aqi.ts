export type AqiLevel = "Good" | "Moderate" | "Poor";

export interface AqiMarker {
  id: string;
  name: string;
  lat: number;
  lng: number;
  aqi: number;
  level: AqiLevel;
}

export interface AlertItem {
  id: string;
  title: string;
  message: string;
  severity: "low" | "medium" | "high";
  time: string;
}
