import os
import pymysql
import re

DATABASE_URL = 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb'

def check_data():
    url = re.sub(r'^mysql\+pymysql://', '', DATABASE_URL)
    m = re.match(
        r'(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>.+)',
        url
    )
    
    conn = pymysql.connect(
        user=m.group('user'),
        password=m.group('password'),
        host=m.group('host'),
        port=int(m.group('port') or 3306),
        database=m.group('db'),
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT `class`, standard, section, roll_number FROM students LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

if __name__ == '__main__':
    check_data()
