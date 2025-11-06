"""
View data stored in PostgreSQL database on Render.

This script connects to your Render PostgreSQL database and displays
the stored data in various formats.

Usage:
    # Using DATABASE_URL (recommended for Render)
    $env:DATABASE_URL='postgres://user:pass@host:5432/aqi_db'
    python scripts\view_render_db_data.py

    # Or using individual environment variables
    $env:DB_HOST='dpg-xxx.oregon-postgres.render.com'
    $env:DB_NAME='aqi_db'
    $env:DB_USER='aqi_user'
    $env:DB_PASSWORD='your_password'
    python scripts\view_render_db_data.py
"""

import os
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from tabulate import tabulate
except ImportError as e:
    print(f"Missing required package: {e}")
    print("\nInstall required packages:")
    print("  pip install psycopg2-binary tabulate")
    sys.exit(1)


def get_db_connection():
    """Get database connection using environment variables."""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Parse DATABASE_URL (common on Render, Heroku)
        result = urlparse(database_url)
        
        # Validate hostname
        hostname = result.hostname
        if hostname and not hostname.endswith('.render.com') and not hostname.endswith('.postgres.render.com'):
            print(f"\n⚠️  WARNING: Hostname looks incomplete: {hostname}")
            print(f"   Expected format: dpg-xxxxx.oregon-postgres.render.com")
            print(f"   Your URL might be truncated or incorrect.\n")
        
        conn_params = {
            'host': hostname,
            'database': result.path[1:],  # Remove leading '/'
            'user': result.username,
            'password': result.password,
            'port': result.port or 5432,
        }
        print(f"✓ Connecting using DATABASE_URL to {hostname}...")
    else:
        # Use individual environment variables
        conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'aqi_db'),
            'user': os.getenv('DB_USER', 'aqi_user'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', 5432)),
        }
        
        if not conn_params['password']:
            raise RuntimeError(
                '''Database password not provided. Set one of:
  1. DATABASE_URL (recommended for Render):
     $env:DATABASE_URL='postgres://user:pass@host:5432/aqi_db'
     
  2. Individual variables:
     $env:DB_HOST='dpg-xxx.oregon-postgres.render.com'
     $env:DB_PASSWORD='your_password'
     
Then run:
  python scripts\\view_render_db_data.py
'''
            )
        print(f"✓ Connecting to {conn_params['host']}...")
    
    try:
        conn = psycopg2.connect(**conn_params)
        print(f"✓ Connected to database: {conn_params['database']}\n")
        return conn
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print(f"\n✗ Connection failed: {error_msg}")
        print("\n" + "="*80)
        print("TROUBLESHOOTING GUIDE")
        print("="*80)
        
        if "Unknown host" in error_msg or "translate host name" in error_msg:
            print("\n❌ HOSTNAME ISSUE DETECTED")
            print("\nThe hostname in your DATABASE_URL is incomplete or incorrect.")
            print("\n📋 How to get the CORRECT Internal Database URL:")
            print("   1. Go to: https://dashboard.render.com/")
            print("   2. Click on your database: 'aqi-database' or 'aqi_db_gr7o'")
            print("   3. Click the 'Info' or 'Connect' tab")
            print("   4. Find 'Internal Database URL' (NOT External)")
            print("   5. Click 'Copy' button (don't type it manually!)")
            print("\n✅ Correct format example:")
            print("   postgres://aqi_user:password@dpg-xxxxx.oregon-postgres.render.com/aqi_db")
            print("                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            print("                                  Must end with .render.com")
            print("\n❌ Your current hostname seems to be:")
            if database_url:
                result = urlparse(database_url)
                print(f"   {result.hostname}")
                print("\n💡 This looks truncated. Please copy the FULL URL from Render Dashboard.")
        else:
            print("\n📋 Troubleshooting steps:")
            print("  1. Get your DATABASE_URL from Render Dashboard:")
            print("     Dashboard → Database → Info → Internal Database URL")
            print("  2. Make sure to copy the COMPLETE URL (use the Copy button)")
            print("  3. Set it in PowerShell:")
            print("     $env:DATABASE_URL='postgres://...'")
            print("  4. Run this script again")
        
        print("\n" + "="*80)
        sys.exit(1)


def get_table_info(conn):
    """Get information about all tables."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                table_name,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        return cur.fetchall()


def get_table_row_count(conn, table_name):
    """Get row count for a specific table."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cur.fetchone()[0]


def view_pollution_data_summary(conn):
    """View summary of pollution_data table."""
    print("\n" + "="*80)
    print("POLLUTION DATA SUMMARY")
    print("="*80)
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Overall stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_rows,
                MIN(timestamp) as earliest_data,
                MAX(timestamp) as latest_data,
                COUNT(DISTINCT city) as unique_cities,
                COUNT(DISTINCT DATE_TRUNC('hour', timestamp)) as distinct_hours
            FROM pollution_data;
        """)
        stats = cur.fetchone()
        
        print(f"\nOverall Statistics:")
        print(f"  Total Records: {stats['total_rows']:,}")
        print(f"  Unique Cities: {stats['unique_cities']}")
        print(f"  Distinct Hours: {stats['distinct_hours']}")
        print(f"  Earliest Data: {stats['earliest_data']}")
        print(f"  Latest Data:   {stats['latest_data']}")
        
        # Per-city stats
        cur.execute("""
            SELECT 
                city,
                COUNT(*) as record_count,
                MIN(timestamp) as first_record,
                MAX(timestamp) as latest_record,
                COUNT(DISTINCT DATE_TRUNC('hour', timestamp)) as hours_collected
            FROM pollution_data
            GROUP BY city
            ORDER BY record_count DESC
            LIMIT 20;
        """)
        city_stats = cur.fetchall()
        
        print(f"\nPer-City Coverage (Top 20):")
        headers = ['City', 'Records', 'Hours', 'First Record', 'Latest Record']
        rows = []
        for row in city_stats:
            rows.append([
                row['city'],
                f"{row['record_count']:,}",
                row['hours_collected'],
                row['first_record'].strftime('%Y-%m-%d %H:%M') if row['first_record'] else 'N/A',
                row['latest_record'].strftime('%Y-%m-%d %H:%M') if row['latest_record'] else 'N/A'
            ])
        print(tabulate(rows, headers=headers, tablefmt='grid'))


def view_recent_pollution_data(conn, limit=10):
    """View most recent pollution data records."""
    print("\n" + "="*80)
    print(f"RECENT POLLUTION DATA (Last {limit} records)")
    print("="*80 + "\n")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                id,
                city,
                timestamp,
                aqi_value,
                pm25,
                pm10,
                data_source
            FROM pollution_data
            ORDER BY timestamp DESC
            LIMIT %s;
        """, (limit,))
        records = cur.fetchall()
        
        if not records:
            print("  No data found in pollution_data table.")
            return
        
        headers = ['ID', 'City', 'Timestamp', 'AQI', 'PM2.5', 'PM10', 'Source']
        rows = []
        for r in records:
            rows.append([
                r['id'],
                r['city'],
                r['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                r['aqi_value'] if r['aqi_value'] else 'N/A',
                f"{r['pm25']:.1f}" if r['pm25'] else 'N/A',
                f"{r['pm10']:.1f}" if r['pm10'] else 'N/A',
                r['data_source'] if r['data_source'] else 'N/A'
            ])
        print(tabulate(rows, headers=headers, tablefmt='grid'))


def view_predictions_summary(conn):
    """View summary of predictions table."""
    print("\n" + "="*80)
    print("PREDICTIONS SUMMARY")
    print("="*80)
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check if predictions table exists
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'predictions' AND table_schema = 'public';
        """)
        if cur.fetchone()['count'] == 0:
            print("\n  Predictions table does not exist yet.")
            return
        
        # Check if table has data
        cur.execute("SELECT COUNT(*) as count FROM predictions;")
        count = cur.fetchone()['count']
        
        if count == 0:
            print("\n  ℹ️  Predictions table exists but is currently empty.")
            print("     Predictions will be generated once models are trained.")
            return
        
        # If we have data, show stats (add later when schema is known)
        print(f"\n  Total Predictions: {count:,}")


def view_alerts_summary(conn):
    """View summary of alerts table."""
    print("\n" + "="*80)
    print("ALERTS SUMMARY")
    print("="*80)
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check if alerts table exists
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'alerts' AND table_schema = 'public';
        """)
        if cur.fetchone()['count'] == 0:
            print("\n  Alerts table does not exist yet.")
            return
        
        # Overall stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_alerts,
                COUNT(CASE WHEN active THEN 1 END) as active_alerts,
                COUNT(DISTINCT city) as cities_with_alerts
            FROM alerts;
        """)
        stats = cur.fetchone()
        
        print(f"\nOverall Statistics:")
        print(f"  Total Alerts: {stats['total_alerts']:,}")
        print(f"  Active Alerts: {stats['active_alerts']}")
        print(f"  Cities: {stats['cities_with_alerts']}")
        
        # Only show details if there are alerts
        if stats['total_alerts'] == 0:
            return
        
        # Recent alerts
        cur.execute("""
            SELECT 
                id,
                city,
                threshold_type,
                threshold_value,
                active,
                created_at,
                last_notified
            FROM alerts
            ORDER BY created_at DESC
            LIMIT 10;
        """)
        alerts = cur.fetchall()
        
        if alerts:
            print(f"\nRecent Alerts (Last 10):")
            headers = ['ID', 'City', 'Type', 'Threshold', 'Active', 'Created', 'Last Notified']
            rows = []
            for a in alerts:
                rows.append([
                    a['id'],
                    a['city'],
                    a['threshold_type'],
                    a['threshold_value'],
                    '✓' if a['active'] else '✗',
                    a['created_at'].strftime('%Y-%m-%d %H:%M'),
                    a['last_notified'].strftime('%Y-%m-%d %H:%M') if a['last_notified'] else 'Never'
                ])
            print(tabulate(rows, headers=headers, tablefmt='grid'))


def view_all_tables(conn):
    """View all tables and their row counts."""
    print("\n" + "="*80)
    print("DATABASE TABLES OVERVIEW")
    print("="*80 + "\n")
    
    tables = get_table_info(conn)
    
    if not tables:
        print("  No tables found in database.")
        return
    
    headers = ['Table Name', 'Columns', 'Row Count']
    rows = []
    for table in tables:
        table_name = table['table_name']
        row_count = get_table_row_count(conn, table_name)
        rows.append([
            table_name,
            table['column_count'],
            f"{row_count:,}"
        ])
    
    print(tabulate(rows, headers=headers, tablefmt='grid'))


def main():
    """Main function to display database contents."""
    print("\n" + "="*80)
    print("RENDER POSTGRESQL DATABASE VIEWER")
    print("="*80 + "\n")
    
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Display various views
        view_all_tables(conn)
        view_pollution_data_summary(conn)
        view_recent_pollution_data(conn, limit=15)
        view_predictions_summary(conn)
        view_alerts_summary(conn)
        
        print("\n" + "="*80)
        print("✓ Database inspection complete!")
        print("="*80 + "\n")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
