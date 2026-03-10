import pymysql

conn = pymysql.connect(host='mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech', port=32261, user='root', password='Vish0803', database='ihrdb', cursorclass=pymysql.cursors.DictCursor)
cur = conn.cursor()

for table in ['staff_leave_quotas', 'staff_od_quotas', 'staff_permission_quotas']:
    print(f"\n=== {table} ===")
    cur.execute(f"SHOW CREATE TABLE {table}")
    row = cur.fetchone()
    print(row['Create Table'])
    
    # Check record count
    cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
    print(f"Records: {cur.fetchone()['cnt']}")

conn.close()
