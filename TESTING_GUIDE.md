# HIERARCHICAL TIMETABLE SYSTEM - TESTING GUIDE

**Version**: 1.0  
**Date**: February 9, 2026  
**Status**: Ready for Testing

---

## PRE-TESTING CHECKLIST

- [x] Backend code implemented
- [x] API endpoints registered
- [x] Database tables created
- [ ] Database initialized in test environment
- [ ] Test data prepared
- [ ] Frontend UI created (pending)
- [ ] Postman/REST client configured

---

## SECTION 1: DATABASE VERIFICATION

### Test 1.1: Database Tables Exist
```python
# In Python shell
from database import get_db

db = get_db()
cursor = db.cursor()

REQUIRED_TABLES = [
    'timetable_organization_config',
    'timetable_academic_levels',
    'timetable_sections',
    'timetable_hierarchical_assignments',
    'timetable_staff_availability',
    'timetable_conflict_logs'
]

for table in REQUIRED_TABLES:
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
    if cursor.fetchone():
        print(f"✓ {table} exists")
    else:
        print(f"✗ {table} MISSING")
```

**Expected Output**:
```
✓ timetable_organization_config exists
✓ timetable_academic_levels exists
✓ timetable_sections exists
✓ timetable_hierarchical_assignments exists
✓ timetable_staff_availability exists
✓ timetable_conflict_logs exists
```

### Test 1.2: Column Additions
```python
# Check new columns in existing tables
cursor.execute("PRAGMA table_info(schools)")
columns = [col[1] for col in cursor.fetchall()]
if 'organization_type' in columns:
    print("✓ schools.organization_type added")
else:
    print("✗ schools.organization_type MISSING")

cursor.execute("PRAGMA table_info(timetable_assignments)")
required_cols = ['section_id', 'level_id', 'subject_name', 'room_number', 'assignment_type']
for col in required_cols:
    if col in [c[1] for c in cursor.fetchall()]:
        print(f"✓ timetable_assignments.{col} added")
    else:
        print(f"✗ timetable_assignments.{col} MISSING")
```

---

## SECTION 2: API ENDPOINT TESTING

### Test 2.1: API Registration
```bash
# Start Flask app
python app.py

# In another terminal, test if endpoint exists
curl -s http://localhost:5500/api/hierarchical-timetable/organization/config | python -m json.tool
```

**Expected Response**:
```json
{
  "success": false,
  "error": "Organization config not found"
}
```

### Test 2.2: Organization Type Setup
```bash
# Set organization to School (Classes 1-12)
curl -X POST http://localhost:5500/api/hierarchical-timetable/organization/set-type \
  -H "Content-Type: application/json" \
  -d '{"organization_type": "school"}' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Organization type set to school"
}
```

**Verify in Database**:
```sql
SELECT organization_type, total_levels FROM timetable_organization_config WHERE school_id=1;
-- Expected: school, 12

SELECT COUNT(*), level_number FROM timetable_academic_levels WHERE school_id=1;
-- Expected: 12 rows (Class 1 through Class 12)
```

---

## SECTION 3: ACADEMIC STRUCTURE TESTING

### Test 3.1: Get Academic Levels
```bash
curl http://localhost:5500/api/hierarchical-timetable/levels \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "level_type": "class",
      "level_number": 1,
      "level_name": "Class 1",
      "is_active": 1
    },
    {
      "id": 2,
      "level_type": "class",
      "level_number": 2,
      "level_name": "Class 2",
      "is_active": 1
    },
    ...
    {
      "id": 12,
      "level_type": "class",
      "level_number": 12,
      "level_name": "Class 12",
      "is_active": 1
    }
  ]
}
```

### Test 3.2: Create Sections
```bash
# Create Section A for Class 1
curl -X POST http://localhost:5500/api/hierarchical-timetable/sections/create \
  -H "Content-Type: application/json" \
  -d '{
    "level_id": 1,
    "section_name": "A",
    "capacity": 60
  }' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "section_id": 1,
  "message": "Section A created successfully"
}
```

### Test 3.3: Create Multiple Sections
```bash
# Create B and C sections for Class 1
for section in B C; do
  curl -X POST http://localhost:5500/api/hierarchical-timetable/sections/create \
    -H "Content-Type: application/json" \
    -d "{\"level_id\": 1, \"section_name\": \"$section\", \"capacity\": 60}" \
    -b "user_type=admin; user_id=1; school_id=1"
done

# Create sections for remaining classes (Optional - for testing)
# This creates full structure: 12 classes × 3 sections each = 36 sections
```

### Test 3.4: List All Sections
```bash
curl http://localhost:5500/api/hierarchical-timetable/sections/all \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "school_id": 1,
      "level_id": 1,
      "section_name": "A",
      "section_code": "A",
      "capacity": 60,
      "level_number": 1,
      "level_name": "Class 1"
    },
    {
      "id": 2,
      "school_id": 1,
      "level_id": 1,
      "section_name": "B",
      "section_code": "B",
      "capacity": 60,
      "level_number": 1,
      "level_name": "Class 1"
    },
    ...
  ]
}
```

---

## SECTION 4: CONFLICT DETECTION TESTING

### Test 4.1: Check Staff Availability (No Conflict)
```bash
# First assignment - should be available
curl -X POST http://localhost:5500/api/hierarchical-timetable/check-staff-availability \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "day_of_week": 1,
    "period_number": 2,
    "section_id": 1
  }' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "is_available": true,
  "reason": "Staff is available"
}
```

### Test 4.2: Assign Staff to Section
```bash
# Create first assignment
curl -X POST http://localhost:5500/api/hierarchical-timetable/assign-staff \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "section_id": 1,
    "level_id": 1,
    "day_of_week": 1,
    "period_number": 2,
    "subject_name": "Mathematics",
    "room_number": "A101"
  }' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "assignment_id": 1,
  "message": "Staff assigned to period successfully"
}
```

### Test 4.3: Double-Booking Prevention (CRITICAL TEST)
```bash
# Try to assign same staff to different section same time - SHOULD FAIL
curl -X POST http://localhost:5500/api/hierarchical-timetable/check-staff-availability \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "day_of_week": 1,
    "period_number": 2,
    "section_id": 2
  }' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response** (CONFLICT DETECTED):
```json
{
  "success": true,
  "is_available": false,
  "conflicts": ["Class 1 - A"],
  "reason": "Staff already assigned to: Class 1 - A"
}
```

### Test 4.4: Different Period - SHOULD SUCCEED
```bash
# Same staff, same section, DIFFERENT period - should work
curl -X POST http://localhost:5500/api/hierarchical-timetable/check-staff-availability \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "day_of_week": 1,
    "period_number": 3,
    "section_id": 2
  }' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "is_available": true,
  "reason": "Staff is available"
}
```

### Test 4.5: Daily Limit Testing
```python
# Create 6 assignments for same staff on same day (max allowed)
staff_id = 1
day = 1  # Monday
section_ids = [1, 2, 3, 4, 5, 6]

for i, section_id in enumerate(section_ids):
    period = i + 1  # Periods 1-6
    # POST /assign-staff for each
    # All should succeed
    pass

# Try 7th assignment - should FAIL
# POST /assign-staff with period=7
# Expected: {"success": false, "error": "Maximum daily classes (6) reached"}
```

### Test 4.6: Section Uniqueness
```bash
# Create two assignments for same section same time
# 1st: Staff 1 → Section 1, Monday Period 2
# 2nd: Staff 2 → Section 1, Monday Period 2 - SHOULD FAIL

curl -X POST http://localhost:5500/api/hierarchical-timetable/check-section-availability \
  -H "Content-Type: application/json" \
  -d '{
    "section_id": 1,
    "day_of_week": 1,
    "period_number": 2
  }' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "is_available": false,
  "assigned_staff": "Staff 1",
  "reason": "Section already has Staff 1 assigned"
}
```

---

## SECTION 5: VIEW TESTING

### Test 5.1: Staff Schedule View
```bash
# Get complete schedule for Staff 1
curl http://localhost:5500/api/hierarchical-timetable/staff-schedule/1 \
  -b "user_type=staff; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "schedule": [
      {
        "assignment_id": 1,
        "day_of_week": 1,
        "period_number": 2,
        "section_name": "A",
        "level_name": "Class 1",
        "subject_name": "Mathematics",
        "start_time": "09:30:00",
        "end_time": "10:15:00",
        "room_number": "A101",
        "is_locked": 0
      }
    ],
    "conflict_count": 0,
    "conflicts": []
  }
}
```

### Test 5.2: Section Schedule View
```bash
# Get complete schedule for Section 1
curl http://localhost:5500/api/hierarchical-timetable/section-schedule/1 \
  -b "user_type=staff; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "section_info": {
      "section_name": "A",
      "level_name": "Class 1",
      "level_number": 1,
      "capacity": 60
    },
    "schedule": [
      {
        "day_of_week": 1,
        "period_number": 2,
        "staff_name": "Staff Name",
        "subject_name": "Mathematics",
        "start_time": "09:30:00",
        "end_time": "10:15:00",
        "room_number": "A101"
      }
    ]
  }
}
```

### Test 5.3: Color-Coded Grid (Staff)
```bash
# Get visual grid for Staff 1
curl http://localhost:5500/api/hierarchical-timetable/grid/staff/1 \
  -b "user_type=staff; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "Sunday": {
      "1": {"status": "free", "color": "#90EE90", "staff": "", "section": "", "subject": ""},
      "2": {"status": "free", "color": "#90EE90", ...},
      ...
    },
    "Monday": {
      "1": {"status": "free", "color": "#90EE90", ...},
      "2": {"status": "occupied", "color": "#87CEEB", "staff": "", "section": "Class 1-A", "subject": "Mathematics"},
      "3": {"status": "free", "color": "#90EE90", ...},
      ...
    },
    ...
  }
}
```

### Test 5.4: Color-Coded Grid (Section)
```bash
# Get visual grid for Section 1
curl http://localhost:5500/api/hierarchical-timetable/grid/section/1 \
  -b "user_type=staff; user_id=1; school_id=1"
```

**Expected**: Similar structure with staff names instead of section names

---

## SECTION 6: COLLEGE MODE TESTING

### Test 6.1: Set Organization to College
```bash
# Set organization to College (Years 1-4)
curl -X POST http://localhost:5500/api/hierarchical-timetable/organization/set-type \
  -H "Content-Type: application/json" \
  -d '{"organization_type": "college"}' \
  -b "user_type=admin; user_id=2; school_id=2"
```

**Expected**: Year 1, Year 2, Year 3, Year 4 created

### Test 6.2: Verify College Levels
```bash
curl http://localhost:5500/api/hierarchical-timetable/levels \
  -b "user_type=admin; user_id=2; school_id=2"
```

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {"id": 1, "level_type": "year", "level_number": 1, "level_name": "Year 1"},
    {"id": 2, "level_type": "year", "level_number": 2, "level_name": "Year 2"},
    {"id": 3, "level_type": "year", "level_number": 3, "level_name": "Year 3"},
    {"id": 4, "level_type": "year", "level_number": 4, "level_name": "Year 4"}
  ]
}
```

---

## SECTION 7: DELETION TESTING

### Test 7.1: Delete Assignment
```bash
# Delete assignment 1
curl -X DELETE http://localhost:5500/api/hierarchical-timetable/assignment/1 \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Assignment deleted successfully"
}
```

### Test 7.2: Verify Deletion
```bash
# Check staff schedule - assignment should be gone
curl http://localhost:5500/api/hierarchical-timetable/staff-schedule/1 \
  -b "user_type=staff; user_id=1; school_id=1"
```

**Expected**: schedule array is empty or doesn't contain deleted assignment

---

## SECTION 8: ERROR HANDLING TESTING

### Test 8.1: Missing Required Fields
```bash
# Missing required field (day_of_week)
curl -X POST http://localhost:5500/api/hierarchical-timetable/check-staff-availability \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "period_number": 2
  }' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**:
```json
{
  "success": false,
  "error": "Missing required fields: staff_id, day_of_week, period_number"
}
```

### Test 8.2: Authentication Failure
```bash
# No authentication cookies
curl -X POST http://localhost:5500/api/hierarchical-timetable/assign-staff \
  -H "Content-Type: application/json" \
  -d '{"staff_id": 1, ...}'
```

**Expected Response** (401):
```json
{
  "success": false,
  "error": "Unauthorized access. Admin required."
}
```

### Test 8.3: Invalid Section/Staff ID
```bash
# Reference non-existent staff
curl -X POST http://localhost:5500/api/hierarchical-timetable/assign-staff \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 99999,
    "section_id": 1,
    "level_id": 1,
    "day_of_week": 1,
    "period_number": 2
  }' \
  -b "user_type=admin; user_id=1; school_id=1"
```

**Expected Response**: Either succeeds (no FK constraint) or returns database error

---

## TEST DATA SETUP SCRIPT

```python
#!/usr/bin/env python
"""Populate test data for hierarchical timetable testing"""

from database import get_db
from hierarchical_timetable import HierarchicalTimetableManager as HTM

def setup_test_data():
    db = get_db()
    cursor = db.cursor()
    
    # 1. Set up School organization
    print("1. Setting up School organization...")
    HTM.set_organization_type(school_id=1, org_type='school')
    
    # 2. Create sections for each class
    print("2. Creating sections...")
    cursor.execute("SELECT id FROM timetable_academic_levels WHERE school_id=1")
    levels = cursor.fetchall()
    
    for level in levels:
        level_id = level[0]
        for section_name in ['A', 'B', 'C']:
            HTM.create_section(1, level_id, section_name, 60)
    
    db.commit()
    print(f"   Created {len(levels) * 3} sections (3 per class)")
    
    # 3. Create test assignments
    print("3. Creating test assignments...")
    test_staff_ids = [1, 2, 3, 4, 5]
    
    cursor.execute("SELECT id, level_id FROM timetable_sections WHERE school_id=1 LIMIT 10")
    sections = cursor.fetchall()
    
    assignment_count = 0
    for staff_id in test_staff_ids:
        for section_id, level_id in sections:
            for day in range(5):  # Mon-Fri
                for period in range(1, 6):  # Periods 1-5
                    result = HTM.assign_staff_to_period(
                        school_id=1,
                        staff_id=staff_id,
                        section_id=section_id,
                        level_id=level_id,
                        day_of_week=day,
                        period_number=period,
                        subject_name="Test Subject",
                        room_number="A101"
                    )
                    if result['success']:
                        assignment_count += 1
                    # Note: Many will fail due to conflicts - that's expected!
    
    print(f"   Created {assignment_count} assignments")
    print("\n✓ Test data setup complete!")

if __name__ == '__main__':
    setup_test_data()
```

---

## TEST RESULTS TEMPLATE

```
HIERARCHICAL TIMETABLE SYSTEM - TEST RESULTS
Date: _______________
Tester: _______________

SECTION 1: DATABASE
[ ] Database tables exist (all 6)
[ ] Column additions in place
[ ] Foreign keys working
Notes: _____________________

SECTION 2: API ENDPOINTS
[ ] All 12 endpoints registered
[ ] Authentication working
[ ] Error responses formatted correctly
Notes: _____________________

SECTION 3: ACADEMIC STRUCTURE
[ ] Organization type toggle works
[ ] Default levels generated
[ ] Sections created successfully
Notes: _____________________

SECTION 4: CONFLICT DETECTION ⭐ CRITICAL
[ ] No conflicts - staff available (passes)
[ ] Double-booking prevented (fails correctly)
[ ] Different period allowed (passes)
[ ] Daily limit enforced (fails at limit+1)
[ ] Section uniqueness maintained (fails correctly)
Notes: _____________________

SECTION 5: VIEWS
[ ] Staff schedule displays correctly
[ ] Section schedule displays correctly
[ ] Color-coded grid renders properly
[ ] Grid colors match status
Notes: _____________________

SECTION 6: COLLEGE MODE
[ ] Organization type set to college
[ ] 4 years created instead of 12
[ ] Year names correct
Notes: _____________________

SECTION 7: DELETION
[ ] Assignments delete successfully
[ ] Deleted assignments removed from views
Notes: _____________________

SECTION 8: ERROR HANDLING
[ ] Missing fields rejected with 400
[ ] Authentication failures return 401
[ ] Database errors return 500
[ ] Conflict errors return 400 with details
Notes: _____________________

OVERALL STATUS: ⭐⭐⭐⭐⭐ (5/5)
Ready for Production: YES / NO

Blocker Issues: _____________________
Minor Issues: _____________________
Recommendations: _____________________
```

---

## PERFORMANCE TEST

```python
import time
import requests

def perf_test():
    base_url = "http://localhost:5500/api/hierarchical-timetable"
    cookies = {"user_type": "admin", "user_id": "1", "school_id": "1"}
    
    tests = [
        ("GET", f"{base_url}/levels", None),
        ("GET", f"{base_url}/sections/all", None),
        ("GET", f"{base_url}/staff-schedule/1", None),
        ("POST", f"{base_url}/check-staff-availability", 
         {"staff_id": 1, "day_of_week": 1, "period_number": 2}),
    ]
    
    for method, url, data in tests:
        start = time.time()
        if method == "GET":
            requests.get(url, cookies=cookies)
        else:
            requests.post(url, json=data, cookies=cookies)
        elapsed = (time.time() - start) * 1000  # ms
        print(f"{method:4} {url.split('/')[-1]:30} | {elapsed:6.1f} ms")

perf_test()
```

**Expected Results**:
- Simple GET/POST: 5-15ms
- Complex queries (schedule, grid): 20-50ms
- All operations: < 100ms

---

**Status**: Ready for testing  
**Last Updated**: February 9, 2026
