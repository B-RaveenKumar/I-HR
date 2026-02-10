# Timetable System - Testing & Troubleshooting Guide

## Pre-Testing Checklist

- [ ] Database initialized successfully
- [ ] `timetable_manager.py` module importable
- [ ] `app.py` loads without errors
- [ ] All templates present in `/templates` folder
- [ ] Sidebar menu links visible
- [ ] Application running without console errors

---

## Quick Test Script

Run this to verify basic setup:

```python
# In Flask shell: flask shell

# Test 1: Import modules
from timetable_manager import TimetableManager
from database import get_db
print("✓ Modules imported")

# Test 2: Check database tables
db = get_db()
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'timetable%'")
tables = cursor.fetchall()
print(f"✓ Found {len(tables)} timetable tables")
for table in tables:
    print(f"  - {table[0]}")

# Test 3: Check admin route
from app import app
with app.test_client() as client:
    print("✓ Routes registered")
```

---

## Manual Testing Flow

### 1️⃣ Company Admin - Enable Timetable

**Steps**:
1. Login as Company Admin
2. Navigate to: Company Dashboard → Select a School
3. Look for "Timetable Settings" option
4. **Expected**: Button/link visible
5. Click it
6. **Expected**: Page shows toggle switch
7. Toggle ON
8. **Expected**: "ENABLED" status message

**If Failed**:
- [ ] Check if route `/company/timetable_settings/<id>` exists
- [ ] Check session user_type is 'company_admin'
- [ ] Check template exists: `company_timetable_settings.html`
- [ ] Check for JavaScript errors in console

---

### 2️⃣ Admin - Configure Periods

**Prerequisites**: Timetable enabled for school

**Steps**:
1. Login as School Admin
2. Check sidebar for "Timetable Management"
3. **Expected**: Link visible (only if enabled)
4. Click it
5. **Expected**: Dashboard loads with 3 tabs
6. On "Period Configuration" tab:
   - Period Number: `9`
   - Period Name: `Extra Period`
   - Start Time: `14:00`
   - End Time: `14:30`
7. Click "Add Period"
8. **Expected**: Success notification + Period appears below

**If Failed**:
- [ ] Check browser console for errors
- [ ] Check server logs for error messages
- [ ] Verify CSRF token present
- [ ] Check if schema tables created: `sqlite3 vishnorex.db ".tables" | grep timetable`

**Database Check**:
```sql
SELECT * FROM timetable_periods WHERE school_id = 1;
```

---

### 3️⃣ Admin - Set Department Permissions

**Steps**:
1. In Timetable Management
2. Click "Department Permissions" tab
3. Find "Library" department
4. **Check**: Both "Can Send Requests" and "Can Receive Requests"
5. Click "Save Permissions"
6. **Expected**: Success notification

**Database Verification**:
```sql
SELECT * FROM timetable_department_permissions WHERE department = 'Library';
```

---

### 4️⃣ Staff - View Timetable

**Steps**:
1. Login as Staff member
2. Check sidebar for "My Timetable"
3. **Expected**: Link visible (only if module enabled)
4. Click it
5. **Expected**: Timetable grid displays
6. **Verify**:
   - [ ] Week layout (Mon-Sat)
   - [ ] All periods visible
   - [ ] Period times display
   - [ ] Status indicators show

**If Not Visible**:
- [ ] Check if timetable enabled for school
- [ ] Check session school_id set correctly
- [ ] Check table `timetable_periods` has data
- [ ] Check browser console for JavaScript errors

---

### 5️⃣ Staff - Request Alteration

**Prerequisites**: Assigned to a period

**Steps**:
1. On personal timetable
2. Find assigned period (blue)
3. Click "Request Change"
4. **Expected**: Modal appears
5. Select Target Department
6. **Expected**: Available staff loads in dropdown
7. Select a staff member
8. Add reason
9. Click "Send Request"
10. **Expected**: Success notification + modal closes

**If Modal Doesn't Open**:
- [ ] Check browser console for errors
- [ ] Check period is marked as assigned
- [ ] Check period is not locked
- [ ] Check department allows outbound alterations

**If Department Locked**:
- This is correct behavior - button should be hidden
- Verify in database: `allow_alterations = 0`

---

### 6️⃣ Staff - Accept/Reject Alteration

**Prerequisites**: Pending request received

**Steps**:
1. On personal timetable
2. Look for "Pending Alteration Requests" section
3. **Expected**: Shows requests from other staff
4. Click "Accept"
5. **Expected**: Success notification + timetable updates

**Debug Pending Requests**:
```sql
SELECT * FROM timetable_alteration_requests 
WHERE status = 'pending' 
AND target_staff_id = <staff_id>;
```

---

### 7️⃣ Staff - Add Self-Allocation

**Prerequisites**: Empty period available

**Steps**:
1. On personal timetable
2. Find empty period (yellow)
3. Click "Add Class"
4. **Expected**: Modal appears
5. Enter class name
6. Read warning about admin lock
7. Click "Add Class"
8. **Expected**: Success notification + status changes to "Self-Added" (cyan)

**If Empty Slots Missing**:
- Admin must leave some slots unassigned
- Check database: `is_assigned = 0`
- Make sure not all periods have assignments

---

### 8️⃣ Staff - Try to Delete Self-Allocation

**Steps**:
1. On personal timetable
2. Find self-allocated period (cyan)
3. Look for "Delete" button
4. **Expected**: Button disabled or says "(Locked)"
5. Try to click
6. **Expected**: Does nothing or error message

**Verify Lock in Database**:
```sql
SELECT * FROM timetable_self_allocations WHERE staff_id = <staff_id>;
```
Should show `is_admin_locked = 1`

---

### 9️⃣ Admin - Override Assignment

**Prerequisites**: Period assigned to a staff

**Steps**:
1. In Timetable Management
2. "Staff Assignments" tab
3. Select a staff member
4. Click "View Timetable"
5. Find an assigned period
6. **Expected**: Period details show
7. Click "Re-assign"
8. **Expected**: Modal or option to select new staff
9. Select different staff
10. Add optional notes
11. Click "Process"
12. **Expected**: Success notification

**Verify Override in Database**:
```sql
SELECT * FROM timetable_alteration_requests 
WHERE alteration_type = 'admin_override' 
ORDER BY processed_at DESC 
LIMIT 1;
```

---

## Common Issues & Solutions

### Issue: Timetable Link Not Showing in Sidebar

**Cause**: Module not enabled or user type incorrect

**Solution**:
```python
# Check if enabled
from timetable_manager import TimetableManager
TimetableManager.enable_timetable_for_school(school_id, True)

# Verify
is_enabled = TimetableManager.is_timetable_enabled(school_id)
print(f"Timetable enabled: {is_enabled}")
```

---

### Issue: "Request Alteration" Button Hidden

**Possible Causes**:
1. Department has alterations disabled
2. Period is locked
3. Department has `allow_alterations = 0`

**Solution**:
```python
# Check department permission
can_send = TimetableManager.can_department_send_alterations(school_id, dept)
print(f"Can send: {can_send}")

# Enable if needed
TimetableManager.set_department_permission(school_id, dept, True, True)
```

---

### Issue: Department Missing from Dropdown

**Cause**: Department has inbound alterations disabled

**Solution**:
```python
# Check inbound permission
can_receive = TimetableManager.can_department_receive_alterations(school_id, dept)
print(f"Can receive: {can_receive}")

# Enable if needed
TimetableManager.set_department_permission(school_id, dept, True, True)
```

---

### Issue: Modal Not Opening

**Cause**: JavaScript error or missing form

**Solution**:
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for red error messages
4. Check for JavaScript syntax errors
5. Try refreshing page
6. Clear browser cache

---

### Issue: Data Not Persisting

**Cause**: Database not committing changes

**Solution**:
```python
# In Flask shell
from database import get_db
db = get_db()
db.commit()  # Force commit
```

---

### Issue: "Permission Denied" Error

**Cause**: Session user_type incorrect or school_id mismatch

**Solution**:
1. Check session values: `session['user_type']`, `session['school_id']`
2. Verify route protection:
   - Company Admin routes: `session['user_type'] != 'company_admin'`
   - Admin routes: `session['user_type'] != 'admin'`
   - Staff routes: `session['user_type'] != 'staff'`

---

### Issue: Timetable Grid Not Loading

**Cause**: No periods configured or query error

**Solution**:
```python
# Check if periods exist
from timetable_manager import TimetableManager
periods = TimetableManager.get_periods(school_id)
print(f"Periods found: {len(periods)}")

# If none, add them
TimetableManager.add_period(school_id, 1, "Period 1", "09:00", "09:45")
```

---

## Database Verification Queries

### Check All Tables Created
```sql
SELECT name FROM sqlite_master 
WHERE type='table' AND name LIKE 'timetable%' 
ORDER BY name;
```

### Check School Timetable Settings
```sql
SELECT * FROM timetable_settings WHERE school_id = 1;
```

### Check All Periods
```sql
SELECT * FROM timetable_periods WHERE school_id = 1 ORDER BY period_number;
```

### Check Department Permissions
```sql
SELECT * FROM timetable_department_permissions WHERE school_id = 1;
```

### Check Staff Assignments
```sql
SELECT ta.*, s.full_name 
FROM timetable_assignments ta
JOIN staff s ON ta.staff_id = s.id
WHERE ta.school_id = 1
ORDER BY ta.day_of_week, ta.period_number;
```

### Check Alteration Requests
```sql
SELECT tar.*, 
       sr.full_name as requester, 
       tr.full_name as target
FROM timetable_alteration_requests tar
LEFT JOIN staff sr ON tar.requester_staff_id = sr.id
LEFT JOIN staff tr ON tar.target_staff_id = tr.id
WHERE tar.school_id = 1
ORDER BY tar.created_at DESC;
```

### Check Self-Allocations
```sql
SELECT tsa.*, s.full_name
FROM timetable_self_allocations tsa
JOIN staff s ON tsa.staff_id = s.id
WHERE tsa.school_id = 1
ORDER BY tsa.day_of_week, tsa.period_number;
```

---

## Performance Testing

### Load Test: Create Many Periods
```python
for i in range(1, 51):  # 50 periods
    start_hour = 9 + (i // 4)
    start_min = (i % 4) * 15
    TimetableManager.add_period(
        school_id, i, 
        f"Period {i}",
        f"{start_hour:02d}:{start_min:02d}",
        f"{start_hour:02d}:{start_min+15:02d}"
    )
```

### Load Test: Create Many Assignments
```python
import random
for staff_id in range(1, 51):
    for day in range(6):
        for period in range(1, 9):
            if random.random() > 0.3:  # 70% assignment rate
                TimetableManager.assign_staff_to_period(
                    school_id, staff_id, day, period, "Test Class"
                )
```

---

## Debug Mode: Enable Verbose Logging

```python
# In app.py, change:
# logger.setLevel(logging.INFO)
# To:
logger.setLevel(logging.DEBUG)

# Also enable SQLite query logging:
import sqlite3
sqlite3.enable_trace()  # Logs all SQL queries
```

---

## Browser Console Checks

### What to Look For
1. Red error messages (JS errors)
2. CORS errors
3. 404 Not Found (missing routes)
4. 403 Forbidden (permissions)
5. 500 Internal Server Error (server issue)

### Check Network Tab
- Look at POST requests to `/staff/timetable/request_alteration`
- Verify response status: 200 OK
- Verify response JSON: `{"success": true}`

---

## Final Verification

Before declaring testing complete:

- [ ] All 9 manual test steps completed
- [ ] No JavaScript console errors
- [ ] No server error logs
- [ ] Database queries return expected data
- [ ] Notifications appear when expected
- [ ] All UI elements responsive
- [ ] Permission checks working correctly
- [ ] Data persists after page reload

---

**Last Updated**: January 22, 2026
**Version**: 1.0
