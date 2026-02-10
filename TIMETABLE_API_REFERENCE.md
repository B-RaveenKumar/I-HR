# Timetable Management - API Reference

## Quick Reference: All Routes & Endpoints

---

## COMPANY ADMIN ROUTES

### Enable/Disable Timetable Module

**Route**: `GET/POST /company/timetable_settings/<int:school_id>`

**Access**: Company Admin only

**Methods**:
- `GET`: Display current settings
- `POST`: Update settings

**Parameters**:
- `school_id` (URL): School ID
- `timetable_enabled` (Form): Checkbox, on/off

**Returns**:
- GET: HTML template with current status
- POST: Redirect to school details

**Example**:
```bash
POST /company/timetable_settings/5
Headers: Content-Type: application/x-www-form-urlencoded
Body: timetable_enabled=on
```

---

## ADMIN ROUTES

### Main Dashboard

**Route**: `GET /admin/timetable`

**Access**: School Admin only

**Returns**: HTML dashboard with three tabs (Periods, Permissions, Assignments)

**Example**:
```bash
GET /admin/timetable
Session: school_id=5, user_type=admin
```

---

### Manage Periods

**Route**: `GET/POST/PUT /admin/timetable/periods`

**Access**: School Admin only

**GET Parameters**:
- None

**POST/PUT JSON Body**:
```json
{
  "period_number": 9,
  "period_name": "Period 9",
  "start_time": "14:00",
  "end_time": "14:30"
}
```

**Returns**:
```json
{
  "success": true,
  "message": "Period added successfully.",
  "periods": [
    {
      "id": 1,
      "period_number": 1,
      "period_name": "Period 1",
      "start_time": "09:00",
      "end_time": "09:45",
      "duration_minutes": 45,
      "is_active": 1
    }
  ]
}
```

**Examples**:
```bash
# Get all periods
GET /admin/timetable/periods

# Add new period
POST /admin/timetable/periods
Content-Type: application/json
{
  "period_number": 9,
  "period_name": "Period 9",
  "start_time": "14:00",
  "end_time": "14:30"
}
```

---

### Manage Department Permissions

**Route**: `GET/POST/PUT /admin/timetable/department_permissions`

**Access**: School Admin only

**GET Parameters**: None

**POST/PUT JSON Body**:
```json
{
  "department": "Library",
  "allow_alterations": false,
  "allow_inbound": false
}
```

**Returns**:
```json
{
  "success": true,
  "message": "Permissions set for Library department.",
  "permissions": [
    {
      "id": 1,
      "department": "Mathematics",
      "allow_alterations": true,
      "allow_inbound": true
    }
  ]
}
```

**Examples**:
```bash
# Get all permissions
GET /admin/timetable/department_permissions

# Set permissions (lock Library)
POST /admin/timetable/department_permissions
Content-Type: application/json
{
  "department": "Library",
  "allow_alterations": false,
  "allow_inbound": false
}
```

---

### View Staff Assignments

**Route**: `GET/POST/PUT /admin/timetable/staff_assignments`

**Access**: School Admin only

**GET Parameters**:
- `staff_id` (query): Staff ID (required)

**POST/PUT JSON Body**:
```json
{
  "staff_id": 15,
  "day_of_week": 0,
  "period_number": 3,
  "class_subject": "Mathematics"
}
```

**Returns** (GET):
```json
{
  "success": true,
  "timetable": {
    "Monday": [
      {
        "period_number": 1,
        "period_name": "Period 1",
        "start_time": "09:00",
        "end_time": "09:45",
        "assigned": true,
        "class_subject": "Mathematics",
        "is_locked": false,
        "is_self_allocated": false
      }
    ]
  }
}
```

**Examples**:
```bash
# Get staff timetable
GET /admin/timetable/staff_assignments?staff_id=15

# Add assignment
POST /admin/timetable/staff_assignments
Content-Type: application/json
{
  "staff_id": 15,
  "day_of_week": 0,
  "period_number": 3,
  "class_subject": "Mathematics"
}
```

---

### Admin Override (Force Reassign)

**Route**: `POST /admin/timetable/override`

**Access**: School Admin only

**JSON Body**:
```json
{
  "assignment_id": 42,
  "new_staff_id": 20,
  "notes": "Staff 15 is absent today"
}
```

**Returns**:
```json
{
  "success": true,
  "message": "Assignment reassigned from Staff 15 to Staff 20."
}
```

**Example**:
```bash
POST /admin/timetable/override
Content-Type: application/json
{
  "assignment_id": 42,
  "new_staff_id": 20,
  "notes": "Staff 15 is absent today"
}
```

**Side Effects**:
- Creates audit entry in alteration_requests table
- Sends notifications to both staff members

---

### Delete Self-Allocation (Admin Only)

**Route**: `POST /admin/timetable/delete_self_allocation`

**Access**: School Admin only

**JSON Body**:
```json
{
  "allocation_id": 5
}
```

**Returns**:
```json
{
  "success": true,
  "message": "Self-allocation deleted successfully."
}
```

---

## STAFF ROUTES

### View Personal Timetable

**Route**: `GET /staff/timetable`

**Access**: Staff only

**Parameters**: None (uses session staff_id)

**Returns**: HTML template with timetable grid

---

### Request Period Alteration

**Route**: `POST /staff/timetable/request_alteration`

**Access**: Staff only

**JSON Body**:
```json
{
  "assignment_id": 42,
  "target_staff_id": 20,
  "target_department": "Mathematics",
  "reason": "Need to attend medical appointment"
}
```

**Returns**:
```json
{
  "success": true,
  "message": "Alteration request created successfully.",
  "request_id": 123
}
```

**Validation**:
- Department must allow outbound alterations
- Target department must allow inbound alterations

**Example**:
```bash
POST /staff/timetable/request_alteration
Content-Type: application/json
{
  "assignment_id": 42,
  "target_staff_id": 20,
  "reason": "Medical appointment"
}
```

---

### Respond to Alteration Request

**Route**: `POST /staff/timetable/respond_alteration`

**Access**: Staff only

**JSON Body**:
```json
{
  "request_id": 123,
  "accepted": true,
  "reason": "No problem, I can take this period"
}
```

**Returns**:
```json
{
  "success": true,
  "message": "Request accepted successfully."
}
```

**Side Effects** (if accepted):
- Updates timetable_assignments
- Sends notification to requester

---

### Add Self-Allocation (Fill Empty Slot)

**Route**: `POST /staff/timetable/add_self_allocation`

**Access**: Staff only

**JSON Body**:
```json
{
  "day_of_week": 0,
  "period_number": 3,
  "class_subject": "Extra Mathematics Class"
}
```

**Returns**:
```json
{
  "success": true,
  "message": "Class added successfully. (Admin locked)"
}
```

**Constraints**:
- Period must not already be assigned
- Entry is automatically admin_locked

---

### Attempt Delete Self-Allocation (Staff)

**Route**: `POST /staff/timetable/delete_self_allocation`

**Access**: Staff only

**JSON Body**:
```json
{
  "allocation_id": 5
}
```

**Returns** (Always fails for staff):
```json
{
  "success": false,
  "message": "You do not have permission to delete this entry."
}
```

---

## API ENDPOINTS

### Get All Departments

**Route**: `GET /api/timetable/departments`

**Access**: Authenticated users only

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "departments": ["Mathematics", "Science", "English", "Library", "PE"]
}
```

---

### Get Staff by Department

**Route**: `GET /api/timetable/department_staff/<department>`

**Access**: Authenticated users only

**Parameters**:
- `department` (URL): Department name

**Returns**:
```json
{
  "success": true,
  "staff": [
    {
      "id": 15,
      "staff_id": "EMP001",
      "full_name": "John Doe",
      "department": "Mathematics"
    }
  ]
}
```

---

### Get Pending Alteration Requests

**Route**: `GET /api/timetable/alteration_requests`

**Access**: Staff only

**Parameters**: None (uses session staff_id)

**Returns**:
```json
{
  "success": true,
  "requests": [
    {
      "id": 123,
      "requester_id": 20,
      "requester_name": "Jane Smith",
      "assignment_id": 42,
      "reason": "Medical appointment",
      "status": "pending",
      "created_at": "2026-01-22 10:30:00"
    }
  ]
}
```

---

## ERROR RESPONSES

All endpoints return consistent error responses:

### Permission Denied
```json
{
  "success": false,
  "error": "Unauthorized"
}
```
**HTTP Status**: 401

### Validation Error
```json
{
  "success": false,
  "error": "Missing required fields"
}
```
**HTTP Status**: 400

### Not Found
```json
{
  "success": false,
  "error": "Assignment not found or does not belong to you."
}
```
**HTTP Status**: 404

### Server Error
```json
{
  "success": false,
  "error": "Error message here"
}
```
**HTTP Status**: 500

---

## CSRF Protection

All POST, PUT, DELETE requests require CSRF token:

**Headers**:
```
X-CSRFToken: <token-value>
```

**Or Form Field**:
```html
<input type="hidden" name="csrf_token" value="...">
```

---

## Authentication

All endpoints require active session:

**Session Variables**:
- `user_id`: User ID
- `user_type`: 'company_admin', 'admin', or 'staff'
- `school_id`: School ID (admin/staff only)

---

## Rate Limiting

No rate limiting implemented. Consider adding for production:
- 10 requests/minute for alterations
- 60 requests/minute for view operations

---

## Webhooks (Future)

Not implemented but could add:
- POST /webhooks/alteration_accepted
- POST /webhooks/alteration_rejected
- POST /webhooks/admin_override

---

## Data Types

### Time Format
- Format: HH:MM or HH:MM:SS
- Examples: "09:00", "14:30:00"
- Range: 00:00 to 23:59

### Day of Week
- 0 = Monday
- 1 = Tuesday
- 2 = Wednesday
- 3 = Thursday
- 4 = Friday
- 5 = Saturday

### Status Values
- pending: Awaiting response
- accepted: Accepted by target
- rejected: Rejected by target
- admin_override: Force assigned by admin

### Alteration Types
- peer_swap: Staff-to-staff swap
- self_allocation: Empty slot filling
- admin_override: Admin reassignment

---

## Pagination (Future Enhancement)

Not currently implemented but recommend for large datasets:
```
GET /admin/timetable/periods?page=1&limit=20
```

---

## Sorting (Future Enhancement)

Not currently implemented but recommend:
```
GET /api/timetable/alteration_requests?sort=created_at&order=desc
```

---

## Filtering (Future Enhancement)

Not currently implemented but recommend:
```
GET /admin/timetable/periods?department=Mathematics&status=active
```

---

**Last Updated**: January 22, 2026
**Version**: 1.0
