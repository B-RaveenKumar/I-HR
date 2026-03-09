"""
Migration script to create student_attendance table
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

def create_student_attendance_table():
    """Create student_attendance table if it doesn't exist"""
    
    print("Connecting to database...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ Connected successfully\n")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'ihrdb' 
            AND table_name = 'student_attendance'
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✓ student_attendance table already exists")
            
            # Check columns
            cursor.execute("SHOW COLUMNS FROM student_attendance")
            columns = [row[0] for row in cursor.fetchall()]
            print(f"  Existing columns: {', '.join(columns)}\n")
            return True
        
        print("Creating student_attendance table...")
        cursor.execute("""
            CREATE TABLE student_attendance (
                id INT PRIMARY KEY AUTO_INCREMENT,
                student_id INT NOT NULL,
                school_id INT NOT NULL,
                date DATE NOT NULL,
                morning_status VARCHAR(20) CHECK(morning_status IN ('present', 'absent', 'late', 'leave')),
                morning_time TIME,
                morning_marked_by INT,
                morning_notes TEXT,
                afternoon_status VARCHAR(20) CHECK(afternoon_status IN ('present', 'absent', 'late', 'leave')),
                afternoon_time TIME,
                afternoon_marked_by INT,
                afternoon_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (school_id) REFERENCES schools(id),
                FOREIGN KEY (morning_marked_by) REFERENCES staff(id),
                FOREIGN KEY (afternoon_marked_by) REFERENCES staff(id),
                UNIQUE KEY unique_student_date (student_id, date)
            )
        """)
        conn.commit()
        print("✓ student_attendance table created successfully\n")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Migration error: {e}")
        return False

if __name__ == "__main__":
    print("=== Student Attendance Table Migration ===\n")
    create_student_attendance_table()
