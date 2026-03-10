"""
Check what's in timetable_hierarchical_assignments for specific staff
"""

import pymysql
from urllib.parse import urlparse

def parse_mysql_url(url):
    """Parse MySQL URL to get connection details"""
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
    print("CHECKING timetable_hierarchical_assignments TABLE")
    print("="*80)
    
    try:
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = conn.cursor()
        
        # Check all assignments in hierarchical table
        print("\nAll assignments in timetable_hierarchical_assignments:")
        print("-"*80)
        cursor.execute("""
            SELECT id, school_id, staff_id, section_id, level_id, 
                   day_of_week, period_number, subject_name, room_number, created_at
            FROM timetable_hierarchical_assignments
            WHERE staff_id IS NOT NULL
            ORDER BY staff_id, day_of_week, period_number
        """)
        records = cursor.fetchall()
        
        print(f"Total records: {len(records)}\n")
        
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
                    4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
        
        if records:
            # Group by staff
            by_staff = {}
            for r in records:
                staff_id = r['staff_id']
                if staff_id not in by_staff:
                    by_staff[staff_id] = []
                by_staff[staff_id].append(r)
            
            for staff_id, recs in sorted(by_staff.items()):
                print(f"Staff ID: {staff_id}")
                for r in recs:
                    day = day_names.get(r['day_of_week'], f"Day {r['day_of_week']}")
                    subject = r['subject_name'] or '(no subject)'
                    section = str(r['section_id']) if r['section_id'] else 'N/A'
                    level = str(r['level_id']) if r['level_id'] else 'N/A'
                    created = str(r['created_at']) if r['created_at'] else 'N/A'
                    rec_id = r['id'] if r['id'] is not None else 0
                    print(f"  ID:{rec_id:3d} | {day:9s} Period {r['period_number']} | "
                          f"Subject: {subject:15s} | Section: {section} | Created: {created}")
                print()
        
        # Specific check for Staff 89 and 98
        print("\n" + "="*80)
        print("FOCUS: Staff 89 (Raveen Kumar B) and Staff 98 (Velmurugan P)")
        print("="*80)
        
        for staff_id in [89, 98]:
            cursor.execute("""
                SELECT id, day_of_week, period_number, subject_name, section_id, created_at
                FROM timetable_hierarchical_assignments
                WHERE staff_id = %s
                ORDER BY day_of_week, period_number
            """, (staff_id,))
            staff_records = cursor.fetchall()
            
            print(f"\nStaff {staff_id}: {len(staff_records)} assignment(s)")
            if staff_records:
                for r in staff_records:
                    day = day_names.get(r['day_of_week'], f"Day {r['day_of_week']}")
                    subject = r['subject_name'] or '(no subject)'
                    print(f"  Record ID {r['id']}: {day}, Period {r['period_number']}, "
                          f"Subject: {subject}, Section: {r['section_id']}, Created: {r['created_at']}")
        
        print("\n" + "="*80)
        print("OPTIONS:")
        print("="*80)
        print("1. Delete specific assignment by ID")
        print("2. Delete all assignments for a specific staff")
        print("3. Delete all assignments for school 4")
        print("4. Cancel (no changes)")
        print()
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            record_id = input("Enter record ID to delete: ").strip()
            if record_id.isdigit():
                cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE id = %s", (int(record_id),))
                conn.commit()
                print(f"\n✅ Deleted record ID {record_id}")
        
        elif choice == "2":
            staff_id = input("Enter staff ID to delete all assignments for: ").strip()
            if staff_id.isdigit():
                cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE staff_id = %s", (int(staff_id),))
                deleted = cursor.rowcount
                conn.commit()
                print(f"\n✅ Deleted {deleted} assignments for staff {staff_id}")
        
        elif choice == "3":
            confirm = input("Delete ALL assignments for school 4? (yes/no): ").strip().lower()
            if confirm == 'yes':
                cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE school_id = 4")
                deleted = cursor.rowcount
                conn.commit()
                print(f"\n✅ Deleted {deleted} assignments for school 4")
            else:
                print("\n✗ Cancelled")
        
        else:
            print("\n✗ Cancelled")
        
        cursor.close()
        conn.close()
        
        if choice in ["1", "2", "3"]:
            print("\n💡 RESTART Flask to see changes!")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
