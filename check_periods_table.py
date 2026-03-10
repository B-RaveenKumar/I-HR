"""
Check timetable_periods table structure in MySQL
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
    print("CHECK timetable_periods TABLE")
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
    
    # Check if table exists
    cursor.execute("SHOW TABLES LIKE 'timetable_periods'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("❌ Table 'timetable_periods' does NOT exist!")
        print("\nCreating table...")
        
        cursor.execute("""
            CREATE TABLE timetable_periods (
                id INT AUTO_INCREMENT PRIMARY KEY,
                school_id INT NOT NULL,
                level_id INT,
                section_id INT,
                day_of_week INT,
                period_number INT NOT NULL,
                period_name VARCHAR(255),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                duration_minutes INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_school (school_id),
                INDEX idx_level_section (level_id, section_id),
                INDEX idx_day (day_of_week)
            )
        """)
        conn.commit()
        print("✅ Table created successfully!")
    else:
        print("✓ Table 'timetable_periods' exists")
    
    # Show table structure
    print("\nTable structure:")
    print("-"*80)
    cursor.execute("DESCRIBE timetable_periods")
    columns = cursor.fetchall()
    
    for col in columns:
        print(f"  {col['Field']:20s} | {col['Type']:20s} | Null:{col['Null']} | Key:{col['Key']} | Extra:{col['Extra']}")
    
    # Check for records
    cursor.execute("SELECT COUNT(*) as count FROM timetable_periods")
    count = cursor.fetchone()['count']
    print(f"\nTotal records: {count}")
    
    if count > 0:
        print("\nSample records:")
        cursor.execute("SELECT * FROM timetable_periods LIMIT 5")
        records = cursor.fetchall()
        for r in records:
            print(f"  ID:{r['id']} | School:{r['school_id']} Level:{r.get('level_id')} Sect:{r.get('section_id')} | Period:{r['period_number']} {r['period_name']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
