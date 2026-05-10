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

def check_schedules():
    params = _parse_mysql_url(DATABASE_URL)
    conn = pymysql.connect(**params)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    print("Checking scheduled_reports table...")
    cursor.execute("SELECT * FROM scheduled_reports")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    print("\nChecking system_settings for SMTP...")
    cursor.execute("SELECT * FROM system_settings WHERE setting_key = 'company_otp_provider_config'")
    smtp = cursor.fetchone()
    print(smtp)
    
    conn.close()

if __name__ == "__main__":
    check_schedules()
