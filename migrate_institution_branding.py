"""
Database Migration Script: Add Institution Branding Support
Adds logo_path and branding_enabled columns to schools table
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = 'vishnorex.db'
BACKUP_DIR = 'backups'

def create_backup():
    """Create a backup of the database before migration"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'vishnorex_before_branding_{timestamp}.db')
    
    if os.path.exists(DB_PATH):
        import shutil
        shutil.copy2(DB_PATH, backup_file)
        print(f"✅ Database backup created: {backup_file}")
        return backup_file
    return None

def add_branding_columns():
    """Add logo_path and branding_enabled columns to schools table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(schools)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add logo_path column if it doesn't exist
        if 'logo_path' not in columns:
            cursor.execute('''
                ALTER TABLE schools 
                ADD COLUMN logo_path TEXT DEFAULT NULL
            ''')
            print("✅ Added 'logo_path' column to schools table")
        else:
            print("ℹ️  'logo_path' column already exists")
        
        # Add branding_enabled column if it doesn't exist
        if 'branding_enabled' not in columns:
            cursor.execute('''
                ALTER TABLE schools 
                ADD COLUMN branding_enabled INTEGER DEFAULT 1
            ''')
            print("✅ Added 'branding_enabled' column to schools table (default: enabled)")
        else:
            print("ℹ️  'branding_enabled' column already exists")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
        # Show current schools
        cursor.execute("SELECT id, name, logo_path, branding_enabled FROM schools")
        schools = cursor.fetchall()
        if schools:
            print("\n📋 Current Schools:")
            for school in schools:
                status = "Enabled" if school[3] else "Disabled"
                logo = school[2] if school[2] else "No logo"
                print(f"   ID: {school[0]} | {school[1]} | Logo: {logo} | Branding: {status}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def create_upload_directories():
    """Create necessary directories for logo uploads"""
    upload_dirs = [
        'static/uploads',
        'static/uploads/logos',
        'static/images'
    ]
    
    for directory in upload_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"ℹ️  Directory exists: {directory}")

def create_default_logo():
    """Create a placeholder for default logo if it doesn't exist"""
    default_logo_path = 'static/images/default_logo.png'
    if not os.path.exists(default_logo_path):
        print(f"\n⚠️  Default logo not found at: {default_logo_path}")
        print("   Please place a default logo image at this location")
        print("   Recommended size: 200x60px or similar aspect ratio")

if __name__ == '__main__':
    print("="*60)
    print("INSTITUTION BRANDING MIGRATION")
    print("="*60)
    print()
    
    # Step 1: Backup
    backup_file = create_backup()
    
    # Step 2: Add columns
    add_branding_columns()
    
    # Step 3: Create upload directories
    print("\n📁 Setting up upload directories...")
    create_upload_directories()
    
    # Step 4: Check for default logo
    create_default_logo()
    
    print("\n" + "="*60)
    print("MIGRATION COMPLETE!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("   1. Add institution logos via Admin Panel or directly to database")
    print("   2. Restart Flask application to load context processor")
    print("   3. Test by logging in with different institution accounts")
    print("   4. Update SQL: UPDATE schools SET logo_path='static/uploads/logos/school_name.png' WHERE id=X")
    print()
