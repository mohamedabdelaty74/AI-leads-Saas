#!/usr/bin/env python3
"""
Database Reset Script
Drops all tables and recreates them with the latest schema
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from models.base import Base, engine
from models.tenant import Tenant
from models.user import User
from models.campaign import Campaign, CampaignLead

def reset_database():
    """Drop all tables and recreate them"""
    print("=" * 60)
    print("DATABASE RESET")
    print("=" * 60)
    print()

    # Confirm action
    print("WARNING: This will DELETE ALL DATA in the database!")
    print(f"Database: {os.getenv('DATABASE_URL', 'Not set')}")
    print()

    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("[CANCELLED] Operation cancelled")
        return

    print()
    print("Dropping all tables...")
    try:
        # Drop all tables with CASCADE to handle foreign key dependencies
        from sqlalchemy import text
        with engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]

            # Drop each table with CASCADE
            for table in tables:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            conn.commit()

        print("[OK] All tables dropped")
    except Exception as e:
        print(f"[ERROR] Error dropping tables: {e}")
        return

    print()
    print("Creating tables with new schema...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created")
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        return

    print()
    print("=" * 60)
    print("[SUCCESS] DATABASE RESET COMPLETE")
    print("=" * 60)
    print()
    print("Tables created:")
    print("  - tenants")
    print("  - users")
    print("  - campaigns")
    print("  - campaign_leads")
    print()

if __name__ == "__main__":
    reset_database()
