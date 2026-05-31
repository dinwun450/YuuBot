import os
import snowflake.connector
import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# quick sanity check (do not print secrets)
REQUIRED_ENV = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
]
missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
if missing:
    print(f"Warning: missing env vars: {missing}. .env not loaded or keys absent.")

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
MAG_CUTOFF = 2.5

def fetch_geojson(url: str, timeout: int = 10) -> dict:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def ms_to_iso(ms):
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat()
    except Exception:
        return ""

def upload_csv_to_snowflake_stage(local_path: Path, stage_name: str = "EARTHQUAKE_STAGE"):
    """
    Upload local_path to an internal Snowflake stage using the connector's PUT command.
    Requires these env vars: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,
    SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA. Optional: SNOWFLAKE_ROLE.
    """
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA")

    if not all([account, user, password, warehouse, database, schema]):
        raise RuntimeError(
            "Missing Snowflake env vars. Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, "
            "SNOWFLAKE_PASSWORD, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA. "
            "DO IT RIGHT AWAY!"
        )

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database=database,
        schema=schema
    )
    cur = conn.cursor()
    try:
        # ensure stage exists and create a simple CSV file format
        cur.execute(
            f"CREATE STAGE IF NOT EXISTS {stage_name} "
            "FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1 "
            "FIELD_OPTIONALLY_ENCLOSED_BY = '\"')"
        )

        p = local_path.resolve()
        # use a proper file URI for PUT; Path.as_uri() yields file:///... on Windows and file://... on Unix
        file_uri = p.as_uri()

        # PUT the file to the named stage; overwrite if exists
        cur.execute(f"PUT '{file_uri}' @{stage_name} AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
        # list files to confirm
        cur.execute(f"LIST @{stage_name}")
        rows = cur.fetchall()
        print("Stage contents:")
        for r in rows:
            print(r)
    finally:
        cur.close()
        conn.close()

def save_features_to_csv(features: list, out_path: Path):
    # gather all property keys
    prop_keys = set()
    for f in features:
        prop_keys.update(f.get("properties", {}).keys())

    # ensure deterministic order, but keep 'time' early if present
    sorted_props = sorted(k for k in prop_keys if k != "time")
    if "time" in prop_keys:
        sorted_props.insert(0, "time")

    headers = ["id"] + sorted_props + ["time_iso", "longitude", "latitude", "depth"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()

        for f in features:
            row = {}
            fid = f.get("id", "")
            props = f.get("properties", {}) or {}
            geom = f.get("geometry", {}) or {}
            coords = geom.get("coordinates", []) or []

            # basic fields
            row["id"] = fid
            for k in sorted_props:
                row[k] = props.get(k, "")

            # time ISO conversion if available
            if "time" in props and props.get("time") is not None:
                try:
                    row["time_iso"] = ms_to_iso(int(props.get("time")))
                except Exception:
                    row["time_iso"] = ""
            else:
                row["time_iso"] = ""

            # coordinates: [lon, lat, depth]
            row["longitude"] = coords[0] if len(coords) > 0 else ""
            row["latitude"] = coords[1] if len(coords) > 1 else ""
            row["depth"] = coords[2] if len(coords) > 2 else ""

            writer.writerow(row)

def _mag_at_least(feature, cutoff):
    try:
        mag = feature.get("properties", {}).get("mag")
        if mag is None:
            return False
        return float(mag) >= cutoff
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="Download USGS monthly earthquakes to CSV")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("all_month.csv"),
        help="Output CSV file (default: all_month.csv)",
    )
    parser.add_argument(
        "--upload-stage",
        action="store_true",
        help="Upload the generated CSV to Snowflake stage EARTHQUAKE_STAGE (env vars required)",
    )
    args = parser.parse_args()

    try:
        data = fetch_geojson(USGS_URL)
    except Exception as e:
        print(f"Failed to download GeoJSON: {e}", file=sys.stderr)
        sys.exit(1)

    all_features = data.get("features", [])
    features = [f for f in all_features if _mag_at_least(f, MAG_CUTOFF)]

    save_features_to_csv(features, args.output)
    print(f"Wrote {len(features)} features (mag >= {MAG_CUTOFF}) to {args.output}")

    if args.upload_stage:
        try:
            upload_csv_to_snowflake_stage(args.output, stage_name="EARTHQUAKE_STAGE")
            print("Upload to Snowflake stage completed successfully.")
        except Exception as e:
            print(f"Failed to upload to Snowflake stage: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        print("Upload to Snowflake stage not requested; skipping.")

if __name__ == "__main__":
    main()