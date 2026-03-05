from app import app
from database import get_db

def migrate_mysql():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        print("Migrating MySQL DB...")
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sub_admin_permissions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            staff_id VARCHAR(100) NOT NULL,
            module_name VARCHAR(100) NOT NULL,
            school_id INT NOT NULL,
            can_view TINYINT(1) DEFAULT 1,
            can_edit TINYINT(1) DEFAULT 0,
            can_delete TINYINT(1) DEFAULT 0,
            UNIQUE(staff_id, module_name, school_id)
        )
        ''')
        
        db.commit()
        print("Table 'sub_admin_permissions' created successfully!")

if __name__ == '__main__':
    migrate_mysql()
