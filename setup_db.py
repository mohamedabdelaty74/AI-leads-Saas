"""
PostgreSQL Database Setup Script
Creates database and user for Elite Creatif
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

# PostgreSQL admin credentials
ADMIN_USER = "postgres"
ADMIN_PASSWORD = "TestUser123"
ADMIN_HOST = "localhost"
ADMIN_PORT = 5432

# New database configuration
DB_NAME = "elite_creatif_saas"
DB_USER = "elite_creatif_user"
DB_PASSWORD = "EliteCreatif2025!SecurePass"

def create_database():
    """Create the PostgreSQL database and user"""

    print("=" * 60)
    print("Elite Creatif - PostgreSQL Setup")
    print("=" * 60)

    try:
        # Connect to PostgreSQL server (default database 'postgres')
        print("\n[1/5] Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            dbname="postgres",
            user=ADMIN_USER,
            password=ADMIN_PASSWORD,
            host=ADMIN_HOST,
            port=ADMIN_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("[OK] Connected successfully!")

        # Check if database exists
        print(f"\n[2/5] Checking if database '{DB_NAME}' exists...")
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()

        if exists:
            print(f"⚠ Database '{DB_NAME}' already exists. Dropping...")
            # Terminate existing connections
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{DB_NAME}'
                AND pid <> pg_backend_pid();
            """)
            cursor.execute(f"DROP DATABASE {DB_NAME}")
            print("[OK] Dropped existing database")

        # Create database
        print(f"\n[3/5] Creating database '{DB_NAME}'...")
        cursor.execute(f"CREATE DATABASE {DB_NAME} ENCODING 'UTF8'")
        print("[OK] Database created successfully!")

        # Close connection to postgres database
        cursor.close()
        conn.close()

        # Connect to new database to set up extensions
        print(f"\n[4/5] Setting up database extensions...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=ADMIN_USER,
            password=ADMIN_PASSWORD,
            host=ADMIN_HOST,
            port=ADMIN_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Create UUID extension
        cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        print("[OK] UUID extension enabled")

        # Check if user exists
        print(f"\n[5/5] Creating application user '{DB_USER}'...")
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (DB_USER,)
        )
        user_exists = cursor.fetchone()

        if user_exists:
            print(f"⚠ User '{DB_USER}' already exists. Dropping...")
            cursor.execute(f"DROP USER {DB_USER}")

        # Create application user
        cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
        print(f"[OK] User '{DB_USER}' created")

        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
        cursor.execute(f"GRANT ALL ON SCHEMA public TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER}")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER}")
        print("[OK] Privileges granted")

        # Close connections
        cursor.close()
        conn.close()

        # Success summary
        print("\n" + "=" * 60)
        print("[SUCCESS] PostgreSQL Setup Completed Successfully!")
        print("=" * 60)
        print(f"\nDatabase Configuration:")
        print(f"  Database: {DB_NAME}")
        print(f"  User:     {DB_USER}")
        print(f"  Password: {DB_PASSWORD}")
        print(f"  Host:     {ADMIN_HOST}")
        print(f"  Port:     {ADMIN_PORT}")
        print(f"\nConnection String:")
        print(f"  postgresql://{DB_USER}:{DB_PASSWORD}@{ADMIN_HOST}:{ADMIN_PORT}/{DB_NAME}")
        print("\n" + "=" * 60)

        return True

    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        print(f"\nError Details:")
        print(f"  Code: {e.pgcode}")
        print(f"  Message: {e.pgerror}")
        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
