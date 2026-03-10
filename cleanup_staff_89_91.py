"""
Check and clean staff 89 and 91 assignments
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
    print("CHECK AND CLEAN STAFF 89 & 91 ASSIGNMENTS")
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
    
    # Get staff names
    print("\nStaff Information:")
    print("-"*80)
    try:
        cursor.execute("SELECT id, full_name FROM staff WHERE id IN (89, 91)")
        staff = cursor.fetchall()
        for s in staff:
            print(f"  ID:{s['id']} - {s['full_name']}")
    except Exception as e:
        print(f"  (Could not fetch staff names: {e})")
        print("  Staff IDs: 89, 91")
    
    # Check timetable_hierarchical_assignments
    print("\n1. Checking timetable_hierarchical_assignments...")
    print("-"*80)
    cursor.execute("""
        SELECT * FROM timetable_hierarchical_assignments 
        WHERE staff_id IN (89, 91) 
        ORDER BY staff_id, day_of_week, period_number
    """)
    hierarchical = cursor.fetchall()
    
    if hierarchical:
        print(f"Found {len(hierarchical)} records:")
        for r in hierarchical:
            print(f"  ID:{r['id']:3d} | Staff:{r['staff_id']} | Day:{r['day_of_week']} Period:{r['period_number']} | Subject:{r.get('subject_name', 'N/A')}")
    else:
        print("  ✓ No records found")
    
    # Check timetable_assignments
    print("\n2. Checking timetable_assignments...")
    print("-"*80)
    cursor.execute("""
        SELECT * FROM timetable_assignments 
        WHERE staff_id IN (89, 91)
        ORDER BY staff_id, day_of_week, period_number
    """)
    direct = cursor.fetchall()
    
    if direct:
        print(f"Found {len(direct)} records:")
        for r in direct:
            print(f"  ID:{r['id']:3d} | Staff:{r['staff_id']} | Day:{r['day_of_week']} Period:{r['period_number']}")
    else:
        print("  ✓ No records found")
    
    # Check timetable_self_allocations
    print("\n3. Checking timetable_self_allocations...")
    print("-"*80)
    cursor.execute("""
        SELECT * FROM timetable_self_allocations 
        WHERE staff_id IN (89, 91)
        ORDER BY staff_id, day_of_week, period_number
    """)
    self_alloc = cursor.fetchall()
    
    if self_alloc:
        print(f"Found {len(self_alloc)} records:")
        for r in self_alloc:
            print(f"  ID:{r['id']:3d} | Staff:{r['staff_id']} | Day:{r['day_of_week']} Period:{r['period_number']}")
    else:
        print("  ✓ No records found")
    
    # Calculate totals
    total_89_h = sum(1 for r in hierarchical if r['staff_id'] == 89)
    total_89_d = sum(1 for r in direct if r['staff_id'] == 89)
    total_89_s = sum(1 for r in self_alloc if r['staff_id'] == 89)
    total_89 = total_89_h + total_89_d + total_89_s
    
    total_91_h = sum(1 for r in hierarchical if r['staff_id'] == 91)
    total_91_d = sum(1 for r in direct if r['staff_id'] == 91)
    total_91_s = sum(1 for r in self_alloc if r['staff_id'] == 91)
    total_91 = total_91_h + total_91_d + total_91_s
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Staff 89: {total_89_h} hierarchical + {total_89_d} direct + {total_89_s} self = {total_89} total")
    print(f"Staff 91: {total_91_h} hierarchical + {total_91_d} direct + {total_91_s} self = {total_91} total")
    
    total_all = total_89 + total_91
    
    if total_all == 0:
        print("\n✅ No assignments found - database is clean!")
        cursor.close()
        conn.close()
        return
    
    print(f"\n⚠️ Found {total_all} unwanted assignments!")
    print("\nDELETING ALL ASSIGNMENTS...")
    print("="*80)
    
    deleted_counts = {'hierarchical': 0, 'direct': 0, 'self': 0}
    
    # Delete from hierarchical
    if hierarchical:
        print("\nDeleting from timetable_hierarchical_assignments...")
        cursor.execute("DELETE FROM timetable_hierarchical_assignments WHERE staff_id IN (89, 91)")
        deleted_counts['hierarchical'] = cursor.rowcount
        print(f"  ✓ Deleted {deleted_counts['hierarchical']} records")
    
    # Delete from direct assignments
    if direct:
        print("\nDeleting from timetable_assignments...")
        cursor.execute("DELETE FROM timetable_assignments WHERE staff_id IN (89, 91)")
        deleted_counts['direct'] = cursor.rowcount
        print(f"  ✓ Deleted {deleted_counts['direct']} records")
    
    # Delete from self allocations
    if self_alloc:
        print("\nDeleting from timetable_self_allocations...")
        cursor.execute("DELETE FROM timetable_self_allocations WHERE staff_id IN (89, 91)")
        deleted_counts['self'] = cursor.rowcount
        print(f"  ✓ Deleted {deleted_counts['self']} records")
    
    conn.commit()
    
    # Verify cleanup
    print("\nVerifying cleanup...")
    print("-"*80)
    cursor.execute("""
        SELECT COUNT(*) as count FROM timetable_hierarchical_assignments WHERE staff_id IN (89, 91)
    """)
    remaining_h = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM timetable_assignments WHERE staff_id IN (89, 91)
    """)
    remaining_d = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM timetable_self_allocations WHERE staff_id IN (89, 91)
    """)
    remaining_s = cursor.fetchone()['count']
    
    remaining_total = remaining_h + remaining_d + remaining_s
    
    if remaining_total == 0:
        print("✅ All assignments deleted successfully!")
        print(f"\nDeleted: {deleted_counts['hierarchical']} hierarchical + {deleted_counts['direct']} direct + {deleted_counts['self']} self = {sum(deleted_counts.values())} total")
    else:
        print(f"⚠️ Still {remaining_total} assignments remaining")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ CLEANUP COMPLETE!")
    print("   Refresh the Staff Period Assignments & Availability page")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
