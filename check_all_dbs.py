import sqlite3
import os

print('=' * 80)
print('CHECKING ALL DATABASE FILES')
print('=' * 80)

instance_path = os.path.join(os.path.dirname(__file__), 'instance')

for db_file in ['vishnorex.db', 'staff_management.db', 'database.db']:
    db_path = os.path.join(instance_path, db_file)
    
    if not os.path.exists(db_path):
        print(f'\n❌ {db_file}: NOT FOUND')
        continue
    
    print(f'\n✓ {db_file}')
    print('-' * 80)
    
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f'  Tables ({len(tables)}): {", ".join([t[0] for t in tables[:10]])}')
        
        # Check schools
        cursor.execute("SELECT COUNT(*) FROM schools" if 'schools' in [t[0] for t in tables] else "SELECT 0")
        school_count = cursor.fetchone()[0]
        if school_count > 0:
            cursor.execute("SELECT id, name FROM schools LIMIT 3")
            schools = cursor.fetchall()
            print(f'  Schools ({school_count}):')
            for s in schools:
                print(f'    - ID {s[0]}: {s[1]}')
        
        # Check staff
        if 'staff' in [t[0] for t in tables]:
            cursor.execute("SELECT COUNT(*) FROM staff")
            staff_count = cursor.fetchone()[0]
            print(f'  Staff: {staff_count}')
        
        db.close()
    except Exception as e:
        print(f'  Error: {e}')

print('\n' + '=' * 80)
