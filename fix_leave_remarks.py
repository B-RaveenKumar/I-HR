# fix_leave_remarks.py
import os
import pymysql
import re

DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb')

def _parse_mysql_url(url):
    url = re.sub(r'^mysql\+pymysql://', '', url)
    m = re.match(
        r'(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>.+)',
        url
    )
    if not m:
        raise ValueError(f"Cannot parse DATABASE_URL: {url!r}")
    return {
        'user':     m.group('user'),
        'password': m.group('password'),
        'host':     m.group('host'),
        'port':     int(m.group('port') or 3306),
        'database': m.group('db'),
        'charset':  'utf8mb4',
        'autocommit': True
    }

def fix():
    params = _parse_mysql_url(DATABASE_URL)
    conn = pymysql.connect(**params)
    cursor = conn.cursor()
    
    for table in ['leave_applications', 'on_duty_applications', 'permission_applications']:
        print(f"\nChecking columns in {table}...")
        cursor.execute(f"SHOW COLUMNS FROM {table}")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Columns in {table}: {columns}")
        
        if 'admin_remarks' not in columns:
            print(f"Adding admin_remarks to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN admin_remarks TEXT")
            print(f"Success: Added admin_remarks to {table}")
            
    conn.close()

if __name__ == "__main__":
    fix()
