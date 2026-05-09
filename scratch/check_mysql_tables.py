import os
import pymysql
import re

DATABASE_URL = 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb'

def _parse_mysql_url(url):
    url = re.sub(r'^mysql\+pymysql://', '', url)
    m = re.match(r'(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>.+)', url)
    return {
        'user': m.group('user'),
        'password': m.group('password'),
        'host': m.group('host'),
        'port': int(m.group('port') or 3306),
        'database': m.group('db'),
        'charset': 'utf8mb4'
    }

params = _parse_mysql_url(DATABASE_URL)
conn = pymysql.connect(**params)
try:
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tables in database:")
        for t in tables:
            print(f"- {t[0]}")
        
        cursor.execute("SHOW COLUMNS FROM scheduled_reports")
        columns = cursor.fetchall()
        print("\nColumns in scheduled_reports:")
        for c in columns:
            print(f"- {c[0]} ({c[1]})")
finally:
    conn.close()
