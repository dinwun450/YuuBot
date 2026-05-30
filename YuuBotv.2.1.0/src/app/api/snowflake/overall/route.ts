import { executeQuery, type SnowflakeSchema } from "../../../../lib/snowflake";
import {
  refreshGlobalOverallEarthquakes,
  refreshJapaneseOverallEarthquakes,
} from "../../../../lib/earthquake-refresh";

function resolveSchema(input: string | null): SnowflakeSchema {
  return input?.toUpperCase() === "JP" ? "JP" : "GLOBAL";
}

function isMissingTableError(error: unknown) {
  return String(error).includes("does not exist or not authorized");
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const schema = resolveSchema(url.searchParams.get("schema") || process.env.SNOWFLAKE_SCHEMA || "GLOBAL");
  const limit = Number.parseInt(url.searchParams.get("limit") || "1000", 10);

  const sql =
    schema === "JP"
      ? `SELECT date, time, epicenter AS location, magnitude, intensity, lat, lon FROM all_jp_earthquakes LIMIT ${limit}`
      : `SELECT date, time, magnitude, location, title, tsunami, lat, lon FROM all_earthquakes_week LIMIT ${limit}`;

  try {
    const rows = await executeQuery(sql, [], schema);
    const mapped = rows.map((row) => {
      const record = row as Record<string, unknown>;

      return {
        date: record.DATE ?? record.date ?? null,
        time: record.TIME ?? record.time ?? null,
        magnitude: record.MAGNITUDE ?? record.magnitude ?? null,
        location: record.LOCATION ?? record.location ?? record.EPICENTER ?? record.epicenter ?? null,
        title: record.TITLE ?? record.title ?? null,
        tsunami: record.TSUNAMI ?? record.tsunami ?? null,
        intensity: record.INTENSITY ?? record.intensity ?? null,
        lat: record.LAT ?? record.lat ?? null,
        lon: record.LON ?? record.lon ?? null,
      };
    });

    return Response.json(mapped);
  } catch (error) {
    if (isMissingTableError(error)) {
      return Response.json([]);
    }

    return Response.json({ error: String(error) }, { status: 500 });
  }
}

export async function POST(req: Request) {
  const url = new URL(req.url);
  const schema = resolveSchema(url.searchParams.get("schema") || process.env.SNOWFLAKE_SCHEMA || "GLOBAL");

  try {
    const result =
      schema === "JP"
        ? await refreshJapaneseOverallEarthquakes(schema)
        : await refreshGlobalOverallEarthquakes(schema);

    return Response.json(result);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}