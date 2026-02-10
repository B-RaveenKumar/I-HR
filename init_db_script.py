#!/usr/bin/env python3
import sys
sys.path.insert(0, 'd:/VISHNRX/ProjectVX')
from app import app
from database import init_db

with app.app_context():
    init_db(app)
    print('✅ Database initialized')

# Verify tables
import sqlite3
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%timetable%' OR name LIKE '%assignment%')")
tables = cursor.fetchall()
print("\nVerified Tables:")
for table in tables:
    print(f"  ✅ {table[0]}")
conn.close()
