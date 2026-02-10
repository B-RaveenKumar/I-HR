#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Get ALL tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = cursor.fetchall()

print(f"\n=== TOTAL TABLES: {len(all_tables)} ===\n")

# Find timetable-related
timetable_tables = [t for t in all_tables if 'timetable' in t[0].lower() or 'assignment' in t[0].lower()]

if timetable_tables:
    print("✅ TIMETABLE-RELATED TABLES FOUND:\n")
    for table in timetable_tables:
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        row_count = cursor.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        print(f"  📊 {table[0]}")
        print(f"     Rows: {row_count}, Columns: {len(columns)}")
else:
    print("❌ NO TIMETABLE-RELATED TABLES FOUND\n")
    print("Available tables:")
    for table in all_tables[:20]:
        print(f"  - {table[0]}")

conn.close()
