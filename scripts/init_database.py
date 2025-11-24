"""
Initialize the database and create all tables

🎓 TEACHING: How to run this
1. Open terminal
2. Run: python scripts/init_database.py
3. This creates elite_creatif_production.db with all tables
"""

import sys
import os

# Add parent directory to path so we can import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import Base, engine, init_db
from models.tenant import Tenant
from models.user import User
from models.campaign import Campaign, CampaignLead
from models.email import Email, EmailEvent
from models.whatsapp import WhatsAppTemplate, WhatsAppMessage

def main():
    print("=" * 60)
    print("Elite Creatif - Database Initialization")
    print("=" * 60)
    print()
    print("Creating tables...")
    print()

    # Create all tables
    init_db()

    print()
    print("=" * 60)
    print("Tables created:")
    print("=" * 60)
    for table in Base.metadata.sorted_tables:
        print(f"  ✅ {table.name}")

    print()
    print("=" * 60)
    print("SUCCESS! Database is ready to use.")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run: python scripts/create_demo_data.py")
    print("  2. Start API: python backend/main.py")
    print()

if __name__ == "__main__":
    main()
