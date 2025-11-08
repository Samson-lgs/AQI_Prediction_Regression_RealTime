import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import argparse
from datetime import datetime, timedelta

# Prefer DATABASE_URL (Render/Heroku style). Fallback to DB_* env vars.
database_url = os.getenv('DATABASE_URL')
if database_url:
    parsed = urlparse(database_url)
    conn_args = dict(
        host=parsed.hostname,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        port=parsed.port or 5432
    )
else:
    conn_args = dict(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'aqi_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

print("Connecting with:", {k: (v if k != 'password' else '***') for k,v in conn_args.items()})

# CLI arguments for filtering
parser = argparse.ArgumentParser(description="Export pollution_data from Render/PostgreSQL")
parser.add_argument("--days", type=int, default=None, help="Limit to last N days (e.g., 30)")
parser.add_argument("--city", type=str, default=None, help="Filter by specific city name")
parser.add_argument("--limit", type=int, default=None, help="Limit number of rows (e.g., 50000)")
parser.add_argument("--outfile", type=str, default=None, help="Output CSV path (default: render_pollution_data.csv)")
parser.add_argument("--sslmode", type=str, default=None, help="SSL mode for PostgreSQL (e.g., require)")
args = parser.parse_args()

# Many managed providers require SSL; default to require when DATABASE_URL is used
connect_kwargs = conn_args.copy()
if args.sslmode:
    connect_kwargs["sslmode"] = args.sslmode
elif database_url:
    connect_kwargs["sslmode"] = "require"

conn = psycopg2.connect(**connect_kwargs)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Build WHERE clause
where_clauses = []
params = []
if args.days and args.days > 0:
    # Use NOW() - interval for server-side; no params needed
    where_clauses.append(f"timestamp >= NOW() - INTERVAL '{args.days} days'")
if args.city:
    where_clauses.append("city = %s")
    params.append(args.city)

where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
limit_sql = f" LIMIT {int(args.limit)}" if args.limit and args.limit > 0 else ""

query = f"""
SELECT id, city, timestamp, pm25, pm10, no2, so2, co, o3, aqi_value, data_source, created_at
FROM pollution_data
{where_sql}
ORDER BY timestamp DESC{limit_sql};
"""

print("Running export query...")
cur.execute(query, params if params else None)
rows = cur.fetchall()
print(f"Fetched {len(rows)} rows from pollution_data")

# Convert to DataFrame and save
df = pd.DataFrame([dict(r) for r in rows])
out_name = args.outfile or 'render_pollution_data.csv'
output_path = os.path.join(os.path.dirname(__file__), '..', out_name)
df.to_csv(output_path, index=False)
print(f"Saved to {os.path.abspath(output_path)}")

cur.close()
conn.close()
print("Done.")
