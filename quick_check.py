#!/usr/bin/env python
"""Quick check of staff and periods"""

import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

db = sqlite3.connect(DATABASE)
cursor = db.cursor()

# Check staff by school
print("=" * 60)
print("STAFF BY SCHOOL")
print("=" * 60)
cursor.execute('SELECT DISTINCT school_id, COUNT(*) FROM staff GROUP BY school_id')
for school_id, count in cursor.fetchall():
    print(f"School {school_id}: {count} staff")

# Check periods
print("\n" + "=" * 60)
print("PERIODS")
print("=" * 60)
cursor.execute('SELECT COUNT(*) FROM timetable_periods')
print(f"Total periods: {cursor.fetchone()[0]}")

# Check which schools have periods
cursor.execute('SELECT DISTINCT school_id FROM timetable_periods')
schools_with_periods = [row[0] for row in cursor.fetchall()]
print(f"Schools with periods: {schools_with_periods}")

db.close()
print("\n✓ Done")
