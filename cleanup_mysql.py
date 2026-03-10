"""
Cleanup old assignments from MySQL database
"""

import pymysql
from urllib.parse import urlparse

def parse_mysql_url(url):
    """Parse MySQL URL to get connection details"""
    # Remove mysql+pymysql:// prefix
    url = url.replace('mysql+pymysql://', '')
    
    # Parse the URL
    parts = urlparse(f'mysql://{url}')
    
    return {
        'host': parts.hostname,
        'port': parts.port or 3306,
        'user': parts.username,
        'password': parts.password,
        'database': parts.path.lstrip('/')
    }

def main():
    # MySQL connection details
    db_url = 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb'
    config = parse_mysql_url(db_url)
    
    print("\n" + "="*80)
    print("MYSQL DATABASE CLEANUP - timetable_assignments")
    print("="*80)
    print(f"\nConnecting to:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Database: {config['database']}")
    
    try:
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            cursorclass=pymysql.cursors.DictCursor
        )
        print("  ✓ Connected successfully")
        
        cursor = conn.cursor()
        
        # Check current state
        print("\n" + "-"*80)
        print("Checking timetable_assignments table...")
        cursor.execute("""
            SELECT id, school_id, staff_id, day_of_week, period_number, class_subject
            FROM timetable_assignments
            WHERE staff_id IS NOT NULL
            ORDER BY school_id, staff_id, day_of_week, period_number
        """)
        records = cursor.fetchall()
        
        print(f"Found {len(records)} records with staff assignments")
        
        if not records:
            print("\n✓ Table is already clean!")
            return
        
        # Show records grouped by school and staff
        print("\nCurrent assignments:")
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
                    4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
        
        by_staff = {}
        for r in records:
            key = (r['school_id'], r['staff_id'])
            if key not in by_staff:
                by_staff[key] = []
            by_staff[key].append(r)
        
        for (school_id, staff_id), recs in by_staff.items():
            print(f"\n  School {school_id}, Staff {staff_id}:")
            for r in recs:
                day = day_names.get(r['day_of_week'], f"Day {r['day_of_week']}")
                print(f"    {day}: Period {r['period_number']} - {r['class_subject']}")
        
        # Delete all
        print("\n" + "="*80)
        print("DELETING all old staff assignments...")
        cursor.execute("DELETE FROM timetable_assignments WHERE staff_id IS NOT NULL")
        deleted = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ SUCCESS! Deleted {deleted} records")
        print("="*80)
        print("\n💡 NEXT STEP: Restart Flask application")
        print("   The availability view will now show correct data")
        print()
        
        cursor.close()
        conn.close()
        
    except pymysql.err.OperationalError as e:
        print(f"\n✗ Connection Error: {e}")
        print("\n  Possible issues:")
        print("  - MySQL server is not accessible")
        print("  - Incorrect credentials")
        print("  - Firewall blocking connection")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
