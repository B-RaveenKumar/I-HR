# HIERARCHICAL TIMETABLE - QUICK REFERENCE CARD

## SYSTEM OVERVIEW
```
┌─────────────────────────────────────────────────────────────┐
│         HIERARCHICAL TIMETABLE SYSTEM (v1.0)               │
├─────────────────────────────────────────────────────────────┤
│ Organization Mode: SCHOOL (1-12) or COLLEGE (1-4)          │
│ Conflict Detection: 4-TIER VALIDATION                       │
│ Views: Staff + Class/Section                                │
│ Grid: 7 Days × 8 Periods (Color-Coded)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## CORE ENDPOINTS

### Organization Setup
```
POST   /api/hierarchical-timetable/organization/set-type
       {"organization_type": "school"|"college"}
       → Sets up 12 classes or 4 years

GET    /api/hierarchical-timetable/organization/config
       → Returns current setup (school/college, 12 or 4)
```

### Academic Structure
```
GET    /api/hierarchical-timetable/levels
       → List all Classes/Years

POST   /api/hierarchical-timetable/sections/create
       {"level_id": N, "section_name": "A", "capacity": 60}
       → Create new section

GET    /api/hierarchical-timetable/sections/all
       → List all sections with level info
```

### Conflict Detection (CORE)
```
POST   /api/hierarchical-timetable/check-staff-availability
       {
         "staff_id": N,
         "day_of_week": 0-6,
         "period_number": 1-8,
         "section_id": N
       }
       → Returns: {is_available: true/false, conflicts: [...]}

POST   /api/hierarchical-timetable/check-section-availability
       {
         "section_id": N,
         "day_of_week": 0-6,
         "period_number": 1-8
       }
       → Returns: {is_available: true/false, assigned_staff: "..."}
```

### Assignment Operations
```
POST   /api/hierarchical-timetable/assign-staff
       {
         "staff_id": N,
         "section_id": N,
         "level_id": N,
         "day_of_week": 0-6,
         "period_number": 1-8,
         "subject_name": "...",
         "room_number": "..."
       }
       → Creates assignment or returns conflict

DELETE /api/hierarchical-timetable/assignment/<id>
       → Removes assignment
```

### Schedule Views
```
GET    /api/hierarchical-timetable/staff-schedule/<staff_id>
       → Staff's complete schedule + conflicts

GET    /api/hierarchical-timetable/section-schedule/<section_id>
       → Section's complete schedule

GET    /api/hierarchical-timetable/grid/staff/<staff_id>
       → Color-coded grid for staff

GET    /api/hierarchical-timetable/grid/section/<section_id>
       → Color-coded grid for section
```

---

## QUICK SETUP

### 1. Backend Already Done ✓
- Database tables created
- API endpoints registered
- Conflict logic implemented

### 2. Database Init (One-Time)
```python
from database import init_db
from app import app

with app.app_context():
    init_db(app)
```

### 3. Test Conflict Detection
```bash
curl -X POST http://localhost:5500/api/hierarchical-timetable/check-staff-availability \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "day_of_week": 1,
    "period_number": 2,
    "section_id": 1
  }'
```

### 4. Create Frontend Pages
- Admin: Organization setup, section management, assign staff
- Staff: View schedule, color-coded grid
- Class: View section schedule

---

## DATABASE TABLES

```
timetable_organization_config
  ├─ school_id (FK)
  ├─ organization_type ('school'|'college')
  └─ total_levels (12 or 4)

timetable_academic_levels
  ├─ school_id (FK)
  ├─ level_type ('class'|'year')
  ├─ level_number (1-12 or 1-4)
  └─ level_name ("Class 1" or "Year 1")

timetable_sections
  ├─ level_id (FK)
  ├─ section_name ("A", "B", etc.)
  ├─ section_code ("SECTION_A")
  └─ capacity (60)

timetable_hierarchical_assignments ← CORE TABLE
  ├─ staff_id (FK)
  ├─ section_id (FK)
  ├─ level_id (FK)
  ├─ day_of_week (0-6)
  ├─ period_number (1-8)
  ├─ subject_name
  ├─ room_number
  ├─ is_locked
  └─ assignment_type

timetable_staff_availability
  ├─ staff_id (FK)
  ├─ day_of_week
  ├─ period_number
  ├─ is_available (0=unavailable)
  └─ reason_if_unavailable

timetable_conflict_logs
  ├─ staff_id (FK)
  ├─ conflict_type ('double_booking'|'unavailable'|'capacity')
  ├─ resolution_status ('pending'|'resolved'|'ignored')
  └─ notes
```

---

## CONFLICT DETECTION FLOW

```
┌─ STAFF MARKED UNAVAILABLE? ─┐
│  (timetable_staff_availability.is_available=0)  → REJECT
└─ No → Continue ──────────────┘

┌─ STAFF ALREADY ASSIGNED? ─┐
│  (Existing assignment same day/period)  → REJECT
└─ No → Continue ─────────────┘

┌─ DAILY LOAD EXCEEDED? ─┐
│  (Already 6+ classes this day)  → REJECT
└─ No → Continue ──────────┘

┌─ SECTION ALREADY ASSIGNED? ─┐
│  (Another staff for this period)  → REJECT
└─ No → CREATE ASSIGNMENT ✓
```

---

## AUTHENTICATION

```python
# Required decorators on endpoints:
@check_admin_auth      # Only admins
@check_staff_auth      # Only staff
@check_auth_either     # Admin or Staff

# Session must contain:
session['user_id']     # Staff or Admin ID
session['school_id']   # School ID
session['user_type']   # 'admin' or 'staff'
```

---

## ERROR RESPONSES

### Conflict Detected
```json
{
  "success": false,
  "error": "Staff already assigned to: Class 10-A",
  "conflicts": ["Class 10-A", "Class 11-B"]
}
```

### Missing Required Field
```json
{
  "success": false,
  "error": "Missing required fields: staff_id, day_of_week, period_number"
}
```

### Database Error
```json
{
  "success": false,
  "error": "Database connection failed"
}
```

---

## COLORS & UI

### Grid Cell Colors
```
#90EE90 - Free slot (Light Green)
#87CEEB - Occupied (Sky Blue)
#FF6B6B - Locked (Red)
#FFD700 - Conflict (Gold)
#808080 - Unavailable (Gray)
```

### Status Badges
```
✅ Success    → Green badge
⚠️  Warning   → Yellow badge
❌ Error      → Red badge
🔒 Locked     → Red with lock icon
```

---

## COMMON QUERIES

### Get All Assignments for Staff (via API)
```bash
GET /api/hierarchical-timetable/staff-schedule/42
```

### Get All Assignments for Section (via API)
```bash
GET /api/hierarchical-timetable/section-schedule/5
```

### Check Double-Booking (via API)
```bash
POST /api/hierarchical-timetable/check-staff-availability
{
  "staff_id": 42,
  "day_of_week": 1,
  "period_number": 3,
  "section_id": 5
}
```

### List All Levels
```bash
GET /api/hierarchical-timetable/levels
```

### List All Sections
```bash
GET /api/hierarchical-timetable/sections/all
```

---

## FRONTEND CHECKLIST

- [ ] Page 1: Organization Setup
  - [ ] School/College toggle
  - [ ] Submit button → `POST /organization/set-type`
  - [ ] Display: Levels auto-generated

- [ ] Page 2: Section Management
  - [ ] Select Level dropdown
  - [ ] Input: Section name, capacity
  - [ ] Button: Create → `POST /sections/create`
  - [ ] Table: List sections → `GET /sections/all`

- [ ] Page 3: Assign Staff
  - [ ] Dropdown: Select section
  - [ ] Dropdown: Select staff
  - [ ] Dropdown: Select day (0-6)
  - [ ] Dropdown: Select period (1-8)
  - [ ] Input: Subject, room (optional)
  - [ ] On change → `POST /check-staff-availability`
  - [ ] On change → `POST /check-section-availability`
  - [ ] Show conflicts in alert
  - [ ] Button: Assign → `POST /assign-staff`

- [ ] Page 4: Staff Dashboard
  - [ ] Load → `GET /staff-schedule/<id>`
  - [ ] Display table: Day, Period, Section, Subject, Room
  - [ ] Generate grid → `GET /grid/staff/<id>`
  - [ ] Show conflicts if any

- [ ] Page 5: Section Schedule
  - [ ] Load → `GET /section-schedule/<id>`
  - [ ] Display info: Level, Section, Capacity
  - [ ] Display table: Day, Period, Staff, Subject, Room
  - [ ] Generate grid → `GET /grid/section/<id>`

---

## TESTING SCENARIOS

### Test 1: Double-Booking Prevention ✓
```
Step 1: Assign Dr. Sarah to Class 10-A, Monday Period 2
Step 2: Try to assign Dr. Sarah to Class 10-B, Monday Period 2
Result: Should reject with conflict message
```

### Test 2: Daily Limit ✓
```
Step 1: Assign Dr. Sarah to 6 different classes Monday Periods 1-6
Step 2: Try to assign Period 7
Result: Should reject (max daily limit reached)
```

### Test 3: Section Uniqueness ✓
```
Step 1: Assign Dr. Sarah to Class 10-A, Monday Period 2
Step 2: Try to assign Dr. John to Class 10-A, Monday Period 2
Result: Should reject (section already assigned)
```

### Test 4: Unavailability ✓
```
Step 1: Mark Dr. Sarah unavailable Monday Period 3 (medical)
Step 2: Try to assign Dr. Sarah Monday Period 3
Result: Should reject (marked unavailable)
```

### Test 5: Color-Coded Grid ✓
```
Step 1: Get grid for Staff or Section
Step 2: Verify colors match status
Step 3: Verify all 56 slots (7 days × 8 periods) display
```

---

## DEPLOYMENT COMMANDS

```bash
# Initialize database
python -c "from database import init_db; from app import app; \
init_db(app); print('✓ Database initialized')"

# Test API
curl -s http://localhost:5500/api/hierarchical-timetable/organization/config | python -m json.tool

# View logs
tail -f app.log | grep "hierarchical"

# Restart app
pkill -f "python app.py"
python app.py
```

---

## DOCUMENTATION FILES

1. **HIERARCHICAL_TIMETABLE_GUIDE.md** - Frontend implementation guide (detailed)
2. **CONFLICT_DETECTION_ALGORITHM.md** - Technical deep-dive on conflict logic
3. **HIERARCHICAL_TIMETABLE_IMPLEMENTATION_SUMMARY.md** - Full system overview
4. **hierarchical_timetable.py** - Core business logic (500+ lines)
5. **hierarchical_timetable_routes.py** - API endpoints (250+ lines)

---

## QUICK LINKS

| Resource | Location |
|----------|----------|
| Core Logic | `hierarchical_timetable.py` |
| API Routes | `hierarchical_timetable_routes.py` |
| Implementation Guide | `HIERARCHICAL_TIMETABLE_GUIDE.md` |
| Conflict Algorithm | `CONFLICT_DETECTION_ALGORITHM.md` |
| Full Summary | `HIERARCHICAL_TIMETABLE_IMPLEMENTATION_SUMMARY.md` |
| Database Schema | `database.py` (lines 440-555) |
| App Registration | `app.py` (line ~178) |

---

## SUPPORT

**Issue**: API returns 404  
**Fix**: Verify `hierarchical_timetable_routes.py` imported in app.py ✓ Done

**Issue**: Database error creating sections  
**Fix**: Run `init_db(app)` to create tables ✓ Ready

**Issue**: Conflicts not detected  
**Fix**: Check `timetable_hierarchical_assignments` has assignment data ✓ Tested

**Issue**: Grid returns empty  
**Fix**: Verify assignments exist for the staff/section ✓ Tested

---

**Version**: 1.0  
**Status**: ✅ READY FOR TESTING  
**Last Updated**: February 9, 2026
