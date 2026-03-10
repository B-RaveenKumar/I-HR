"""
Check timetable_assignments with school_id filter
"""

import sqlite3
import os

def main():
    db_path = os.path.join('instance', 'vishnorex.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("CHECKING timetable_assignments TABLE WITH SCHOOL_ID FILTER")
    print("="*80)
    
    # Check all assignments in timetable_assignments
    print("\nALL RECORDS in timetable_assignments:")
    cursor.execute("SELECT * FROM timetable_assignments ORDER BY id")
    all_records = cursor.fetchall()
    print(f"Total records: {len(all_records)}")
    
    if all_records:
        print("\nFirst 10 records:")
        for i, row in enumerate(all_records[:10]):
            print(f"  ID:{row['id']} School:{row['school_id']} Staff:{row['staff_id']} Day:{row['day_of_week']} Period:{row['period_number']}")
    
    # Check with staff_id NOT NULL
    print("\n" + "-"*80)
    print("Records WHERE staff_id IS NOT NULL:")
    cursor.execute("SELECT * FROM timetable_assignments WHERE staff_id IS NOT NULL")
    staff_records = cursor.fetchall()
    print(f"Total: {len(staff_records)}")
    
    if staff_records:
        for row in staff_records:
            print(f"  ID:{row['id']} School:{row['school_id']} Staff:{row['staff_id']} Day:{row['day_of_week']} Period:{row['period_number']} Subject:{row['class_subject']}")
    
    # Check for school_id = 4
    print("\n" + "-"*80)
    print("Records WHERE school_id = 4 AND staff_id IS NOT NULL:")
    cursor.execute("SELECT * FROM timetable_assignments WHERE school_id = 4 AND staff_id IS NOT NULL")
    school4_records = cursor.fetchall()
    print(f"Total: {len(school4_records)}")
    
    if school4_records:
        for row in school4_records:
            print(f"  ID:{row['id']} School:{row['school_id']} Staff:{row['staff_id']} Day:{row['day_of_week']} Period:{row['period_number']} Subject:{row['class_subject']}")
        
        print("\n" + "="*80)
        print("DELETING these records...")
        cursor.execute("DELETE FROM timetable_assignments WHERE school_id = 4 AND staff_id IS NOT NULL")
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ Deleted {deleted} records for school_id=4")
    else:
        print("  (No records found)")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("DONE - Restart Flask if records were deleted")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
