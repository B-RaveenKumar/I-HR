import pymysql

conn = pymysql.connect(host='mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech', port=32261, user='root', password='Vish0803', database='ihrdb', cursorclass=pymysql.cursors.DictCursor)
cur = conn.cursor()

tables = ['staff_leave_quotas', 'staff_od_quotas', 'staff_permission_quotas']

# First fix the string 'CURRENT_TIMESTAMP' values in varchar columns
for table in tables:
    print(f"\n=== Fixing timestamps in {table} ===")
    # Set bad string values to NULL first
    cur.execute(f"UPDATE {table} SET created_at = NULL WHERE created_at = 'CURRENT_TIMESTAMP' OR created_at = ''")
    print(f"  Fixed {cur.rowcount} created_at rows")
    cur.execute(f"UPDATE {table} SET updated_at = NULL WHERE updated_at = 'CURRENT_TIMESTAMP' OR updated_at = ''")
    print(f"  Fixed {cur.rowcount} updated_at rows")
    conn.commit()
    
    # Now alter to TIMESTAMP
    try:
        cur.execute(f"""ALTER TABLE {table}
            MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            MODIFY COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP""")
        conn.commit()
        print(f"  Altered to TIMESTAMP columns")
    except Exception as e:
        print(f"  Error: {e}")

# Verify final state
print("\n=== Final Verification ===")
for table in tables:
    cur.execute(f"SHOW CREATE TABLE {table}")
    row = cur.fetchone()
    print(f"\n{row['Create Table']}")

# Test INSERT
print("\n=== Test INSERT ===")
try:
    cur.execute("""INSERT INTO staff_leave_quotas
        (staff_id, school_id, quota_year, leave_type, allocated_days, used_days)
        VALUES (%s, %s, %s, %s, %s, 0)
        ON DUPLICATE KEY UPDATE allocated_days = VALUES(allocated_days)""",
        (91, 4, 2026, 'CL', 12))
    print(f"INSERT CL: OK (rows={cur.rowcount})")
    
    cur.execute("""INSERT INTO staff_leave_quotas
        (staff_id, school_id, quota_year, leave_type, allocated_days, used_days)
        VALUES (%s, %s, %s, %s, %s, 0)
        ON DUPLICATE KEY UPDATE allocated_days = VALUES(allocated_days)""",
        (91, 4, 2026, 'SL', 7))
    print(f"INSERT SL: OK (rows={cur.rowcount})")
    
    cur.execute("""INSERT INTO staff_od_quotas
        (staff_id, school_id, quota_year, allocated_days, used_days)
        VALUES (%s, %s, %s, %s, 0)
        ON DUPLICATE KEY UPDATE allocated_days = VALUES(allocated_days)""",
        (91, 4, 2026, 10))
    print(f"INSERT OD: OK (rows={cur.rowcount})")
    
    cur.execute("""INSERT INTO staff_permission_quotas
        (staff_id, school_id, quota_year, allocated_hours, used_hours)
        VALUES (%s, %s, %s, %s, 0.0)
        ON DUPLICATE KEY UPDATE allocated_hours = VALUES(allocated_hours)""",
        (91, 4, 2026, 15.0))
    print(f"INSERT Permission: OK (rows={cur.rowcount})")
    
    conn.commit()
    
    # Verify all records exist
    cur.execute("SELECT * FROM staff_leave_quotas WHERE staff_id = 91 AND quota_year = 2026")
    for r in cur.fetchall():
        print(f"  Leave {r['leave_type']}: allocated={r['allocated_days']}")
    
    cur.execute("SELECT * FROM staff_od_quotas WHERE staff_id = 91 AND quota_year = 2026")
    for r in cur.fetchall():
        print(f"  OD: allocated={r['allocated_days']}")
    
    cur.execute("SELECT * FROM staff_permission_quotas WHERE staff_id = 91 AND quota_year = 2026")
    for r in cur.fetchall():
        print(f"  Permission: allocated={r['allocated_hours']}")
    
    # Clean up
    cur.execute("DELETE FROM staff_leave_quotas WHERE staff_id = 91 AND quota_year = 2026")
    cur.execute("DELETE FROM staff_od_quotas WHERE staff_id = 91 AND quota_year = 2026")
    cur.execute("DELETE FROM staff_permission_quotas WHERE staff_id = 91 AND quota_year = 2026")
    conn.commit()
    print("\nTest records cleaned up - ALL INSERTS WORKING!")
    
except Exception as e:
    print(f"Test INSERT failed: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()

conn.close()
