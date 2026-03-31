"""
Migration: attendance selection foundation
- Add schools.attendance_mode (default biometric)
- Add staff.card_uid for ID scan fallback
- Create attendance_qr_tokens table
- Create attendance_otp_challenges table
Supports both MySQL and SQLite.
"""

import os
import re

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb'
)
USE_MYSQL = DATABASE_URL.startswith('mysql')


def _connect_mysql():
    import pymysql

    url = re.sub(r'^mysql\+pymysql://', '', DATABASE_URL)
    match = re.match(
        r'(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>.+)',
        url
    )
    if not match:
        raise ValueError('Cannot parse DATABASE_URL')

    return pymysql.connect(
        user=match.group('user'),
        password=match.group('password'),
        host=match.group('host'),
        port=int(match.group('port') or 3306),
        database=match.group('db'),
        charset='utf8mb4'
    )


def _connect_sqlite():
    import sqlite3

    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')
    return sqlite3.connect(db_path)


def _column_exists(cursor, table_name, column_name):
    if USE_MYSQL:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s
            """,
            (table_name, column_name)
        )
        return cursor.fetchone()[0] > 0

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)


def _ensure_columns(cursor):
    if not _column_exists(cursor, 'schools', 'attendance_mode'):
        if USE_MYSQL:
            cursor.execute("ALTER TABLE schools ADD COLUMN attendance_mode VARCHAR(32) DEFAULT 'biometric'")
        else:
            cursor.execute("ALTER TABLE schools ADD COLUMN attendance_mode TEXT DEFAULT 'biometric'")
        print('Added schools.attendance_mode')
    else:
        print('schools.attendance_mode already exists')

    if not _column_exists(cursor, 'staff', 'card_uid'):
        if USE_MYSQL:
            cursor.execute("ALTER TABLE staff ADD COLUMN card_uid VARCHAR(128) NULL")
        else:
            cursor.execute("ALTER TABLE staff ADD COLUMN card_uid TEXT")
        print('Added staff.card_uid')
    else:
        print('staff.card_uid already exists')


def _ensure_tables(cursor):
    if USE_MYSQL:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_qr_tokens (
                id INT PRIMARY KEY AUTO_INCREMENT,
                school_id INT NOT NULL,
                token_jti VARCHAR(128) NOT NULL,
                token_hash VARCHAR(128) NOT NULL,
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used_by_staff_id INT,
                used_at TIMESTAMP NULL,
                status VARCHAR(32) DEFAULT 'active'
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_otp_challenges (
                id INT PRIMARY KEY AUTO_INCREMENT,
                school_id INT NOT NULL,
                staff_id INT NOT NULL,
                channel VARCHAR(24) NOT NULL,
                otp_hash VARCHAR(128) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                attempts INT DEFAULT 0,
                max_attempts INT DEFAULT 3,
                verified_at TIMESTAMP NULL,
                status VARCHAR(32) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    else:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_qr_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id INTEGER NOT NULL,
                token_jti TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used_by_staff_id INTEGER,
                used_at TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_otp_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id INTEGER NOT NULL,
                staff_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                otp_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                verified_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    print('Ensured attendance_qr_tokens and attendance_otp_challenges tables')


def _upsert_setting(cursor, key, value, description):
    if USE_MYSQL:
        cursor.execute('SELECT id FROM system_settings WHERE setting_key = %s LIMIT 1', (key,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                '''
                UPDATE system_settings
                SET setting_value = %s, description = %s, updated_at = CURRENT_TIMESTAMP
                WHERE setting_key = %s
                ''',
                (value, description, key)
            )
        else:
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 FROM system_settings')
            next_id = cursor.fetchone()[0]
            cursor.execute(
                '''
                INSERT INTO system_settings (id, setting_key, setting_value, description, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ''',
                (next_id, key, value, description)
            )
    else:
        cursor.execute(
            '''
            INSERT INTO system_settings (setting_key, setting_value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                description = excluded.description,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (key, value, description)
        )


def _backfill_defaults(cursor):
    # Normalize NULL/empty attendance_mode values.
    if USE_MYSQL:
        cursor.execute("UPDATE schools SET attendance_mode = 'biometric' WHERE attendance_mode IS NULL OR attendance_mode = ''")
    else:
        cursor.execute("UPDATE schools SET attendance_mode = 'biometric' WHERE attendance_mode IS NULL OR TRIM(attendance_mode) = ''")

    cursor.execute('SELECT id, attendance_mode FROM schools')
    schools = cursor.fetchall()

    created_settings = 0
    for school in schools:
        school_id = school[0]
        mode = (school[1] or 'biometric').strip().lower() if school[1] else 'biometric'
        _upsert_setting(
            cursor,
            f'attendance_mode_school_{school_id}',
            mode,
            'Per-school attendance mode'
        )
        created_settings += 1

    print(f'Backfilled attendance_mode defaults for {len(schools)} school(s) and synced {created_settings} system_settings entries')


def run_migration():
    conn = _connect_mysql() if USE_MYSQL else _connect_sqlite()
    cursor = conn.cursor()

    try:
        _ensure_columns(cursor)
        _ensure_tables(cursor)
        _backfill_defaults(cursor)
        conn.commit()
        print('Attendance selection migration completed successfully')
    except Exception as exc:
        conn.rollback()
        print(f'Migration failed: {exc}')
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    run_migration()
