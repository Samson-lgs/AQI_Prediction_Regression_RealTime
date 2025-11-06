"""
Quick test script to validate DATABASE_URL and test connection.

Usage:
    $env:DATABASE_URL='postgres://...'
    python scripts\test_db_connection.py
"""

import os
import sys
from urllib.parse import urlparse

def validate_database_url():
    """Validate DATABASE_URL format and components."""
    print("\n" + "="*80)
    print("DATABASE_URL VALIDATOR & CONNECTION TESTER")
    print("="*80 + "\n")
    
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable is not set!\n")
        print("To set it in PowerShell:")
        print("  $env:DATABASE_URL='postgres://user:pass@host.render.com/dbname'\n")
        return False
    
    print(f"✓ DATABASE_URL is set\n")
    
    # Parse URL
    try:
        result = urlparse(database_url)
    except Exception as e:
        print(f"❌ Failed to parse DATABASE_URL: {e}\n")
        return False
    
    # Check components
    print("📋 Parsed Components:")
    print(f"   Scheme:   {result.scheme}")
    print(f"   Username: {result.username}")
    print(f"   Password: {'*' * len(result.password) if result.password else 'MISSING'}")
    print(f"   Hostname: {result.hostname}")
    print(f"   Port:     {result.port or 5432}")
    print(f"   Database: {result.path[1:] if result.path else 'MISSING'}")
    print()
    
    # Validate components
    issues = []
    
    if result.scheme not in ['postgres', 'postgresql']:
        issues.append(f"❌ Invalid scheme: '{result.scheme}' (should be 'postgres' or 'postgresql')")
    
    if not result.username:
        issues.append("❌ Username is missing")
    
    if not result.password:
        issues.append("❌ Password is missing")
    
    if not result.hostname:
        issues.append("❌ Hostname is missing")
    elif not result.hostname.endswith('.render.com'):
        issues.append(f"⚠️  Hostname doesn't end with '.render.com': {result.hostname}")
        issues.append("   This might indicate a truncated URL")
        issues.append("   Expected format: dpg-xxxxx.oregon-postgres.render.com")
    
    if not result.path or result.path == '/':
        issues.append("❌ Database name is missing")
    
    if issues:
        print("⚠️  Issues Found:")
        for issue in issues:
            print(f"   {issue}")
        print()
        return False
    
    print("✅ All components look valid!\n")
    
    # Try to connect
    print("🔌 Testing connection...")
    try:
        import psycopg2
        
        conn_params = {
            'host': result.hostname,
            'database': result.path[1:],
            'user': result.username,
            'password': result.password,
            'port': result.port or 5432,
            'connect_timeout': 10
        }
        
        print(f"   Connecting to {result.hostname}...")
        conn = psycopg2.connect(**conn_params)
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print(f"\n✅ CONNECTION SUCCESSFUL!")
        print(f"\n📊 Database Info:")
        print(f"   PostgreSQL Version: {version.split(',')[0]}")
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"   Tables found: {len(tables)}")
            for table in tables:
                print(f"      - {table[0]}")
        else:
            print("   No tables found (database might be new)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ Ready to run: python scripts\\view_render_db_data.py")
        print("="*80 + "\n")
        
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed!")
        print("   Install it with: pip install psycopg2-binary\n")
        return False
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}\n")
        print("Troubleshooting:")
        print("  1. Make sure you copied the INTERNAL Database URL (not External)")
        print("  2. Check that the URL is complete and not truncated")
        print("  3. Verify your database is running in Render Dashboard")
        print("  4. Try copying the URL again using the Copy button\n")
        return False


if __name__ == '__main__':
    success = validate_database_url()
    sys.exit(0 if success else 1)
