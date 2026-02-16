"""
Migration script to fix timetable_periods UNIQUE constraint.
This script recreates the table with the correct constraint that allows
different classes/sections to have the same period numbers.
"""

import sqlite3
import os

def migrate_timetable_periods():
    # Find the database file
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found!")
        return

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Create a new table with the correct constraint
        print("Step 1: Creating new table with correct constraint...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_periods_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            level_id INTEGER,
            section_id INTEGER,
            period_number INTEGER NOT NULL,
            period_name TEXT,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration_minutes INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            day_of_week INTEGER,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (level_id) REFERENCES timetable_academic_levels(id),
            FOREIGN KEY (section_id) REFERENCES timetable_sections(id),
            UNIQUE(school_id, level_id, section_id, period_number)
        )
        ''')

        # Step 2: Check if old table exists and has data
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timetable_periods'")
        if cursor.fetchone():
            print("Step 2: Copying existing data from old table...")

            # Get column names from old table
            cursor.execute("PRAGMA table_info(timetable_periods)")
            old_columns = [col[1] for col in cursor.fetchall()]

            # Build column list for copying (only columns that exist in both tables)
            new_columns = ['id', 'school_id', 'level_id', 'section_id', 'period_number',
                          'period_name', 'start_time', 'end_time', 'duration_minutes',
                          'is_active', 'created_at', 'updated_at', 'day_of_week']

            columns_to_copy = [col for col in new_columns if col in old_columns]
            columns_str = ', '.join(columns_to_copy)

            # Copy data
            cursor.execute(f'''
            INSERT INTO timetable_periods_new ({columns_str})
            SELECT {columns_str} FROM timetable_periods
            ''')

            rows_copied = cursor.rowcount
            print(f"Copied {rows_copied} rows from old table")

            # Step 3: Drop old table
            print("Step 3: Dropping old table...")
            cursor.execute("DROP TABLE timetable_periods")
        else:
            print("No existing timetable_periods table found, creating fresh table")

        # Step 4: Rename new table
        print("Step 4: Renaming new table...")
        cursor.execute("ALTER TABLE timetable_periods_new RENAME TO timetable_periods")

        # Commit changes
        conn.commit()
        print("\n✓ Migration completed successfully!")
        print("You can now add periods for different classes/sections without constraint errors.")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("Timetable Periods Migration Script")
    print("="*60)
    migrate_timetable_periods()
