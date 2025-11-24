"""
Verify data is stored in PostgreSQL
"""

import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

print("=" * 60)
print("Verifying PostgreSQL Data")
print("=" * 60)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check tables
    print("\n[1/3] Checking tables...")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print(f"[OK] Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # Check users
    print("\n[2/3] Checking users table...")
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    print(f"[OK] Users in database: {user_count}")

    if user_count > 0:
        cursor.execute("""
            SELECT id, email, first_name, last_name, role, is_active, created_at
            FROM users
            LIMIT 5;
        """)
        users = cursor.fetchall()
        print("\nRecent users:")
        for user in users:
            print(f"  - {user[2]} {user[3]} ({user[1]}) - Role: {user[4]}")

    # Check tenants
    print("\n[3/3] Checking tenants table...")
    cursor.execute("SELECT COUNT(*) FROM tenants;")
    tenant_count = cursor.fetchone()[0]
    print(f"[OK] Tenants in database: {tenant_count}")

    if tenant_count > 0:
        cursor.execute("""
            SELECT id, name, company_email, status, plan
            FROM tenants
            LIMIT 5;
        """)
        tenants = cursor.fetchall()
        print("\nRecent tenants:")
        for tenant in tenants:
            print(f"  - {tenant[1]} ({tenant[2]}) - Plan: {tenant[4]}, Status: {tenant[3]}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("[SUCCESS] PostgreSQL verification complete!")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] Verification failed: {e}")
    exit(1)
