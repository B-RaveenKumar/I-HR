import pymysql

conn = pymysql.connect(host='mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech', port=32261, user='root', password='Vish0803', database='ihrdb', cursorclass=pymysql.cursors.DictCursor)
cur = conn.cursor()

tables = ['staff_leave_quotas', 'staff_od_quotas', 'staff_permission_quotas']

for table in tables:
    print(f"\n=== Fixing {table} ===")
    
    # Get max id
    cur.execute(f"SELECT MAX(id) as max_id FROM {table}")
    row = cur.fetchone()
    max_id = row['max_id'] or 0
    print(f"  Max id: {max_id}")
    
    # Fix any id=0 rows (assign them proper IDs)
    cur.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE id = 0")
    zero_count = cur.fetchone()['cnt']
    if zero_count > 0:
        print(f"  Found {zero_count} rows with id=0, fixing...")
        cur.execute(f"SELECT * FROM {table} WHERE id = 0")
        zero_rows = cur.fetchall()
        for zr in zero_rows:
            max_id += 1
            cur.execute(f"UPDATE {table} SET id = %s WHERE id = 0 LIMIT 1", (max_id,))
        conn.commit()
        print(f"  Fixed, new max_id: {max_id}")
    
    # Add AUTO_INCREMENT to id column
    try:
        cur.execute(f"ALTER TABLE {table} MODIFY COLUMN id INT NOT NULL AUTO_INCREMENT")
        print(f"  Added AUTO_INCREMENT")
    except Exception as e:
        print(f"  Error adding AUTO_INCREMENT: {e}")
    
    # Set AUTO_INCREMENT value
    auto_inc = max_id + 1
    try:
        cur.execute(f"ALTER TABLE {table} AUTO_INCREMENT = {auto_inc}")
        print(f"  Set AUTO_INCREMENT = {auto_inc}")
    except Exception as e:
        print(f"  Error setting AUTO_INCREMENT: {e}")
    
    conn.commit()

# Also fix column types on staff_permission_quotas
print("\n=== Fixing permission_quotas column types ===")
try:
    cur.execute("""ALTER TABLE staff_permission_quotas 
        MODIFY COLUMN allocated_hours DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        MODIFY COLUMN used_hours DECIMAL(10,2) NOT NULL DEFAULT 0.00""")
    conn.commit()
    print("  Fixed allocated_hours and used_hours to DECIMAL(10,2)")
except Exception as e:
    print(f"  Error: {e}")

# Fix created_at/updated_at on all tables
print("\n=== Fixing timestamp columns ===")
for table in tables:
    try:
        cur.execute(f"""ALTER TABLE {table}
            MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            MODIFY COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP""")
        conn.commit()
        print(f"  Fixed timestamps on {table}")
    except Exception as e:
        print(f"  Error on {table}: {e}")

# Verify
print("\n=== Verification ===")
for table in tables:
    cur.execute(f"SHOW CREATE TABLE {table}")
    row = cur.fetchone()
    print(f"\n{row['Create Table']}")

# Test INSERT now works
print("\n=== Test INSERT ===")
try:
    cur.execute("""INSERT INTO staff_leave_quotas
        (staff_id, school_id, quota_year, leave_type, allocated_days, used_days)
        VALUES (%s, %s, %s, %s, %s, 0)
        ON DUPLICATE KEY UPDATE allocated_days = VALUES(allocated_days)""",
        (91, 4, 2026, 'CL', 12))
    print(f"INSERT CL: rows affected = {cur.rowcount}")
    
    cur.execute("""INSERT INTO staff_leave_quotas
        (staff_id, school_id, quota_year, leave_type, allocated_days, used_days)
        VALUES (%s, %s, %s, %s, %s, 0)
        ON DUPLICATE KEY UPDATE allocated_days = VALUES(allocated_days)""",
        (91, 4, 2026, 'SL', 7))
    print(f"INSERT SL: rows affected = {cur.rowcount}")
    
    conn.commit()
    
    cur.execute("SELECT * FROM staff_leave_quotas WHERE staff_id = 91 AND quota_year = 2026")
    for r in cur.fetchall():
        print(f"  {r['leave_type']}: allocated={r['allocated_days']}, used={r['used_days']}")
    
    # Clean up test records
    cur.execute("DELETE FROM staff_leave_quotas WHERE staff_id = 91 AND quota_year = 2026")
    conn.commit()
    print("Test records cleaned up")
    
except Exception as e:
    print(f"Test INSERT failed: {e}")
    conn.rollback()

conn.close()
print("\nDone!")
