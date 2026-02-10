# Staff Period Assignment - Testing Guide

## 📋 Pre-Test Checklist

- [ ] Python dependencies installed (Flask, SQLite3)
- [ ] Database initialized with test data
- [ ] Server running on localhost:5000
- [ ] Admin account created and logged in
- [ ] Test staff members exist in database
- [ ] Test periods configured (at least 8 periods)

---

## Test Environment Setup

### 1. Verify Database
```sql
-- Check staff table
SELECT COUNT(*) as total_staff FROM staff WHERE school_id = 1;

-- Check periods table
SELECT COUNT(*) as total_periods FROM timetable_periods WHERE school_id = 1;

-- Check assignments table exists
SELECT COUNT(*) as total_assignments FROM timetable_assignments WHERE school_id = 1;
```

### 2. Create Test Staff (if needed)
```python
from database import get_db

db = get_db()
db.execute('''
    INSERT INTO staff (school_id, first_name, last_name, email, phone, staff_id)
    VALUES (1, 'John', 'Doe', 'john@test.com', '9876543210', 'STF001'),
           (1, 'Jane', 'Smith', 'jane@test.com', '9876543211', 'STF002'),
           (1, 'Bob', 'Wilson', 'bob@test.com', '9876543212', 'STF003'),
           (1, 'Alice', 'Brown', 'alice@test.com', '9876543213', 'STF004')
''')
db.commit()
```

### 3. Verify Periods Exist
```python
db = get_db()
periods = db.execute('SELECT * FROM timetable_periods WHERE school_id = 1').fetchall()
print(f"Found {len(periods)} periods")
for p in periods:
    print(f"Period {p[2]}: {p[3]} - {p[4]}")
```

---

## Test Suite 1: UI Navigation Tests

### Test 1.1: Access Page
**Objective:** Verify page loads correctly

**Steps:**
1. Go to `/admin/staff-period-assignment`
2. Verify page title shows "Staff Period Assignment"
3. Verify three main sections visible:
   - Assignment Form (left)
   - Staff Schedule View (right)
   - All Assignments Table (bottom)

**Expected Result:** ✅ All sections display correctly

---

### Test 1.2: Staff Dropdown
**Objective:** Verify staff list loads

**Steps:**
1. Click on staff dropdown
2. Verify list contains all staff members
3. Verify format: "First Last (Staff-ID)"
4. Select "John Doe"

**Expected Result:** ✅ Dropdown populates and selects correctly

---

### Test 1.3: Day Selection
**Objective:** Verify day selector

**Steps:**
1. Click on different days
2. Observe visual feedback (highlighting)
3. Click "Tuesday"
4. Verify Tuesday is highlighted in blue

**Expected Result:** ✅ Only selected day highlighted

---

### Test 1.4: Period Dropdown
**Objective:** Verify period list

**Steps:**
1. Click period dropdown
2. Verify all periods listed
3. Verify format: "Period X: HH:MM - HH:MM"
4. Select "Period 3"

**Expected Result:** ✅ All periods display with correct times

---

## Test Suite 2: Assignment Creation Tests

### Test 2.1: Valid Assignment
**Objective:** Create valid staff period assignment

**Steps:**
1. Staff: "John Doe"
2. Day: Monday
3. Period: Period 1
4. Click "Assign Period"

**Expected Result:**
- ✅ Success message appears
- ✅ Form clears
- ✅ Right panel updates showing new assignment
- ✅ Assignment appears in All Assignments table

**Data Verification:**
```sql
SELECT * FROM timetable_assignments 
WHERE staff_id = (SELECT id FROM staff WHERE first_name = 'John' AND last_name = 'Doe')
AND day_of_week = 1 AND period_number = 1;
```

---

### Test 2.2: Multiple Assignments
**Objective:** Assign multiple periods to same staff

**Steps:**
1. Staff: "John Doe"
2. Day: Monday, Period: 2, Assign ✓
3. Day: Tuesday, Period: 2, Assign ✓
4. Day: Wednesday, Period: 3, Assign ✓
5. Day: Thursday, Period: 4, Assign ✓

**Expected Result:**
- ✅ All 4 assignments succeed
- ✅ Right panel shows all 4 periods
- ✅ Total count shows "4 periods"
- ✅ All visible in table

---

### Test 2.3: Different Staff
**Objective:** Assign same period to different staff

**Steps:**
1. Staff: "Jane Smith"
2. Day: Monday
3. Period: Period 1
4. Click "Assign"

**Expected Result:**
- ✅ Assignment succeeds
- ✅ Both John and Jane assigned to Monday Period 1 (allowed)
- ✅ Both visible in All Assignments table

---

## Test Suite 3: Conflict Detection Tests

### Test 3.1: Duplicate Assignment Prevention
**Objective:** Prevent duplicate assignments

**Precondition:** John Doe has Monday Period 1 assigned

**Steps:**
1. Staff: "John Doe"
2. Day: Monday
3. Period: Period 1
4. Click "Assign"

**Expected Result:**
- ❌ Error message appears
- ❌ Message: "Staff is already assigned to this period on this day"
- ❌ No new assignment created
- ❌ Form not cleared

**Verify:**
```sql
SELECT COUNT(*) FROM timetable_assignments 
WHERE staff_id = (SELECT id FROM staff WHERE first_name = 'John')
AND day_of_week = 1 AND period_number = 1;
-- Should return 1, not 2
```

---

### Test 3.2: Multiple Conflicts on Same Day
**Objective:** Allow multiple periods same day, prevent time conflicts

**Precondition:** John Doe has Monday Period 1 assigned

**Steps:**
1. Staff: "John Doe"
2. Day: Monday
3. Period: Period 2 (different from 1)
4. Click "Assign"

**Expected Result:**
- ✅ Assignment succeeds (different period allowed)
- ✅ No conflict error

---

### Test 3.3: Invalid Staff
**Objective:** Verify staff validation

**Steps:**
1. Manually edit form to staff_id = 99999
2. Submit form (use browser console)

**Expected Result:**
- ❌ Error message: "Staff member not found"
- ❌ Assignment not created

---

### Test 3.4: Invalid Period
**Objective:** Verify period validation

**Steps:**
1. Staff: "John Doe"
2. Day: Monday
3. Manually set period = 99999
4. Submit (use browser console)

**Expected Result:**
- ❌ Error message: "Period not found"
- ❌ Assignment not created

---

## Test Suite 4: View & Display Tests

### Test 4.1: Staff Schedule Right Panel
**Objective:** Verify right panel displays correctly

**Precondition:** John Doe has 3 periods assigned

**Steps:**
1. Select John Doe from dropdown
2. Observe right panel

**Expected Result:**
- ✅ Shows "John Doe - 3 periods" header
- ✅ Table shows all 3 periods with:
  - Day name
  - Period number
  - Time range
  - Remove button
- ✅ No empty state message

---

### Test 4.2: Empty Staff View
**Objective:** Verify empty state message

**Precondition:** Create new staff member with no assignments

**Steps:**
1. Select staff with no assignments
2. Observe right panel

**Expected Result:**
- ✅ Shows empty state message
- ✅ Message: "Select a staff member to view their assigned periods" or "has no assigned periods yet"
- ✅ No table shown

---

### Test 4.3: All Assignments Table
**Objective:** Verify table displays all assignments

**Precondition:** Multiple staff have assignments

**Steps:**
1. Scroll to bottom
2. Observe All Assignments table

**Expected Result:**
- ✅ All assignments visible
- ✅ Columns: Staff Name, Day, Period, Time, Status, Action
- ✅ All data accurate
- ✅ Table scrollable if many entries

---

### Test 4.4: Table Updates
**Objective:** Verify table updates in real-time

**Steps:**
1. Note current table count
2. Assign new period
3. Check if table immediately updates

**Expected Result:**
- ✅ Table updates without page refresh
- ✅ New assignment appears in table
- ✅ All data correct

---

## Test Suite 5: Removal Tests

### Test 5.1: Remove from Right Panel
**Objective:** Remove assignment from staff schedule view

**Precondition:** John Doe has 2+ periods

**Steps:**
1. Select John Doe
2. Click "Remove" button for Period 1
3. Confirm in dialog

**Expected Result:**
- ✅ Assignment removed
- ✅ Success message appears
- ✅ Right panel updates (period removed)
- ✅ Total count decreases
- ✅ Assignment gone from table

**Verify:**
```sql
SELECT COUNT(*) FROM timetable_assignments WHERE staff_id = [johns_id];
-- Count should decrease by 1
```

---

### Test 5.2: Remove from Table
**Objective:** Remove assignment from All Assignments table

**Steps:**
1. Find assignment in table
2. Click "Remove" button at end of row
3. Confirm in dialog

**Expected Result:**
- ✅ Assignment removed
- ✅ Row disappears from table
- ✅ Success message appears
- ✅ Staff view updates if that staff selected

---

### Test 5.3: Cancel Removal
**Objective:** Verify cancellation works

**Steps:**
1. Click "Remove" button
2. Click "Cancel" in confirmation dialog

**Expected Result:**
- ✅ Dialog closes
- ✅ Assignment remains
- ✅ No changes made

---

## Test Suite 6: API Tests

### Test 6.1: API - Assign Period
**Objective:** Test assignment via API

**cURL Command:**
```bash
curl -X POST http://localhost:5000/api/timetable/staff-period/assign \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "day_of_week": 1,
    "period_number": 3
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "✅ Period 3 assigned to John Doe on day 1",
  "assignment_id": 42,
  "staff_name": "John Doe",
  "day_of_week": 1,
  "period_number": 3
}
```

**Verification:**
- ✅ assignment_id returned
- ✅ Status code 200
- ✅ Data in database

---

### Test 6.2: API - List Periods
**Objective:** Test retrieving staff periods via API

**cURL Command:**
```bash
curl http://localhost:5000/api/timetable/staff-period/list/1
```

**Expected Response:**
```json
{
  "success": true,
  "staff_id": 1,
  "staff_name": "John Doe",
  "periods": [
    {
      "assignment_id": 42,
      "period_number": 3,
      "day_of_week": 1,
      "day_name": "Monday",
      "start_time": "09:30",
      "end_time": "10:30"
    }
  ],
  "total_periods": 1
}
```

**Verification:**
- ✅ Status code 200
- ✅ All periods included
- ✅ Correct day names
- ✅ Times formatted correctly

---

### Test 6.3: API - Remove Assignment
**Objective:** Test removal via API

**cURL Command:**
```bash
curl -X POST http://localhost:5000/api/timetable/staff-period/remove/42
```

**Expected Response:**
```json
{
  "success": true,
  "message": "✅ Removed period 3 assignment for John Doe on Monday",
  "staff_name": "John Doe"
}
```

**Verification:**
- ✅ Status code 200
- ✅ Assignment deleted from database
- ✅ Correct message returned

---

### Test 6.4: API - Invalid Request
**Objective:** Test API error handling

**cURL Command (missing field):**
```bash
curl -X POST http://localhost:5000/api/timetable/staff-period/assign \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1
  }'
```

**Expected Response:**
```json
{
  "success": false,
  "error": "Missing required field: day_of_week"
}
```

---

## Test Suite 7: Authentication Tests

### Test 7.1: Unauthenticated Access
**Objective:** Verify page requires login

**Steps:**
1. Log out
2. Go to `/admin/staff-period-assignment`

**Expected Result:**
- ❌ Redirected to login page
- ❌ Cannot access page without auth

---

### Test 7.2: Non-Admin Access
**Objective:** Verify only admins can access

**Steps:**
1. Log in as staff member
2. Try to go to `/admin/staff-period-assignment`

**Expected Result:**
- ❌ Access denied or redirected
- ❌ Error message shown

---

### Test 7.3: API Authentication
**Objective:** Verify API requires auth

**cURL Command (no auth):**
```bash
curl http://localhost:5000/api/timetable/staff-period/list/1
```

**Expected Response:**
```json
{
  "success": false,
  "error": "Unauthorized"
}
```

---

## Test Suite 8: Performance Tests

### Test 8.1: Page Load Time
**Objective:** Verify page loads quickly

**Steps:**
1. Open Developer Tools (F12)
2. Go to Network tab
3. Load `/admin/staff-period-assignment`
4. Note load time

**Expected Result:**
- ✅ Page loads in < 2 seconds
- ✅ All components render
- ✅ No console errors

---

### Test 8.2: Assignment Creation Speed
**Objective:** Verify assignment creation is fast

**Steps:**
1. Time the assignment process
2. From selection to success message

**Expected Result:**
- ✅ Completes in < 500ms
- ✅ No lag in UI

---

### Test 8.3: Table Rendering
**Objective:** Verify table handles many rows

**Steps:**
1. Create 50+ assignments
2. Observe table

**Expected Result:**
- ✅ Table still responsive
- ✅ No browser freeze
- ✅ Scrolling smooth

---

## Test Suite 9: Edge Cases

### Test 9.1: Maximum Assignments
**Objective:** Test limits

**Steps:**
1. Assign staff to all 7 days × 8 periods = 56 periods
2. Try to add 57th

**Expected Result:**
- ✅ All 56 succeed
- ✅ 57th can be attempted (no hard limit)
- ✅ System remains stable

---

### Test 9.2: Rapid Clicks
**Objective:** Test double-click prevention

**Steps:**
1. Click "Assign" button rapidly multiple times
2. Observe

**Expected Result:**
- ✅ Only one assignment created
- ✅ No duplicate entries
- ✅ Button disabled during submission

---

### Test 9.3: Special Characters
**Objective:** Test data with special characters

**Precondition:** Create staff with name "O'Brien-Smith"

**Steps:**
1. Assign period to this staff
2. Verify in table and database

**Expected Result:**
- ✅ Name displays correctly
- ✅ No SQL injection
- ✅ Database stores correctly

---

## Test Suite 10: Data Consistency

### Test 10.1: Database Consistency
**Objective:** Verify database state matches UI

**Steps:**
1. Create 5 assignments via UI
2. Query database directly
3. Compare

```sql
SELECT COUNT(*) FROM timetable_assignments 
WHERE created_at >= NOW() - INTERVAL 10 MINUTE;
```

**Expected Result:**
- ✅ Count matches UI count
- ✅ All data fields match
- ✅ Timestamps are valid

---

### Test 10.2: Cross-Browser Consistency
**Objective:** Verify UI works on multiple browsers

**Browsers to Test:**
- Chrome ✓
- Firefox ✓
- Safari ✓
- Edge ✓

**Steps:**
1. Test UI in each browser
2. Test assignment flow
3. Check for visual issues

**Expected Result:**
- ✅ Works consistently
- ✅ No visual glitches
- ✅ All buttons functional

---

## Test Automation Script

```python
#!/usr/bin/env python3
"""Automated test suite for Staff Period Assignment"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}

class TestRunner:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
        self.results = []

    def test_assign_period(self):
        """Test: Create assignment"""
        payload = {
            "staff_id": 1,
            "day_of_week": 1,
            "period_number": 3
        }
        response = requests.post(
            f"{self.base_url}/api/timetable/staff-period/assign",
            json=payload,
            headers=HEADERS
        )
        
        if response.status_code == 200 and response.json()['success']:
            self.passed += 1
            return response.json()['assignment_id']
        else:
            self.failed += 1
            return None

    def test_get_staff_periods(self, staff_id=1):
        """Test: Retrieve staff periods"""
        response = requests.get(
            f"{self.base_url}/api/timetable/staff-period/list/{staff_id}",
            headers=HEADERS
        )
        
        if response.status_code == 200 and response.json()['success']:
            self.passed += 1
        else:
            self.failed += 1

    def test_remove_assignment(self, assignment_id):
        """Test: Remove assignment"""
        response = requests.post(
            f"{self.base_url}/api/timetable/staff-period/remove/{assignment_id}",
            headers=HEADERS
        )
        
        if response.status_code == 200 and response.json()['success']:
            self.passed += 1
        else:
            self.failed += 1

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 50)
        print("Staff Period Assignment - Test Suite")
        print(f"Time: {datetime.now()}")
        print("=" * 50)

        # Test 1
        print("\nTest 1: Create Assignment...")
        assignment_id = self.test_assign_period()
        print(f"Result: {'PASS' if assignment_id else 'FAIL'}")

        # Test 2
        print("\nTest 2: Get Staff Periods...")
        self.test_get_staff_periods()
        print(f"Result: PASS" if self.passed > 1 else "Result: FAIL")

        # Test 3
        if assignment_id:
            print("\nTest 3: Remove Assignment...")
            self.test_remove_assignment(assignment_id)
            print(f"Result: PASS" if self.failed < 1 else "Result: FAIL")

        # Summary
        print("\n" + "=" * 50)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}")
        print("=" * 50)

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
```

---

## Test Report Template

```
TEST REPORT: Staff Period Assignment
Date: [DATE]
Tester: [NAME]
Browser: [BROWSER & VERSION]
System: [OS]

=== SUMMARY ===
Total Tests: [ ]
Passed: [ ]
Failed: [ ]
Skipped: [ ]
Success Rate: [ ]%

=== DETAILED RESULTS ===

[Test Suite Name]
- Test 1.1: [Status] [Notes]
- Test 1.2: [Status] [Notes]
- Test 1.3: [Status] [Notes]

=== ISSUES FOUND ===
1. [Issue Description]
   Severity: [Critical/Major/Minor]
   Steps to Reproduce: [Steps]
   Expected: [Expected Result]
   Actual: [Actual Result]

=== SIGN-OFF ===
Tester: ____________________
Date: ____________________
Status: [ ] Approved [ ] Approved with Notes [ ] Rejected
```

---

## Regression Test Checklist

**After each update, verify:**
- [ ] Page loads without errors
- [ ] Staff dropdown populates
- [ ] Day selection works
- [ ] Period dropdown works
- [ ] Assignment creation works
- [ ] Right panel updates
- [ ] Table updates
- [ ] Removal works
- [ ] Error handling works
- [ ] API endpoints work
- [ ] No console errors
- [ ] No database errors

---

**Status:** ✅ Ready for Testing  
**Last Updated:** 2024  
**Version:** 1.0
