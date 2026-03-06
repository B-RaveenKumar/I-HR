"""
Quick diagnostic to check timetable module settings
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("TIMETABLE MODULE DIAGNOSTIC")
print("=" * 60)

# Check if timetable_management_enabled column exists
cursor.execute("PRAGMA table_info(schools)")
columns = cursor.fetchall()
column_names = [col['name'] for col in columns]

print("\n📋 Schools table columns:")
for col in column_names:
    if 'management_enabled' in col or 'enabled' in col:
        print(f"   ✓ {col}")

if 'timetable_management_enabled' in column_names:
    print("\n✅ timetable_management_enabled column EXISTS")
    
    # Check current values for all schools
    cursor.execute("SELECT id, name, timetable_management_enabled FROM schools")
    schools = cursor.fetchall()
    
    print(f"\n📊 Current timetable module status for all schools:")
    print("-" * 60)
    for school in schools:
        status = "🟢 ENABLED" if school['timetable_management_enabled'] else "🔴 DISABLED"
        print(f"   School ID {school['id']}: {school['name']}")
        print(f"   Status: {status} (value: {school['timetable_management_enabled']})")
        print("-" * 60)
else:
    print("\n❌ timetable_management_enabled column DOES NOT EXIST")
    print("   ⚠️  You need to run: python add_module_columns_to_schools.py")

conn.close()

print("\n💡 To disable timetable for a school:")
print("   UPDATE schools SET timetable_management_enabled = 0 WHERE id = <school_id>;")
print("\n💡 To enable timetable for a school:")
print("   UPDATE schools SET timetable_management_enabled = 1 WHERE id = <school_id>;")
print("=" * 60)
