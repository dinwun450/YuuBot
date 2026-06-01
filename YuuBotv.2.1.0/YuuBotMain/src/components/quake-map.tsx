"use client";

import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";

type EarthquakeRecord = {
  date?: string | null;
  time?: string | null;
  magnitude?: number | string | null;
  location?: string | null;
  title?: string | null;
  tsunami?: boolean | string | null;
  intensity?: string | null;
  lat?: number | string | null;
  lon?: number | string | null;
};

type MapPoint = EarthquakeRecord & {
  source: "GLOBAL" | "JP";
  id: string;
  lat: number;
  lon: number;
};

function parseNumber(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function FitBounds({ points }: { points: MapPoint[] }) {
  const map = useMap();

  useEffect(() => {
    const coords = points
      .map((point) => [parseNumber(point.lat), parseNumber(point.lon)] as const)
      .filter((pair): pair is readonly [number, number] => pair[0] !== null && pair[1] !== null)
      .map(([lat, lon]) => [lat, lon] as [number, number]);

    if (coords.length === 1) {
      map.setView(coords[0], 5, { animate: true });
      return;
    }

    if (coords.length > 1) {
      map.fitBounds(coords, { padding: [24, 24], maxZoom: 5 });
    }
  }, [map, points]);

  return null;
}

export function QuakeMap() {
  const [points, setPoints] = useState<MapPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadMapData() {
      setIsLoading(true);
      setError(null);

      try {
        const [globalResponse, japanResponse] = await Promise.all([
          fetch("/api/snowflake/overall?schema=GLOBAL&limit=200", { cache: "no-store" }),
          fetch("/api/snowflake/overall?schema=JP&limit=200", { cache: "no-store" }),
        ]);

        if (!globalResponse.ok) {
          throw new Error(`Global feed failed: ${globalResponse.status}`);
        }

        if (!japanResponse.ok) {
          throw new Error(`Japan feed failed: ${japanResponse.status}`);
        }

        const [globalRows, japanRows] = (await Promise.all([
          globalResponse.json(),
          japanResponse.json(),
        ])) as [EarthquakeRecord[], EarthquakeRecord[]];

        const normalized: MapPoint[] = [
          ...globalRows.map((row, index) => ({
            ...row,
            source: "GLOBAL" as const,
            id: `global-${index}-${row.date ?? ""}-${row.time ?? ""}`,
          })),
          ...japanRows.map((row, index) => ({
            ...row,
            source: "JP" as const,
            id: `jp-${index}-${row.date ?? ""}-${row.time ?? ""}`,
          })),
        ].flatMap((row) => {
          const lat = parseNumber(row.lat);
          const lon = parseNumber(row.lon);

          if (lat === null || lon === null) {
            return [] as MapPoint[];
          }

          return [
            {
              ...row,
              lat,
              lon,
            },
          ];
        });

        if (isMounted) {
          setPoints(normalized);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load quake data");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadMapData();

    return () => {
      isMounted = false;
    };
  }, []);

  const center = useMemo<[number, number]>(() => {
    if (points.length === 0) return [20, 0];

    const sample = points[0];
    const lat = parseNumber(sample.lat) ?? 20;
    const lon = parseNumber(sample.lon) ?? 0;
    return [lat, lon];
  }, [points]);

  return (
    <div className="quake-map-shell glassflow">
      <div className="quake-map-header">
        <div>
          <h3>Earthquake map</h3>
          <p>Live markers from Snowflake-backed Japan and global feeds.</p>
        </div>
        <div className="quake-map-stats">
          <span>{points.length} points</span>
          <span>Global + Japan</span>
        </div>
      </div>

      <div className="quake-map-frame">
        {isLoading ? <p className="quake-map-status">Loading map data…</p> : null}
        {error ? <p className="quake-map-status quake-map-status--error">{error}</p> : null}

        <MapContainer center={center} zoom={2} scrollWheelZoom className="quake-map-canvas">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <FitBounds points={points} />

          {points.map((point) => {
            const lat = parseNumber(point.lat);
            const lon = parseNumber(point.lon);

            if (lat === null || lon === null) return null;

            const magnitude = parseNumber(point.magnitude) ?? 0;
            const radius = Math.max(5, Math.min(18, 4 + magnitude * 2));
            const isJapan = point.source === "JP";

            return (
              <CircleMarker
                key={point.id}
                center={[lat, lon]}
                radius={radius}
                pathOptions={{
                  color: isJapan ? "#85ecce" : "#bec2ff",
                  fillColor: isJapan ? "#85ecce" : "#bec2ff",
                  fillOpacity: 0.55,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="quake-map-popup">
                    <strong>{point.source === "JP" ? "Japan" : "Global"} earthquake</strong>
                    <p>{point.location ?? point.title ?? "Unknown location"}</p>
                    <p>
                      Magnitude: {point.magnitude ?? "-"}
                      {point.intensity ? ` • Intensity: ${point.intensity}` : ""}
                    </p>
                    <p>
                      {point.date ?? "-"} {point.time ?? ""}
                    </p>
                    {typeof point.tsunami === "boolean" ? (
                      <p>Tsunami: {point.tsunami ? "Yes" : "No"}</p>
                    ) : null}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
