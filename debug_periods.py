import sqlite3
import os

db_path = 'instance/vishnorex.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
cursor = db.cursor()

print("TIMETABLE PERIODS TABLE INFO:")
cursor.execute("PRAGMA table_info(timetable_periods)")
for col in cursor.fetchall():
    print(dict(col))

print("\nTIMETABLE PERIODS DATA:")
cursor.execute("SELECT * FROM timetable_periods")
rows = cursor.fetchall()
for row in rows:
    print(dict(row))

db.close()
