"""
Remove duplicate assignments after NULL id fix
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
    print("REMOVE DUPLICATE ASSIGNMENTS")
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
    
    # Find duplicates
    print("\nFinding duplicate assignments...")
    cursor.execute("""
        SELECT school_id, staff_id, section_id, day_of_week, period_number, 
               MIN(subject_name) as subject_name, COUNT(*) as count, GROUP_CONCAT(id) as ids
        FROM timetable_hierarchical_assignments
        GROUP BY school_id, staff_id, section_id, day_of_week, period_number
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("✓ No duplicates found!")
        cursor.close()
        conn.close()
        return
    
    print(f"Found {len(duplicates)} duplicate assignment groups:")
    
    day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
    
    for dup in duplicates:
        day = day_names.get(dup['day_of_week'], f"Day {dup['day_of_week']}")
        subject = dup['subject_name'] or '(empty)'
        print(f"\n  Staff {dup['staff_id']}: {day}, Period {dup['period_number']}, Subject: {subject}")
        print(f"  Count: {dup['count']} duplicates, IDs: {dup['ids']}")
        
        # Keep the lowest ID, delete the rest
        ids = [int(x.strip()) for x in dup['ids'].split(',')]
        keep_id = min(ids)
        delete_ids = [x for x in ids if x != keep_id]
        
        print(f"  Action: Keep ID {keep_id}, Delete IDs {delete_ids}")
        
        for del_id in delete_ids:
            cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE id = %s", (del_id,))
    
    conn.commit()
    
    print("\n✅ Duplicates removed!")
    
    # Show final state
    cursor.execute("""
        SELECT id, school_id, staff_id, section_id, day_of_week, period_number, subject_name
        FROM timetable_hierarchical_assignments
        ORDER BY id
    """)
    all_records = cursor.fetchall()
    
    print(f"\nFinal state ({len(all_records)} records):")
    for r in all_records:
        day = day_names.get(r['day_of_week'], f"Day {r['day_of_week']}")
        subject = r['subject_name'] or '(empty)'
        print(f"  ID:{r['id']:3d} | Staff {r['staff_id']}: {day}, Period {r['period_number']}, Subject: {subject}")
    
    cursor.close()
    conn.close()
    
    print("\n💡 Restart Flask to load updated data!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
