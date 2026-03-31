import database


def main():
    conn = database._connect_mysql() if database._USE_MYSQL else database._connect_sqlite()
    try:
        print(f"USE_MYSQL={database._USE_MYSQL}")
        if database._USE_MYSQL:
            conn.execute('ALTER TABLE system_settings MODIFY setting_value TEXT NULL')
            conn.execute('ALTER TABLE system_settings MODIFY description TEXT NULL')
            conn.commit()
            cols = conn.execute(
                'SELECT COLUMN_NAME, COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS '
                'WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? '
                'AND COLUMN_NAME IN (?, ?) ORDER BY COLUMN_NAME',
                ('system_settings', 'setting_value', 'description')
            ).fetchall()
            print('UPDATED_COLS=', [(c['COLUMN_NAME'], c['COLUMN_TYPE']) for c in cols])
        else:
            print('SQLite backend detected; no schema change needed.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
