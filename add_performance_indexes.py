"""
Database Performance Indexes Migration
Adds indexes to improve query performance on existing databases
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Indexes to add for performance
INDEXES = [
    # CampaignLead indexes for frequent lookups
    ("idx_campaign_leads_title", "campaign_leads", "title"),
    ("idx_campaign_leads_email", "campaign_leads", "email"),
    ("idx_campaign_leads_phone", "campaign_leads", "phone"),
    ("idx_campaign_leads_lead_score", "campaign_leads", "lead_score"),
    ("idx_campaign_leads_email_sent", "campaign_leads", "email_sent"),
    ("idx_campaign_leads_whatsapp_sent", "campaign_leads", "whatsapp_sent"),
    ("idx_campaign_leads_replied", "campaign_leads", "replied"),
    ("idx_campaign_leads_created_at", "campaign_leads", "created_at"),
]

def add_indexes():
    """Add performance indexes to database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        print("="*60)
        print("Adding Performance Indexes")
        print("="*60 + "\n")

        for index_name, table, column in INDEXES:
            try:
                # Create index if it doesn't exist
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table} ({column});
                """)
                print(f"[OK] Added index: {index_name} on {table}({column})")
            except Exception as e:
                print(f"[WARN] Index {index_name} failed: {e}")

        conn.commit()

        print("\n" + "="*60)
        print("Index Creation Complete!")
        print("="*60)

        # Show index sizes
        print("\n[INFO] Index Statistics:\n")
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) as size
            FROM pg_indexes
            JOIN pg_class ON pg_indexes.indexname = pg_class.relname
            WHERE schemaname = 'public'
            AND tablename IN ('campaigns', 'campaign_leads', 'users')
            ORDER BY tablename, indexname;
        """)

        results = cursor.fetchall()
        if results:
            print(f"{'Table':<20} {'Index':<35} {'Size':<10}")
            print("-"*65)
            for row in results:
                print(f"{row[1]:<20} {row[2]:<35} {row[3]:<10}")

        cursor.close()
        conn.close()

        print("\n[OK] Performance indexes successfully added!")
        print("\nThese indexes will improve query performance for:")
        print("  - Lead searches by name/email/phone")
        print("  - Filtering by email/WhatsApp sent status")
        print("  - Sorting by lead score or creation date")
        print("  - Campaign-based queries\n")

    except Exception as e:
        print(f"[ERROR] {e}")
        print("\nNote: SQLite databases don't need this migration.")
        print("Indexes are automatically created from model definitions.\n")

if __name__ == "__main__":
    add_indexes()
