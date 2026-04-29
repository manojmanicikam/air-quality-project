"""
map_module.py
─────────────
Builds an interactive Folium map that:
  1. Seeds ~30 random AQI zones around the sensor location
  2. Lets the user click a destination anywhere on the map
  3. Computes a "clean-air route" via a graph of street-like waypoints,
     preferring paths through low-AQI zones using Dijkstra's algorithm
  4. Draws the route with colour-coded AQI overlays along the path

No external routing API needed — all computed locally with a synthetic
road graph built from the seeded AQI points.
"""

import math
import random
import heapq
import folium
from folium import MacroElement
from jinja2 import Template

# ── Sensor / origin ──────────────────────────────────────────────────────────
SENSOR_LAT = 13.127879413345047
SENSOR_LON = 77.58657587251105

# ── AQI palette (fg colour, bg colour) ───────────────────────────────────────
AQI_PALETTE = {
    "Good":                  ("#4ade80", "#052e16"),
    "Moderate":              ("#facc15", "#1c1608"),
    "Unhealthy (Sensitive)": ("#fb923c", "#1c0e08"),
    "Unhealthy":             ("#f87171", "#1c0808"),
    "Very Unhealthy":        ("#c084fc", "#160820"),
    "Hazardous":             ("#fb7185", "#200810"),
}

def _aqi_label(aqi: int) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Moderate"
    if aqi <= 150:  return "Unhealthy (Sensitive)"
    if aqi <= 200:  return "Unhealthy"
    if aqi <= 300:  return "Very Unhealthy"
    return "Hazardous"

def _aqi_color(aqi: int) -> str:
    return AQI_PALETTE[_aqi_label(aqi)][0]

# ── Haversine distance (metres) ───────────────────────────────────────────────
def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a  = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# ── Seed deterministic AQI zones ─────────────────────────────────────────────
def _seed_zones(rng: random.Random, n: int = 30) -> list[dict]:
    """
    Generate n zones within ~1.5 km of the sensor.
    Mix of Good (40%), Moderate (25%), Unhealthy(Sensitive) (15%),
    Unhealthy (10%), Very Unhealthy (7%), Hazardous (3%).
    """
    buckets = (
        [(0,  50)]  * 12 +   # Good
        [(51, 100)] * 7  +   # Moderate
        [(101,150)] * 5  +   # Unhealthy (Sensitive)
        [(151,200)] * 3  +   # Unhealthy
        [(201,300)] * 2  +   # Very Unhealthy
        [(301,400)] * 1      # Hazardous
    )
    rng.shuffle(buckets)
    zones = []
    for i, (lo, hi) in enumerate(buckets[:n]):
        # Polar offset so zones spread around sensor
        angle  = rng.uniform(0, 2 * math.pi)
        radius = rng.uniform(100, 1400)          # metres
        dlat   = (radius * math.cos(angle)) / 111_320
        dlon   = (radius * math.sin(angle)) / (111_320 * math.cos(math.radians(SENSOR_LAT)))
        aqi    = rng.randint(lo, hi)
        zones.append({
            "id":  i,
            "lat": SENSOR_LAT + dlat,
            "lon": SENSOR_LON + dlon,
            "aqi": aqi,
            "radius": rng.randint(80, 220),      # influence radius (m) for display
        })
    # always include the origin as a Good zone
    zones.append({"id": n, "lat": SENSOR_LAT, "lon": SENSOR_LON,
                  "aqi": 25, "radius": 120})
    return zones

# ── Build synthetic road graph ────────────────────────────────────────────────
def _build_graph(nodes: list[dict], max_edge_m: float = 600) -> dict:
    """
    Connect each node to all others within max_edge_m.
    Edge weight = distance * aqi_penalty so cleaner air = cheaper path.
    """
    graph = {n["id"]: [] for n in nodes}
    for i, a in enumerate(nodes):
        for j, b in enumerate(nodes):
            if i >= j:
                continue
            dist = _haversine(a["lat"], a["lon"], b["lat"], b["lon"])
            if dist > max_edge_m:
                continue
            # penalty: AQI 0-50 → ×1.0,  AQI 300+ → ×4.0
            # so dirty air makes edges much more expensive than detour cost
            penalty_a = 1.0 + (a["aqi"] / 100) * 1.5
            penalty_b = 1.0 + (b["aqi"] / 100) * 1.5
            weight = dist * (penalty_a + penalty_b) / 2
            graph[a["id"]].append((weight, dist, b["id"]))
            graph[b["id"]].append((weight, dist, a["id"]))
    return graph

# ── Dijkstra ─────────────────────────────────────────────────────────────────
def _dijkstra(graph: dict, start: int, end: int) -> list[int]:
    dist   = {k: math.inf for k in graph}
    prev   = {}
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == end:
            break
        for weight, _, v in graph[u]:
            nd = d + weight
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    # reconstruct
    path, cur = [], end
    while cur in prev:
        path.append(cur)
        cur = prev[cur]
    path.append(start)
    return list(reversed(path))

# ── Find nearest graph node to a lat/lon ─────────────────────────────────────
def _nearest(nodes: list[dict], lat: float, lon: float) -> int:
    return min(nodes, key=lambda n: _haversine(n["lat"], n["lon"], lat, lon))["id"]

# ── JavaScript click handler injected into the map ───────────────────────────
_CLICK_JS = """
{% macro script(this, kwargs) %}
(function () {
    // Node data baked in at render time
    var NODES   = {{ nodes_json }};
    var EDGES   = {{ edges_json }};   // [{from, to, dist, weight}]
    var ORIGIN  = {{ origin_id }};

    function haversine(lat1, lon1, lat2, lon2) {
        var R = 6371000, toR = Math.PI / 180;
        var dLat = (lat2 - lat1) * toR, dLon = (lon2 - lon1) * toR;
        var a = Math.sin(dLat/2)**2 +
                Math.cos(lat1*toR)*Math.cos(lat2*toR)*Math.sin(dLon/2)**2;
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }

    function nearest(lat, lon) {
        var best = null, bestD = Infinity;
        NODES.forEach(function(n) {
            var d = haversine(lat, lon, n.lat, n.lon);
            if (d < bestD) { bestD = d; best = n.id; }
        });
        return best;
    }

    function dijkstra(startId, endId) {
        var dist = {}, prev = {}, visited = new Set();
        NODES.forEach(function(n){ dist[n.id] = Infinity; });
        dist[startId] = 0;

        // simple priority queue via sorted array
        var pq = [[0, startId]];
        while (pq.length) {
            pq.sort(function(a,b){ return a[0]-b[0]; });
            var top = pq.shift(), d = top[0], u = top[1];
            if (visited.has(u)) continue;
            visited.add(u);
            if (u === endId) break;
            EDGES.forEach(function(e) {
                var v = null;
                if (e.from === u) v = e.to;
                else if (e.to === u) v = e.from;
                if (v === null) return;
                var nd = d + e.weight;
                if (nd < dist[v]) {
                    dist[v] = nd;
                    prev[v] = u;
                    pq.push([nd, v]);
                }
            });
        }
        var path = [], cur = endId;
        while (prev[cur] !== undefined) { path.push(cur); cur = prev[cur]; }
        path.push(startId);
        return path.reverse();
    }

    function aqiColor(aqi) {
        if (aqi <= 50)  return '#4ade80';
        if (aqi <= 100) return '#facc15';
        if (aqi <= 150) return '#fb923c';
        if (aqi <= 200) return '#f87171';
        if (aqi <= 300) return '#c084fc';
        return '#fb7185';
    }
    function aqiLabel(aqi) {
        if (aqi <= 50)  return 'Good';
        if (aqi <= 100) return 'Moderate';
        if (aqi <= 150) return 'Unhealthy (Sensitive)';
        if (aqi <= 200) return 'Unhealthy';
        if (aqi <= 300) return 'Very Unhealthy';
        return 'Hazardous';
    }

    var nodeMap = {};
    NODES.forEach(function(n){ nodeMap[n.id] = n; });

    var routeLayer = null, destMarker = null;

    {{ this._parent.get_name() }}.on('click', function(e) {
        var lat = e.latlng.lat, lon = e.latlng.lng;

        // Remove old route & marker
        if (routeLayer)  { routeLayer.remove();  routeLayer  = null; }
        if (destMarker)  { destMarker.remove();  destMarker  = null; }

        var destId = nearest(lat, lon);
        var path   = dijkstra(ORIGIN, destId);

        if (path.length < 2) return;

        // Draw each segment colour-coded by its midpoint AQI zone
        for (var i = 0; i < path.length - 1; i++) {
            var a = nodeMap[path[i]], b = nodeMap[path[i+1]];
            var avgAqi = Math.round((a.aqi + b.aqi) / 2);
            var color  = aqiColor(avgAqi);
            var seg = L.polyline(
                [[a.lat, a.lon], [b.lat, b.lon]],
                { color: color, weight: 6, opacity: 0.9,
                  dashArray: avgAqi > 100 ? '8 4' : null }
            ).addTo({{ this._parent.get_name() }});
            seg.bindTooltip('AQI ' + avgAqi + ' — ' + aqiLabel(avgAqi));
            if (i === 0) routeLayer = seg;
        }

        // Destination marker
        destMarker = L.marker([nodeMap[destId].lat, nodeMap[destId].lon], {
            icon: L.divIcon({
                html: '<div style="background:#38bdf8;width:16px;height:16px;'+
                      'border-radius:50%;border:3px solid #fff;box-shadow:0 0 8px #38bdf8"></div>',
                iconSize: [16,16], iconAnchor: [8,8]
            })
        }).addTo({{ this._parent.get_name() }});
        destMarker.bindPopup(
            '<b>🏁 Destination</b><br>' +
            '<span style="font-size:.8rem;color:#555">Clean-air route calculated.<br>' +
            'Segments coloured by AQI level.</span>'
        ).openPopup();
    });
})();
{% endmacro %}
"""

class _ClickRouter(MacroElement):
    def __init__(self, nodes, edges, origin_id):
        import json
        super().__init__()
        self._template = Template(_CLICK_JS)
        self.nodes_json  = json.dumps(nodes)
        self.edges_json  = json.dumps(edges)
        self.origin_id   = origin_id

# ── Public builder ────────────────────────────────────────────────────────────
def build_aqi_map(live_aqi: int | None = None, seed: int = 42) -> folium.Map:
    """
    Returns a fully built Folium map with:
      • Coloured AQI circles for each seeded zone
      • "I'm here" origin marker
      • JS click-to-route handler (clean-air Dijkstra)

    live_aqi : if provided, overrides the origin zone's AQI with the live sensor value.
    seed     : fixed seed for reproducible zone placement.
    """
    rng   = random.Random(seed)
    zones = _seed_zones(rng)

    # Inject live sensor reading into origin zone
    if live_aqi is not None:
        for z in zones:
            if z["lat"] == SENSOR_LAT and z["lon"] == SENSOR_LON:
                z["aqi"] = live_aqi
                break

    graph = _build_graph(zones)

    # ── Serialise graph for JS ────────────────────────────────────────────────
    nodes_js, edges_js = [], []
    for z in zones:
        nodes_js.append({"id": z["id"], "lat": z["lat"],
                         "lon": z["lon"], "aqi": z["aqi"]})
    seen = set()
    for u, neighbours in graph.items():
        for weight, dist, v in neighbours:
            key = (min(u,v), max(u,v))
            if key in seen: continue
            seen.add(key)
            edges_js.append({"from": u, "to": v,
                             "weight": round(weight, 2),
                             "dist":   round(dist, 2)})

    origin_id = next(z["id"] for z in zones
                     if z["lat"] == SENSOR_LAT and z["lon"] == SENSOR_LON)

    # ── Map ───────────────────────────────────────────────────────────────────
    m = folium.Map(
        location=[SENSOR_LAT, SENSOR_LON],
        zoom_start=15,
        tiles="CartoDB dark_matter",
    )

    # AQI zone circles
    for z in zones:
        label = _aqi_label(z["aqi"])
        fg, bg = AQI_PALETTE[label]
        folium.CircleMarker(
            location=[z["lat"], z["lon"]],
            radius=z["radius"] / 10,          # folium radius is in px ~ metres/10
            color=fg,
            fill=True,
            fill_color=fg,
            fill_opacity=0.22,
            weight=1,
            tooltip=f'AQI {z["aqi"]} — {label}',
            popup=folium.Popup(
                f'<div style="font-family:sans-serif;text-align:center">'
                f'<b style="color:{fg};font-size:1.1rem">AQI {z["aqi"]}</b><br>'
                f'<span style="color:#555">{label}</span></div>',
                max_width=160,
            ),
        ).add_to(m)

    # Origin "I'm here" marker
    folium.Marker(
        location=[SENSOR_LAT, SENSOR_LON],
        tooltip="📍 I'm here — click anywhere to route",
        popup=folium.Popup(
            f'<div style="font-family:sans-serif;text-align:center;min-width:160px">'
            f'<b>📍 Sensor Location</b><br>'
            f'<span style="font-size:.85rem;color:#38bdf8">AQI {live_aqi or 25}</span><br>'
            f'<span style="font-size:.72rem;color:#888">'
            f'Click anywhere on the map<br>to get a clean-air route</span></div>',
            max_width=200,
        ),
        icon=folium.Icon(color="red", icon_color="white",
                         icon="map-marker", prefix="fa"),
    ).add_to(m)

    # Instruction banner
    folium.map.Marker(
        [SENSOR_LAT + 0.012, SENSOR_LON],
        icon=folium.DivIcon(
            html="""
            <div style="
                background:rgba(11,15,26,0.88);
                color:#e2e8f0;
                font-family:'DM Sans',sans-serif;
                font-size:0.78rem;
                padding:7px 14px;
                border-radius:8px;
                border:1px solid #1e293b;
                white-space:nowrap;
                box-shadow:0 2px 12px #000a;
            ">
                🖱️ Click anywhere on the map to route via clean air
            </div>""",
            icon_size=(310, 36),
            icon_anchor=(155, 18),
        ),
    ).add_to(m)

    # Inject JS router
    router = _ClickRouter(nodes_js, edges_js, origin_id)
    m.add_child(router)

    return m