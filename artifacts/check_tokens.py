import os
import sys
from flask import Flask

sys.path.append(os.getcwd())
from database import get_db

app = Flask(__name__)

with app.app_context():
    try:
        db = get_db()
        # Check Staff ID 91 and 410
        rows = db.execute('SELECT id, staff_id, full_name FROM staff WHERE id IN (91, 410)').fetchall()
        print("Staff Identities:")
        for row in rows:
            print(dict(row))
            
        # Check tokens again
        tokens = db.execute('SELECT * FROM user_fcm_tokens').fetchall()
        print("\nRegistered Tokens:")
        for t in tokens:
            print(dict(t))
    except Exception as e:
        print(f"Error: {e}")
