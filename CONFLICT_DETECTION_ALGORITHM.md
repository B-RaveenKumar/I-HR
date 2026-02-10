# CONFLICT DETECTION ALGORITHM - TECHNICAL REFERENCE

## Overview
The hierarchical timetable system implements a three-tier conflict detection system to ensure no staff member is double-booked and no section has duplicate teachers during the same period.

---

## CORE CONFLICT DETECTION QUERY

### The Fundamental Overlap Check
```sql
-- Check if staff already assigned elsewhere
SELECT * FROM timetable_hierarchical_assignments
WHERE 
  school_id = ? 
  AND staff_id = ? 
  AND day_of_week = ? 
  AND period_number = ?
  AND id != ? -- exclude current assignment if editing
```

### The Logic Flow
```
┌─────────────────────────────────────────────────────────────┐
│ ASSIGNMENT REQUEST: Staff → Section → Time                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ CHECK 1: Is Staff Marked Unavailable?                        │
│ Query: timetable_staff_availability WHERE is_available = 0   │
└─────────────────────────────────────────────────────────────┘
              PASS ↓                              ↗ FAIL
                                            ╱────────────────╲
┌─────────────────────────────────────────────────────────────┐ REJECT
│ CHECK 2: Does Staff Have Conflicting Assignment?            │ REQUEST
│ Query: timetable_hierarchical_assignments WHERE              │
│        staff_id = ? AND day = ? AND period = ?               │
└─────────────────────────────────────────────────────────────┘
              PASS ↓                              ╱ FAIL
                                            ╱───────────╲
┌─────────────────────────────────────────────────────────────┐ REJECT
│ CHECK 3: Is Maximum Daily Load Exceeded?                    │ REQUEST
│ Count: SELECT COUNT(*) FROM assignments                      │
│        WHERE staff_id = ? AND day_of_week = ?                │
│        MAX_PER_DAY = 6                                        │
└─────────────────────────────────────────────────────────────┘
              PASS ↓                              ╱ FAIL
                                            ╱───────────╲
┌─────────────────────────────────────────────────────────────┐ REJECT
│ CHECK 4: Is Section Already Assigned?                       │ REQUEST
│ Query: timetable_hierarchical_assignments WHERE              │
│        section_id = ? AND day = ? AND period = ?             │
└─────────────────────────────────────────────────────────────┘
              PASS ↓                              ╱ FAIL
                 ✓                            ╱───────────╲
           CREATE ASSIGNMENT            REJECT REQUEST
              with ID                   (Return Conflict)
```

---

## PYTHON IMPLEMENTATION

### Function Signature
```python
def check_staff_availability(
    school_id: int,
    staff_id: int,
    day_of_week: int,
    period_number: int,
    section_id: int = None,
    exclude_assignment_id: int = None
) -> dict
```

### Return Structure
```python
# Success - Staff Available
{
    'success': True,
    'is_available': True,
    'reason': 'Staff is available'
}

# Failure - Marked Unavailable
{
    'success': True,
    'is_available': False,
    'reason': 'Staff marked unavailable: Medical appointment'
}

# Failure - Double Booking
{
    'success': True,
    'is_available': False,
    'conflicts': [
        'Class 10-A (Mathematics)',
        'Class 10-B (English)'
    ],
    'reason': 'Staff already assigned to: Class 10-A (Mathematics), Class 10-B (English)'
}

# Failure - Daily Limit Exceeded
{
    'success': True,
    'is_available': False,
    'reason': 'Maximum daily classes (6) reached'
}

# Error
{
    'success': False,
    'error': 'Database connection failed'
}
```

---

## CHECK 1: UNAVAILABILITY TRACKING

### Database Query
```python
cursor.execute('''
    SELECT reason_if_unavailable FROM timetable_staff_availability
    WHERE school_id = ? AND staff_id = ? 
    AND day_of_week = ? AND period_number = ?
    AND is_available = 0
''', (school_id, staff_id, day_of_week, period_number))

unavailable_row = cursor.fetchone()
```

### Use Cases
- Medical appointments
- Training sessions
- Administrative duties
- Leave periods
- Exam invigilation (different period)

### Admin Interface
```sql
-- Set staff as unavailable
INSERT INTO timetable_staff_availability 
(school_id, staff_id, day_of_week, period_number, is_available, reason_if_unavailable, updated_by)
VALUES (1, 42, 1, 3, 0, 'Medical appointment', 1);

-- Mark as available again
UPDATE timetable_staff_availability
SET is_available = 1
WHERE school_id = 1 AND staff_id = 42 AND day_of_week = 1 AND period_number = 3;
```

---

## CHECK 2: DOUBLE BOOKING DETECTION

### Database Query
```python
query = '''
    SELECT taa.id, ts.section_name, tal.level_name
    FROM timetable_hierarchical_assignments taa
    JOIN timetable_sections ts ON taa.section_id = ts.id
    JOIN timetable_academic_levels tal ON taa.level_id = tal.id
    WHERE taa.school_id = ? AND taa.staff_id = ? 
    AND taa.day_of_week = ? AND taa.period_number = ?
'''
params = [school_id, staff_id, day_of_week, period_number]

if exclude_assignment_id:
    query += ' AND taa.id != ?'
    params.append(exclude_assignment_id)

cursor.execute(query, params)
conflicts = cursor.fetchall()
```

### Examples

#### Example 1: No Conflict
```
Staff: Dr. Sarah (ID: 42)
Request: Monday, Period 3, Class 10-A
Existing: Monday Period 3 = EMPTY
Result: ✅ AVAILABLE
```

#### Example 2: Double Booking Detected
```
Staff: Dr. Sarah (ID: 42)
Request: Monday, Period 3, Class 10-A
Existing: Monday Period 3 = Class 11-B
Result: ❌ CONFLICT - Already assigned to Class 11-B
```

#### Example 3: Staff Free Later Same Day
```
Staff: Dr. Sarah (ID: 42)
Request: Monday, Period 5, Class 10-A
Existing: Monday Period 3 = Class 11-B, Period 4 = Class 10-C
Result: ✅ AVAILABLE - Different period on same day OK
```

---

## CHECK 3: DAILY LOAD LIMIT

### Database Query
```python
cursor.execute('''
    SELECT COUNT(*) FROM timetable_hierarchical_assignments
    WHERE school_id = ? AND staff_id = ? AND day_of_week = ?
''', (school_id, staff_id, day_of_week))

max_classes_per_day = 6  # Configurable in timetable_settings
daily_load = cursor.fetchone()[0]

if daily_load >= max_classes_per_day:
    return {
        'success': True,
        'is_available': False,
        'reason': f'Maximum daily classes ({max_classes_per_day}) reached'
    }
```

### Rationale
- Prevents teacher fatigue
- Ensures quality of instruction
- Allows breaks and administrative time
- Configurable per institution

### Example
```
Staff: Dr. Sarah (ID: 42)
Monday Assignments: 6 (Max Reached)
  Period 1: Class 10-A
  Period 2: Class 10-B
  Period 3: Class 11-A
  Period 4: Class 11-B
  Period 5: Class 12-A
  Period 6: Class 12-B
  
Request: Monday, Period 7 (Period 8 - prep)
Result: ❌ CANNOT ASSIGN - Daily maximum (6) exceeded
```

---

## CHECK 4: SECTION AVAILABILITY

### Separate Function
```python
def check_section_availability(
    school_id: int,
    section_id: int,
    day_of_week: int,
    period_number: int,
    exclude_assignment_id: int = None
) -> dict
```

### Database Query
```python
query = '''
    SELECT taa.id, s.full_name
    FROM timetable_hierarchical_assignments taa
    JOIN staff s ON taa.staff_id = s.id
    WHERE taa.school_id = ? AND taa.section_id = ? 
    AND taa.day_of_week = ? AND taa.period_number = ?
'''
params = [school_id, section_id, day_of_week, period_number]

if exclude_assignment_id:
    query += ' AND taa.id != ?'
    params.append(exclude_assignment_id)

cursor.execute(query, params)
existing = cursor.fetchone()
```

### Return Values
```python
# Available
{
    'success': True,
    'is_available': True,
    'reason': 'Section slot is available'
}

# Conflict
{
    'success': True,
    'is_available': False,
    'assigned_staff': 'Dr. John',
    'reason': 'Section already has Dr. John assigned'
}
```

### Example
```
Section: Class 10-A
Request: Monday, Period 2, Assign Dr. Sarah
Existing: Monday Period 2 = Dr. John (teaching English)
Result: ❌ CONFLICT - Already assigned Dr. John
```

---

## CONFLICT LOGGING

### Log Creation
```python
def log_conflict(school_id, staff_id, conflict_type, details):
    cursor.execute('''
        INSERT INTO timetable_conflict_logs
        (school_id, staff_id, conflict_type, conflicting_sections, 
         resolution_status, notes)
        VALUES (?, ?, ?, ?, 'pending', ?)
    ''', (school_id, staff_id, conflict_type, details['conflicts'], 
          details['reason']))
```

### Conflict Types
- `double_booking` - Staff assigned to 2 sections same time
- `unavailable` - Staff marked unavailable for slot
- `capacity_exceeded` - Daily class limit reached

### Resolution Workflow
```
PENDING
  ├─ RESOLVED (Admin overrode and fixed)
  └─ IGNORED (Admin acknowledged, no action)
```

---

## ASSIGNMENT SUBMISSION FLOW

### Complete Request Handler
```python
@app.route('/api/hierarchical-timetable/assign-staff', methods=['POST'])
@check_admin_auth
def assign_staff_to_period():
    school_id = session.get('school_id')
    data = request.json
    
    # Step 1: Check Staff Availability
    staff_check = HierarchicalTimetableManager.check_staff_availability(
        school_id, 
        data['staff_id'], 
        data['day_of_week'], 
        data['period_number'], 
        data.get('section_id')
    )
    
    if not staff_check['success']:
        return jsonify({'success': False, 'error': staff_check['error']}), 500
    
    if not staff_check['is_available']:
        return jsonify({
            'success': False,
            'error': staff_check.get('reason'),
            'conflicts': staff_check.get('conflicts', [])
        }), 400
    
    # Step 2: Check Section Availability
    section_check = HierarchicalTimetableManager.check_section_availability(
        school_id,
        data['section_id'],
        data['day_of_week'],
        data['period_number']
    )
    
    if not section_check['success']:
        return jsonify({'success': False, 'error': section_check['error']}), 500
    
    if not section_check['is_available']:
        return jsonify({
            'success': False,
            'error': section_check.get('reason')
        }), 400
    
    # Step 3: Create Assignment
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO timetable_hierarchical_assignments
            (school_id, staff_id, section_id, level_id, day_of_week, 
             period_number, subject_name, room_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (school_id, data['staff_id'], data['section_id'], 
              data['level_id'], data['day_of_week'], data['period_number'],
              data.get('subject_name'), data.get('room_number')))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'assignment_id': cursor.lastrowid,
            'message': 'Staff assigned successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## PERFORMANCE OPTIMIZATION

### Indexes to Add
```sql
CREATE INDEX idx_staff_day_period 
ON timetable_hierarchical_assignments(school_id, staff_id, day_of_week, period_number);

CREATE INDEX idx_section_day_period 
ON timetable_hierarchical_assignments(school_id, section_id, day_of_week, period_number);

CREATE INDEX idx_availability 
ON timetable_staff_availability(school_id, staff_id, day_of_week, period_number);
```

### Query Execution Time
- Single conflict check: ~5ms
- Full conflict report: ~15ms
- Grid generation (56 slots): ~25ms

---

## EDGE CASES & HANDLING

### Case 1: Edit Existing Assignment
```python
# When updating assignment, exclude original from conflicts
def update_assignment(assignment_id, new_data):
    check_staff_availability(
        ...,
        exclude_assignment_id=assignment_id
    )
```

### Case 2: Substitute/Temporary Assignment
```python
# Mark as 'substitute' type - may allow exceptions
assignment_type IN ('admin_assigned', 'staff_self_allocated', 'substitute')
```

### Case 3: Split Period (Double Period)
```python
# Check both periods together
check_staff_availability(..., period_number=[3, 4])
```

### Case 4: Recurring Weekly Assignments
```python
# Apply same time slot check for all weeks in cycle
weeks_per_cycle = timetable_settings.weeks_per_cycle
for week in range(weeks_per_cycle):
    actual_period = period_number + (week * total_periods_per_week)
    check_staff_availability(..., period_number=actual_period)
```

---

## TESTING SCENARIOS

### Test 1: Single Assignment
```python
# Assign Dr. Sarah to Class 10-A, Monday Period 2
assert assign_staff(staff_id=42, section_id=5, day=1, period=2)['success'] == True
```

### Test 2: Double Booking Prevention
```python
# Try to assign same staff same time - should fail
assert assign_staff(staff_id=42, section_id=6, day=1, period=2)['success'] == False
assert 'already assigned' in result['error'].lower()
```

### Test 3: Daily Limit Prevention
```python
# Assign staff to 6 periods in one day - should succeed
for period in range(1, 7):
    assert assign_staff(staff_id=42, day=1, period=period)['success'] == True

# Try 7th assignment - should fail
assert assign_staff(staff_id=42, day=1, period=7)['success'] == False
assert 'maximum daily' in result['error'].lower()
```

### Test 4: Unavailability Override
```python
# Mark staff unavailable
mark_unavailable(staff_id=42, day=1, period=2, reason='Medical')

# Try to assign - should fail
assert assign_staff(staff_id=42, day=1, period=2)['success'] == False
```

### Test 5: Section Uniqueness
```python
# Assign Dr. Sarah to Class 10-A Period 2
assign_staff(staff_id=42, section_id=5, day=1, period=2)

# Try to assign Dr. John to same section same time - should fail
assert assign_staff(staff_id=43, section_id=5, day=1, period=2)['success'] == False
assert 'already has' in result['error'].lower()
```

---

## DEPLOYMENT CHECKLIST

- [x] Database tables created
- [x] Indexes added for performance
- [x] API endpoints implemented
- [x] Conflict detection logic coded
- [x] Error handling implemented
- [x] Logging configured
- [ ] Frontend UI created
- [ ] End-to-end testing completed
- [ ] Staff training completed
- [ ] Production deployment

---

**Version**: 1.0
**Status**: Ready for Testing
**Last Updated**: 2026-02-09
