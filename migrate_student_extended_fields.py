"""
Migration script to add extended fields to students table
Adds: admission_number, student_type, tenth/twelfth marks, parent details, documents, custom fields
"""
import sqlite3
import os
import glob

def migrate_database(db_path):
    """Add new columns to students table"""
    print(f"\n{'='*60}")
    print(f"Migrating database: {db_path}")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of columns to add with their SQL definitions
    new_columns = [
        ("admission_number", "TEXT"),
        ("student_type", "TEXT DEFAULT 'Day Scholar'"),
        ("mother_name", "TEXT"),
        ("mother_phone", "TEXT"),
        ("parent_occupation", "TEXT"),
        ("tenth_marks", "TEXT"),
        ("tenth_percentage", "REAL"),
        ("twelfth_marks", "TEXT"),
        ("twelfth_percentage", "REAL"),
        ("skills", "TEXT"),
        ("tc_number", "TEXT"),
        ("aadhar_number", "TEXT"),
        ("custom_fields", "TEXT"),
    ]
    
    # Check which columns already exist
    cursor.execute("PRAGMA table_info(students)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    added_count = 0
    skipped_count = 0
    
    for column_name, column_def in new_columns:
        if column_name in existing_columns:
            print(f"  ⏭️  Column '{column_name}' already exists - skipping")
            skipped_count += 1
        else:
            try:
                # For MySQL compatibility, wrap reserved keywords in backticks
                if column_name == 'class':
                    sql = f"ALTER TABLE students ADD COLUMN `{column_name}` {column_def}"
                else:
                    sql = f"ALTER TABLE students ADD COLUMN {column_name} {column_def}"
                
                cursor.execute(sql)
                print(f"  ✅ Added column: {column_name} ({column_def})")
                added_count += 1
            except Exception as e:
                print(f"  ❌ Error adding column '{column_name}': {str(e)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Summary: {added_count} columns added, {skipped_count} already existed")
    return added_count > 0

def main():
    """Migrate all school databases"""
    print("\n" + "="*60)
    print("STUDENT EXTENDED FIELDS MIGRATION")
    print("="*60)
    print("\nThis script will add new fields to the students table:")
    print("  • Admission Number, Student Type (Hostel/Day Scholar)")
    print("  • Mother's name and phone")
    print("  • Parent occupation")
    print("  • 10th & 12th marks and percentages")
    print("  • Skills and achievements")
    print("  • TC Number and Aadhar Number")
    print("  • Custom fields (JSON)")
    print("="*60)
    
    # Find all school databases
    db_files = glob.glob("school_*.db")
    
    if not db_files:
        print("\n⚠️  No school databases found!")
        print("   Looking for files matching pattern: school_*.db")
        return
    
    print(f"\n🔍 Found {len(db_files)} school database(s):")
    for db in db_files:
        print(f"   • {db}")
    
    # Ask for confirmation
    response = input(f"\n❓ Proceed with migration? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n❌ Migration cancelled by user")
        return
    
    # Migrate each database
    migrated_count = 0
    for db_file in db_files:
        try:
            if migrate_database(db_file):
                migrated_count += 1
        except Exception as e:
            print(f"\n❌ Error migrating {db_file}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"✅ Migration complete!")
    print(f"   Databases processed: {len(db_files)}")
    print(f"   Databases modified: {migrated_count}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
