"""
Database Migration Script: Unified Biometric Ecosystem
Creates tables for multi-device, ADMS, and Local Agent support with institution segregation.

Run this script to upgrade from single-device to multi-device architecture.
"""

import sqlite3
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    db_path = 'vishnorex.db'
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    return sqlite3.connect(db_path)

def backup_database():
    """Create backup before migration"""
    db_path = 'vishnorex.db'
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_filename = f"vishnorex_pre_biometric_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    import shutil
    shutil.copy2(db_path, backup_path)
    logger.info(f"✓ Database backup created: {backup_path}")
    return backup_path

def check_existing_tables(conn):
    """Check which tables already exist"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    return existing_tables

def migrate_step_1_create_biometric_agents(conn):
    """Step 1: Create biometric_agents table for Local Agent software"""
    logger.info("Step 1: Creating biometric_agents table...")
    
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='biometric_agents'")
    if cursor.fetchone():
        logger.warning("  ⚠ Table 'biometric_agents' already exists, skipping...")
        return False
    
    cursor.execute('''
        CREATE TABLE biometric_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            agent_name VARCHAR(100) NOT NULL,
            api_key VARCHAR(64) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            last_heartbeat DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('CREATE INDEX idx_agents_school ON biometric_agents(school_id)')
    cursor.execute('CREATE INDEX idx_agents_active ON biometric_agents(is_active)')
    
    conn.commit()
    logger.info("  ✓ Table 'biometric_agents' created successfully")
    return True

def migrate_step_2_create_biometric_devices(conn):
    """Step 2: Create biometric_devices table for multi-device management"""
    logger.info("Step 2: Creating biometric_devices table...")
    
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='biometric_devices'")
    if cursor.fetchone():
        logger.warning("  ⚠ Table 'biometric_devices' already exists, skipping...")
        return False
    
    cursor.execute('''
        CREATE TABLE biometric_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            agent_id INTEGER,
            device_name VARCHAR(100) NOT NULL,
            connection_type VARCHAR(20) CHECK(connection_type IN ('Direct_LAN', 'ADMS', 'Agent_LAN')) NOT NULL,
            ip_address VARCHAR(45),
            port INTEGER DEFAULT 4370,
            serial_number VARCHAR(50),
            is_active BOOLEAN DEFAULT 1,
            last_sync DATETIME,
            sync_status VARCHAR(20) DEFAULT 'unknown',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
            FOREIGN KEY (agent_id) REFERENCES biometric_agents(id) ON DELETE SET NULL,
            UNIQUE(school_id, device_name)
        )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('CREATE INDEX idx_devices_school ON biometric_devices(school_id)')
    cursor.execute('CREATE INDEX idx_devices_agent ON biometric_devices(agent_id)')
    cursor.execute('CREATE INDEX idx_devices_serial ON biometric_devices(serial_number)')
    cursor.execute('CREATE INDEX idx_devices_active ON biometric_devices(is_active)')
    
    conn.commit()
    logger.info("  ✓ Table 'biometric_devices' created successfully")
    return True

def migrate_step_3_add_school_id_to_cloud_devices(conn):
    """Step 3: Add school_id column to cloud_devices table"""
    logger.info("Step 3: Adding school_id to cloud_devices table...")
    
    cursor = conn.cursor()
    
    # Check if cloud_devices table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_devices'")
    if not cursor.fetchone():
        logger.warning("  ⚠ Table 'cloud_devices' does not exist, skipping...")
        return False
    
    # Check if school_id column already exists
    cursor.execute("PRAGMA table_info(cloud_devices)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'school_id' in columns:
        logger.warning("  ⚠ Column 'school_id' already exists in cloud_devices, skipping...")
        return False
    
    # Add school_id column
    cursor.execute('ALTER TABLE cloud_devices ADD COLUMN school_id INTEGER')
    
    # Add foreign key constraint (SQLite doesn't support ALTER TABLE ADD CONSTRAINT)
    # We'll enforce this in application logic
    
    # Create index
    cursor.execute('CREATE INDEX idx_cloud_devices_school ON cloud_devices(school_id)')
    
    conn.commit()
    logger.info("  ✓ Column 'school_id' added to cloud_devices")
    return True

def migrate_step_4_optimize_attendance_queries(conn):
    """Step 4: Add index on attendance(school_id) for faster queries"""
    logger.info("Step 4: Optimizing attendance table queries...")
    
    cursor = conn.cursor()
    
    # Check if attendance table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'")
    if not cursor.fetchone():
        logger.warning("  ⚠ Table 'attendance' does not exist, skipping...")
        return False
    
    # Check if index already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_attendance_school_date'")
    if cursor.fetchone():
        logger.warning("  ⚠ Index 'idx_attendance_school_date' already exists, skipping...")
        return False
    
    # Create composite index for common queries
    cursor.execute('CREATE INDEX idx_attendance_school_date ON attendance(school_id, date)')
    
    conn.commit()
    logger.info("  ✓ Index 'idx_attendance_school_date' created")
    return True

def migrate_step_5_migrate_existing_device(conn):
    """Step 5: Migrate existing hardcoded device to new schema"""
    logger.info("Step 5: Migrating existing device configuration...")
    
    cursor = conn.cursor()
    
    # Check if any devices already exist
    cursor.execute("SELECT COUNT(*) FROM biometric_devices")
    device_count = cursor.fetchone()[0]
    
    if device_count > 0:
        logger.warning(f"  ⚠ {device_count} device(s) already exist, skipping migration...")
        return False
    
    # Get the first school/institution (default)
    cursor.execute("SELECT id, name FROM schools ORDER BY id LIMIT 1")
    school = cursor.fetchone()
    
    if not school:
        logger.warning("  ⚠ No schools found in database. Please create at least one school first.")
        return False
    
    school_id, school_name = school
    
    # Insert the legacy device
    cursor.execute('''
        INSERT INTO biometric_devices 
        (school_id, device_name, connection_type, ip_address, port, is_active, last_sync)
        VALUES (?, 'Legacy Main Device', 'Direct_LAN', '192.168.1.201', 4370, 1, CURRENT_TIMESTAMP)
    ''', (school_id,))
    
    conn.commit()
    logger.info(f"  ✓ Legacy device (192.168.1.201) migrated to school: {school_name}")
    logger.info(f"    Device ID: {cursor.lastrowid}, Institution ID: {school_id}")
    return True

def migrate_step_6_update_cloud_devices_with_school(conn):
    """Step 6: Assign existing cloud devices to first school"""
    logger.info("Step 6: Updating cloud_devices with school_id...")
    
    cursor = conn.cursor()
    
    # Check if cloud_devices table has data
    cursor.execute("SELECT COUNT(*) FROM cloud_devices WHERE school_id IS NULL")
    unassigned_count = cursor.fetchone()[0]
    
    if unassigned_count == 0:
        logger.info("  ✓ All cloud devices already assigned to schools")
        return False
    
    # Get the first school
    cursor.execute("SELECT id FROM schools ORDER BY id LIMIT 1")
    school = cursor.fetchone()
    
    if not school:
        logger.warning("  ⚠ No schools found. Cloud devices remain unassigned.")
        return False
    
    school_id = school[0]
    
    # Update all unassigned cloud devices
    cursor.execute('UPDATE cloud_devices SET school_id = ? WHERE school_id IS NULL', (school_id,))
    updated = cursor.rowcount
    
    conn.commit()
    logger.info(f"  ✓ Assigned {updated} cloud device(s) to school ID: {school_id}")
    return True

def verify_migration(conn):
    """Verify migration was successful"""
    logger.info("\n=== Migration Verification ===")
    
    cursor = conn.cursor()
    
    # Check biometric_agents table
    cursor.execute("SELECT COUNT(*) FROM biometric_agents")
    agents_count = cursor.fetchone()[0]
    logger.info(f"✓ biometric_agents table: {agents_count} agent(s)")
    
    # Check biometric_devices table
    cursor.execute("SELECT COUNT(*) FROM biometric_devices")
    devices_count = cursor.fetchone()[0]
    logger.info(f"✓ biometric_devices table: {devices_count} device(s)")
    
    # Check cloud_devices school_id
    cursor.execute("SELECT COUNT(*) FROM cloud_devices WHERE school_id IS NOT NULL")
    cloud_assigned = cursor.fetchone()[0]
    logger.info(f"✓ cloud_devices with school_id: {cloud_assigned} device(s)")
    
    # Check attendance index
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_attendance_school_date'")
    attendance_index = cursor.fetchone()
    logger.info(f"✓ attendance index: {'Created' if attendance_index else 'Not Created'}")
    
    # Show device details
    if devices_count > 0:
        logger.info("\n=== Registered Devices ===")
        cursor.execute('''
            SELECT d.id, d.device_name, d.connection_type, d.ip_address, 
                   d.serial_number, s.name as school_name
            FROM biometric_devices d
            LEFT JOIN schools s ON d.school_id = s.id
        ''')
        for row in cursor.fetchall():
            device_id, name, conn_type, ip, serial, school = row
            logger.info(f"  Device #{device_id}: {name} ({conn_type})")
            logger.info(f"    Institution: {school}")
            if ip:
                logger.info(f"    IP: {ip}")
            if serial:
                logger.info(f"    Serial: {serial}")

def main():
    """Run the migration"""
    logger.info("=" * 60)
    logger.info("Unified Biometric Ecosystem - Database Migration")
    logger.info("=" * 60)
    
    try:
        # Step 0: Backup database
        logger.info("\nStep 0: Creating backup...")
        backup_path = backup_database()
        
        # Connect to database
        conn = get_db_connection()
        logger.info("\n✓ Connected to database")
        
        # Run migration steps
        steps = [
            migrate_step_1_create_biometric_agents,
            migrate_step_2_create_biometric_devices,
            migrate_step_3_add_school_id_to_cloud_devices,
            migrate_step_4_optimize_attendance_queries,
            migrate_step_5_migrate_existing_device,
            migrate_step_6_update_cloud_devices_with_school
        ]
        
        logger.info("\n=== Running Migration Steps ===\n")
        changes_made = False
        
        for step_func in steps:
            result = step_func(conn)
            if result:
                changes_made = True
        
        # Verify migration
        verify_migration(conn)
        
        # Close connection
        conn.close()
        
        logger.info("\n" + "=" * 60)
        if changes_made:
            logger.info("✓✓✓ Migration completed successfully! ✓✓✓")
            logger.info(f"Backup saved at: {backup_path}")
        else:
            logger.info("✓ Database already up to date (no changes needed)")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {str(e)}")
        logger.error("Database has been backed up. You can restore from backup if needed.")
        raise

if __name__ == "__main__":
    main()
