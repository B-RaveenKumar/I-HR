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

def migrate():
    params = _parse_mysql_url(DATABASE_URL)
    conn = pymysql.connect(**params)
    cursor = conn.cursor()
    
    print("Creating report_history table if not exists...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_history (
            id INT PRIMARY KEY AUTO_INCREMENT,
            school_id INT NOT NULL,
            report_type VARCHAR(100) NOT NULL,
            report_name VARCHAR(255) NOT NULL,
            format VARCHAR(50) NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("Success: report_history table is ready")
    conn.close()

if __name__ == "__main__":
    migrate()
