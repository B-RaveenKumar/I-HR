"""
Fix timetable_sections table AUTO_INCREMENT issue
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
    print("FIX timetable_sections TABLE AUTO_INCREMENT")
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
    
    # Step 1: Check current table structure
    print("\nStep 1: Checking table structure...")
    print("-"*80)
    cursor.execute("DESCRIBE timetable_sections")
    columns = cursor.fetchall()
    
    print("Current columns:")
    for col in columns:
        print(f"  {col['Field']}: {col['Type']} | Null:{col['Null']} | Key:{col['Key']} | Default:{col['Default']} | Extra:{col['Extra']}")
    
    has_auto_increment = any(col['Extra'] == 'auto_increment' for col in columns if col['Field'] == 'id')
    print(f"\nAUTO_INCREMENT status: {'✓ Enabled' if has_auto_increment else '✗ DISABLED'}")
    
    # Step 2: Check existing records
    print("\nStep 2: Checking existing records...")
    print("-"*80)
    cursor.execute("SELECT * FROM timetable_sections ORDER BY id")
    records = cursor.fetchall()
    
    print(f"Total records: {len(records)}")
    if records:
        print("\nExisting sections:")
        for r in records:
            id_str = str(r['id']) if r['id'] is not None else 'NULL'
            print(f"  ID:{id_str:4s} | School:{r['school_id']} Level:{r['level_id']} | Name:{r['section_name']}")
    
    # Check for problematic records
    cursor.execute("SELECT COUNT(*) as count FROM timetable_sections WHERE id IS NULL OR id = 0")
    problem_count = cursor.fetchone()['count']
    
    if problem_count > 0:
        print(f"\n⚠️ Found {problem_count} records with NULL or 0 id")
    
    # Step 3: Fix AUTO_INCREMENT
    if not has_auto_increment or problem_count > 0:
        print("\nStep 3: Fixing AUTO_INCREMENT...")
        print("-"*80)
        
        # Get records to preserve
        cursor.execute("SELECT school_id, level_id, section_name FROM timetable_sections")
        all_records = cursor.fetchall()
        
        # Drop and recreate with proper structure
        print("Recreating table with proper AUTO_INCREMENT...")
        
        # Backup data
        print(f"  Backing up {len(all_records)} records...")
        
        # Drop table
        cursor.execute("DROP TABLE IF EXISTS timetable_sections")
        print("  ✓ Dropped old table")
        
        # Recreate with AUTO_INCREMENT and all required columns
        cursor.execute("""
            CREATE TABLE timetable_sections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                school_id INT NOT NULL,
                level_id INT NOT NULL,
                section_name VARCHAR(255) NOT NULL,
                section_code VARCHAR(255) NOT NULL,
                capacity INT DEFAULT 60,
                is_active INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_section (school_id, level_id, section_code)
            )
        """)
        print("  ✓ Created new table with AUTO_INCREMENT")
        
        # Restore data
        if all_records:
            print(f"  Restoring {len(all_records)} records...")
            for r in all_records:
                # Generate section_code from section_name (same logic as app)
                section_code = str(r['section_name']).strip().upper().replace(" ", "_")
                cursor.execute("""
                    INSERT INTO timetable_sections (school_id, level_id, section_name, section_code)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE section_name = section_name
                """, (r['school_id'], r['level_id'], r['section_name'], section_code))
            print(f"  ✓ Restored {len(all_records)} records")
        
        conn.commit()
        print("\n✅ Table structure fixed!")
    else:
        print("\n✅ Table already has proper AUTO_INCREMENT")
    
    # Step 4: Verify fix
    print("\nStep 4: Verifying fix...")
    print("-"*80)
    cursor.execute("DESCRIBE timetable_sections")
    columns = cursor.fetchall()
    
    id_column = next((col for col in columns if col['Field'] == 'id'), None)
    if id_column and id_column['Extra'] == 'auto_increment':
        print("✓ id column has AUTO_INCREMENT")
        print("✓ id column is PRIMARY KEY")
        
        # Show final records
        cursor.execute("SELECT * FROM timetable_sections ORDER BY id")
        final_records = cursor.fetchall()
        print(f"\nFinal state ({len(final_records)} sections):")
        for r in final_records:
            print(f"  ID:{r['id']:3d} | School:{r['school_id']} Level:{r['level_id']} | Name:{r['section_name']}")
        
        # Test insert
        print("\nTesting new insert...")
        try:
            cursor.execute("""
                INSERT INTO timetable_sections (school_id, level_id, section_name)
                VALUES (999, 999, 'TEST_SECTION')
            """)
            test_id = cursor.lastrowid
            print(f"✓ Test insert successful with auto-generated ID: {test_id}")
            
            # Clean up test record
            cursor.execute("DELETE FROM timetable_sections WHERE id = %s", (test_id,))
            conn.commit()
            print("✓ Test record cleaned up")
        except Exception as e:
            print(f"✗ Test insert failed: {e}")
    else:
        print("✗ AUTO_INCREMENT still not configured properly")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("💡 NEXT STEP: Restart Flask application")
    print("   After restart, section creation will work correctly!")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
