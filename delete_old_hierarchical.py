"""
Delete unwanted old assignments from timetable_hierarchical_assignments
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
    print("DELETE UNWANTED HIERARCHICAL ASSIGNMENTS")
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
    
    # Records to delete based on user feedback
    # Staff 89: Keep Period 1 (Mentor), Delete Period 3 (ID: 20)
    # Staff 98: Delete both Period 2 (ID: 21) and Period 6 (ID: 22)
    
    records_to_delete = [20, 21, 22]
    
    print("\nRecords that will be deleted:")
    print("-"*80)
    
    for rec_id in records_to_delete:
        cursor.execute("""
            SELECT staff_id, day_of_week, period_number, subject_name
            FROM timetable_hierarchical_assignments
            WHERE id = %s
        """, (rec_id,))
        rec = cursor.fetchone()
        if rec:
            day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
                        4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
            day = day_names.get(rec['day_of_week'], f"Day {rec['day_of_week']}")
            subject = rec['subject_name'] or '(no subject)'
            print(f"  ID {rec_id}: Staff {rec['staff_id']}, {day}, Period {rec['period_number']}, Subject: {subject}")
    
    print("\n" + "="*80)
    confirm = input("Delete these records? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        for rec_id in records_to_delete:
            cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE id = %s", (rec_id,))
        
        conn.commit()
        deleted = len(records_to_delete)
        print(f"\n✅ SUCCESS! Deleted {deleted} old assignment records")
        print("\n💡 NEXT STEP: Restart Flask application")
        print("\nExpected results after restart:")
        print("  - Staff 89 (Raveen Kumar B): 1 assigned period (Period 1)")
        print("  - Staff 98 (Velmurugan P): 0 assigned periods (all free)")
        print()
    else:
        print("\n✗ Cancelled. No changes made.")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
