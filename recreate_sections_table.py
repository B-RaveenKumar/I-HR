"""
Recreate timetable_sections table with proper schema including section_code
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
    print("RECREATE timetable_sections TABLE WITH PROPER SCHEMA")
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
    cursor.execute("DESCRIBE timetable_sections")
    columns = cursor.fetchall()
    
    print("Current columns:")
    for col in columns:
        print(f"  {col['Field']}: {col['Type']}")
    
    has_section_code = any(col['Field'] == 'section_code' for col in columns)
    print(f"\nHas section_code column: {'✓ YES' if has_section_code else '✗ NO'}")
    
    # Step 2: Backup existing data
    print("\nStep 2: Backing up existing data...")
    print("-"*80)
    cursor.execute("SELECT school_id, level_id, section_name FROM timetable_sections")
    backup_records = cursor.fetchall()
    print(f"Backed up {len(backup_records)} records")
    
    # Step 3: Drop and recreate table
    print("\nStep 3: Recreating table with proper schema...")
    print("-"*80)
    
    cursor.execute("DROP TABLE IF EXISTS timetable_sections")
    print("  ✓ Dropped old table")
    
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
            UNIQUE KEY unique_section (school_id, level_id, section_code),
            INDEX idx_school_level (school_id, level_id),
            INDEX idx_active (is_active)
        )
    """)
    print("  ✓ Created new table with proper schema")
    
    # Step 4: Restore data
    if backup_records:
        print("\nStep 4: Restoring data...")
        print("-"*80)
        restored = 0
        for r in backup_records:
            # Generate section_code from section_name
            section_code = str(r['section_name']).strip().upper().replace(" ", "_")
            try:
                cursor.execute("""
                    INSERT INTO timetable_sections (school_id, level_id, section_name, section_code)
                    VALUES (%s, %s, %s, %s)
                """, (r['school_id'], r['level_id'], r['section_name'], section_code))
                restored += 1
            except pymysql.err.IntegrityError as e:
                print(f"  ⚠️ Skipped duplicate: School {r['school_id']}, Level {r['level_id']}, Section {r['section_name']}")
        
        conn.commit()
        print(f"  ✓ Restored {restored} records")
    
    # Step 5: Verify
    print("\nStep 5: Verification...")
    print("-"*80)
    cursor.execute("DESCRIBE timetable_sections")
    columns = cursor.fetchall()
    
    required_columns = ['id', 'school_id', 'level_id', 'section_name', 'section_code', 'capacity', 'is_active', 'created_at', 'updated_at']
    print("Required columns check:")
    for col_name in required_columns:
        has_col = any(col['Field'] == col_name for col in columns)
        status = "✓" if has_col else "✗"
        print(f"  {status} {col_name}")
    
    id_col = next((col for col in columns if col['Field'] == 'id'), None)
    if id_col and id_col['Extra'] == 'auto_increment':
        print("\n✓ id column has AUTO_INCREMENT")
    
    # Show final data
    cursor.execute("SELECT * FROM timetable_sections ORDER BY id")
    final_records = cursor.fetchall()
    print(f"\nFinal records ({len(final_records)}):")
    for r in final_records:
        print(f"  ID:{r['id']:3d} | School:{r['school_id']} Level:{r['level_id']} | Name:{r['section_name']} Code:{r['section_code']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ SUCCESS! Table recreated with proper schema")
    print("   Restart Flask to use the updated table")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
