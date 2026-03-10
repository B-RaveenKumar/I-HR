"""
Fix timetable_periods table structure
"""

import pymysql
from urllib.parse import urlparse

def parse_mysql_url(url):
    url = url.replace('mysql+pymysql://', '')
    parts = urlparse(f'mysql://{url}')
    return {
        'host': parts.hostname,
        'port': parts.port or 3306,
        'user': parts.username,
        'password': parts.password,
        'database': parts.path.lstrip('/')
    }

def main():
    db_url = 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb'
    config = parse_mysql_url(db_url)
    
    print("\n" + "="*80)
    print("FIX timetable_periods TABLE")
    print("="*80)
    
    conn = pymysql.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        cursorclass=pymysql.cursors.DictCursor
    )
    
    cursor = conn.cursor()
    
    # Step 1: Check current structure
    print("\nStep 1: Current table structure...")
    print("-"*80)
    cursor.execute("DESCRIBE timetable_periods")
    columns = cursor.fetchall()
    
    print("Current columns:")
    for col in columns:
        print(f"  {col['Field']:20s} | {col['Type']:20s} | Extra:{col['Extra']}")
    
    id_col = next((col for col in columns if col['Field'] == 'id'), None)
    has_auto_increment = id_col and id_col['Extra'] == 'auto_increment'
    print(f"\nAUTO_INCREMENT: {'✓' if has_auto_increment else '✗ MISSING'}")
    
    # Step 2: Backup existing data
    print("\nStep 2: Backing up existing data...")
    print("-"*80)
    cursor.execute("""
        SELECT school_id, level_id, section_id, day_of_week, period_number, 
               period_name, start_time, end_time, duration_minutes
        FROM timetable_periods
    """)
    backup_records = cursor.fetchall()
    print(f"Backed up {len(backup_records)} records")
    
    if backup_records:
        print("\nExisting periods:")
        for r in backup_records:
            print(f"  School:{r['school_id']} L:{r['level_id']} S:{r['section_id']} Day:{r['day_of_week']} | P{r['period_number']}: {r['period_name']} ({r['start_time']}-{r['end_time']})")
    
    # Step 3: Drop and recreate table
    print("\nStep 3: Recreating table with proper schema...")
    print("-"*80)
    
    cursor.execute("DROP TABLE IF EXISTS timetable_periods")
    print("  ✓ Dropped old table")
    
    cursor.execute("""
        CREATE TABLE timetable_periods (
            id INT AUTO_INCREMENT PRIMARY KEY,
            school_id INT NOT NULL,
            level_id INT,
            section_id INT,
            day_of_week INT,
            period_number INT NOT NULL,
            period_name VARCHAR(255),
            start_time VARCHAR(10) NOT NULL,
            end_time VARCHAR(10) NOT NULL,
            duration_minutes INT,
            is_active INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_school (school_id),
            INDEX idx_level_section (level_id, section_id),
            INDEX idx_day (day_of_week),
            INDEX idx_period_number (period_number)
        )
    """)
    print("  ✓ Created new table with proper schema")
    
    # Step 4: Restore data
    if backup_records:
        print("\nStep 4: Restoring data...")
        print("-"*80)
        restored = 0
        for r in backup_records:
            try:
                cursor.execute("""
                    INSERT INTO timetable_periods 
                    (school_id, level_id, section_id, day_of_week, period_number, 
                     period_name, start_time, end_time, duration_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    r['school_id'], r['level_id'], r['section_id'], r['day_of_week'],
                    r['period_number'], r['period_name'], r['start_time'], 
                    r['end_time'], r['duration_minutes']
                ))
                restored += 1
            except Exception as e:
                print(f"  ⚠️ Error restoring period: {e}")
        
        conn.commit()
        print(f"  ✓ Restored {restored} records")
    
    # Step 5: Verify
    print("\nStep 5: Verification...")
    print("-"*80)
    cursor.execute("DESCRIBE timetable_periods")
    columns = cursor.fetchall()
    
    id_col = next((col for col in columns if col['Field'] == 'id'), None)
    if id_col and id_col['Extra'] == 'auto_increment':
        print("✓ id column has AUTO_INCREMENT")
    
    required_columns = ['id', 'school_id', 'level_id', 'section_id', 'day_of_week', 
                        'period_number', 'period_name', 'start_time', 'end_time', 
                        'duration_minutes', 'is_active', 'created_at', 'updated_at']
    print("\nRequired columns:")
    for col_name in required_columns:
        has_col = any(col['Field'] == col_name for col in columns)
        status = "✓" if has_col else "✗"
        print(f"  {status} {col_name}")
    
    # Show final data
    cursor.execute("SELECT * FROM timetable_periods ORDER BY id")
    final_records = cursor.fetchall()
    print(f"\nFinal records ({len(final_records)}):")
    for r in final_records:
        print(f"  ID:{r['id']:3d} | School:{r['school_id']} L:{r['level_id']} S:{r['section_id']} Day:{r['day_of_week']} | P{r['period_number']}: {r['period_name']}")
    
    # Test insert
    print("\nTesting new insert...")
    try:
        cursor.execute("""
            INSERT INTO timetable_periods 
            (school_id, level_id, section_id, day_of_week, period_number, period_name, start_time, end_time, duration_minutes)
            VALUES (999, 999, 999, 1, 99, 'TEST', '09:00', '10:00', 60)
        """)
        test_id = cursor.lastrowid
        print(f"✓ Test insert successful with auto-generated ID: {test_id}")
        
        # Clean up test record
        cursor.execute("DELETE FROM timetable_periods WHERE id = %s", (test_id,))
        conn.commit()
        print("✓ Test record cleaned up")
    except Exception as e:
        print(f"✗ Test insert failed: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ SUCCESS! Table fixed with proper schema")
    print("   Restart Flask to use the updated table")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
