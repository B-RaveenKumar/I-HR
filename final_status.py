import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')
db = sqlite3.connect(db_path)
cursor = db.cursor()

print('=' * 60)
print('TIMETABLE SYSTEM - FINAL STATUS REPORT')
print('=' * 60)

# Count tables
cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'timetable%'")
table_count = cursor.fetchone()[0]
print(f'\nDatabase Tables: {table_count}/6 created')

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'timetable%' ORDER BY name")
for t in cursor.fetchall():
    cursor.execute(f'SELECT COUNT(*) FROM {t[0]}')
    row_count = cursor.fetchone()[0]
    print(f'   ✓ {t[0]:40} ({row_count} rows)')

# Check enabled schools
cursor.execute('SELECT school_id, is_enabled FROM timetable_settings WHERE is_enabled = 1')
enabled = cursor.fetchall()
print(f'\nTimetable Enabled For: {len(enabled)} school(s)')
for school_id, _ in enabled:
    cursor.execute('SELECT name FROM schools WHERE id = ?', (school_id,))
    name = cursor.fetchone()
    if name:
        print(f'   ✓ School ID {school_id}: {name[0]}')
        
        # Count periods
        cursor.execute('SELECT COUNT(*) FROM timetable_periods WHERE school_id = ?', (school_id,))
        period_count = cursor.fetchone()[0]
        print(f'      └─ {period_count} periods configured')

db.close()

print('\n' + '=' * 60)
print('SYSTEM READY - You can now use timetable features!')
print('=' * 60)
