import sqlite3
import os

def migrate():
    # Paths to databases
    db_path = os.path.join(os.path.dirname(__file__), 'attendance.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Migrating {db_path}...")
    
    # Create sub_admin_permissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sub_admin_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id VARCHAR NOT NULL,
            module_name VARCHAR NOT NULL,
            school_id INTEGER NOT NULL,
            can_view BOOLEAN DEFAULT 1,
            can_edit BOOLEAN DEFAULT 0,
            can_delete BOOLEAN DEFAULT 0,
            UNIQUE(staff_id, module_name, school_id)
        )
    ''')
    
    # The staff table is in attendance.db (we checked earlier it has staff details via checking queries like 'FROM staff s')
    
    conn.commit()
    conn.close()
    
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
