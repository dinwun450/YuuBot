import { executeQuery, type SnowflakeSchema } from "../../../../lib/snowflake";
import {
  refreshGlobalCoordinateEarthquakes,
  refreshJapaneseCoordinateEarthquakes,
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
      ? `SELECT lat, lon FROM jp_earthquakes_coords WHERE lat IS NOT NULL AND lon IS NOT NULL LIMIT ${limit}`
      : `SELECT lat, lon FROM all_earthquakes_week_coords WHERE lat IS NOT NULL AND lon IS NOT NULL LIMIT ${limit}`;

  try {
    const rows = await executeQuery(sql, [], schema);
    const mapped = rows.map((row) => {
      const record = row as Record<string, unknown>;

      return {
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
        ? await refreshJapaneseCoordinateEarthquakes(schema)
        : await refreshGlobalCoordinateEarthquakes(schema);

    return Response.json(result);
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 });
  }
}