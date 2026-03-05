"""
Quick debug script to verify sub_admin_permissions table state.
Run with: python debug_sub_admin.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

# Load env
from dotenv import load_dotenv
load_dotenv()

# Try SQLite first
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'attendance.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== sub_admin_permissions ===")
rows = cur.execute("SELECT * FROM sub_admin_permissions").fetchall()
if rows:
    for r in rows:
        print(dict(r))
else:
    print("EMPTY - no rows found!")

print("\n=== staff table (first 5, relevant fields) ===")
rows = cur.execute("SELECT id, school_id, staff_id, full_name FROM staff LIMIT 5").fetchall()
for r in rows:
    print(dict(r))

conn.close()

# Also check if MySQL is used
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    print(f"\n==> MySQL DATABASE_URL detected: {DATABASE_URL[:40]}...")
    try:
        import pymysql
        # Parse URL manually
        # Format: mysql://user:pass@host/dbname
        url = DATABASE_URL.replace('mysql://', '').replace('mysql+pymysql://', '')
        user_pass, host_db = url.split('@')
        user, passwd = user_pass.split(':', 1)
        host_port_db = host_db.split('/')
        host_port = host_port_db[0]
        dbname = host_port_db[1].split('?')[0]
        host = host_port.split(':')[0]
        port = int(host_port.split(':')[1]) if ':' in host_port else 3306

        conn = pymysql.connect(host=host, user=user, password=passwd,
                               database=dbname, port=port,
                               cursorclass=pymysql.cursors.DictCursor)
        with conn.cursor() as cur:
            print("\n=== MySQL sub_admin_permissions ===")
            cur.execute("SELECT * FROM sub_admin_permissions")
            rows = cur.fetchall()
            if rows:
                for r in rows:
                    print(r)
            else:
                print("EMPTY - no rows in MySQL!")

            print("\n=== MySQL staff (first 5) ===")
            cur.execute("SELECT id, school_id, staff_id, full_name FROM staff LIMIT 5")
            for r in cur.fetchall():
                print(r)
        conn.close()
    except Exception as e:
        print(f"MySQL error: {e}")
else:
    print("\n==> No DATABASE_URL — using SQLite only")
