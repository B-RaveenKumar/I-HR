"""
Database Migration Script: Universal ADMS Receiver Support
Adds protocol-agnostic columns to biometric_devices table for multi-format device support.

This migration enables the system to:
1. Track device model and firmware version
2. Auto-detect and store protocol type (Text/JSON/XML)
3. Support all biometric types (Face, Finger, Palm, Card)
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
    
    backup_filename = f"vishnorex_pre_universal_adms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    import shutil
    shutil.copy2(db_path, backup_path)
    logger.info(f"✓ Database backup created: {backup_path}")
    return backup_path

def add_universal_adms_columns(conn):
    """Add columns for universal ADMS protocol support"""
    logger.info("Adding Universal ADMS columns to biometric_devices table...")
    
    cursor = conn.cursor()
    
    # Check if biometric_devices table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='biometric_devices'")
    if not cursor.fetchone():
        logger.error("  ❌ Table 'biometric_devices' does not exist!")
        logger.error("  Please run 'migrate_biometric_system.py' first.")
        return False
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(biometric_devices)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Define new columns to add
    new_columns = [
        ('device_model', 'VARCHAR(100)', 'Device model name (e.g., uFace802, K40, SpeedFace)'),
        ('firmware_ver', 'VARCHAR(50)', 'Firmware version'),
        ('protocol_type', "VARCHAR(20) DEFAULT 'Text' CHECK(protocol_type IN ('Text', 'JSON', 'XML', 'Auto'))", 'Data format protocol'),
        ('biometric_types', 'TEXT', 'JSON array of supported types: ["face", "fingerprint", "palm", "card"]'),
        ('platform', 'VARCHAR(50)', 'Device platform/architecture'),
        ('last_handshake', 'DATETIME', 'Last device handshake/options request'),
        ('raw_options_data', 'TEXT', 'Raw device options data for debugging')
    ]
    
    added_count = 0
    for col_name, col_type, description in new_columns:
        if col_name not in columns:
            try:
                cursor.execute(f'ALTER TABLE biometric_devices ADD COLUMN {col_name} {col_type}')
                logger.info(f"  ✓ Added column: {col_name} - {description}")
                added_count += 1
            except Exception as e:
                logger.error(f"  ❌ Failed to add column {col_name}: {e}")
        else:
            logger.info(f"  ⚠ Column '{col_name}' already exists, skipping...")
    
    if added_count > 0:
        conn.commit()
        logger.info(f"  ✓ Successfully added {added_count} column(s)")
    
    return True

def create_protocol_detection_log_table(conn):
    """Create table to log raw protocol data for debugging"""
    logger.info("Creating protocol_detection_log table...")
    
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='protocol_detection_log'")
    if cursor.fetchone():
        logger.warning("  ⚠ Table 'protocol_detection_log' already exists, skipping...")
        return False
    
    cursor.execute('''
        CREATE TABLE protocol_detection_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            serial_number VARCHAR(50),
            request_method VARCHAR(10),
            request_path VARCHAR(255),
            content_type VARCHAR(100),
            raw_body TEXT,
            raw_headers TEXT,
            detected_format VARCHAR(20),
            parsed_successfully BOOLEAN DEFAULT 0,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES biometric_devices(id) ON DELETE SET NULL
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX idx_protocol_log_device ON protocol_detection_log(device_id)')
    cursor.execute('CREATE INDEX idx_protocol_log_serial ON protocol_detection_log(serial_number)')
    cursor.execute('CREATE INDEX idx_protocol_log_date ON protocol_detection_log(created_at)')
    
    conn.commit()
    logger.info("  ✓ Table 'protocol_detection_log' created successfully")
    return True

def create_unknown_device_log_table(conn):
    """Create table to capture data from unregistered devices"""
    logger.info("Creating unknown_device_log table...")
    
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='unknown_device_log'")
    if cursor.fetchone():
        logger.warning("  ⚠ Table 'unknown_device_log' already exists, skipping...")
        return False
    
    cursor.execute('''
        CREATE TABLE unknown_device_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number VARCHAR(50),
            ip_address VARCHAR(45),
            device_model VARCHAR(100),
            firmware_ver VARCHAR(50),
            platform VARCHAR(50),
            request_type VARCHAR(50),
            raw_payload TEXT,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            attempt_count INTEGER DEFAULT 1,
            notes TEXT
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX idx_unknown_device_serial ON unknown_device_log(serial_number)')
    cursor.execute('CREATE INDEX idx_unknown_device_ip ON unknown_device_log(ip_address)')
    
    conn.commit()
    logger.info("  ✓ Table 'unknown_device_log' created successfully")
    return True

def main():
    """Main migration function"""
    print("=" * 80)
    print("UNIVERSAL ADMS RECEIVER - DATABASE MIGRATION")
    print("=" * 80)
    print("\nThis migration adds support for:")
    print("  • Multi-protocol device detection (Text, JSON, XML)")
    print("  • Device model and firmware tracking")
    print("  • Unknown device logging")
    print("  • Protocol debugging capabilities")
    print("=" * 80)
    
    try:
        # Create backup
        backup_path = backup_database()
        print(f"\n✓ Backup created: {backup_path}")
        
        # Connect to database
        conn = get_db_connection()
        logger.info("✓ Connected to database")
        
        # Run migrations
        print("\n--- Running Migrations ---\n")
        
        success_count = 0
        
        if add_universal_adms_columns(conn):
            success_count += 1
        
        if create_protocol_detection_log_table(conn):
            success_count += 1
        
        if create_unknown_device_log_table(conn):
            success_count += 1
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        print(f"\n✓ Successfully completed {success_count} migration step(s)")
        print("\n📋 Next Steps:")
        print("  1. Restart your Flask application")
        print("  2. Review the UNIVERSAL_ADMS_RECEIVER.md documentation")
        print("  3. Test with different device types")
        print("  4. Monitor protocol_detection_log for debugging")
        print("\n🔍 To view unknown devices attempting to connect:")
        print("     SELECT * FROM unknown_device_log ORDER BY last_seen DESC;")
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
