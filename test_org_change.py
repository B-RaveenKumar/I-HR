import os
from database import get_db, init_db
from hierarchical_timetable import HierarchicalTimetableManager

# To avoid setting up full flask context, just call the manager directly
def test():
    print("Testing Organization Type Change and sections consistency")
    
    # Check current sections
    db = get_db()
    cursor = db.cursor()
    
    print("Current levels:")
    cursor.execute('SELECT id, level_type, level_number, level_name, is_active FROM timetable_academic_levels')
    for row in cursor.fetchall():
        print(dict(row))
        
    print("\nCurrent sections:")
    cursor.execute('SELECT id, school_id, level_id, section_name, section_code FROM timetable_sections')
    for row in cursor.fetchall():
        print(dict(row))

    print("\nChanging Org Type to College...")
    HierarchicalTimetableManager.set_organization_type(1, 'college')
    
    print("\nLevels after College:")
    cursor.execute('SELECT id, level_type, level_number, level_name, is_active FROM timetable_academic_levels')
    for row in cursor.fetchall():
        print(dict(row))
        
    print("\nChanging Org Type back to School...")
    HierarchicalTimetableManager.set_organization_type(1, 'school')
    
    print("\nLevels after School:")
    cursor.execute('SELECT id, level_type, level_number, level_name, is_active FROM timetable_academic_levels')
    for row in cursor.fetchall():
        print(dict(row))

if __name__ == "__main__":
    from app import app
    with app.app_context():
        test()
