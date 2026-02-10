from app import app
from database import get_db

with app.app_context():
    db = get_db()
    cols = db.execute('PRAGMA table_info(holidays)').fetchall()
    print("Holidays table columns:")
    for col in cols:
        print(f"  {col[1]}: {col[2]}")