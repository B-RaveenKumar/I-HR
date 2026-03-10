import pymysql

conn = pymysql.connect(host='mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech', port=32261, user='root', password='Vish0803', database='ihrdb', cursorclass=pymysql.cursors.DictCursor)
cur = conn.cursor()

# Find Manjukumaran
cur.execute("SELECT id, staff_id, school_id FROM staff WHERE staff_id = %s", ('832501',))
staff = cur.fetchone()
print('Staff:', staff)

if staff:
    sid = staff['id']
    school_id = staff['school_id']
    
    # Check leave quotas
    cur.execute("SELECT * FROM staff_leave_quotas WHERE staff_id = %s AND quota_year = 2026", (sid,))
    rows = cur.fetchall()
    print(f"\nLeave quotas ({len(rows)} records):")
    for r in rows:
        print(f"  {r}")
    
    # Check with school_id filter
    cur.execute("SELECT * FROM staff_leave_quotas WHERE staff_id = %s AND school_id = %s AND quota_year = 2026", (sid, school_id))
    rows = cur.fetchall()
    print(f"\nLeave quotas with school_id={school_id} ({len(rows)} records):")
    for r in rows:
        print(f"  {r}")
    
    # Check OD quotas
    cur.execute("SELECT * FROM staff_od_quotas WHERE staff_id = %s AND quota_year = 2026", (sid,))
    rows = cur.fetchall()
    print(f"\nOD quotas ({len(rows)} records):")
    for r in rows:
        print(f"  {r}")
    
    # Check Permission quotas
    cur.execute("SELECT * FROM staff_permission_quotas WHERE staff_id = %s AND quota_year = 2026", (sid,))
    rows = cur.fetchall()
    print(f"\nPermission quotas ({len(rows)} records):")
    for r in rows:
        print(f"  {r}")

    # Also check unique keys
    cur.execute("SHOW INDEX FROM staff_leave_quotas WHERE Non_unique = 0")
    print("\nUnique keys on staff_leave_quotas:")
    for r in cur.fetchall():
        print(f"  {r['Key_name']}: {r['Column_name']}")

conn.close()
