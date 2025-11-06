import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta


def get_conn():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    # Fallback to individual environment variables
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 5432))
    dbname = os.getenv('DB_NAME', 'aqi_db')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD')

    # Helpful error when password is missing to avoid psycopg2 low-level error
    if not password:
                raise RuntimeError(
                        '''Database password not provided. Set the DB_PASSWORD environment variable or provide a full DATABASE_URL (postgres://user:pass@host:port/dbname).
Example (PowerShell):
    $env:DB_PASSWORD='mypassword'
    .\\aqi_env\\Scripts\\python.exe scripts\\report_data_coverage.py
'''
                )

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )


def main():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Overall min/max and total rows
            cur.execute(
                """
                SELECT 
                  MIN(timestamp) AS earliest,
                  MAX(timestamp) AS latest,
                  COUNT(*) AS total_rows
                FROM pollution_data;
                """
            )
            overall = cur.fetchone()
            earliest = overall['earliest']
            latest = overall['latest']
            total_rows = overall['total_rows'] or 0

            if earliest and latest:
                span_hours = int((latest - earliest).total_seconds() // 3600)
            else:
                span_hours = 0

            # Distinct hour buckets overall
            cur.execute(
                """
                SELECT COUNT(*) AS hours
                FROM (
                  SELECT date_trunc('hour', timestamp) AS hour
                  FROM pollution_data
                  GROUP BY 1
                ) h;
                """
            )
            overall_hours = cur.fetchone()['hours'] if cur.rowcount is not None else 0

            # Per-city coverage summary (top 10 by distinct hours)
            cur.execute(
                """
                SELECT 
                  city,
                  COUNT(DISTINCT date_trunc('hour', timestamp)) AS hours_covered,
                  MIN(timestamp) AS first_seen,
                  MAX(timestamp) AS last_seen,
                  COUNT(*) AS rows
                FROM pollution_data
                GROUP BY city
                ORDER BY hours_covered DESC
                LIMIT 10;
                """
            )
            top_cities = cur.fetchall()

            # Coverage in last windows
            def coverage_window(hours):
                cur.execute(
                    """
                    SELECT 
                      city,
                      COUNT(DISTINCT date_trunc('hour', timestamp)) AS hours_present
                    FROM pollution_data
                    WHERE timestamp >= NOW() - INTERVAL %s
                    GROUP BY city
                    ORDER BY city;
                    """,
                    (f"{hours} hours",)
                )
                return cur.fetchall()

            cov_24h = coverage_window(24)
            cov_48h = coverage_window(48)
            cov_168h = coverage_window(168)

            print("==== DATA COVERAGE SUMMARY ====")
            print(f"Total rows: {total_rows}")
            print(f"Earliest sample: {earliest}")
            print(f"Latest sample:   {latest}")
            print(f"Span (hours):    {span_hours}")
            print(f"Distinct hours (overall): {overall_hours}")
            print()

            print("Top 10 cities by distinct hours covered:")
            for row in top_cities:
                print(f" - {row['city']}: {row['hours_covered']} hours, rows={row['rows']}, first={row['first_seen']}, last={row['last_seen']}")
            print()

            def summarize_coverage(rows, window):
                # Compute simple completeness = hours_present / window
                complete = [r for r in rows if r['hours_present'] >= window]
                print(f"Coverage window last {window}h: {len(rows)} cities with data; {len(complete)} cities fully covered ({window}/ {window})")
                # Show a few examples
                for r in rows[:10]:
                    pct = round(100 * (r['hours_present'] / window), 1)
                    print(f"   {r['city']}: {r['hours_present']}h ({pct}%)")
                print()

            summarize_coverage(cov_24h, 24)
            summarize_coverage(cov_48h, 48)
            summarize_coverage(cov_168h, 168)

            # Overall answer
            print("==== ANSWER ====")
            print(f"Approximate total distinct hourly buckets collected so far: {overall_hours}")
            if earliest and latest:
                print(f"Time span covered (from earliest to latest): ~{span_hours} hours")


if __name__ == '__main__':
    main()
