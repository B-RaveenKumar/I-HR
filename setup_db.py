#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
os.chdir('d:/VISHNRX/ProjectVX')
sys.path.insert(0, 'd:/VISHNRX/ProjectVX')
from app import app
from database import init_db

print("Initializing database...")

with app.app_context():
    init_db(app)
    print("[OK] Database initialized")

# Verify tables exist
import sqlite3
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print(f"\n[OK] Total tables: {len(tables)}")

# Check for timetable tables
timetable_tables = [t for t in tables if 'timetable' in t[0].lower() or 'assignment' in t[0].lower()]
print("\n[TABLES] Timetable-related tables:")
for table in timetable_tables:
    row_count = cursor.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
    print(f"  [OK] {table[0]} ({row_count} rows)")

conn.close()
print("\n[OK] Database verification complete!")
