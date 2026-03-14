# database.py
import sqlite3
from flask import g
import os

# ---------------------------------------------------------------------------
# DATABASE BACKEND CONFIGURATION
# ---------------------------------------------------------------------------
# Set the DATABASE_URL environment variable to switch to MySQL/MariaDB.
#
# MySQL  : mysql+pymysql://user:password@host:port/dbname
# SQLite : leave DATABASE_URL unset  →  uses local instance/vishnorex.db
#
# Example .env / environment variable:
#   DATABASE_URL=mysql+pymysql://root:Password@mysql-env-jgahcdvwyo.ap-south-1a.lb.nimbuz.tech:31124/vishnorex
#
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb')

# Fallback SQLite path (used when DATABASE_URL is not set)
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

# Detect backend from URL prefix
_USE_MYSQL = DATABASE_URL.startswith('mysql')


def _parse_mysql_url(url):
    """
    Parse  mysql+pymysql://user:password@host:port/dbname
    Returns dict suitable for pymysql.connect(**kwargs).
    """
    import re
    # Strip scheme
    url = re.sub(r'^mysql\+pymysql://', '', url)
    # Split user:password@host:port/dbname
    m = re.match(
        r'(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>.+)',
        url
    )
    if not m:
        raise ValueError(f"Cannot parse DATABASE_URL: {url!r}")
    return {
        'user':     m.group('user'),
        'password': m.group('password'),
        'host':     m.group('host'),
        'port':     int(m.group('port') or 3306),
        'database': m.group('db'),
        'charset':  'utf8mb4',
        'autocommit': False,
        # Remove ONLY_FULL_GROUP_BY so legacy SQLite-style GROUP BY queries work.
        # Also remove NO_ZERO_DATE / NO_ZERO_IN_DATE / STRICT_TRANS_TABLES to
        # avoid INSERT errors for optional date/time columns with empty strings.
        'init_command': (
            "SET SESSION sql_mode = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE("
            "    @@SESSION.sql_mode,"
            "    'ONLY_FULL_GROUP_BY',''),"
            "    'NO_ZERO_DATE',''),"
            "    'NO_ZERO_IN_DATE',''),"
            "    'STRICT_TRANS_TABLES',''),"
            "    'ERROR_FOR_DIVISION_BY_ZERO','')"
        ),
    }


def _coerce_mysql_value(val):
    """
    PyMySQL returns TIME columns as datetime.timedelta, but all app code
    expects datetime.time (same as sqlite3). Convert here once so every
    fetch site works without changes.
    Also coerce bytes → str for BLOB/BINARY columns that hold text.
    """
    import datetime as _dt
    if isinstance(val, _dt.timedelta):
        total = int(val.total_seconds())
        # Handle negative timedelta (shouldn't happen for TIME, but be safe)
        if total < 0:
            total = 0
        h, rem = divmod(total, 3600)
        m, s   = divmod(rem, 60)
        return _dt.time(h % 24, m, s)
    if isinstance(val, (bytes, bytearray)):
        try:
            return val.decode('utf-8')
        except Exception:
            return val
    return val


class _MySQLRow(dict):
    """dict subclass that also supports index-based access like sqlite3.Row."""
    def __init__(self, cursor, row):
        cols = [d[0] for d in cursor.description]
        coerced = [_coerce_mysql_value(v) for v in row]
        super().__init__(zip(cols, coerced))
        self._list = coerced

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._list[key]
        return super().__getitem__(key)

    def keys(self):
        return super().keys()


class _MySQLCursorWrapper:
    """Wraps a pymysql cursor so it looks like an sqlite3 cursor."""

    def __init__(self, raw_cursor, conn_wrapper):
        self._cur = raw_cursor
        self._conn = conn_wrapper

    # Convert SQLite syntax → MySQL syntax
    @staticmethod
    def _adapt(sql):
        import re
        # Placeholder substitution
        sql = sql.replace('?', '%s')
        # SQLite AUTOINCREMENT → MySQL AUTO_INCREMENT
        sql = re.sub(r'\bAUTOINCREMENT\b', 'AUTO_INCREMENT', sql)
        # SQLite INTEGER PRIMARY KEY → MySQL INT PRIMARY KEY
        sql = re.sub(r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTO_INCREMENT\b',
                     'INT PRIMARY KEY AUTO_INCREMENT', sql, flags=re.IGNORECASE)
        # BOOLEAN → TINYINT(1)
        sql = re.sub(r'\bBOOLEAN\b', 'TINYINT(1)', sql)
        # REAL → DOUBLE
        sql = re.sub(r'\bREAL\b', 'DOUBLE', sql)
        # MySQL: TEXT columns can't have DEFAULT values → VARCHAR(500)
        lines = sql.split('\n')
        fixed = []
        for line in lines:
            if re.search(r'\bTEXT\b', line, re.IGNORECASE) and re.search(r'\bDEFAULT\b', line, re.IGNORECASE):
                line = re.sub(r'\bTEXT\b', 'VARCHAR(500)', line, flags=re.IGNORECASE)
            fixed.append(line)
        sql = '\n'.join(fixed)
        # sqlite_master → INFORMATION_SCHEMA equivalents
        # "SELECT sql FROM sqlite_master ..." → returns no rows (skip SQLite-only migrations)
        sql = re.sub(
            r"SELECT\s+sql\s+FROM\s+sqlite_master\b[^\n]*",
            "SELECT '' AS `sql` FROM INFORMATION_SCHEMA.TABLES WHERE 1=0",
            sql, flags=re.IGNORECASE
        )
        # "SELECT name FROM sqlite_master WHERE type='table' AND name='X'"
        sql = re.sub(
            r"SELECT\s+name\s+FROM\s+sqlite_master\s+WHERE\s+type\s*=\s*'table'\s+AND\s+name\s*=\s*(%s|'[^']*')",
            r"SELECT table_name AS name FROM INFORMATION_SCHEMA.TABLES WHERE table_schema=DATABASE() AND table_name=\1",
            sql, flags=re.IGNORECASE
        )
        # "SELECT name FROM sqlite_master WHERE type='table'"
        sql = re.sub(
            r"SELECT\s+name\s+FROM\s+sqlite_master\s+WHERE\s+type\s*=\s*'table'",
            "SELECT table_name AS name FROM INFORMATION_SCHEMA.TABLES WHERE table_schema=DATABASE()",
            sql, flags=re.IGNORECASE
        )
        # PRAGMA table_info(table) → INFORMATION_SCHEMA equivalent (returns cid/name/type/notnull/dflt_value/pk)
        def _pragma_table_info(m):
            tbl = m.group(1).strip('`"\'')
            return (
                "SELECT ORDINAL_POSITION-1 AS cid, COLUMN_NAME AS `name`, "
                "COLUMN_TYPE AS `type`, "
                "CASE WHEN IS_NULLABLE='NO' THEN 1 ELSE 0 END AS `notnull`, "
                "COLUMN_DEFAULT AS dflt_value, "
                "CASE WHEN COLUMN_KEY='PRI' THEN 1 ELSE 0 END AS pk "
                "FROM INFORMATION_SCHEMA.COLUMNS "
                f"WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{tbl}' "
                "ORDER BY ORDINAL_POSITION"
            )
        sql = re.sub(r'\bPRAGMA\s+table_info\s*\(\s*([^\)]+?)\s*\)', _pragma_table_info, sql, flags=re.IGNORECASE)
        # PRAGMA foreign_keys ... → no-op
        sql = re.sub(r'\bPRAGMA\s+foreign_keys\s*=\s*\w+\b', 'SELECT 1', sql, flags=re.IGNORECASE)
        # PRAGMA ... (any other pragma, consume optional (args)) → no-op
        sql = re.sub(r'\bPRAGMA\s+\w+(?:\s*\([^)]*\))?', 'SELECT 1', sql, flags=re.IGNORECASE)
        # Convert double-quoted string literals → single-quoted (SQLite allows "val", MySQL needs 'val')
        # Only replace "value" that follow SQL keywords or operators, not bare identifiers
        sql = re.sub(
            r'(?<=[=\(\,\s])\"([^\"\\n]*)\"(?=[,\)\s]|$)',
            lambda m: "'" + m.group(1).replace("'", "\\'") + "'",
            sql
        )
        # INSERT OR IGNORE → INSERT IGNORE
        sql = re.sub(r'\bINSERT\s+OR\s+IGNORE\b', 'INSERT IGNORE', sql, flags=re.IGNORECASE)
        # INSERT OR REPLACE → REPLACE
        sql = re.sub(r'\bINSERT\s+OR\s+REPLACE\b', 'REPLACE', sql, flags=re.IGNORECASE)

        # ── CAST type aliases ─────────────────────────────────────────────────
        # CAST(... AS INTEGER) → CAST(... AS SIGNED)  [MySQL ≥5.5 doesn't accept INTEGER in CAST]
        sql = re.sub(r'\bCAST\s*\(([^)]+)\bAS\s+INTEGER\s*\)',
                     lambda m: 'CAST(' + m.group(1) + 'AS SIGNED)',
                     sql, flags=re.IGNORECASE)
        # CAST(... AS TEXT) → CAST(... AS CHAR)
        sql = re.sub(r'\bCAST\s*\(([^)]+)\bAS\s+TEXT\s*\)',
                     lambda m: 'CAST(' + m.group(1) + 'AS CHAR)',
                     sql, flags=re.IGNORECASE)

        # ── SQLite strftime → MySQL date functions ────────────────────────────
        _strftime_map = {
            '%Y-%m-%d': lambda c: f'DATE({c})',
            '%Y-%m':    lambda c: f"DATE_FORMAT({c}, '%%Y-%%m')",
            '%Y':       lambda c: f'YEAR({c})',
            '%m':       lambda c: f'MONTH({c})',
            '%d':       lambda c: f'DAY({c})',
            '%H':       lambda c: f'HOUR({c})',
            '%M':       lambda c: f'MINUTE({c})',
            '%S':       lambda c: f'SECOND({c})',
            '%W':       lambda c: f'WEEK({c})',
            '%w':       lambda c: f'(DAYOFWEEK({c})-1)',
            '%j':       lambda c: f'DAYOFYEAR({c})',
        }
        def _strftime_to_mysql(m):
            fmt = m.group(1)
            col = m.group(2).strip()
            fn = _strftime_map.get(fmt)
            if fn:
                return fn(col)
            # Escape % signs for other format strings
            escaped_fmt = fmt.replace('%', '%%')
            return f"DATE_FORMAT({col}, '{escaped_fmt}')"
        sql = re.sub(r"strftime\s*\(\s*'([^']*)'\s*,\s*([^)]+)\)",
                     _strftime_to_mysql, sql, flags=re.IGNORECASE)

        # ── julianday arithmetic → DATEDIFF ───────────────────────────────────
        # julianday(a) - julianday(b) → DATEDIFF(a, b)
        def _julianday_diff(m):
            a = m.group(1).strip()
            b = m.group(2).strip()
            a = re.sub(r"'now'", 'CURDATE()', a, flags=re.IGNORECASE)
            b = re.sub(r"'now'", 'CURDATE()', b, flags=re.IGNORECASE)
            return f'DATEDIFF({a}, {b})'
        sql = re.sub(
            r'julianday\s*\(\s*([^)]+)\s*\)\s*-\s*julianday\s*\(\s*([^)]+)\s*\)',
            _julianday_diff, sql, flags=re.IGNORECASE)
        # any remaining bare julianday('now') → TO_DAYS(CURDATE())
        sql = re.sub(r"julianday\s*\(\s*'now'\s*\)", 'TO_DAYS(CURDATE())', sql, flags=re.IGNORECASE)
        sql = re.sub(r'julianday\s*\(\s*([^)]+)\s*\)', r'TO_DAYS(\1)', sql, flags=re.IGNORECASE)

        # ── date('now', '+/-N unit') → DATE_ADD/DATE_SUB ─────────────────────
        def _date_now_offset(m):
            sign   = m.group(1)
            amount = m.group(2)
            unit   = m.group(3).rstrip('sS').upper()  # days→DAY, months→MONTH
            unit_norm = {'DAY': 'DAY', 'MONTH': 'MONTH', 'YEAR': 'YEAR',
                         'WEEK': 'WEEK', 'HOUR': 'HOUR', 'MINUTE': 'MINUTE'}.get(unit, unit)
            fn = 'DATE_ADD' if sign == '+' else 'DATE_SUB'
            return f"{fn}(CURDATE(), INTERVAL {amount} {unit_norm})"
        sql = re.sub(
            r"date\s*\(\s*'now'\s*,\s*'([+\-])(\d+)\s+(\w+)'\s*\)",
            _date_now_offset, sql, flags=re.IGNORECASE)

        # ── DATE('now') / datetime('now') ─────────────────────────────────────
        sql = re.sub(r"\bDATE\s*\(\s*'now'\s*\)", 'CURDATE()', sql, flags=re.IGNORECASE)
        sql = re.sub(r"\bdatetime\s*\(\s*'now'\s*\)", 'NOW()', sql, flags=re.IGNORECASE)

        return sql

    def execute(self, sql, params=()):
        self._cur.execute(self._adapt(sql), params)
        return self

    def executemany(self, sql, seq):
        self._cur.executemany(self._adapt(sql), seq)
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return _MySQLRow(self._cur, row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [_MySQLRow(self._cur, r) for r in rows]

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def description(self):
        return self._cur.description

    def __iter__(self):
        for row in self._cur:
            yield _MySQLRow(self._cur, row)


class _MySQLConnectionWrapper:
    """
    Wraps a raw pymysql connection so every call site in app.py can keep using
    the exact same   db.execute(sql, params)  /  db.commit()  pattern as SQLite.
    """

    def __init__(self, raw_conn):
        self._conn = raw_conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        wrapper = _MySQLCursorWrapper(cur, self)
        wrapper.execute(sql, params)
        return wrapper

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def cursor(self):
        return _MySQLCursorWrapper(self._conn.cursor(), self)

    # Let sqlite3-specific helpers work without crashing on MySQL
    def isolation_level(self):
        return None


def _connect_mysql():
    """Open a new pymysql connection and return it wrapped."""
    try:
        import pymysql
    except ImportError:
        raise RuntimeError(
            "pymysql is not installed. Run:  pip install pymysql"
        )
    params = _parse_mysql_url(DATABASE_URL)
    raw = pymysql.connect(**params)
    return _MySQLConnectionWrapper(raw)


def _connect_sqlite():
    """Open a new SQLite connection."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """
    Return the database connection for the current Flask request.
    Uses MySQL when DATABASE_URL env var is set, otherwise SQLite.
    The connection is cached in Flask's 'g' for the lifetime of the request.
    """
    db = getattr(g, '_database', None)
    if db is None:
        if _USE_MYSQL:
            db = g._database = _connect_mysql()
        else:
            db = g._database = _connect_sqlite()
    return db

def init_db(app):
    # Only needed for SQLite (creates the instance/ folder)
    if not _USE_MYSQL:
        os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # --- Table creation ---
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER,
            staff_id TEXT NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            department TEXT,
            position TEXT,
            gender TEXT,
            date_of_birth DATE,
            date_of_joining DATE,
            photo_data TEXT,
            shift_type TEXT DEFAULT 'general',
            basic_salary DECIMAL(10,2) DEFAULT 0.00,
            hra DECIMAL(10,2) DEFAULT 0.00,
            transport_allowance DECIMAL(10,2) DEFAULT 0.00,
            other_allowances DECIMAL(10,2) DEFAULT 0.00,
            pf_deduction DECIMAL(10,2) DEFAULT 0.00,
            esi_deduction DECIMAL(10,2) DEFAULT 0.00,
            professional_tax DECIMAL(10,2) DEFAULT 0.00,
            other_deductions DECIMAL(10,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, staff_id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time_in TIME,
            time_out TIME,
            overtime_in TIME,
            overtime_out TIME,
            work_hours REAL DEFAULT 0,
            overtime_hours REAL DEFAULT 0,
            status TEXT CHECK(status IN ('present', 'absent', 'late', 'leave', 'left_soon', 'on_duty', 'holiday')),
            notes TEXT,
            on_duty_type TEXT,
            on_duty_location TEXT,
            on_duty_purpose TEXT,
            late_duration_minutes INTEGER DEFAULT 0,
            early_departure_minutes INTEGER DEFAULT 0,
            shift_type TEXT,
            shift_start_time TIME,
            shift_end_time TIME,
            regularization_requested BOOLEAN DEFAULT 0,
            regularization_status TEXT CHECK(regularization_status IN ('pending', 'approved', 'rejected')),
            regularization_reason TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(staff_id, date)
        )
        ''')

        # Create students table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            student_id TEXT NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            `class` TEXT,
            section TEXT,
            roll_number TEXT,
            admission_number TEXT,
            student_type TEXT DEFAULT 'Day Scholar',
            gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
            date_of_birth DATE,
            age INTEGER,
            date_of_admission DATE,
            academic_year TEXT,
            parent_name TEXT,
            parent_phone TEXT,
            parent_email TEXT,
            mother_name TEXT,
            mother_phone TEXT,
            parent_occupation TEXT,
            address TEXT,
            tenth_marks TEXT,
            tenth_percentage REAL,
            twelfth_marks TEXT,
            twelfth_percentage REAL,
            skills TEXT,
            tc_number TEXT,
            aadhar_number TEXT,
            custom_fields TEXT,
            photo_data TEXT,
            theme_preference TEXT DEFAULT 'light',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, student_id)
        )
        ''')

        # Create student attendance table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            date DATE NOT NULL,
            morning_status TEXT CHECK(morning_status IN ('present', 'absent', 'late', 'leave')),
            morning_time TIME,
            morning_marked_by INTEGER,
            morning_notes TEXT,
            afternoon_status TEXT CHECK(afternoon_status IN ('present', 'absent', 'late', 'leave')),
            afternoon_time TIME,
            afternoon_marked_by INTEGER,
            afternoon_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (morning_marked_by) REFERENCES staff(id),
            FOREIGN KEY (afternoon_marked_by) REFERENCES staff(id),
            UNIQUE(student_id, date)
        )
        ''')

        # Create biometric verification log table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS biometric_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            verification_type TEXT CHECK(verification_type IN ('check-in', 'check-out', 'overtime-in', 'overtime-out')) NOT NULL,
            verification_time DATETIME NOT NULL,
            device_ip TEXT,
            biometric_method TEXT CHECK(biometric_method IN ('fingerprint', 'face', 'card', 'password')),
            verification_status TEXT CHECK(verification_status IN ('success', 'failed', 'retry')) DEFAULT 'success',
            notes TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            leave_type TEXT CHECK(leave_type IN ('CL', 'SL', 'EL', 'ML')),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create department shift mappings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS department_shift_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            department TEXT NOT NULL,
            default_shift_type TEXT NOT NULL CHECK(default_shift_type IN ('general', 'morning', 'afternoon', 'evening', 'night', 'overtime')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, department)
        )
        ''')

        # Create on-duty applications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS on_duty_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            duty_type TEXT CHECK(duty_type IN ('Official Work', 'Training', 'Meeting', 'Conference', 'Field Work', 'Other')) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            start_time TIME,
            end_time TIME,
            location TEXT,
            purpose TEXT NOT NULL,
            reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            admin_remarks TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create permission applications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permission_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            permission_type TEXT CHECK(permission_type IN ('Personal Work', 'Medical', 'Emergency', 'Family Function', 'Other')) NOT NULL,
            permission_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration_hours DECIMAL(4,2),
            reason TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            admin_remarks TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create shift definitions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shift_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_type TEXT NOT NULL UNIQUE,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            grace_period_minutes INTEGER DEFAULT 10,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create attendance regularization requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_regularization_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            request_type TEXT CHECK(request_type IN ('late_arrival', 'early_departure')) NOT NULL,
            original_time TIME NOT NULL,
            expected_time TIME NOT NULL,
            duration_minutes INTEGER NOT NULL,
            staff_reason TEXT,
            admin_reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            FOREIGN KEY (attendance_id) REFERENCES attendance(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create holidays table for comprehensive holiday management
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            holiday_name TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            holiday_type TEXT CHECK(holiday_type IN ('institution_wide', 'department_specific')) NOT NULL DEFAULT 'institution_wide',
            description TEXT,
            departments TEXT,  -- JSON array of department names for department-specific holidays
            is_recurring BOOLEAN DEFAULT 0,
            recurring_type TEXT CHECK(recurring_type IN ('yearly', 'monthly', 'weekly')),
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (created_by) REFERENCES admins(id)
        )
        ''')

        # Create weekly off configuration table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_off_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),  -- 0=Sunday, 1=Monday, ..., 6=Saturday
            is_enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, day_of_week)
        )
        ''')

        # Create comprehensive notifications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('admin', 'staff', 'company_admin')),
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'info' CHECK(notification_type IN ('info', 'success', 'warning', 'danger')),
            action_url TEXT,
            is_read BOOLEAN DEFAULT 0,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create sub_admin_permissions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sub_admin_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id VARCHAR(100) NOT NULL,
            module_name VARCHAR(100) NOT NULL,
            school_id INTEGER NOT NULL,
            can_view BOOLEAN DEFAULT 1,
            can_edit BOOLEAN DEFAULT 0,
            can_delete BOOLEAN DEFAULT 0,
            UNIQUE(staff_id, module_name, school_id)
        )
        ''')

        # Create notification logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_type TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT,
            status TEXT NOT NULL CHECK(status IN ('sent', 'failed', 'pending')),
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # --- TIMETABLE MANAGEMENT TABLES ---
        
        # School timetable settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL UNIQUE,
            is_enabled BOOLEAN DEFAULT 0,
            number_of_periods INTEGER DEFAULT 8,
            master_schedule TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        # Master schedule periods table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            level_id INTEGER,
            section_id INTEGER,
            period_number INTEGER NOT NULL,
            period_name TEXT,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration_minutes INTEGER,
            time_slot_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (level_id) REFERENCES timetable_academic_levels(id),
            FOREIGN KEY (section_id) REFERENCES timetable_sections(id),
            UNIQUE(school_id, level_id, section_id, period_number)
        )
        ''')

        # Reusable master time slots used by timetable_periods.time_slot_id
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_period_timings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            slot_label VARCHAR(255) NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration_minutes INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, slot_label, start_time, end_time)
        )
        ''')

        # Department alteration permissions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_department_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            department TEXT NOT NULL,
            allow_alterations BOOLEAN DEFAULT 1,
            allow_inbound BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, department)
        )
        ''')

        # Staff timetable assignments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            period_number INTEGER NOT NULL,
            class_subject TEXT,
            is_assigned BOOLEAN DEFAULT 1,
            is_locked BOOLEAN DEFAULT 0,
            locked_reason TEXT,
            locked_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (locked_by) REFERENCES admins(id),
            UNIQUE(school_id, staff_id, day_of_week, period_number)
        )
        ''')

        # Alteration requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_alteration_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            assignment_id INTEGER NOT NULL,
            requester_staff_id INTEGER NOT NULL,
            target_staff_id INTEGER,
            target_department TEXT,
            alteration_type TEXT CHECK(alteration_type IN ('peer_swap', 'self_allocation', 'admin_override')) DEFAULT 'peer_swap',
            status TEXT CHECK(status IN ('pending', 'accepted', 'rejected', 'admin_override')) DEFAULT 'pending',
            reason TEXT,
            response_reason TEXT,
            admin_notes TEXT,
            responded_by INTEGER,
            responded_at TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (assignment_id) REFERENCES timetable_assignments(id),
            FOREIGN KEY (requester_staff_id) REFERENCES staff(id),
            FOREIGN KEY (target_staff_id) REFERENCES staff(id),
            FOREIGN KEY (responded_by) REFERENCES staff(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Self-allocated periods (staff-filled empty slots) table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_self_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            period_number INTEGER NOT NULL,
            class_subject TEXT NOT NULL,
            is_admin_locked BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            UNIQUE(school_id, staff_id, day_of_week, period_number)
        )
        ''')

        # ==================== HIERARCHICAL TIMETABLE TABLES ====================
        
        # Organization type and level configuration table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_organization_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL UNIQUE,
            organization_type TEXT CHECK(organization_type IN ('school', 'college')) DEFAULT 'school',
            total_levels INTEGER DEFAULT 12,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        # Academic levels (Classes/Years) table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_academic_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            level_type TEXT CHECK(level_type IN ('class', 'year')) DEFAULT 'class',
            level_number INTEGER NOT NULL,
            level_name TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, level_number)
        )
        ''')

        # Dynamic sections for each academic level
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            section_code TEXT NOT NULL,
            capacity INTEGER DEFAULT 60,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (level_id) REFERENCES timetable_academic_levels(id),
            UNIQUE(school_id, level_id, section_code)
        )
        ''')

        # Hierarchical timetable assignments (Staff to Section/Period/Level)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_hierarchical_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            period_number INTEGER NOT NULL,
            subject_name TEXT,
            room_number TEXT,
            is_locked BOOLEAN DEFAULT 0,
            locked_by INTEGER,
            locked_reason TEXT,
            assignment_type TEXT CHECK(assignment_type IN ('admin_assigned', 'staff_self_allocated', 'substitute')) DEFAULT 'admin_assigned',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (section_id) REFERENCES timetable_sections(id),
            FOREIGN KEY (level_id) REFERENCES timetable_academic_levels(id),
            FOREIGN KEY (locked_by) REFERENCES admins(id),
            UNIQUE(school_id, section_id, day_of_week, period_number),
            UNIQUE(school_id, staff_id, section_id, day_of_week, period_number)
        )
        ''')

        # Conflict resolution and availability tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_staff_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            period_number INTEGER NOT NULL,
            is_available BOOLEAN DEFAULT 1,
            reason_if_unavailable TEXT,
            updated_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (updated_by) REFERENCES admins(id),
            UNIQUE(school_id, staff_id, day_of_week, period_number)
        )
        ''')

        # Conflict alerts and logs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_conflict_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            conflict_type TEXT CHECK(conflict_type IN ('double_booking', 'unavailable', 'capacity_exceeded')) DEFAULT 'double_booking',
            conflicting_sections TEXT,
            day_of_week INTEGER,
            period_number INTEGER,
            resolution_status TEXT CHECK(resolution_status IN ('pending', 'resolved', 'ignored')) DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id)
        )
        ''')

        # ==================== FEE MANAGEMENT TABLES ====================

        # Fee types / templates per school
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fee_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, name)
        )
        ''')

        # Student fee assignments
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            student_db_id INTEGER NOT NULL,
            fee_type_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            due_date DATE,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'overdue', 'waived', 'partial')),
            paid_date DATE,
            payment_mode TEXT,
            notes TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (student_db_id) REFERENCES students(id),
            FOREIGN KEY (fee_type_id) REFERENCES fee_types(id)
        )
        ''')

        # --- Safe column additions ---
        def ensure_column_exists(table, column_def, column_name):
            if _USE_MYSQL:
                # MySQL: query INFORMATION_SCHEMA to check column existence
                cursor.execute(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
                    (table, column_name)
                )
                row = cursor.fetchone()
                exists = (row[0] if row else 0) > 0
            else:
                cursor.execute(f"PRAGMA table_info({table})")
                exists = any(col[1] == column_name for col in cursor.fetchall())
            if not exists:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

        ensure_column_exists('schools', 'logo_url TEXT', 'logo_url')
        ensure_column_exists('schools', 'is_hidden BOOLEAN DEFAULT 0', 'is_hidden')
        ensure_column_exists('staff', 'photo_url TEXT', 'photo_url')
        ensure_column_exists('staff', 'password_hash TEXT', 'password_hash')
        ensure_column_exists('staff', 'shift_type TEXT DEFAULT "general"', 'shift_type')

        # Add new staff fields for enhanced staff management
        ensure_column_exists('staff', 'first_name TEXT', 'first_name')
        ensure_column_exists('staff', 'last_name TEXT', 'last_name')
        ensure_column_exists('staff', 'date_of_birth DATE', 'date_of_birth')
        ensure_column_exists('staff', 'date_of_joining DATE', 'date_of_joining')
        ensure_column_exists('staff', 'destination TEXT', 'destination')
        ensure_column_exists('staff', 'gender TEXT CHECK(gender IN ("Male", "Female", "Other"))', 'gender')

        # Enhanced attendance tracking columns
        ensure_column_exists('attendance', 'late_duration_minutes INTEGER DEFAULT 0', 'late_duration_minutes')
        ensure_column_exists('attendance', 'early_departure_minutes INTEGER DEFAULT 0', 'early_departure_minutes')
        ensure_column_exists('attendance', 'shift_start_time TIME', 'shift_start_time')
        ensure_column_exists('attendance', 'shift_end_time TIME', 'shift_end_time')
        ensure_column_exists('attendance', 'regularization_requested BOOLEAN DEFAULT 0', 'regularization_requested')
        ensure_column_exists('attendance', 'regularization_status TEXT CHECK(regularization_status IN ("pending", "approved", "rejected")) DEFAULT NULL', 'regularization_status')
        ensure_column_exists('attendance', 'regularization_reason TEXT', 'regularization_reason')

        # Add hierarchical timetable support columns
        ensure_column_exists('schools', 'organization_type TEXT CHECK(organization_type IN ("school", "college")) DEFAULT "school"', 'organization_type')
        ensure_column_exists('timetable_settings', 'enable_hierarchical_timetable BOOLEAN DEFAULT 1', 'enable_hierarchical_timetable')
        ensure_column_exists('timetable_settings', 'weeks_per_cycle INTEGER DEFAULT 1', 'weeks_per_cycle')
        ensure_column_exists('timetable_settings', 'max_classes_per_staff_per_day INTEGER DEFAULT 6', 'max_classes_per_staff_per_day')
        ensure_column_exists('timetable_assignments', 'section_id INTEGER', 'section_id')
        ensure_column_exists('timetable_assignments', 'level_id INTEGER', 'level_id')
        ensure_column_exists('timetable_assignments', 'subject_name TEXT', 'subject_name')
        ensure_column_exists('timetable_assignments', 'room_number TEXT', 'room_number')
        ensure_column_exists('timetable_assignments', 'assignment_type TEXT CHECK(assignment_type IN ("admin_assigned", "staff_self_allocated", "substitute")) DEFAULT "admin_assigned"', 'assignment_type')

        ensure_column_exists('timetable_periods', 'level_id INTEGER', 'level_id')
        ensure_column_exists('timetable_periods', 'section_id INTEGER', 'section_id')
        ensure_column_exists('timetable_periods', 'day_of_week INTEGER', 'day_of_week')
        ensure_column_exists('timetable_periods', 'time_slot_id INTEGER', 'time_slot_id')
        
        # Add reason_if_unavailable to timetable_conflict_logs
        ensure_column_exists('timetable_conflict_logs', 'reason_if_unavailable TEXT', 'reason_if_unavailable')

        # Backfill reusable period timings from existing timetable_periods rows.
        cursor.execute('''
            SELECT id, school_id, period_number, period_name, start_time, end_time, duration_minutes, time_slot_id
            FROM timetable_periods
            WHERE start_time IS NOT NULL AND end_time IS NOT NULL
        ''')

        period_rows = cursor.fetchall()
        for row in period_rows:
            if row['time_slot_id']:
                continue

            school_id = row['school_id']
            slot_label = (row['period_name'] or '').strip() or f"Period {row['period_number']}"
            start_time = row['start_time']
            end_time = row['end_time']
            duration_minutes = row['duration_minutes']

            cursor.execute('''
                SELECT id
                FROM timetable_period_timings
                WHERE school_id = ? AND slot_label = ? AND start_time = ? AND end_time = ?
                LIMIT 1
            ''', (school_id, slot_label, start_time, end_time))
            existing_slot = cursor.fetchone()

            if existing_slot:
                slot_id = existing_slot['id']
            else:
                cursor.execute('''
                    INSERT INTO timetable_period_timings
                    (school_id, slot_label, start_time, end_time, duration_minutes, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (school_id, slot_label, start_time, end_time, duration_minutes))
                slot_id = cursor.lastrowid

            cursor.execute('''
                UPDATE timetable_periods
                SET time_slot_id = ?
                WHERE id = ?
            ''', (slot_id, row['id']))

        # Add student management columns
        ensure_column_exists('students', 'age INTEGER', 'age')
        ensure_column_exists('students', 'academic_year TEXT', 'academic_year')
        # Add fee partial-payment column
        ensure_column_exists('student_fees', 'paid_amount REAL DEFAULT 0', 'paid_amount')

        # Fix status CHECK constraint to include 'partial'
        if _USE_MYSQL:
            # MySQL: drop the auto-named constraint and recreate with 'partial' included
            for _cname in ('student_fees_chk_1', 'student_fees_chk_status'):
                try:
                    cursor.execute(f"ALTER TABLE student_fees DROP CHECK `{_cname}`")
                except Exception:
                    pass
            try:
                cursor.execute(
                    "ALTER TABLE student_fees ADD CONSTRAINT student_fees_chk_status "
                    "CHECK(status IN ('pending','paid','overdue','waived','partial'))"
                )
            except Exception:
                pass
        else:
            # SQLite: recreate the table if the current schema lacks 'partial'
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='student_fees'")
            _row = cursor.fetchone()
            if _row and "'partial'" not in (_row[0] or ''):
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_fees_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_id INTEGER NOT NULL,
                        student_db_id INTEGER NOT NULL,
                        fee_type_id INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        paid_amount REAL DEFAULT 0,
                        due_date DATE,
                        status TEXT DEFAULT 'pending' CHECK(status IN ('pending','paid','overdue','waived','partial')),
                        paid_date DATE,
                        payment_mode TEXT,
                        notes TEXT,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (school_id) REFERENCES schools(id),
                        FOREIGN KEY (student_db_id) REFERENCES students(id),
                        FOREIGN KEY (fee_type_id) REFERENCES fee_types(id)
                    )
                ''')
                cursor.execute('''
                    INSERT INTO student_fees_new
                    SELECT id, school_id, student_db_id, fee_type_id, amount,
                           COALESCE(paid_amount, 0), due_date, status, paid_date,
                           payment_mode, notes, created_by, created_at, updated_at
                    FROM student_fees
                ''')
                cursor.execute('DROP TABLE student_fees')
                cursor.execute('ALTER TABLE student_fees_new RENAME TO student_fees')

        # Create cloud-related tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_attendance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            verification_type TEXT NOT NULL,
            punch_code INTEGER DEFAULT 0,
            status INTEGER DEFAULT 0,
            verify_method INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT DEFAULT 'ZK_BIOMETRIC',
            local_ip TEXT,
            local_port INTEGER DEFAULT 4370,
            cloud_enabled BOOLEAN DEFAULT TRUE,
            sync_interval INTEGER DEFAULT 30,
            last_sync TIMESTAMP,
            status TEXT DEFAULT 'unknown',
            organization_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            sync_type TEXT NOT NULL,
            records_count INTEGER DEFAULT 0,
            success BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            sync_started_at TIMESTAMP,
            sync_completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            organization_id TEXT NOT NULL,
            permissions TEXT DEFAULT 'read',
            is_active BOOLEAN DEFAULT TRUE,
            expires_at TIMESTAMP,
            last_used_at TIMESTAMP,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            staff_name TEXT NOT NULL,
            staff_user_id TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by INTEGER,
            FOREIGN KEY (staff_id) REFERENCES staff (id),
            FOREIGN KEY (school_id) REFERENCES schools (id),
            FOREIGN KEY (approved_by) REFERENCES admins (id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff_shift_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            shift_type TEXT NOT NULL,
            effective_from DATE NOT NULL,
            effective_to DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        # Initialize default shift definitions
        cursor.execute('SELECT COUNT(*) FROM shift_definitions')
        if cursor.fetchone()[0] == 0:
            # Insert default shift types as per requirements
            cursor.execute('''
                INSERT INTO shift_definitions (shift_type, start_time, end_time, grace_period_minutes, description)
                VALUES
                ('general', '09:00:00', '17:00:00', 15, 'General Institution Shift'),
                ('morning', '06:00:00', '14:00:00', 15, 'Morning Shift: 6:00 AM - 2:00 PM'),
                ('afternoon', '14:00:00', '22:00:00', 15, 'Afternoon Shift: 2:00 PM - 10:00 PM'),
                ('evening', '16:00:00', '00:00:00', 15, 'Evening Shift: 4:00 PM - 12:00 AM'),
                ('night', '22:00:00', '06:00:00', 15, 'Night Shift: 10:00 PM - 6:00 AM'),
                ('overtime', '18:00:00', '22:00:00', 0, 'Overtime Shift: 6:00 PM - 10:00 PM')
            ''')

        db.commit()


def get_institution_timings():
    """
    Get institution-wide check-in and check-out times from shift_definitions (general shift).
    The 'general' shift in shift_definitions is the single source of truth for default timings.
    
    Returns:
        dict: {
            'checkin_time': datetime.time object,
            'checkout_time': datetime.time object,
            'is_custom': bool (True if found in shift_definitions)
        }
    """
    import datetime
    
    try:
        db = get_db()
        
        # Read from shift_definitions (general shift = single source of truth)
        row = db.execute("""
            SELECT start_time, end_time FROM shift_definitions
            WHERE shift_type = 'general' AND is_active = 1
            LIMIT 1
        """).fetchone()
        
        if row:
            checkin_str  = (row['start_time']  or '09:00:00')[:5]   # strip seconds
            checkout_str = (row['end_time']     or '17:00:00')[:5]
            # Allow HH:MM or HH:MM:SS
            fmt = '%H:%M:%S' if len(row['start_time']) > 5 else '%H:%M'
            checkin_time  = datetime.datetime.strptime(row['start_time'],  fmt).time()
            fmt2 = '%H:%M:%S' if len(row['end_time']) > 5 else '%H:%M'
            checkout_time = datetime.datetime.strptime(row['end_time'], fmt2).time()
            return {
                'checkin_time': checkin_time,
                'checkout_time': checkout_time,
                'is_custom': True
            }
        
        # No general shift found — return defaults
        return {
            'checkin_time': datetime.time(9, 0),
            'checkout_time': datetime.time(17, 0),
            'is_custom': False
        }
        
    except Exception as e:
        print(f"Error getting institution timings: {e}")
        return {
            'checkin_time': datetime.time(9, 0),
            'checkout_time': datetime.time(17, 0),
            'is_custom': False
        }


def migrate_department_shift_constraint():
    """
    Migration: expand the CHECK constraint on department_shift_mappings to include
    'afternoon' and 'overtime', and ensure overtime row exists in shift_definitions.
    Safe to call multiple times (idempotent).
    """
    try:
        db = get_db()

        # Check current constraint via sqlite_master
        row = db.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='department_shift_mappings'"
        ).fetchone()

        if row and 'overtime' not in row['sql']:
            # Recreate table with expanded CHECK constraint
            db.execute('PRAGMA foreign_keys = OFF')
            db.execute('''
                CREATE TABLE IF NOT EXISTS department_shift_mappings_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER NOT NULL,
                    department TEXT NOT NULL,
                    default_shift_type TEXT NOT NULL CHECK(default_shift_type IN
                        ('general', 'morning', 'afternoon', 'evening', 'night', 'overtime')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(id),
                    UNIQUE(school_id, department)
                )
            ''')
            db.execute('''
                INSERT OR IGNORE INTO department_shift_mappings_new
                    (id, school_id, department, default_shift_type, created_at, updated_at)
                SELECT id, school_id, department, default_shift_type, created_at, updated_at
                FROM department_shift_mappings
            ''')
            db.execute('DROP TABLE department_shift_mappings')
            db.execute('ALTER TABLE department_shift_mappings_new RENAME TO department_shift_mappings')
            db.execute('PRAGMA foreign_keys = ON')
            db.commit()
            print('Migration: department_shift_mappings CHECK constraint expanded to include afternoon/overtime')

        # Ensure overtime exists in shift_definitions
        exists = db.execute(
            "SELECT 1 FROM shift_definitions WHERE shift_type = 'overtime'"
        ).fetchone()
        if not exists:
            db.execute('''
                INSERT INTO shift_definitions (shift_type, start_time, end_time, grace_period_minutes, description)
                VALUES ('overtime', '18:00:00', '22:00:00', 0, 'Overtime Shift: 6:00 PM - 10:00 PM')
            ''')
            db.commit()
            print('Migration: overtime shift added to shift_definitions')

        # Ensure afternoon exists in shift_definitions
        exists2 = db.execute(
            "SELECT 1 FROM shift_definitions WHERE shift_type = 'afternoon'"
        ).fetchone()
        if not exists2:
            db.execute('''
                INSERT INTO shift_definitions (shift_type, start_time, end_time, grace_period_minutes, description)
                VALUES ('afternoon', '14:00:00', '22:00:00', 15, 'Afternoon Shift: 2:00 PM - 10:00 PM')
            ''')
            db.commit()
            print('Migration: afternoon shift added to shift_definitions')

    except Exception as e:
        print(f'Warning: migrate_department_shift_constraint failed: {e}')


def migrate_shift_history():
    """
    Migration: create staff_shift_history table and seed initial records for all
    existing staff using their current shift_type (effective from their join date
    or 2000-01-01 if unknown). Safe to call multiple times (idempotent).
    """
    try:
        db = get_db()

        # Ensure table exists
        db.execute('''
            CREATE TABLE IF NOT EXISTS staff_shift_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                shift_type TEXT NOT NULL,
                effective_from DATE NOT NULL,
                effective_to DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id),
                FOREIGN KEY (school_id) REFERENCES schools(id)
            )
        ''')
        db.commit()

        # Seed initial history for staff who have no history record yet
        staff_without_history = db.execute('''
            SELECT s.id, s.school_id, s.shift_type, s.date_of_joining, s.created_at
            FROM staff s
            LEFT JOIN staff_shift_history sh ON sh.staff_id = s.id
            WHERE sh.id IS NULL
        ''').fetchall()

        for staff in staff_without_history:
            effective_from = (
                staff['date_of_joining']
                or (staff['created_at'][:10] if staff['created_at'] else None)
                or '2000-01-01'
            )
            db.execute('''
                INSERT INTO staff_shift_history
                    (staff_id, school_id, shift_type, effective_from, effective_to)
                VALUES (?, ?, ?, ?, NULL)
            ''', (
                staff['id'],
                staff['school_id'],
                staff['shift_type'] or 'general',
                effective_from
            ))

        if staff_without_history:
            db.commit()
            print(f'Migration: seeded shift history for {len(staff_without_history)} staff member(s)')

    except Exception as e:
        print(f'Warning: migrate_shift_history failed: {e}')


def calculate_attendance_status(check_time, verification_type='check-in', grace_minutes=None, date_obj=None, department=None):
    """
    Calculate attendance status based on institution timings, considering holidays.

    Args:
        check_time (datetime.time): Time when staff checked in/out
        verification_type (str): 'check-in' or 'check-out'
        grace_minutes (int): Grace period in minutes for late arrival
        date_obj (datetime.date, optional): Date to check for holidays
        department (str, optional): Department for department-specific holidays

    Returns:
        str: Attendance status ('present', 'late', 'early_departure', 'holiday')
    """
    import datetime

    # Check if the date is a holiday
    if date_obj is None:
        date_obj = datetime.date.today()

    if is_holiday(date_obj, department):
        return 'holiday'

    timings = get_institution_timings()

    if verification_type == 'check-in':
        # Strict timing rule: any time after designated check-in is 'late'
        return 'late' if check_time > timings['checkin_time'] else 'present'

    elif verification_type == 'check-out':
        # For check-out, consider early departure
        return 'early_departure' if check_time < timings['checkout_time'] else 'present'

    else:
        return 'present'


def calculate_standard_working_hours_per_month():
    """
    Calculate standard working hours per month based on institution timing configuration.

    Returns:
        dict: {
            'daily_hours': float,
            'monthly_hours': float,
            'working_days_per_month': int
        }
    """
    import datetime
    import calendar

    try:
        # Get institution timings
        timings = get_institution_timings()
        checkin_time = timings['checkin_time']
        checkout_time = timings['checkout_time']

        # Calculate daily working hours
        checkin_dt = datetime.datetime.combine(datetime.date.today(), checkin_time)
        checkout_dt = datetime.datetime.combine(datetime.date.today(), checkout_time)

        # Handle overnight shifts (if checkout is before checkin)
        if checkout_dt < checkin_dt:
            checkout_dt += datetime.timedelta(days=1)

        daily_hours = (checkout_dt - checkin_dt).total_seconds() / 3600

        # Calculate working days per month (excluding Sundays and holidays)
        # Use current month as reference
        now = datetime.datetime.now()
        total_days = calendar.monthrange(now.year, now.month)[1]
        working_days = 0

        for day in range(1, total_days + 1):
            date_obj = datetime.date(now.year, now.month, day)
            # Exclude Sundays (weekday 6) and holidays
            if date_obj.weekday() != 6 and not is_holiday(date_obj):
                working_days += 1

        monthly_hours = daily_hours * working_days

        return {
            'daily_hours': daily_hours,
            'monthly_hours': monthly_hours,
            'working_days_per_month': working_days
        }

    except Exception as e:
        print(f"Error calculating standard working hours: {e}")
        # Return default values (8 hours/day, 26 working days/month)
        return {
            'daily_hours': 8.0,
            'monthly_hours': 208.0,  # 8 * 26
            'working_days_per_month': 26
        }


def calculate_hourly_rate(base_monthly_salary):
    """
    Calculate hourly rate from base monthly salary using institution timing configuration.

    Args:
        base_monthly_salary (float): Base monthly salary amount

    Returns:
        dict: {
            'hourly_rate': float,
            'daily_rate': float,
            'standard_monthly_hours': float,
            'standard_daily_hours': float
        }
    """
    try:
        base_salary = float(base_monthly_salary)
        if base_salary <= 0:
            return {
                'hourly_rate': 0.0,
                'daily_rate': 0.0,
                'standard_monthly_hours': 0.0,
                'standard_daily_hours': 0.0
            }

        # Get standard working hours
        working_hours = calculate_standard_working_hours_per_month()

        # Calculate rates
        hourly_rate = base_salary / working_hours['monthly_hours'] if working_hours['monthly_hours'] > 0 else 0
        daily_rate = base_salary / working_hours['working_days_per_month'] if working_hours['working_days_per_month'] > 0 else 0

        return {
            'hourly_rate': round(hourly_rate, 2),
            'daily_rate': round(daily_rate, 2),
            'standard_monthly_hours': working_hours['monthly_hours'],
            'standard_daily_hours': working_hours['daily_hours']
        }

    except Exception as e:
        print(f"Error calculating hourly rate: {e}")
        return {
            'hourly_rate': 0.0,
            'daily_rate': 0.0,
            'standard_monthly_hours': 0.0,
            'standard_daily_hours': 0.0
        }


def is_holiday(date_obj, department=None, school_id=None):
    """
    Check if a given date is a holiday.

    Args:
        date_obj (datetime.date): Date to check
        department (str, optional): Department name for department-specific holidays
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        bool: True if the date is a holiday, False otherwise
    """
    import json
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return False

        db = get_db()

        # Check for institution-wide holidays
        institution_holidays = db.execute('''
            SELECT * FROM holidays
            WHERE school_id = ?
            AND holiday_type = 'institution_wide'
            AND is_active = 1
            AND ? BETWEEN start_date AND end_date
        ''', (school_id, date_obj.isoformat())).fetchall()

        if institution_holidays:
            return True

        # Check for department-specific holidays if department is provided
        if department:
            dept_holidays = db.execute('''
                SELECT * FROM holidays
                WHERE school_id = ?
                AND holiday_type = 'department_specific'
                AND is_active = 1
                AND ? BETWEEN start_date AND end_date
            ''', (school_id, date_obj.isoformat())).fetchall()

            for holiday in dept_holidays:
                if holiday['departments']:
                    try:
                        departments = json.loads(holiday['departments'])
                        if department in departments:
                            return True
                    except (json.JSONDecodeError, TypeError):
                        continue

        return False

    except Exception as e:
        print(f"Error checking holiday status: {e}")
        return False


def get_holidays(school_id=None, start_date=None, end_date=None, department=None):
    """
    Get holidays for a school within a date range.

    Args:
        school_id (int, optional): School ID, defaults to current session school_id
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        department (str, optional): Filter by department for department-specific holidays

    Returns:
        list: List of holiday records
    """
    import json
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return []

        db = get_db()

        # Build query conditions
        conditions = ['school_id = ?', 'is_active = 1']
        params = [school_id]

        if start_date:
            conditions.append('end_date >= ?')
            params.append(start_date)

        if end_date:
            conditions.append('start_date <= ?')
            params.append(end_date)

        query = f'''
            SELECT * FROM holidays
            WHERE {' AND '.join(conditions)}
            ORDER BY start_date ASC
        '''

        holidays = db.execute(query, params).fetchall()

        # Filter department-specific holidays if department is specified
        if department:
            filtered_holidays = []
            for holiday in holidays:
                if holiday['holiday_type'] == 'institution_wide':
                    filtered_holidays.append(holiday)
                elif holiday['holiday_type'] == 'department_specific' and holiday['departments']:
                    try:
                        departments = json.loads(holiday['departments'])
                        if department in departments:
                            filtered_holidays.append(holiday)
                    except (json.JSONDecodeError, TypeError):
                        continue
            return filtered_holidays

        return holidays

    except Exception as e:
        print(f"Error getting holidays: {e}")
        return []


def create_holiday(holiday_data):
    """
    Create a new holiday.

    Args:
        holiday_data (dict): Holiday information including name, dates, type, etc.

    Returns:
        dict: Result with success status and holiday_id or error message
    """
    import json
    from flask import session, has_request_context

    try:
        # Handle session data - use provided values or get from session
        if 'school_id' in holiday_data:
            school_id = holiday_data['school_id']
        elif has_request_context():
            school_id = session.get('school_id')
        else:
            return {'success': False, 'message': 'School ID required'}

        if 'created_by' in holiday_data:
            created_by = holiday_data['created_by']
        elif has_request_context():
            created_by = session.get('user_id')
        else:
            created_by = 1  # Default for testing

        if not school_id:
            return {'success': False, 'message': 'Invalid session or school ID'}

        db = get_db()

        # Validate required fields
        required_fields = ['holiday_name', 'start_date', 'end_date', 'holiday_type']
        for field in required_fields:
            if not holiday_data.get(field):
                return {'success': False, 'error': f'Missing required field: {field}'}

        # Prepare departments JSON
        departments_json = None
        if holiday_data.get('departments') and holiday_data['holiday_type'] == 'department_specific':
            departments_json = json.dumps(holiday_data['departments'])

        # Insert holiday
        cursor = db.execute('''
            INSERT INTO holidays (
                school_id, holiday_name, start_date, end_date, holiday_type,
                description, departments, is_recurring, recurring_type, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            school_id,
            holiday_data['holiday_name'],
            holiday_data['start_date'],
            holiday_data['end_date'],
            holiday_data['holiday_type'],
            holiday_data.get('description', ''),
            departments_json,
            holiday_data.get('is_recurring', 0),
            holiday_data.get('recurring_type'),
            created_by
        ))

        db.commit()

        return {
            'success': True,
            'holiday_id': cursor.lastrowid,
            'message': 'Holiday created successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def update_holiday(holiday_id, holiday_data):
    """
    Update an existing holiday.

    Args:
        holiday_id (int): Holiday ID to update
        holiday_data (dict): Updated holiday information

    Returns:
        dict: Result with success status and message
    """
    import json
    from flask import session, has_request_context

    try:
        # Handle session data - use provided values or get from session
        if 'school_id' in holiday_data:
            school_id = holiday_data['school_id']
        elif has_request_context():
            school_id = session.get('school_id')
        else:
            return {'success': False, 'message': 'School ID required'}

        if not school_id:
            return {'success': False, 'message': 'Invalid session or school ID'}

        db = get_db()

        # Check if holiday exists and belongs to the school
        existing_holiday = db.execute('''
            SELECT * FROM holidays WHERE id = ? AND school_id = ?
        ''', (holiday_id, school_id)).fetchone()

        if not existing_holiday:
            return {'success': False, 'error': 'Holiday not found'}

        # Prepare departments JSON
        departments_json = None
        if holiday_data.get('departments') and holiday_data.get('holiday_type') == 'department_specific':
            departments_json = json.dumps(holiday_data['departments'])

        # Update holiday
        db.execute('''
            UPDATE holidays SET
                holiday_name = ?,
                start_date = ?,
                end_date = ?,
                holiday_type = ?,
                description = ?,
                departments = ?,
                is_recurring = ?,
                recurring_type = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (
            holiday_data.get('holiday_name', existing_holiday['holiday_name']),
            holiday_data.get('start_date', existing_holiday['start_date']),
            holiday_data.get('end_date', existing_holiday['end_date']),
            holiday_data.get('holiday_type', existing_holiday['holiday_type']),
            holiday_data.get('description', existing_holiday['description']),
            departments_json,
            holiday_data.get('is_recurring', existing_holiday['is_recurring']),
            holiday_data.get('recurring_type', existing_holiday['recurring_type']),
            holiday_id,
            school_id
        ))

        db.commit()

        return {
            'success': True,
            'message': 'Holiday updated successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_holiday(holiday_id):
    """
    Delete a holiday (soft delete by setting is_active to 0).

    Args:
        holiday_id (int): Holiday ID to delete

    Returns:
        dict: Result with success status and message
    """
    from flask import session

    try:
        school_id = session.get('school_id')

        if not school_id:
            return {'success': False, 'error': 'Invalid session'}

        db = get_db()

        # Check if holiday exists and belongs to the school
        existing_holiday = db.execute('''
            SELECT * FROM holidays WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (holiday_id, school_id)).fetchone()

        if not existing_holiday:
            return {'success': False, 'error': 'Holiday not found'}

        # Soft delete holiday
        db.execute('''
            UPDATE holidays SET
                is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (holiday_id, school_id))

        db.commit()

        return {
            'success': True,
            'message': 'Holiday deleted successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_departments_list(school_id=None):
    """
    Get list of departments for the school.

    Args:
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        list: List of department names
    """
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return []

        db = get_db()

        # Get unique departments from staff table
        departments = db.execute('''
            SELECT DISTINCT department FROM staff
            WHERE school_id = ? AND department IS NOT NULL AND department != ''
            ORDER BY department ASC
        ''', (school_id,)).fetchall()

        return [dept['department'] for dept in departments]

    except Exception as e:
        print(f"Error getting departments list: {e}")
        return []


def save_weekly_off_config(weekly_off_days, school_id=None):
    """
    Save weekly off configuration for a school.

    Args:
        weekly_off_days (list): List of day names (e.g., ['sunday', 'saturday'])
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        dict: Result with success status and message
    """
    from flask import session, has_request_context

    try:
        if not school_id:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return {'success': False, 'error': 'Invalid session'}

        db = get_db()

        # Day name to number mapping
        day_mapping = {
            'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3,
            'thursday': 4, 'friday': 5, 'saturday': 6
        }

        # Clear existing configuration for this school
        db.execute('DELETE FROM weekly_off_config WHERE school_id = ?', (school_id,))

        # Insert new configuration
        for day_name in weekly_off_days:
            day_name_lower = day_name.lower()
            if day_name_lower in day_mapping:
                day_number = day_mapping[day_name_lower]
                db.execute('''
                    INSERT INTO weekly_off_config (school_id, day_of_week, is_enabled)
                    VALUES (?, ?, 1)
                ''', (school_id, day_number))

        db.commit()

        return {
            'success': True,
            'message': 'Weekly off configuration saved successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_weekly_off_config(school_id=None):
    """
    Get weekly off configuration for a school.

    Args:
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        dict: Result with success status and weekly off days
    """
    from flask import session, has_request_context

    try:
        if not school_id:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return {'success': False, 'error': 'Invalid session'}

        db = get_db()

        # Get weekly off configuration
        config = db.execute('''
            SELECT day_of_week FROM weekly_off_config
            WHERE school_id = ? AND is_enabled = 1
            ORDER BY day_of_week
        ''', (school_id,)).fetchall()

        # Number to day name mapping
        day_names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

        weekly_off_days = [day_names[row['day_of_week']] for row in config]

        return {
            'success': True,
            'weekly_off_days': weekly_off_days
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def is_weekly_off_day(date, school_id=None):
    """
    Check if a given date is a weekly off day.

    Args:
        date (datetime.date or str): Date to check
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        bool: True if the date is a weekly off day
    """
    from flask import session, has_request_context
    import datetime

    try:
        if not school_id:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return False

        # Convert string date to datetime.date if needed
        if isinstance(date, str):
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

        # Get day of week - Python's weekday() returns 0=Monday, 6=Sunday
        # We need to convert to JavaScript format: 0=Sunday, 1=Monday, ..., 6=Saturday
        python_weekday = date.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
        our_weekday = (python_weekday + 1) % 7  # Convert: 0=Sunday, 1=Monday, ..., 6=Saturday

        db = get_db()

        # Check if this day is configured as weekly off
        result = db.execute('''
            SELECT COUNT(*) as count FROM weekly_off_config
            WHERE school_id = ? AND day_of_week = ? AND is_enabled = 1
        ''', (school_id, our_weekday)).fetchone()

        return result['count'] > 0

    except Exception as e:
        print(f"Error checking weekly off day: {e}")
        return False


# ===========================
# Department Management Functions
# ===========================

def create_departments_table():
    """Create the departments table if it doesn't exist"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            department_name TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, department_name COLLATE NOCASE)
        )
        ''')
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating departments table: {e}")
        return False


def initialize_default_departments(school_id):
    """Initialize default departments for a school if none exist"""
    try:
        # Create table if it doesn't exist
        create_departments_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if departments already exist for this school
        existing = cursor.execute(
            'SELECT COUNT(*) as count FROM departments WHERE school_id = ?',
            (school_id,)
        ).fetchone()
        
        if existing['count'] > 0:
            return True  # Departments already exist
        
        # Default departments to add
        default_departments = [
            ('Administration', 'Administrative staff and management'),
            ('Teaching', 'Teaching faculty and educators'),
            ('IT & Technology', 'Information technology and technical support'),
            ('Finance', 'Accounting, finance, and budgeting'),
            ('Human Resources', 'HR and personnel management'),
            ('Maintenance', 'Facilities and maintenance staff'),
            ('Library', 'Library staff and resources'),
            ('Security', 'Security and safety personnel')
        ]
        
        # Insert default departments
        for dept_name, description in default_departments:
            cursor.execute('''
                INSERT INTO departments (school_id, department_name, description)
                VALUES (?, ?, ?)
            ''', (school_id, dept_name, description))
        
        db.commit()
        print(f"Initialized {len(default_departments)} default departments for school_id {school_id}")
        return True
        
    except Exception as e:
        print(f"Error initializing default departments: {e}")
        db.rollback()
        return False


def get_all_departments(school_id):
    """Get all active departments for a school"""
    try:
        # Create table if it doesn't exist
        create_departments_table()
        
        db = get_db()
        cursor = db.cursor()
        
        departments = cursor.execute('''
            SELECT id, department_name, description
            FROM departments
            WHERE school_id = ? AND is_active = 1
            ORDER BY department_name
        ''', (school_id,)).fetchall()
        
        # Convert to list of dictionaries
        result = [dict(dept) for dept in departments]
        
        # If no departments exist, initialize defaults
        if not result:
            initialize_default_departments(school_id)
            # Fetch again after initialization
            departments = cursor.execute('''
                SELECT id, department_name, description
                FROM departments
                WHERE school_id = ? AND is_active = 1
                ORDER BY department_name
            ''', (school_id,)).fetchall()
            result = [dict(dept) for dept in departments]
        
        return result
        
    except Exception as e:
        print(f"Error fetching departments: {e}")
        # Return default list if database operation fails
        return [
            {'id': 0, 'department_name': 'Administration', 'description': ''},
            {'id': 0, 'department_name': 'Teaching', 'description': ''},
            {'id': 0, 'department_name': 'IT & Technology', 'description': ''},
            {'id': 0, 'department_name': 'Finance', 'description': ''}
        ]


def add_department(name, description, school_id):
    """Add a new department to the database"""
    db = None
    try:
        if not name or not name.strip():
            return {'success': False, 'message': 'Department name is required'}
        
        name = name.strip()
        
        # Create table if it doesn't exist
        create_departments_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check for existing department (both active and inactive)
        existing = cursor.execute('''
            SELECT id, is_active FROM departments 
            WHERE school_id = ? AND LOWER(department_name) = LOWER(?)
        ''', (school_id, name)).fetchone()
        
        if existing:
            # If department exists and is inactive, reactivate it
            if existing['is_active'] == 0:
                cursor.execute('''
                    UPDATE departments 
                    SET is_active = 1, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND school_id = ?
                ''', (description or '', existing['id'], school_id))
                
                db.commit()
                
                return {
                    'success': True,
                    'message': f'Department "{name}" reactivated successfully',
                    'department_name': name
                }
            else:
                # Department exists and is active
                return {'success': False, 'message': 'Department already exists'}
        
        # Insert new department if it doesn't exist
        cursor.execute('''
            INSERT INTO departments (school_id, department_name, description)
            VALUES (?, ?, ?)
        ''', (school_id, name, description or ''))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Department "{name}" added successfully',
            'department_name': name
        }
        
    except Exception as e:
        print(f"Error adding department: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error adding department: {str(e)}'}


def delete_department(department_id, school_id):
    """Delete a department from the database"""
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if department exists and belongs to this school
        existing = cursor.execute('''
            SELECT department_name FROM departments 
            WHERE id = ? AND school_id = ?
        ''', (department_id, school_id)).fetchone()
        
        if not existing:
            return {'success': False, 'message': 'Department not found'}
        
        department_name = existing['department_name']
        
        # Check if any staff members are assigned to this department
        staff_count = cursor.execute('''
            SELECT COUNT(*) as count FROM staff 
            WHERE school_id = ? AND department = ?
        ''', (school_id, department_name)).fetchone()
        
        if staff_count and staff_count['count'] > 0:
            return {
                'success': False, 
                'message': f'Cannot delete department "{department_name}". {staff_count["count"]} staff member(s) are assigned to it.'
            }
        
        # Soft delete: Set is_active to 0
        cursor.execute('''
            UPDATE departments 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (department_id, school_id))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Department "{department_name}" deleted successfully'
        }
        
    except Exception as e:
        print(f"Error deleting department: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error deleting department: {str(e)}'}


# ===========================
# Position Management Functions
# ===========================

def create_positions_table():
    """Create the positions table if it doesn't exist"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            position_name TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, position_name COLLATE NOCASE)
        )
        ''')
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating positions table: {e}")
        return False


def initialize_default_positions(school_id):
    """Initialize default positions for a school if none exist"""
    try:
        # Create table if it doesn't exist
        create_positions_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if positions already exist for this school
        existing = cursor.execute(
            'SELECT COUNT(*) as count FROM positions WHERE school_id = ?',
            (school_id,)
        ).fetchone()
        
        if existing['count'] > 0:
            return True  # Positions already exist
        
        # Default positions to add
        default_positions = [
            ('Teacher', 'Teaching staff and faculty members'),
            ('Principal', 'School principal and head administrator'),
            ('Vice Principal', 'Assistant to the principal'),
            ('HOD', 'Head of Department'),
            ('Coordinator', 'Department or program coordinator'),
            ('Lab Assistant', 'Laboratory technical assistant'),
            ('Librarian', 'Library management and services'),
            ('Accountant', 'Finance and accounting staff'),
            ('Office Administrator', 'Office management and administration'),
            ('Receptionist', 'Front desk and reception staff'),
            ('Clerk', 'Administrative clerk'),
            ('Peon', 'Support and housekeeping staff'),
            ('Security Guard', 'Security and safety personnel'),
            ('IT Support', 'Information technology support staff'),
            ('Counselor', 'Student counseling and guidance')
        ]
        
        # Insert default positions
        for position_name, description in default_positions:
            cursor.execute('''
                INSERT INTO positions (school_id, position_name, description)
                VALUES (?, ?, ?)
            ''', (school_id, position_name, description))
        
        db.commit()
        print(f"Initialized {len(default_positions)} default positions for school_id {school_id}")
        return True
        
    except Exception as e:
        print(f"Error initializing default positions: {e}")
        db.rollback()
        return False


def get_all_positions(school_id):
    """
    Get all active positions for a school, including positions currently used by staff
    This ensures backward compatibility with legacy position data
    """
    try:
        # Create table if it doesn't exist
        create_positions_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Get active positions from positions table
        positions = cursor.execute('''
            SELECT id, position_name, description
            FROM positions
            WHERE school_id = ? AND is_active = 1
            ORDER BY position_name
        ''', (school_id,)).fetchall()
        
        # Convert to list of dictionaries
        result = [dict(pos) for pos in positions]
        
        # If no positions exist, initialize defaults
        if not result:
            initialize_default_positions(school_id)
            # Fetch again after initialization
            positions = cursor.execute('''
                SELECT id, position_name, description
                FROM positions
                WHERE school_id = ? AND is_active = 1
                ORDER BY position_name
            ''', (school_id,)).fetchall()
            result = [dict(pos) for pos in positions]
        
        # Get position names that are already in the result
        existing_position_names = {pos['position_name'].lower() for pos in result if pos.get('position_name')}
        
        # Also get positions that are currently being used by staff but not in positions table
        # This handles legacy data and deleted positions
        staff_positions = cursor.execute('''
            SELECT DISTINCT destination as position_name
            FROM staff
            WHERE school_id = ? 
            AND destination IS NOT NULL 
            AND TRIM(destination) != ''
            UNION
            SELECT DISTINCT position as position_name
            FROM staff
            WHERE school_id = ? 
            AND position IS NOT NULL 
            AND TRIM(position) != ''
        ''', (school_id, school_id)).fetchall()
        
        # Add staff positions that aren't already in the result
        for staff_pos in staff_positions:
            pos_name = staff_pos['position_name'].strip() if staff_pos['position_name'] else None
            if pos_name and pos_name.lower() not in existing_position_names:
                result.append({
                    'id': 0,  # Legacy position (not in positions table)
                    'position_name': pos_name,
                    'description': 'Legacy position'
                })
                existing_position_names.add(pos_name.lower())
        
        # Sort the final result by position name
        result.sort(key=lambda x: x['position_name'])
        
        return result
        
    except Exception as e:
        print(f"Error fetching positions: {e}")
        # Return default list if database operation fails
        return [
            {'id': 0, 'position_name': 'Teacher', 'description': ''},
            {'id': 0, 'position_name': 'Principal', 'description': ''},
            {'id': 0, 'position_name': 'Vice Principal', 'description': ''},
            {'id': 0, 'position_name': 'HOD', 'description': ''}
        ]


def add_position(name, description, school_id):
    """Add a new position to the database"""
    db = None
    try:
        if not name or not name.strip():
            return {'success': False, 'message': 'Position name is required'}
        
        name = name.strip()
        
        # Create table if it doesn't exist
        create_positions_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check for existing position (both active and inactive)
        existing = cursor.execute('''
            SELECT id, is_active FROM positions 
            WHERE school_id = ? AND LOWER(position_name) = LOWER(?)
        ''', (school_id, name)).fetchone()
        
        if existing:
            # If position exists and is inactive, reactivate it
            if existing['is_active'] == 0:
                cursor.execute('''
                    UPDATE positions 
                    SET is_active = 1, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND school_id = ?
                ''', (description or '', existing['id'], school_id))
                
                db.commit()
                
                return {
                    'success': True,
                    'message': f'Position "{name}" reactivated successfully',
                    'position_name': name
                }
            else:
                # Position exists and is active
                return {'success': False, 'message': 'Position already exists'}
        
        # Insert new position if it doesn't exist
        cursor.execute('''
            INSERT INTO positions (school_id, position_name, description)
            VALUES (?, ?, ?)
        ''', (school_id, name, description or ''))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Position "{name}" added successfully',
            'position_name': name
        }
        
    except Exception as e:
        print(f"Error adding position: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error adding position: {str(e)}'}

def delete_position(position_id, school_id):
    """
    Soft delete a position by setting is_active to 0
    
    Args:
        position_id: The ID of the position to delete
        school_id: The school ID (for security)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify the position belongs to the school
        cursor.execute('''
            SELECT id, position_name FROM positions 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (position_id, school_id))
        
        position = cursor.fetchone()
        
        if not position:
            return {'success': False, 'message': 'Position not found or already deleted'}
        
        position_name = position[1]
        
        # Soft delete the position
        cursor.execute('''
            UPDATE positions 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (position_id, school_id))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Position "{position_name}" deleted successfully'
        }
        
    except Exception as e:
        print(f"Error deleting position: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error deleting position: {str(e)}'}


# =============================================================================
# BIOMETRIC DEVICE MANAGEMENT FUNCTIONS
# =============================================================================

def get_device_for_institution(school_id, device_id=None):
    """
    Get biometric device(s) for an institution
    
    Args:
        school_id: The institution ID
        device_id: Optional specific device ID
    
    Returns:
        Device dict or list of devices
    """
    db = get_db()
    cursor = db.cursor()
    
    if device_id:
        # Get specific device
        cursor.execute('''
            SELECT * FROM biometric_devices 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (device_id, school_id))
        row = cursor.fetchone()
        return dict(row) if row else None
    else:
        # Get all active devices for institution
        cursor.execute('''
            SELECT * FROM biometric_devices 
            WHERE school_id = ? AND is_active = 1
            ORDER BY device_name
        ''', (school_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_primary_device_for_institution(school_id):
    """
    Get the first active device for an institution (for backward compatibility)
    
    Args:
        school_id: The institution ID
    
    Returns:
        Device dict or None
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM biometric_devices 
        WHERE school_id = ? AND is_active = 1
        ORDER BY id
        LIMIT 1
    ''', (school_id,))
    
    row = cursor.fetchone()
    return dict(row) if row else None


def get_all_devices_with_details():
    """
    Get all biometric devices with institution and agent details
    
    Returns:
        List of device dicts with joined data
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            d.id, d.device_name, d.connection_type, d.ip_address, d.port,
            d.serial_number, d.is_active, d.last_sync, d.sync_status,
            s.name as school_name, s.id as school_id,
            a.agent_name, a.id as agent_id, a.is_active as agent_active
        FROM biometric_devices d
        LEFT JOIN schools s ON d.school_id = s.id
        LEFT JOIN biometric_agents a ON d.agent_id = a.id
        ORDER BY d.school_id, d.device_name
    ''')
    
    return [dict(row) for row in cursor.fetchall()]


def create_biometric_device(school_id, device_name, connection_type, ip_address=None, 
                            port=4370, serial_number=None, agent_id=None):
    """
    Create a new biometric device
    
    Args:
        school_id: Institution ID
        device_name: Display name for device
        connection_type: 'Direct_LAN', 'ADMS', or 'Agent_LAN'
        ip_address: IP address (for Direct_LAN or Agent_LAN)
        port: Port number (default 4370)
        serial_number: Serial number (for ADMS)
        agent_id: Local agent ID (for Agent_LAN)
    
    Returns:
        dict: {'success': bool, 'message': str, 'device_id': int}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate connection_type
        valid_types = ['Direct_LAN', 'ADMS', 'Agent_LAN']
        if connection_type not in valid_types:
            return {'success': False, 'message': f'Invalid connection type. Must be one of: {", ".join(valid_types)}'}
        
        # Validate required fields based on connection type
        if connection_type == 'Direct_LAN' and not ip_address:
            return {'success': False, 'message': 'IP address is required for Direct LAN connection'}
        
        if connection_type == 'ADMS' and not serial_number:
            return {'success': False, 'message': 'Serial number is required for ADMS connection'}
        
        if connection_type == 'Agent_LAN' and not agent_id:
            return {'success': False, 'message': 'Agent ID is required for Agent LAN connection'}
        
        # Check for duplicate device name in same institution
        cursor.execute('''
            SELECT id FROM biometric_devices 
            WHERE school_id = ? AND device_name = ? AND is_active = 1
        ''', (school_id, device_name))
        
        existing = cursor.fetchone()
        if existing:
            return {
                'success': False, 
                'message': f'Device name "{device_name}" already exists in this institution. Please use a different name (e.g., "{device_name} 2")'
            }
        
        # Insert device
        cursor.execute('''
            INSERT INTO biometric_devices 
            (school_id, device_name, connection_type, ip_address, port, 
             serial_number, agent_id, is_active, sync_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'pending')
        ''', (school_id, device_name, connection_type, ip_address, port, serial_number, agent_id))
        
        device_id = cursor.lastrowid
        db.commit()
        
        return {
            'success': True,
            'message': f'Device "{device_name}" created successfully',
            'device_id': device_id
        }
        
    except Exception as e:
        print(f"Error creating biometric device: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error creating device: {str(e)}'}


def update_biometric_device(device_id, school_id, device_name=None, ip_address=None, 
                            port=None, serial_number=None, agent_id=None):
    """
    Update biometric device details
    
    Args:
        device_id: Device ID to update
        school_id: Institution ID (for security)
        device_name: New device name (optional)
        ip_address: New IP address (optional)
        port: New port (optional)
        serial_number: New serial number (optional)
        agent_id: New agent ID (optional)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify device belongs to institution
        cursor.execute('''
            SELECT id FROM biometric_devices 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (device_id, school_id))
        
        if not cursor.fetchone():
            return {'success': False, 'message': 'Device not found or access denied'}
        
        # Check for duplicate device name if updating name
        if device_name is not None:
            cursor.execute('''
                SELECT id FROM biometric_devices 
                WHERE school_id = ? AND device_name = ? AND id != ? AND is_active = 1
            ''', (school_id, device_name, device_id))
            
            if cursor.fetchone():
                return {
                    'success': False, 
                    'message': f'Device name "{device_name}" already exists in this institution. Please use a different name.'
                }
        
        # Build update query dynamically
        updates = []
        params = []
        
        if device_name is not None:
            updates.append('device_name = ?')
            params.append(device_name)
        
        if ip_address is not None:
            updates.append('ip_address = ?')
            params.append(ip_address)
        
        if port is not None:
            updates.append('port = ?')
            params.append(port)
        
        if serial_number is not None:
            updates.append('serial_number = ?')
            params.append(serial_number)
        
        if agent_id is not None:
            updates.append('agent_id = ?')
            params.append(agent_id)
        
        if not updates:
            return {'success': False, 'message': 'No fields to update'}
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.extend([device_id, school_id])
        
        query = f'''
            UPDATE biometric_devices 
            SET {', '.join(updates)}
            WHERE id = ? AND school_id = ?
        '''
        
        cursor.execute(query, params)
        db.commit()
        
        return {
            'success': True,
            'message': 'Device updated successfully'
        }
        
    except Exception as e:
        print(f"Error updating biometric device: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error updating device: {str(e)}'}


def delete_biometric_device(device_id, school_id):
    """
    Soft delete a biometric device
    
    Args:
        device_id: Device ID
        school_id: Institution ID (for security)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify device belongs to institution
        cursor.execute('''
            SELECT device_name FROM biometric_devices 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (device_id, school_id))
        
        device = cursor.fetchone()
        if not device:
            return {'success': False, 'message': 'Device not found or already deleted'}
        
        device_name = device[0]
        
        # Soft delete
        cursor.execute('''
            UPDATE biometric_devices 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (device_id, school_id))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Device "{device_name}" deleted successfully'
        }
        
    except Exception as e:
        print(f"Error deleting biometric device: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error deleting device: {str(e)}'}


def update_device_sync_status(device_id, last_sync=None, sync_status='success'):
    """
    Update device sync status and timestamp
    
    Args:
        device_id: Device ID
        last_sync: Last sync datetime (defaults to now in local time)
        sync_status: Sync status ('success', 'failed', 'pending', 'unknown')
    
    Returns:
        bool: Success status
    """
    db = None
    try:
        from datetime import datetime
        db = get_db()
        cursor = db.cursor()
        
        if last_sync is None:
            # Use local time instead of UTC
            last_sync = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            UPDATE biometric_devices 
            SET last_sync = ?, sync_status = ?
            WHERE id = ?
        ''', (last_sync, sync_status, device_id))
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error updating device sync status: {e}")
        if db:
            db.rollback()
        return False


# =============================================================================
# BIOMETRIC AGENT MANAGEMENT FUNCTIONS
# =============================================================================

def get_agents_for_institution(school_id):
    """
    Get all agents for an institution
    
    Args:
        school_id: Institution ID
    
    Returns:
        List of agent dicts
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM biometric_agents 
        WHERE school_id = ? 
        ORDER BY agent_name
    ''', (school_id,))
    
    return [dict(row) for row in cursor.fetchall()]


def get_all_agents_with_details():
    """
    Get all agents with institution details
    
    Returns:
        List of agent dicts with joined data
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            a.id, a.agent_name, a.api_key, a.is_active, 
            a.last_heartbeat, a.created_at,
            s.name as school_name, s.id as school_id,
            COUNT(d.id) as device_count
        FROM biometric_agents a
        LEFT JOIN schools s ON a.school_id = s.id
        LEFT JOIN biometric_devices d ON a.id = d.agent_id AND d.is_active = 1
        GROUP BY a.id
        ORDER BY a.school_id, a.agent_name
    ''')
    
    return [dict(row) for row in cursor.fetchall()]


def create_biometric_agent(school_id, agent_name):
    """
    Create a new local agent
    
    Args:
        school_id: Institution ID
        agent_name: Display name for agent
    
    Returns:
        dict: {'success': bool, 'message': str, 'agent_id': int, 'api_key': str}
    """
    db = None
    try:
        import secrets
        
        db = get_db()
        cursor = db.cursor()
        
        # Generate unique API key
        api_key = secrets.token_urlsafe(48)
        
        # Insert agent
        cursor.execute('''
            INSERT INTO biometric_agents 
            (school_id, agent_name, api_key, is_active)
            VALUES (?, ?, ?, 1)
        ''', (school_id, agent_name, api_key))
        
        agent_id = cursor.lastrowid
        db.commit()
        
        return {
            'success': True,
            'message': f'Agent "{agent_name}" created successfully',
            'agent_id': agent_id,
            'api_key': api_key
        }
        
    except Exception as e:
        print(f"Error creating biometric agent: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error creating agent: {str(e)}'}


def update_agent_heartbeat(api_key):
    """
    Update agent last heartbeat timestamp
    
    Args:
        api_key: Agent API key
    
    Returns:
        dict: {'success': bool, 'agent_id': int, 'school_id': int}
    """
    db = None
    try:
        db = get_db()
        import datetime
        cursor = db.cursor()
        
        # Get current UTC timestamp
        current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get agent info and update heartbeat
        cursor.execute('''
            UPDATE biometric_agents 
            SET last_heartbeat = ?, updated_at = ?
            WHERE api_key = ? AND is_active = 1
        ''', (current_time, current_time, api_key))
        
        if cursor.rowcount == 0:
            return {'success': False, 'message': 'Invalid API key or agent inactive'}
        
        # Get agent details
        cursor.execute('''
            SELECT id, school_id FROM biometric_agents 
            WHERE api_key = ?
        ''', (api_key,))
        
        row = cursor.fetchone()
        db.commit()
        
        return {
            'success': True,
            'agent_id': row[0],
            'school_id': row[1],
            'last_heartbeat': current_time
        }
        
    except Exception as e:
        print(f"Error updating agent heartbeat: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error: {str(e)}'}


def verify_agent_api_key(api_key):
    """
    Verify agent API key and return agent/school info
    
    Args:
        api_key: Agent API key
    
    Returns:
        dict: Agent info or None
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT a.id, a.school_id, a.agent_name, a.is_active,
               s.name as school_name
        FROM biometric_agents a
        LEFT JOIN schools s ON a.school_id = s.id
        WHERE a.api_key = ? AND a.is_active = 1
    ''', (api_key,))
    
    row = cursor.fetchone()
    return dict(row) if row else None


def deactivate_biometric_agent(agent_id, school_id):
    """
    Deactivate a local agent
    
    Args:
        agent_id: Agent ID
        school_id: Institution ID (for security)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify agent belongs to institution
        cursor.execute('''
            SELECT agent_name FROM biometric_agents 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (agent_id, school_id))
        
        agent = cursor.fetchone()
        if not agent:
            return {'success': False, 'message': 'Agent not found or already deactivated'}
        
        agent_name = agent[0]
        
        # Deactivate agent
        cursor.execute('''
            UPDATE biometric_agents 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (agent_id, school_id))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Agent "{agent_name}" deactivated successfully'
        }
        
    except Exception as e:
        print(f"Error deactivating agent: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error deactivating agent: {str(e)}'}


def get_all_schools():
    """
    Get list of all schools for dropdown menus
    
    Returns:
        list: List of school dictionaries with id and name
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, name 
            FROM schools 
            ORDER BY name
        ''')
        
        schools = []
        for row in cursor.fetchall():
            schools.append({
                'id': row[0],
                'name': row[1]
            })
        
        return schools
        
    except Exception as e:
        print(f"Error fetching schools: {e}")
        return []


def get_system_setting(key, default_value=None):
    """
    Get a system setting value by key
    
    Args:
        key: Setting key
        default_value: Default value if setting doesn't exist
    
    Returns:
        Setting value or default_value
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT setting_value FROM system_settings 
            WHERE setting_key = ?
        ''', (key,))
        
        row = cursor.fetchone()
        return row[0] if row else default_value
        
    except Exception as e:
        print(f"Error getting system setting {key}: {e}")
        return default_value


def set_system_setting(key, value, description=None):
    """
    Set a system setting value
    
    Args:
        key: Setting key
        value: Setting value
        description: Optional description
    
    Returns:
        bool: Success status
    """
    db = None
    try:
        import datetime
        db = get_db()
        cursor = db.cursor()
        
        current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO system_settings (setting_key, setting_value, description, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                description = COALESCE(excluded.description, description),
                updated_at = excluded.updated_at
        ''', (key, str(value), description, current_time))
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error setting system setting {key}: {e}")
        if db:
            db.rollback()
        return False
