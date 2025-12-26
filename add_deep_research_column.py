"""
Quick script to add deep_research column to campaign_leads table
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Add the deep_research column
    cursor.execute("ALTER TABLE campaign_leads ADD COLUMN IF NOT EXISTS deep_research TEXT;")

    conn.commit()
    print("Successfully added deep_research column to campaign_leads table")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
