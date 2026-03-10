"""
Auto-fix NULL id records in timetable_hierarchical_assignments
"""

import pymysql
from urllib.parse import urlparse

def parse_mysql_url(url):
    url = url.replace('mysql+pymysql://', '')
    parts = urlparse(f'mysql://{url}')
    return {
        'host': parts.hostname,
        'port': parts.port or 3306,
        'user': parts.username,
        'password': parts.password,
        'database': parts.path.lstrip('/')
    }

def main():
    db_url = 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb'
    config = parse_mysql_url(db_url)
    
    print("\n" + "="*80)
    print("AUTO-FIX NULL ID RECORDS")
    print("="*80)
    
    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        cursorclass=pymysql.cursors.DictCursor
    )
    
    cursor = conn.cursor()
    
    # Step 1: Check for NULL ids
    print("\nStep 1: Checking for NULL id records...")
    cursor.execute("""
        SELECT school_id, staff_id, section_id, level_id, day_of_week, 
               period_number, subject_name, room_number, created_at
        FROM timetable_hierarchical_assignments
        WHERE id IS NULL
    """)
    null_records = cursor.fetchall()
    
    if not null_records:
        print("✓ No NULL id records found. Table is clean!")
        cursor.close()
        conn.close()
        return
    
    print(f"Found {len(null_records)} records with NULL id")
    
    day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
    for r in null_records:
        day = day_names.get(r['day_of_week'], f"Day {r['day_of_week']}")
        subject = r['subject_name'] or '(empty)'
        print(f"  Staff {r['staff_id']}: {day}, Period {r['period_number']}, Subject: {subject}")
    
    # Step 2: First, ensure id column has AUTO_INCREMENT
    print("\nStep 2: Setting up AUTO_INCREMENT on id column...")
    try:
        cursor.execute("""
            ALTER TABLE timetable_hierarchical_assignments 
            MODIFY COLUMN id INT AUTO_INCREMENT PRIMARY KEY
        """)
        print("✓ AUTO_INCREMENT configured")
    except pymysql.err.OperationalError as e:
        if '1068' in str(e):  # Multiple primary keys error
            print("⚠ Primary key already exists, modifying...")
            # Drop primary key first
            cursor.execute("""
                ALTER TABLE timetable_hierarchical_assignments 
                DROP PRIMARY KEY
            """)
            # Add it back with AUTO_INCREMENT
            cursor.execute("""
                ALTER TABLE timetable_hierarchical_assignments 
                MODIFY COLUMN id INT AUTO_INCREMENT PRIMARY KEY
            """)
            print("✓ AUTO_INCREMENT configured after removing old PK")
        else:
            raise
    
    # Step 3: Delete and reinsert records
    print("\nStep 3: Fixing NULL id records...")
    
    # Delete NULL records
    cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE id IS NULL")
    deleted = cursor.rowcount
    print(f"✓ Deleted {deleted} records with NULL id")
    
    # Reinsert with auto-incremented IDs
    for r in null_records:
        cursor.execute("""
            INSERT INTO timetable_hierarchical_assignments
            (school_id, staff_id, section_id, level_id, day_of_week, 
             period_number, subject_name, room_number, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (r['school_id'], r['staff_id'], r['section_id'], r['level_id'],
              r['day_of_week'], r['period_number'], r['subject_name'],
              r['room_number'], r['created_at']))
    
    conn.commit()
    print(f"✓ Reinserted {len(null_records)} records with proper auto-increment IDs")
    
    # Step 4: Verify fix
    print("\nStep 4: Verifying fix...")
    cursor.execute("SELECT COUNT(*) as count FROM timetable_hierarchical_assignments WHERE id IS NULL")
    remaining_nulls = cursor.fetchone()['count']
    
    if remaining_nulls == 0:
        print("✅ SUCCESS! All records now have valid IDs")
        
        # Show all records
        cursor.execute("""
            SELECT id, school_id, staff_id, section_id, day_of_week, period_number, subject_name
            FROM timetable_hierarchical_assignments
            ORDER BY id
        """)
        all_records = cursor.fetchall()
        print(f"\nAll records ({len(all_records)} total):")
        for r in all_records:
            day = day_names.get(r['day_of_week'], f"Day {r['day_of_week']}")
            subject = r['subject_name'] or '(empty)'
            print(f"  ID:{r['id']:3d} | Staff {r['staff_id']}: {day}, Period {r['period_number']}, Subject: {subject}")
    else:
        print(f"⚠ Warning: Still have {remaining_nulls} records with NULL id")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("💡 NEXT STEP: Restart Flask application")
    print("   After restart, assignment deletion will work correctly!")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
