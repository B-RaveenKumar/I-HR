"""
Cleanup old direct staff assignments from timetable_assignments table
This removes outdated assignments that conflict with the new hierarchical system
"""

from app import app
from database import get_db

def check_old_assignments():
    """Check what assignments exist in timetable_assignments table"""
    db = get_db()
    cursor = db.cursor()
    try:
        # Get all assignments with staff details
        query = """
            SELECT 
                ta.id,
                ta.school_id,
                ta.staff_id,
                s.name as staff_name,
                ta.day_of_week,
                ta.period_number,
                ta.class_subject,
                ta.created_at
            FROM timetable_assignments ta
            LEFT JOIN staff s ON ta.staff_id = s.id AND ta.school_id = s.school_id
            WHERE ta.staff_id IS NOT NULL
            ORDER BY ta.school_id, ta.staff_id, ta.day_of_week, ta.period_number
        """
        cursor.execute(query)
        assignments = cursor.fetchall()
        
        if not assignments:
            print("✓ No old assignments found in timetable_assignments table")
            return []
        
        print(f"\n{'='*80}")
        print(f"Found {len(assignments)} old staff assignments in timetable_assignments table:")
        print(f"{'='*80}\n")
        
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
        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
        
        for staff_id, info in staff_assignments.items():
            print(f"Staff: {info['name']} (ID: {staff_id}, School: {info['school_id']})")
            
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
            print()
        
        return assignments
    finally:
        cursor.close()

def delete_old_assignments(staff_id=None):
    """Delete old assignments from timetable_assignments table"""
    db = get_db()
    cursor = db.cursor()
    try:
        if staff_id:
            # Delete for specific staff
            query = "DELETE FROM timetable_assignments WHERE staff_id = ?"
            cursor.execute(query, (staff_id,))
            deleted_count = cursor.rowcount
            print(f"\n✓ Deleted {deleted_count} old assignments for staff ID {staff_id}")
        else:
            # Delete all staff assignments (where staff_id is not null)
            query = "DELETE FROM timetable_assignments WHERE staff_id IS NOT NULL"
            cursor.execute(query)
            deleted_count = cursor.rowcount
            print(f"\n✓ Deleted {deleted_count} old staff assignments from timetable_assignments table")
        
        db.commit()
        return deleted_count
    finally:
        cursor.close()

def main():
    print("\n" + "="*80)
    print("OLD STAFF ASSIGNMENTS CLEANUP")
    print("="*80)
    
    # First, check what exists
    assignments = check_old_assignments()
    
    if not assignments:
        print("\nNothing to clean up!")
        return
    
    # Ask for confirmation
    print(f"\n{'='*80}")
    print("CLEANUP OPTIONS:")
    print(f"{'='*80}")
    print("1. Delete ALL old staff assignments from timetable_assignments table")
    print("2. Delete assignments for specific staff member")
    print("3. Cancel (no changes)")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        confirm = input(f"\n⚠ This will delete {len(assignments)} assignments. Are you sure? (yes/no): ").strip().lower()
        if confirm == 'yes':
            deleted_count = delete_old_assignments()
            print(f"\n✓ Cleanup complete! Deleted {deleted_count} old assignments.")
            print("\n💡 TIP: Restart your Flask application to see the changes in the availability view.")
        else:
            print("\n✗ Cancelled. No changes made.")
    
    elif choice == "2":
        staff_id = input("\nEnter staff ID to delete assignments for: ").strip()
        if staff_id.isdigit():
            staff_id = int(staff_id)
            confirm = input(f"\n⚠ This will delete all assignments for staff ID {staff_id}. Continue? (yes/no): ").strip().lower()
            if confirm == 'yes':
                deleted_count = delete_old_assignments(staff_id=staff_id)
                print(f"\n✓ Cleanup complete! Deleted {deleted_count} assignments.")
                print("\n💡 TIP: Restart your Flask application to see the changes in the availability view.")
            else:
                print("\n✗ Cancelled. No changes made.")
        else:
            print("\n✗ Invalid staff ID. No changes made.")
    
    else:
        print("\n✗ Cancelled. No changes made.")

if __name__ == "__main__":
    try:
        with app.app_context():
            main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
