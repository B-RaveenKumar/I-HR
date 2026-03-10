import pymysql

conn = pymysql.connect(host='mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech', port=32261, user='root', password='Vish0803', database='ihrdb', cursorclass=pymysql.cursors.DictCursor)
cur = conn.cursor()

# Test insert for staff_id=91, school_id=4, year=2026, leave_type=CL
try:
    sql = """INSERT INTO staff_leave_quotas
        (staff_id, school_id, quota_year, leave_type, allocated_days, used_days)
        VALUES (%s, %s, %s, %s, %s, 0)
        ON DUPLICATE KEY UPDATE allocated_days = VALUES(allocated_days)"""
    cur.execute(sql, (91, 4, 2026, 'CL', 12))
    print(f"Rows affected: {cur.rowcount}")
    conn.commit()
    
    # Verify
    cur.execute("SELECT * FROM staff_leave_quotas WHERE staff_id = 91 AND quota_year = 2026")
    rows = cur.fetchall()
    print(f"After insert - {len(rows)} records:")
    for r in rows:
        print(f"  {r}")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

# Clean up our test record
cur.execute("DELETE FROM staff_leave_quotas WHERE staff_id = 91 AND quota_year = 2026")
conn.commit()
print("\nCleaned up test records")

conn.close()
