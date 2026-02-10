#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Check for timetable tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("=== DATABASE VERIFICATION ===\n")
print("Timetable-related tables:")
for table in tables:
    if 'timetable' in table[0].lower() or 'assignment' in table[0].lower():
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"\n✅ {table[0]}")
        print(f"   Columns: {len(columns)}")
        for col in columns:
            print(f"     - {col[1]} ({col[2]})")

conn.close()
