#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os

os.chdir('d:/VISHNRX/ProjectVX')

db_path = 'instance/vishnorex.db'
if not os.path.exists(db_path):
    print(f"Database file not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = cursor.fetchall()

print(f"[INFO] Total tables: {len(all_tables)}")

# Find timetable-related tables
timetable_tables = [t for t in all_tables if 'timetable' in t[0].lower() or 'assignment' in t[0].lower()]

if timetable_tables:
    print("\n[OK] Timetable-related tables found:")
    for table in timetable_tables:
        row_count = cursor.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"  [TABLE] {table[0]}")
        print(f"          Rows: {row_count}, Columns: {len(columns)}")
else:
    print("\n[ERROR] No timetable-related tables found")

conn.close()
print("\n[OK] Verification complete")
