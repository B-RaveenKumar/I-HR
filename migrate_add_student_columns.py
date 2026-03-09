"""
Migration script to add missing columns to students table
Run this script to update your database with new student management fields
"""

import os
os.environ.setdefault('DATABASE_URL', 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb')

from app import app
from database import get_db

def migrate_student_columns():
    """Add missing columns to students table"""
    
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        
        # List of columns to add with their definitions
        columns_to_add = [
            ("admission_number", "VARCHAR(100)"),
            ("student_type", "VARCHAR(50) DEFAULT 'Day Scholar'"),
            ("mother_name", "TEXT"),
            ("mother_phone", "VARCHAR(20)"),
            ("parent_occupation", "TEXT"),
            ("tenth_marks", "VARCHAR(100)"),
            ("tenth_percentage", "DECIMAL(5,2)"),
            ("twelfth_marks", "VARCHAR(100)"),
            ("twelfth_percentage", "DECIMAL(5,2)"),
            ("skills", "TEXT"),
            ("tc_number", "VARCHAR(100)"),
            ("aadhar_number", "VARCHAR(20)"),
            ("custom_fields", "TEXT"),
            ("photo_data", "LONGTEXT"),
            ("student_mobile", "VARCHAR(20)"),
            ("theme_preference", "VARCHAR(20) DEFAULT 'light'")
        ]
        
        try:
            # Check which columns exist
            cursor.execute("SHOW COLUMNS FROM students")
            existing_columns = [row[0] for row in cursor.fetchall()]
            print(f"Existing columns: {existing_columns}")
            
            # Add missing columns
            for column_name, column_definition in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE students ADD COLUMN {column_name} {column_definition}"
                        print(f"Adding column: {column_name}")
                        cursor.execute(sql)
                        conn.commit()
                        print(f"✓ Successfully added column: {column_name}")
                    except Exception as e:
                        if "Duplicate column name" not in str(e):
                            print(f"✗ Error adding {column_name}: {e}")
                        else:
                            print(f"- Column {column_name} already exists")
                else:
                    print(f"- Column {column_name} already exists")
            
            print("\n=== Migration completed successfully ===")
            print("All required columns have been added to the students table.")
            
            return True
            
        except Exception as e:
            print(f"Migration error: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    print("=== Student Table Column Migration ===")
    print("This script will add missing columns to your students table.\n")
    
    migrate_student_columns()
