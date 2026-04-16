import datetime
import os
import sys
import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database


def parse_t(value):
    if value is None:
        return None
    if isinstance(value, datetime.timedelta):
        total = int(value.total_seconds())
        h = (total // 3600) % 24
        m = (total % 3600) // 60
        s = total % 60
        return datetime.time(h, m, s)
    if isinstance(value, datetime.time):
        return value
    raw = str(value)
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    return None


def main():
    params = database._parse_mysql_url(database.DATABASE_URL)
    conn = pymysql.connect(**params)
    cur = conn.cursor()

    cur.execute(
        "SELECT shift_type, start_time, end_time, COALESCE(grace_period_minutes, 0) "
        "FROM shift_definitions WHERE is_active = 1"
    )
    shift_defs = {
        row[0]: {
            "start": str(row[1]),
            "end": str(row[2]),
            "grace": int(row[3] or 0),
        }
        for row in cur.fetchall()
    }

    cur.execute(
        """
        SELECT a.id, a.staff_id, a.time_in, a.time_out,
               COALESCE(a.status, 'present') AS status,
               COALESCE(NULLIF(s.shift_type, ''), 'general') AS staff_shift
        FROM attendance a
        JOIN staff s ON s.id = a.staff_id
        WHERE a.school_id = %s
          AND a.date = CURDATE()
          AND COALESCE(a.notes, '') LIKE 'Attendance via id_scan%%'
        ORDER BY a.id
        """,
        (5,),
    )
    rows = cur.fetchall()

    for row in rows:
        attendance_id, _, time_in, time_out, old_status, staff_shift = row
        shift = shift_defs.get(staff_shift) or shift_defs.get("general")
        if not shift:
            continue

        start = parse_t(shift["start"])
        end = parse_t(shift["end"])
        grace = int(shift.get("grace", 0))
        check_in = parse_t(time_in)
        check_out = parse_t(time_out)

        late_minutes = 0
        early_minutes = 0
        new_status = "present"

        if check_in and start:
            today = datetime.date.today()
            check_in_dt = datetime.datetime.combine(today, check_in)
            start_dt = datetime.datetime.combine(today, start)
            grace_cutoff = start_dt + datetime.timedelta(minutes=grace)

            if check_in_dt > grace_cutoff:
                new_status = "late"
                late_minutes = int((check_in_dt - start_dt).total_seconds() // 60)
            elif check_in_dt > start_dt:
                new_status = "present"
                late_minutes = int((check_in_dt - start_dt).total_seconds() // 60)

        if check_in and check_out and start and end:
            today = datetime.date.today()
            check_out_dt = datetime.datetime.combine(today, check_out)
            end_dt = datetime.datetime.combine(today, end)

            if end < start:
                end_dt = end_dt + datetime.timedelta(days=1)
                if check_out < start:
                    check_out_dt = check_out_dt + datetime.timedelta(days=1)

            if check_out_dt < end_dt:
                early_minutes = int((end_dt - check_out_dt).total_seconds() // 60)
                if new_status != "late":
                    new_status = "left_soon"

        if str(old_status).lower() in {
            "approved_regularization",
            "leave",
            "holiday",
            "on_duty",
            "on_permission",
            "absent",
        }:
            new_status = old_status

        cur.execute(
            """
            UPDATE attendance
            SET status = %s,
                late_duration_minutes = %s,
                early_departure_minutes = %s,
                shift_type = %s,
                shift_start_time = %s,
                shift_end_time = %s
            WHERE id = %s
            """,
            (
                new_status,
                late_minutes,
                early_minutes,
                staff_shift,
                start.strftime("%H:%M:%S") if start else None,
                end.strftime("%H:%M:%S") if end else None,
                attendance_id,
            ),
        )

    conn.commit()

    cur.execute(
        """
        SELECT a.staff_id, s.full_name, a.time_in, a.time_out, a.status,
               COALESCE(a.late_duration_minutes, 0),
               COALESCE(a.early_departure_minutes, 0),
               COALESCE(a.shift_type, '')
        FROM attendance a
        JOIN staff s ON s.id = a.staff_id
        WHERE a.school_id = %s
          AND a.date = CURDATE()
          AND COALESCE(a.notes, '') LIKE 'Attendance via id_scan%%'
        ORDER BY s.full_name
        """,
        (5,),
    )

    updated = cur.fetchall()
    print(f"updated_rows={len(updated)}")
    for record in updated:
        print(record)

    conn.close()


if __name__ == "__main__":
    main()
