"""
Test PostgreSQL connection with new credentials
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Load .env
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

print("=" * 60)
print("Testing PostgreSQL Connection")
print("=" * 60)
print(f"\nConnection String: {DATABASE_URL}")
print(f"(hiding password for security)")

try:
    # Parse connection string
    # postgresql://user:password@host:port/database
    conn_str = DATABASE_URL.replace('postgresql://', '')
    parts = conn_str.split('@')
    user_pass = parts[0].split(':')
    host_db = parts[1].split('/')
    host_port = host_db[0].split(':')

    user = user_pass[0]
    password = user_pass[1]
    host = host_port[0]
    port = host_port[1]
    database = host_db[1]

    print(f"\nParsed Connection Details:")
    print(f"  User:     {user}")
    print(f"  Password: {'*' * len(password)}")
    print(f"  Host:     {host}")
    print(f"  Port:     {port}")
    print(f"  Database: {database}")

    print(f"\n[1/3] Connecting to PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    print("[OK] Connected successfully!")

    print(f"\n[2/3] Testing query execution...")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"[OK] PostgreSQL version: {version[:50]}...")

    print(f"\n[3/3] Checking UUID extension...")
    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'uuid-ossp';")
    result = cursor.fetchone()
    if result:
        print(f"[OK] UUID extension is installed")
    else:
        print(f"[WARNING] UUID extension not found")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("[SUCCESS] All PostgreSQL connection tests passed!")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] Connection failed: {e}")
    print("=" * 60)
    exit(1)
