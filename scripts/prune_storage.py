import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor


def log(msg: str):
    print(msg, flush=True)


def get_db_size_bytes(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT pg_database_size(current_database())")
        (size_bytes,) = cur.fetchone()
        return int(size_bytes)


def human_bytes(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def delete_older_than(conn, table: str, ts_col: str, days: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {table} WHERE {ts_col} < NOW() - INTERVAL %s",
            (f"{days} days",),
        )
        deleted = cur.rowcount
    conn.commit()
    return deleted


def prune_in_batches(conn, table: str, ts_col: str, batch_rows: int) -> int:
    """Delete oldest rows in batches using an indexed id selection."""
    with conn.cursor() as cur:
        cur.execute(
            f"""
            WITH old AS (
              SELECT id FROM {table}
              ORDER BY {ts_col} ASC
              LIMIT %s
            )
            DELETE FROM {table} t
            WHERE t.id IN (SELECT id FROM old);
            """,
            (batch_rows,),
        )
        deleted = cur.rowcount
    conn.commit()
    return deleted


def maybe_vacuum(conn, full: bool = False):
    with conn.cursor() as cur:
        if full:
            log("Running VACUUM FULL (this may lock tables)...")
            cur.execute("VACUUM FULL")
        else:
            log("Running VACUUM (ANALYZE)...")
            cur.execute("VACUUM (ANALYZE)")
    conn.commit()


def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        log("ERROR: DATABASE_URL is required")
        sys.exit(1)

    storage_gb = float(os.getenv("DB_STORAGE_GB", "1"))
    threshold_pct = int(os.getenv("RETENTION_THRESHOLD_PCT", "85"))
    target_pct = int(os.getenv("RETENTION_TARGET_PCT", "75"))
    allow_vacuum_full = os.getenv("ALLOW_VACUUM_FULL", "0") == "1"

    capacity_bytes = int(storage_gb * (1024 ** 3))

    log(
        f"Pruner starting with capacity={storage_gb} GB, threshold={threshold_pct}%, target={target_pct}%"
    )

    conn = psycopg2.connect(db_url)
    try:
        used = get_db_size_bytes(conn)
        usage_pct = (used / capacity_bytes) * 100 if capacity_bytes > 0 else 0
        log(f"Current DB size: {human_bytes(used)} ({usage_pct:.1f}% of {storage_gb} GB)")

        if usage_pct < threshold_pct:
            log("Below threshold; no pruning needed.")
            return

        # Try age-based pruning with progressively tighter windows
        windows = [180, 120, 90, 60, 45, 30, 21, 14, 7, 3, 1]
        total_deleted = 0
        for days in windows:
            log(f"Pruning rows older than {days} days...")
            deleted = 0
            deleted += delete_older_than(conn, "pollution_data", "timestamp", days)
            deleted += delete_older_than(conn, "weather_data", "timestamp", days)
            deleted += delete_older_than(conn, "predictions", "forecast_timestamp", days)
            deleted += delete_older_than(conn, "model_performance", "metric_date", days)
            deleted += delete_older_than(conn, "city_statistics", "metric_date", days)
            deleted += delete_older_than(conn, "region_statistics", "metric_date", days)
            total_deleted += deleted
            log(f"Deleted {deleted} rows for cutoff {days} days")

            maybe_vacuum(conn, full=False)
            time.sleep(1)

            used = get_db_size_bytes(conn)
            usage_pct = (used / capacity_bytes) * 100 if capacity_bytes > 0 else 0
            log(
                f"After pruning {days}d: size={human_bytes(used)} ({usage_pct:.1f}% of {storage_gb} GB)"
            )
            if usage_pct <= target_pct:
                break

        if usage_pct > target_pct and allow_vacuum_full:
            # As a last resort, attempt VACUUM FULL on the two largest tables
            log("Usage still high; attempting VACUUM FULL on main tables...")
            with conn.cursor() as cur:
                cur.execute("VACUUM FULL pollution_data")
                cur.execute("VACUUM FULL weather_data")
            conn.commit()
            used = get_db_size_bytes(conn)
            usage_pct = (used / capacity_bytes) * 100 if capacity_bytes > 0 else 0
            log(
                f"After VACUUM FULL: size={human_bytes(used)} ({usage_pct:.1f}% of {storage_gb} GB)"
            )

        if usage_pct > threshold_pct:
            log(
                "WARNING: Still above threshold after pruning. Consider increasing DB storage or reducing retention."
            )
        else:
            log(
                f"Pruning complete. Total rows deleted: {total_deleted}. Current usage: {usage_pct:.1f}%"
            )

    finally:
        conn.close()


if __name__ == "__main__":
    main()
