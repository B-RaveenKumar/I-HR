# Advanced Timetable Management & Dynamic Alteration System - Implementation Guide

## Overview
A complete modular timetable management system with three-level access control and comprehensive period alteration features for VishnoRex staff management system.

## System Architecture

### Three-Level Access Control

#### Level 1: Company Admin (Gatekeeper)
- **Access**: Company Admin Panel > School Settings
- **Function**: Enable/Disable timetable module for each school
- **Implementation**: `company_timetable_settings` route and template
- **UI Location**: Company school details page with toggle switch

#### Level 2: School Admin (Configuration & Override)
- **Access**: Admin Dashboard > Timetable Management
- **Functions**:
  1. Dynamic Period Configuration - Add/Edit periods with scalable structure
  2. Department-Level Alteration Locks - Restrict departments from sending/receiving requests
  3. Admin Override (Forced Reassignment) - Instantly reassign periods to staff
- **Implementation**: `admin_timetable` route with tabbed interface

#### Level 3: Staff (Self-Service & Peer Swapping)
- **Access**: Staff Dashboard > My Timetable
- **Functions**:
  1. View personal timetable with period details
  2. Request peer-to-peer alterations (with approval workflow)
  3. Self-allocate empty slots (admin-locked after creation)
  4. Respond to incoming alteration requests
- **Implementation**: `staff_timetable` route with interactive UI

---

## Database Schema

### New Tables Created

#### 1. `timetable_settings`
Stores school-level timetable configuration
```sql
CREATE TABLE timetable_settings (
    id INTEGER PRIMARY KEY,
    school_id INTEGER UNIQUE,
    is_enabled BOOLEAN DEFAULT 0,
    number_of_periods INTEGER DEFAULT 8,
    master_schedule TEXT DEFAULT '{}',
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id)
)
```

#### 2. `timetable_periods`
Master schedule period definitions
```sql
CREATE TABLE timetable_periods (
    id INTEGER PRIMARY KEY,
    school_id INTEGER,
    period_number INTEGER,
    period_name TEXT,
    start_time TIME,
    end_time TIME,
    duration_minutes INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id),
    UNIQUE(school_id, period_number)
)
```

#### 3. `timetable_department_permissions`
Department-level alteration permissions
```sql
CREATE TABLE timetable_department_permissions (
    id INTEGER PRIMARY KEY,
    school_id INTEGER,
    department TEXT,
    allow_alterations BOOLEAN DEFAULT 1,    -- Outbound: Can send requests?
    allow_inbound BOOLEAN DEFAULT 1,        -- Inbound: Can receive requests?
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id),
    UNIQUE(school_id, department)
)
```

#### 4. `timetable_assignments`
Staff period assignments
```sql
CREATE TABLE timetable_assignments (
    id INTEGER PRIMARY KEY,
    school_id INTEGER,
    staff_id INTEGER,
    day_of_week INTEGER,           -- 0-5: Mon-Sat
    period_number INTEGER,
    class_subject TEXT,
    is_assigned BOOLEAN DEFAULT 1,
    is_locked BOOLEAN DEFAULT 0,
    locked_reason TEXT,
    locked_by INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id),
    FOREIGN KEY (staff_id) REFERENCES staff(id),
    FOREIGN KEY (locked_by) REFERENCES admins(id),
    UNIQUE(school_id, staff_id, day_of_week, period_number)
)
```

#### 5. `timetable_alteration_requests`
Alteration request tracking and approval workflow
```sql
CREATE TABLE timetable_alteration_requests (
    id INTEGER PRIMARY KEY,
    school_id INTEGER,
    assignment_id INTEGER,
    requester_staff_id INTEGER,
    target_staff_id INTEGER,           -- Specific staff for swap (optional)
    target_department TEXT,            -- Department for generic request (optional)
    alteration_type TEXT,              -- peer_swap, self_allocation, admin_override
    status TEXT,                       -- pending, accepted, rejected, admin_override
    reason TEXT,
    response_reason TEXT,
    admin_notes TEXT,
    responded_by INTEGER,              -- Staff member who responded
    responded_at TIMESTAMP,
    processed_by INTEGER,              -- Admin who processed
    processed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id),
    FOREIGN KEY (assignment_id) REFERENCES timetable_assignments(id),
    FOREIGN KEY (requester_staff_id) REFERENCES staff(id),
    FOREIGN KEY (target_staff_id) REFERENCES staff(id),
    FOREIGN KEY (responded_by) REFERENCES staff(id),
    FOREIGN KEY (processed_by) REFERENCES admins(id)
)
```

#### 6. `timetable_self_allocations`
Staff self-filled empty slots (admin-locked)
```sql
CREATE TABLE timetable_self_allocations (
    id INTEGER PRIMARY KEY,
    school_id INTEGER,
    staff_id INTEGER,
    day_of_week INTEGER,
    period_number INTEGER,
    class_subject TEXT,
    is_admin_locked BOOLEAN DEFAULT 1,  -- Always locked after creation
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id),
    FOREIGN KEY (staff_id) REFERENCES staff(id),
    UNIQUE(school_id, staff_id, day_of_week, period_number)
)
```

---

## Python Module: `timetable_manager.py`

### Core Class: `TimetableManager`

#### Key Methods

**Company Admin Functions:**
- `enable_timetable_for_school(school_id, enabled)` - Enable/disable module
- `is_timetable_enabled(school_id)` - Check if enabled

**School Admin Functions:**
- `add_period(school_id, period_number, period_name, start_time, end_time)` - Add/modify periods
- `get_periods(school_id)` - Get all periods
- `set_department_permission(school_id, department, allow_alterations, allow_inbound)` - Set permissions
- `get_department_permissions(school_id)` - Get all permissions
- `admin_override_assignment(school_id, assignment_id, new_staff_id, admin_id, notes)` - Force reassign

**Staff Functions:**
- `get_staff_timetable(school_id, staff_id)` - Get personal timetable
- `request_alteration(school_id, assignment_id, requester_staff_id, target_staff_id, target_department, reason)` - Request swap
- `respond_to_alteration_request(request_id, responder_staff_id, accepted, reason)` - Accept/reject
- `add_self_allocation(school_id, staff_id, day_of_week, period_number, class_subject)` - Fill empty slot
- `delete_self_allocation(school_id, allocation_id, deleter_type)` - Delete (admin only)

**Helper Functions:**
- `get_all_departments(school_id)` - Get departments for filtering
- `get_staff_by_department(school_id, department)` - Get staff in department

---

## Flask Routes & API Endpoints

### Company Admin Routes

```python
@app.route('/company/timetable_settings/<int:school_id>', methods=['GET', 'POST'])
# Toggle timetable module for a school
```

### Admin Routes

```python
@app.route('/admin/timetable')
# Main timetable dashboard

@app.route('/admin/timetable/periods', methods=['GET', 'POST', 'PUT'])
# Manage periods

@app.route('/admin/timetable/department_permissions', methods=['GET', 'POST', 'PUT'])
# Set department permissions

@app.route('/admin/timetable/staff_assignments', methods=['GET', 'POST', 'PUT'])
# Manage staff assignments

@app.route('/admin/timetable/override', methods=['POST'])
# Force reassign period

@app.route('/admin/timetable/delete_self_allocation', methods=['POST'])
# Delete self-allocation (admin only)
```

### Staff Routes

```python
@app.route('/staff/timetable')
# View personal timetable

@app.route('/staff/timetable/request_alteration', methods=['POST'])
# Request period alteration

@app.route('/staff/timetable/respond_alteration', methods=['POST'])
# Accept/reject alteration request

@app.route('/staff/timetable/add_self_allocation', methods=['POST'])
# Fill empty slot with class

@app.route('/staff/timetable/delete_self_allocation', methods=['POST'])
# Attempt to delete (will fail with permission error)
```

### API Endpoints

```python
@app.route('/api/timetable/departments', methods=['GET'])
# Get all departments

@app.route('/api/timetable/department_staff/<department>', methods=['GET'])
# Get staff in specific department

@app.route('/api/timetable/alteration_requests', methods=['GET'])
# Get pending requests for current staff
```

---

## Templates

### 1. `company_timetable_settings.html`
**Purpose**: Company admin enables/disables timetable for schools
**Features**:
- Toggle switch for module activation
- Status indicator
- Clean, centered UI with gradient background

### 2. `admin_timetable_dashboard.html`
**Purpose**: School admin timetable configuration interface
**Features**:
- Tabbed interface (Periods | Permissions | Assignments)
- Add new periods with time pickers
- View all configured periods
- Department permission checklist
- Staff assignment selector

### 3. `staff_timetable.html`
**Purpose**: Staff view personal timetable and manage alterations
**Features**:
- Weekly timetable grid (Mon-Sat)
- Period status indicators (Assigned, Empty, Locked, Self-Added)
- Request Alteration modal
- Add Class modal
- Pending requests panel
- Real-time department filtering

---

## Key Features Implemented

### ✅ Feature 1: Dynamic Period Configuration
- Admin can add/modify periods with start and end times
- System calculates period duration automatically
- Scalable: Supports standard 8 periods or custom numbers
- Test: Add a 9th period and verify it appears on staff timetable

### ✅ Feature 2: Department-Level Alteration Lock
**Two-Way Blocking:**
1. **Outbound Block**: Staff from locked departments cannot send requests
   - "Request Alteration" button hidden
2. **Inbound Block**: Staff cannot select locked departments as targets
   - Department removed from dropdown in request form
- Test: Disable alterations for Library Dept, verify Librarian cannot request

### ✅ Feature 3: Admin Override (Forced Alteration)
- Admin clicks filled slot → Selects "Re-assign"
- Instant reassignment without staff acceptance
- Both original and new staff receive notifications
- Audit trail created in alteration_requests table
- Test: Move period from Staff A to Staff C, verify C gets it immediately

### ✅ Feature 4: Peer-to-Peer Alteration (Substitution)
- Staff requests alteration from their period
- Target staff receives notification
- Two possible outcomes:
  - **Accept**: Period swapped, timetable updated
  - **Reject**: Request cancelled, original staff keeps period
- Dashboard shows "Altered (Sent)" and "Altered (Received)" status
- Test: Staff A requests Staff B, B accepts, verify both see correct status

### ✅ Feature 5: Self-Allocation with Admin Lock
**Empty Slot Workflow:**
1. Staff finds empty period
2. Clicks "Add Class" and fills subject name
3. Entry saved and **automatically locked** by admin
4. Staff cannot view delete button (permission denied)
5. Admin can delete anytime
- Test: Add class as staff, attempt delete (fails), login as admin (succeeds)

### ✅ Feature 6: Bidirectional Department Isolation
- Separate toggles for "Can Send Requests" and "Can Receive Requests"
- UI shows all departments with checkbox matrix
- Test 1: Disable outbound, verify button hidden for that dept's staff
- Test 2: Disable inbound, verify dropdown filters out that dept

---

## User Interface Integration

### Navigation Updates

**Admin Sidebar** (base_modern.html):
- Added "Timetable Management" link with calendar icon
- Routes to `/admin/timetable`

**Staff Sidebar** (staff_dashboard.html):
- Added "My Timetable" link with calendar icon
- Routes to `/staff/timetable`

---

## Notification Integration

### Auto-Triggered Notifications

1. **Admin Override**
   - Original staff: "Admin has reassigned Period X to [New Staff Name]"
   - New staff: "Admin has assigned a new period to you"

2. **Peer Swap Request**
   - Target staff: "[Requester Name] has requested to swap a period with you"

3. **Request Response**
   - Requester: "Your alteration request has been [accepted|rejected]"

**Implementation**: Uses existing `NotificationManager.notify_user()` with:
- `user_id`: Staff member to notify
- `user_type`: 'staff'
- `notification_type`: 'info', 'success', or 'warning'

---

## Testing Scenarios

### Test 1: Scalability
```
Precondition: Timetable enabled, default 8 periods
Action: Admin adds 9th Period (2:00 PM - 2:30 PM)
Expected: Period appears on staff timetable grid
Result: ✓ Pass
```

### Test 2: Department Lock - Outbound
```
Precondition: Library Dept has "Can Send Requests" disabled
Action: Log in as Librarian, view timetable
Expected: No "Request Alteration" button visible
Result: ✓ Pass
```

### Test 3: Department Lock - Inbound
```
Precondition: Library Dept has "Can Receive Requests" disabled
Action: Log in as Math Teacher, open Request Alteration modal
Expected: "Library" not in Target Department dropdown
Result: ✓ Pass
```

### Test 4: Peer Swap
```
Scenario: Staff A requests Staff B
1. Staff A: Click period → "Request Change" → Select Staff B → Send
2. Staff B: Receives notification
3. Staff B: Accept request
Expected: 
   - Staff A sees "Altered (Sent)" status
   - Staff B sees "Altered (Received)" status
   - Period swapped on both timetables
Result: ✓ Pass
```

### Test 5: Admin Override
```
Precondition: Period assigned to Staff A
Action: Admin → Override → Select Staff C → Process
Expected:
   - Period instantly appears on Staff C's timetable
   - No acceptance required from Staff C
   - Both staff receive notifications
Result: ✓ Pass
```

### Test 6: Self-Allocation Lock
```
Step 1: Login as Staff, find empty slot, "Add Class" → "Math Extra"
Step 2: Entry appears with status "Self-Added"
Step 3: Try to delete (staff) → Button disabled
Step 4: Login as Admin → Verify delete works
Expected:
   - Staff cannot delete their own self-allocations
   - Admin can delete any self-allocation
Result: ✓ Pass
```

---

## Security Considerations

1. **Authentication**: All routes protected with session checks
2. **Authorization**: Role-based access control (company_admin, admin, staff)
3. **CSRF Protection**: All POST requests require CSRF token
4. **Data Validation**: Input validation on all parameters
5. **Permission Checks**: Department permissions validated before actions
6. **Audit Trail**: Alterations logged in database with timestamps and user IDs

---

## Error Handling

### Exception Management
- All database operations wrapped in try-except blocks
- Detailed logging for debugging
- User-friendly error messages returned to frontend
- Toast notifications for UI feedback

### Validation
- Period time validation (end > start)
- Staff existence verification
- Department existence checks
- Circular swap prevention

---

## Future Enhancements

1. **Recurring Timetables**: Support for pattern-based scheduling
2. **Bulk Import**: CSV import for period and assignment data
3. **Conflict Detection**: Identify double bookings or gaps
4. **Analytics**: Alteration request statistics and reports
5. **Export**: Generate timetable PDFs for printing
6. **Scheduling Algorithm**: Auto-generate optimal schedules

---

## File Summary

### New Files Created
1. `timetable_manager.py` - Core management class (~600 lines)
2. `templates/company_timetable_settings.html` - Company admin UI (~300 lines)
3. `templates/admin_timetable_dashboard.html` - Admin configuration UI (~600 lines)
4. `templates/staff_timetable.html` - Staff timetable view (~700 lines)

### Modified Files
1. `database.py` - Added 6 new tables and schema
2. `app.py` - Added import, ~400 lines of routes
3. `templates/base_modern.html` - Added timetable link to admin sidebar
4. `templates/staff_dashboard.html` - Added timetable link to staff sidebar

---

## Installation & Deployment

1. **Database Migration**
   - Existing `init_db()` function auto-creates new tables
   - No manual migration needed for existing installations

2. **Module Integration**
   - `timetable_manager.py` already imported in `app.py`
   - All routes ready for use

3. **Configuration**
   - No additional config files needed
   - Uses existing database and session management

4. **Testing**
   - Run test scenarios in test/order:
     1. Scalability → Period creation
     2. Department locks → Permissions
     3. Admin override → Override functionality
     4. Peer swapping → Request workflow
     5. Self-allocation → Empty slot filling

---

## Support & Documentation

For issues or questions:
1. Check test scenarios for usage examples
2. Review route documentation in code comments
3. Check database schema for data structure
4. Review error messages and logging output

---

**Version**: 1.0
**Last Updated**: January 22, 2026
**Status**: Production Ready
