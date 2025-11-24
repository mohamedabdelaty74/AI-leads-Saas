"""Show all tables in the database"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import Base, engine

print("=" * 60)
print("DATABASE TABLES")
print("=" * 60)
print()

for table in Base.metadata.sorted_tables:
    print(f"[+] {table.name}")
    print(f"    Columns:")
    for col in table.columns:
        nullable = "NULL" if col.nullable else "NOT NULL"
        primary = " [PRIMARY KEY]" if col.primary_key else ""
        print(f"      - {col.name}: {col.type} {nullable}{primary}")
    print()

print("=" * 60)
print(f"Total: {len(Base.metadata.sorted_tables)} tables created")
print("=" * 60)
