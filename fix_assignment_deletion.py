"""
Check for problematic records in timetable_hierarchical_assignments that might cause deletion errors
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
    print("CHECKING FOR PROBLEMATIC RECORDS")
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
    
    # Check for records with NULL id
    print("\n1. Checking for records with NULL id...")
    print("-"*80)
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM timetable_hierarchical_assignments
        WHERE id IS NULL
    """)
    null_id_count = cursor.fetchone()['count']
    print(f"Records with NULL id: {null_id_count}")
    
    if null_id_count > 0:
        cursor.execute("""
            SELECT school_id, staff_id, section_id, day_of_week, period_number, subject_name
            FROM timetable_hierarchical_assignments
            WHERE id IS NULL
            LIMIT 10
        """)
        null_records = cursor.fetchall()
        print("\nSample records with NULL id:")
        for r in null_records:
            print(f"  School:{r['school_id']} Staff:{r['staff_id']} Section:{r['section_id']} "
                  f"Day:{r['day_of_week']} Period:{r['period_number']} Subject:{r['subject_name']}")
    
    # Check table structure
    print("\n2. Checking table structure...")
    print("-"*80)
    cursor.execute("DESCRIBE timetable_hierarchical_assignments")
    columns = cursor.fetchall()
    print("\nTable columns:")
    for col in columns:
        print(f"  {col['Field']}: {col['Type']} | Null:{col['Null']} | Key:{col['Key']} | Default:{col['Default']} | Extra:{col['Extra']}")
    
    # Check for auto-increment
    cursor.execute("""
        SELECT AUTO_INCREMENT
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'timetable_hierarchical_assignments'
    """, (config['database'],))
    auto_inc = cursor.fetchone()
    print(f"\nAuto-increment value: {auto_inc['AUTO_INCREMENT'] if auto_inc else 'N/A'}")
    
    # Check all records
    print("\n3. Checking all records...")
    print("-"*80)
    cursor.execute("""
        SELECT id, school_id, staff_id, section_id, day_of_week, period_number, subject_name
        FROM timetable_hierarchical_assignments
        ORDER BY id
    """)
    all_records = cursor.fetchall()
    print(f"Total records: {len(all_records)}")
    
    if all_records:
        print("\nAll records:")
        day_names = {1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}
        for r in all_records:
            id_str = str(r['id']) if r['id'] is not None else 'NULL'
            day = day_names.get(r['day_of_week'], f"D{r['day_of_week']}")
            subject = r['subject_name'] or '(empty)'
            print(f"  ID:{id_str:4s} | School:{r['school_id']} Staff:{r['staff_id']} Section:{r['section_id']} | "
                  f"{day} P{r['period_number']} | Subject:{subject}")
    
    print("\n" + "="*80)
    print("FIX OPTIONS:")
    print("="*80)
    
    if null_id_count > 0:
        print("\n⚠️ ISSUE FOUND: Records with NULL id cannot be deleted via API")
        print("\nOption 1: Add auto-increment IDs to NULL records")
        print("Option 2: Delete NULL records manually")
        print("Option 3: Recreate table with proper constraints")
        
        choice = input("\nEnter option (1/2/3/cancel): ").strip()
        
        if choice == "1":
            # This won't work directly, need to delete and reinsert
            print("\n⚠️ Cannot directly add IDs to existing NULL records")
            print("Need to delete and reinsert. Proceed? (yes/no): ", end='')
            if input().strip().lower() == 'yes':
                # Get records to preserve
                cursor.execute("""
                    SELECT school_id, staff_id, section_id, level_id, day_of_week, 
                           period_number, subject_name, room_number, created_at
                    FROM timetable_hierarchical_assignments
                    WHERE id IS NULL
                """)
                records_to_fix = cursor.fetchall()
                
                # Delete NULL records
                cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE id IS NULL")
                deleted = cursor.rowcount
                print(f"\nDeleted {deleted} records with NULL id")
                
                # Reinsert with auto-increment
                for r in records_to_fix:
                    cursor.execute("""
                        INSERT INTO timetable_hierarchical_assignments
                        (school_id, staff_id, section_id, level_id, day_of_week, 
                         period_number, subject_name, room_number, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (r['school_id'], r['staff_id'], r['section_id'], r['level_id'],
                          r['day_of_week'], r['period_number'], r['subject_name'],
                          r['room_number'], r['created_at']))
                
                conn.commit()
                print(f"✅ Reinserted {len(records_to_fix)} records with proper IDs")
                print("\n💡 Restart Flask to see changes!")
        
        elif choice == "2":
            confirm = input("\nDelete ALL records with NULL id? (yes/no): ").strip().lower()
            if confirm == 'yes':
                cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE id IS NULL")
                deleted = cursor.rowcount
                conn.commit()
                print(f"\n✅ Deleted {deleted} records with NULL id")
                print("\n💡 Restart Flask to see changes!")
        
        else:
            print("\n✗ Cancelled")
    
    else:
        print("\n✅ No problematic records found!")
        print("The 'Error deleting assignment' might be due to:")
        print("  - Permission issues")
        print("  - Assignment already deleted")
        print("  - Frontend sending wrong assignment_id")
        print("\nCheck browser console and Flask logs for more details")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
