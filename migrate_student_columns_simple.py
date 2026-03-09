"""
Simple migration script to add missing columns to students table
"""
import pymysql

# Database connection details
DB_CONFIG = {
    'host': 'mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech',
    'port': 32261,
    'user': 'root',
    'password': 'Vish0803',
    'database': 'ihrdb',
    'charset': 'utf8mb4'
}

def migrate_student_columns():
    """Add missing columns to students table"""
    
    print("Connecting to database...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ Connected successfully\n")
        
        # List of columns to add
        columns_to_add = [
            ("password", "VARCHAR(255)"),
            ("admission_number", "VARCHAR(100)"),
            ("student_type", "VARCHAR(50) DEFAULT 'Day Scholar'"),
            ("parent_name", "VARCHAR(255)"),
            ("parent_phone", "VARCHAR(20)"),
            ("parent_email", "VARCHAR(255)"),
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
            ("student_mobile", "VARCHAR(20)")
        ]
        
        # Check existing columns
        cursor.execute("SHOW COLUMNS FROM students")
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(existing_columns)} existing columns\n")
        
        # Add missing columns
        added_count = 0
        skipped_count = 0
        
        for column_name, column_definition in columns_to_add:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE students ADD COLUMN {column_name} {column_definition}"
                    print(f"Adding column: {column_name}...", end=" ")
                    cursor.execute(sql)
                    conn.commit()
                    print("✓")
                    added_count += 1
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print("- Already exists")
                        skipped_count += 1
                    else:
                        print(f"✗ Error: {e}")
            else:
                print(f"- Column {column_name} already exists")
                skipped_count += 1
        
        print(f"\n=== Migration completed ===")
        print(f"✓ Added: {added_count} columns")
        print(f"- Skipped: {skipped_count} columns")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Migration error: {e}")
        return False

if __name__ == "__main__":
    print("=== Student Table Column Migration ===\n")
    migrate_student_columns()
