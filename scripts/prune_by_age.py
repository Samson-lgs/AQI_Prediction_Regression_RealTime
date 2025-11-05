import os
import sys
import time
import psycopg2
import psycopg2.extensions


def log(msg: str):
    print(msg, flush=True)


def delete_older_than(conn, table: str, col: str, is_date: bool, days: int) -> int:
    """
    Delete rows older than N days based on a timestamp or date column.
    """
    with conn.cursor() as cur:
        if is_date:
            cur.execute(
                f"DELETE FROM {table} WHERE {col} < (CURRENT_DATE - INTERVAL %s)",
                (f"{days} days",),
            )
        else:
            cur.execute(
                f"DELETE FROM {table} WHERE {col} < (NOW() - INTERVAL %s)",
                (f"{days} days",),
            )
        deleted = cur.rowcount
    conn.commit()
    return deleted


def maybe_vacuum(conn, full: bool = False):
    # VACUUM must run outside a transaction block
    old_isolation = conn.isolation_level
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            if full:
                log("Running VACUUM FULL (may lock tables)...")
                cur.execute("VACUUM FULL")
            else:
                log("Running VACUUM (ANALYZE)...")
                cur.execute("VACUUM (ANALYZE)")
    finally:
        conn.set_isolation_level(old_isolation)


def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        log("ERROR: DATABASE_URL is required")
        sys.exit(1)

    days = int(os.getenv("RETENTION_DAYS", "90"))
    vacuum_analyze = os.getenv("VACUUM_ANALYZE", "1") == "1"
    vacuum_full = os.getenv("VACUUM_FULL", "0") == "1"

    log(f"Prune-by-age starting. RETENTION_DAYS={days}")

    conn = psycopg2.connect(db_url)
    try:
        total = 0

        # Timestamp-based tables
        total += delete_older_than(conn, "pollution_data", "timestamp", False, days)
        total += delete_older_than(conn, "weather_data", "timestamp", False, days)
        total += delete_older_than(conn, "predictions", "forecast_timestamp", False, days)

        # Date-based tables
        total += delete_older_than(conn, "model_performance", "metric_date", True, days)
        total += delete_older_than(conn, "city_statistics", "metric_date", True, days)
        total += delete_older_than(conn, "region_statistics", "metric_date", True, days)

        log(f"Deleted rows older than {days} days: {total}")

        if vacuum_analyze or vacuum_full:
            maybe_vacuum(conn, full=vacuum_full)

        log("Prune-by-age complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
