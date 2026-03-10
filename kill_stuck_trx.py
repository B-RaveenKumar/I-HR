import pymysql
from urllib.parse import urlparse

url = 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb'
url = url.replace('mysql+pymysql://', '')
parts = urlparse(f'mysql://{url}')
conn = pymysql.connect(host=parts.hostname, port=parts.port, user=parts.username, password=parts.password, database=parts.path.lstrip('/'), cursorclass=pymysql.cursors.DictCursor)
c = conn.cursor()

# Kill stuck transactions
c.execute('SELECT trx_id, trx_state, trx_started, trx_mysql_thread_id FROM information_schema.INNODB_TRX')
trx = c.fetchall()
print(f'Active transactions: {len(trx)}')

c.execute('SELECT CONNECTION_ID() as cid')
my_id = c.fetchone()['cid']

killed = 0
for t in trx:
    tid = t['trx_mysql_thread_id']
    if tid != my_id:
        try:
            c.execute(f'KILL {tid}')
            killed += 1
            print(f'  Killed thread {tid} (state: {t["trx_state"]}, started: {t["trx_started"]})')
        except Exception as e:
            print(f'  Could not kill {tid}: {e}')

print(f'Killed {killed} stuck transactions' if killed else 'No stuck transactions')

# Verify unique keys exist
for table, cols in [
    ('staff_leave_quotas', 'staff_id, school_id, quota_year, leave_type'),
    ('staff_od_quotas', 'staff_id, school_id, quota_year'),
    ('staff_permission_quotas', 'staff_id, school_id, quota_year')
]:
    c.execute(f'SHOW INDEX FROM {table} WHERE Non_unique = 0 AND Key_name != "PRIMARY"')
    idx = c.fetchall()
    print(f'{table}: {"UNIQUE key OK" if idx else "NO unique key!"}')

conn.close()
