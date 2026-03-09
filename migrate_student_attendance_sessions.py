"""
Add morning/afternoon session columns to student_attendance table
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

def add_session_columns():
    """Add morning and afternoon session columns"""
    
    print("Connecting to database...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ Connected successfully\n")
        
        # Columns to add
        columns_to_add = [
            ("morning_status", "VARCHAR(20)"),
            ("morning_time", "TIME"),
            ("morning_marked_by", "INT"),
            ("morning_notes", "TEXT"),
            ("afternoon_status", "VARCHAR(20)"),
            ("afternoon_time", "TIME"),
            ("afternoon_marked_by", "INT"),
            ("afternoon_notes", "TEXT")
        ]
        
        # Check existing columns
        cursor.execute("SHOW COLUMNS FROM student_attendance")
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(existing_columns)} existing columns\n")
        
        # Add missing columns
        added_count = 0
        skipped_count = 0
        
        for column_name, column_definition in columns_to_add:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE student_attendance ADD COLUMN {column_name} {column_definition}"
                    print(f"Adding column: {column_name}...", end=" ")
                    cursor.execute(sql)
                    conn.commit()
                    print("✓")
                    added_count += 1
                except Exception as e:
                    print(f"✗ Error: {e}")
            else:
                print(f"- Column {column_name} already exists")
                skipped_count += 1
        
        # Add foreign keys if columns were added
        if added_count > 0:
            print("\nAdding foreign key constraints...")
            try:
                # Check if foreign keys exist first
                cursor.execute("""
                    SELECT CONSTRAINT_NAME 
                    FROM information_schema.TABLE_CONSTRAINTS 
                    WHERE TABLE_SCHEMA = 'ihrdb' 
                    AND TABLE_NAME = 'student_attendance' 
                    AND CONSTRAINT_TYPE = 'FOREIGN KEY'
                """)
                existing_fks = [row[0] for row in cursor.fetchall()]
                
                if 'fk_morning_marked_by' not in existing_fks:
                    cursor.execute("""
                        ALTER TABLE student_attendance 
                        ADD CONSTRAINT fk_morning_marked_by 
                        FOREIGN KEY (morning_marked_by) REFERENCES staff(id)
                    """)
                    print("✓ Added morning_marked_by foreign key")
                
                if 'fk_afternoon_marked_by' not in existing_fks:
                    cursor.execute("""
                        ALTER TABLE student_attendance 
                        ADD CONSTRAINT fk_afternoon_marked_by 
                        FOREIGN KEY (afternoon_marked_by) REFERENCES staff(id)
                    """)
                    print("✓ Added afternoon_marked_by foreign key")
                
                conn.commit()
            except Exception as e:
                print(f"Note: Foreign keys might already exist or error occurred: {e}")
        
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
    print("=== Student Attendance Session Columns Migration ===\n")
    add_session_columns()
