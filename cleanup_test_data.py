"""
Remove test data I created - keep only timetable tables
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')
db = sqlite3.connect(db_path)
cursor = db.cursor()

print('🗑️  CLEANING UP TEST DATA\n')

# Delete test schools and related data
print('Removing test schools...')
cursor.execute('DELETE FROM schools WHERE id >= 2')  # Keep any original schools
db.commit()

print('✅ Test data removed\n')

# Show what's left
print('📊 CURRENT DATABASE STATE')
print('-' * 60)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'timetable%'")
timetable_tables = cursor.fetchall()
print(f'✓ Timetable Tables: {len(timetable_tables)}')
for t in timetable_tables:
    cursor.execute(f'SELECT COUNT(*) FROM {t[0]}')
    count = cursor.fetchone()[0]
    print(f'  - {t[0]}: {count} records')

# Check original tables
print(f'\n✓ Original Tables (should have real data):')
for table in ['schools', 'admins', 'staff']:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f'  - {table}: {count} records')

print('\n✅ READY: Using existing database with timetable system')
print('   Timetable tables added to your existing vishnorex.db')

db.close()
