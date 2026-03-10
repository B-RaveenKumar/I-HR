"""
Cleanup old direct staff assignments from timetable_assignments table
Non-interactive version - automatically deletes all old assignments
"""

from app import app
from database import get_db

def main():
    print("\n" + "="*80)
    print("OLD STAFF ASSIGNMENTS CLEANUP")
    print("="*80)
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        try:
            # First check what exists
            print("\nChecking for old assignments...")
            query = """
                SELECT 
                    ta.school_id,
                    ta.staff_id,
                    s.name as staff_name,
                    ta.day_of_week,
                    ta.period_number,
                    ta.class_subject
                FROM timetable_assignments ta
                LEFT JOIN staff s ON ta.staff_id = s.id AND ta.school_id = s.school_id
                WHERE ta.staff_id IS NOT NULL
                ORDER BY ta.school_id, ta.staff_id, ta.day_of_week, ta.period_number
            """
            cursor.execute(query)
            assignments = cursor.fetchall()
            
            if not assignments:
                print("\n✓ No old assignments found in timetable_assignments table")
                print("  The table is already clean!")
                return
            
            print(f"\nFound {len(assignments)} old staff assignments:")
            print("="*80)
            
            # Group by staff
            staff_assignments = {}
            for a in assignments:
                staff_id = a['staff_id']
                if staff_id not in staff_assignments:
                    staff_assignments[staff_id] = {
                        'name': a['staff_name'] or f"Staff ID {staff_id}",
                        'school_id': a['school_id'],
                        'assignments': []
                    }
                staff_assignments[staff_id]['assignments'].append(a)
            
            # Display grouped by staff
            day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
                        4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
            
            for staff_id, info in staff_assignments.items():
                print(f"\nStaff: {info['name']} (ID: {staff_id}, School: {info['school_id']})")
                
                # Group by day
                by_day = {}
                for a in info['assignments']:
                    day = a['day_of_week']
                    if day not in by_day:
                        by_day[day] = []
                    by_day[day].append(a['period_number'])
                
                for day in sorted(by_day.keys()):
                    day_name = day_names.get(day, f'Day {day}')
                    periods = sorted(by_day[day])
                    print(f"  {day_name}: Periods {periods}")
            
            # Delete all old assignments
            print("\n" + "="*80)
            print(f"Deleting {len(assignments)} old assignments...")
            
            delete_query = "DELETE FROM timetable_assignments WHERE staff_id IS NOT NULL"
            cursor.execute(delete_query)
            deleted_count = cursor.rowcount
            db.commit()
            
            print(f"\n✓ SUCCESS! Deleted {deleted_count} old staff assignments")
            print("="*80)
            print("\n💡 NEXT STEPS:")
            print("   1. The old assignments have been removed from timetable_assignments table")
            print("   2. Only timetable_hierarchical_assignments will now be used")
            print("   3. Restart your Flask application to see the updated availability view")
            print("   4. Staff Period Assignments & Availability will now show correct data")
            print()
            
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
        finally:
            cursor.close()

if __name__ == "__main__":
    main()
