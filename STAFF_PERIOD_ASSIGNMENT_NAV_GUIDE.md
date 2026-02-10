# Staff Period Assignment - Navigation & Integration Guide

## 🗺️ Where to Find It

### Access URL
```
http://localhost:5000/admin/staff-period-assignment
```

### Admin Dashboard Navigation Path
```
Dashboard
  ├── Timetable Management
  ├── Staff Period Assignment  ← YOU ARE HERE
  │   ├── Assign Periods
  │   ├── View Staff Schedules
  │   └── Manage Assignments
  └── Other Options
```

---

## 🔗 Links & Integration Points

### Main Dashboard Integration
**File:** `app.py`
**Route:** `@app.route('/admin/staff-period-assignment')`
**Template:** `templates/staff_period_assignment.html`

---

## 🧭 Navigation Map

### From Dashboard:
```
1. Login as Admin
2. Go to Dashboard
3. Look for "Staff Period Assignment" in sidebar/menu
4. Click to access page
```

### From Timetable Management:
```
1. In timetable_management.html
2. Add button: 
   <a href="/admin/staff-period-assignment" class="btn btn-info">
     Period Assignment
   </a>
```

### Direct URL:
```
Type in browser: /admin/staff-period-assignment
```

---

## 📱 Page Navigation

### Left Section: Assignment Form
```
├── Staff Selection
│   └── Dropdown: Select staff member
├── Day Selection
│   └── 7 buttons: Sunday-Saturday
├── Period Selection
│   └── Dropdown: Period 1-8 with times
└── Assign Button
    └── Green button: Submit assignment
```

### Right Section: Staff Schedule
```
├── Header: Selected staff name & count
├── Empty State (if no selections)
├── Schedule Table (if staff selected)
│   ├── Day column
│   ├── Period column
│   ├── Time column
│   └── Remove buttons
```

### Bottom Section: All Assignments
```
├── Table Header
├── Search/Filter (optional)
├── Data Rows
│   ├── Staff Name
│   ├── Day
│   ├── Period
│   ├── Time
│   ├── Status badge
│   └── Remove button
└── Pagination (if many rows)
```

---

## 🎯 Quick Navigation Guide

### Task: Assign a Period
```
1. Open /admin/staff-period-assignment
2. Select staff from dropdown → Field updates
3. Click day (Monday, Tuesday, etc.) → Visual feedback
4. Select period from dropdown → Shows time
5. Click "Assign Period" button → Form processes
6. See success message → Assignment created
```

### Task: View Staff Schedule
```
1. Open /admin/staff-period-assignment
2. Select staff from dropdown
3. Look at right panel → "Staff Assigned Periods" card
4. See all periods with day, period, time
5. Click "Remove" if needed → Remove assignment
```

### Task: Find All Assignments
```
1. Open /admin/staff-period-assignment
2. Scroll to bottom
3. View "All Staff Period Assignments" table
4. Find assignment in rows
5. Click "Remove" at end of row to delete
```

### Task: Navigate Away
```
Option 1: Click browser back button
Option 2: Click "Back to Timetable" button (top right)
Option 3: Use dashboard menu to go elsewhere
```

---

## 🔐 Access Control

### Who Can Access?
- ✅ Admin users
- ❌ Staff members (read-only, if allowed)
- ❌ Regular users
- ❌ Unauthenticated users

### Authentication Required?
- ✅ YES - Must be logged in as admin
- ❌ No public access

### School Context
- ✅ Automatically uses logged-in user's school
- ✅ Data isolated by school_id

---

## 📡 API Navigation (For Developers)

### Endpoint Base Path
```
/api/timetable/staff-period/
```

### Three Main Endpoints

#### 1. Create Assignment
```
POST /api/timetable/staff-period/assign
Accept: application/json
Content-Type: application/json

{
  "staff_id": 5,
  "day_of_week": 1,
  "period_number": 3
}
```

#### 2. List Staff Periods
```
GET /api/timetable/staff-period/list/5
Accept: application/json
```

#### 3. Remove Assignment
```
POST /api/timetable/staff-period/remove/42
Accept: application/json
```

---

## 🗂️ File Structure

### Frontend Files
```
templates/
  ├── staff_period_assignment.html  ← Main UI page
  └── (includes CSS/JS inline)

static/
  ├── css/
  │   └── (optional custom styles)
  └── js/
      └── (optional custom scripts)
```

### Backend Files
```
root/
  ├── app.py  ← Route definition (line ~5405)
  ├── staff_period_assignment.py  ← Business logic (500+ lines)
  ├── timetable_api_routes.py  ← API endpoints (line ~660+)
  └── database.py  ← Database setup (existing)
```

### Documentation Files
```
docs/
  ├── STAFF_PERIOD_ASSIGNMENT_GUIDE.md  ← Complete guide
  ├── STAFF_PERIOD_ASSIGNMENT_QUICK_REF.md  ← Quick reference
  ├── STAFF_PERIOD_ASSIGNMENT_TUTORIAL.md  ← Video script
  ├── STAFF_PERIOD_ASSIGNMENT_TESTING.md  ← Test procedures
  ├── STAFF_PERIOD_ASSIGNMENT_COMPLETE.md  ← Implementation summary
  └── STAFF_PERIOD_ASSIGNMENT_NAV_GUIDE.md  ← This file
```

---

## 🔄 Data Flow

### Assigning a Period
```
User Input (Form)
        ↓
JavaScript Fetch API
        ↓
Backend Route: POST /api/timetable/staff-period/assign
        ↓
Flask Validation
        ↓
StaffPeriodAssignment.assign_period_to_staff()
        ↓
Database Query: INSERT INTO timetable_assignments
        ↓
JSON Response
        ↓
Frontend Update: Display success, reload data
        ↓
User sees updated schedule
```

### Viewing Schedule
```
User Selects Staff (Dropdown)
        ↓
JavaScript Fetch API
        ↓
Backend Route: GET /api/timetable/staff-period/list/{id}
        ↓
StaffPeriodAssignment.get_staff_assigned_periods()
        ↓
Database Query: SELECT from timetable_assignments
        ↓
JSON Response with periods array
        ↓
Frontend Renders Table
        ↓
User sees periods
```

### Removing Assignment
```
User Clicks Remove Button
        ↓
Confirmation Dialog
        ↓
User Confirms
        ↓
JavaScript Fetch API
        ↓
Backend Route: POST /api/timetable/staff-period/remove/{id}
        ↓
StaffPeriodAssignment.remove_staff_period_assignment()
        ↓
Database Query: DELETE FROM timetable_assignments
        ↓
JSON Response
        ↓
Frontend Update: Remove row, reload data
        ↓
User sees updated schedule
```

---

## 🎨 UI Components Reference

### Day Selection Component
```html
<div class="day-option" onclick="selectDay(0)">
  <input type="radio" name="dayOfWeek" value="0">
  <span>Sunday</span>
</div>
```

### Period Dropdown Component
```html
<select id="periodSelect" class="form-select">
  <option value="">-- Choose a period --</option>
  <option value="1">Period 1: 08:00 - 09:00</option>
  <option value="2">Period 2: 09:00 - 10:00</option>
  ...
</select>
```

### Assignment Table Component
```html
<table class="table">
  <tr>
    <th>Staff Name</th>
    <th>Day</th>
    <th>Period</th>
    <th>Time</th>
    <th>Status</th>
    <th>Action</th>
  </tr>
  <tr>
    <td>John Doe</td>
    <td>Monday</td>
    <td>Period 3</td>
    <td>09:30-10:30</td>
    <td><span class="badge">Active</span></td>
    <td>
      <button class="btn btn-danger" onclick="removePeriod(42)">
        Remove
      </button>
    </td>
  </tr>
</table>
```

---

## 🔗 Integration Checklist

### When Adding to Dashboard
```
1. [ ] Add menu link to navigation
2. [ ] Add button to dashboard
3. [ ] Update dashboard breadcrumb
4. [ ] Add to quick links section
5. [ ] Update user documentation
6. [ ] Test access from dashboard
```

### When Adding to Timetable Page
```
1. [ ] Add "Period Assignment" button
2. [ ] Add link to staff_period_assignment page
3. [ ] Update timetable_management.html
4. [ ] Test navigation
```

### When Adding to Admin Panel
```
1. [ ] Add menu item with icon
2. [ ] Add to admin shortcuts
3. [ ] Update breadcrumb navigation
4. [ ] Add to admin help section
```

---

## 📞 Common Navigation Issues

### Issue: Page not found (404)
**Solution:** Verify route registered in app.py
```python
@app.route('/admin/staff-period-assignment')
def staff_period_assignment():
    ...
```

### Issue: Redirect to login
**Solution:** Ensure admin authentication
- Check: session['user_type'] == 'admin'
- Check: session['user_id'] is set

### Issue: Blank page
**Solution:** Check browser console for errors
- Press F12 → Console tab
- Look for JavaScript errors
- Check network tab for failed requests

### Issue: Data not loading
**Solution:** Verify API endpoints
- Check: /api/timetable/staff-period/list works
- Check: Database has staff records
- Check: School context is set

---

## 🔍 Debugging Navigation

### View JavaScript Console
```
1. Press F12
2. Click "Console" tab
3. Look for errors or warnings
4. Check network requests
```

### Check Network Requests
```
1. Press F12
2. Click "Network" tab
3. Perform action (assign period)
4. Look for:
   - POST requests to /api/timetable/staff-period/assign
   - Response status (200 = success)
   - Response body (JSON)
```

### Check Database
```
1. Open database client
2. Connect to your SQLite database
3. Query: SELECT * FROM timetable_assignments LIMIT 10;
4. Verify data present and correct
```

---

## 🎓 Learning Path

### For First-Time Users
```
1. Read: STAFF_PERIOD_ASSIGNMENT_QUICK_REF.md (5 min)
2. Open: /admin/staff-period-assignment (2 min)
3. Practice: Assign 5 periods (5 min)
4. Explore: View staff schedule (2 min)
5. Cleanup: Remove test assignments (2 min)
Total: ~15 minutes
```

### For Developers
```
1. Read: STAFF_PERIOD_ASSIGNMENT_GUIDE.md (20 min)
2. Study: staff_period_assignment.py (15 min)
3. Review: timetable_api_routes.py API endpoints (10 min)
4. Test: API calls with Postman/curl (15 min)
5. Integrate: Add to your app (30 min)
Total: ~90 minutes
```

### For QA/Testers
```
1. Read: STAFF_PERIOD_ASSIGNMENT_TESTING.md (30 min)
2. Setup: Pre-test environment (15 min)
3. Execute: Test suites 1-5 (45 min)
4. Execute: Test suites 6-10 (45 min)
5. Report: Document findings (30 min)
Total: ~2.5 hours
```

---

## 📚 Documentation Cross-References

| Need | Document | Section |
|------|----------|---------|
| Quick Start | Quick Reference | Main Operations |
| How to Use | Complete Guide | Features / Components |
| API Docs | Complete Guide | API Endpoints |
| Python Code | Complete Guide | Backend Implementation |
| Testing | Testing Guide | Test Suite 1-10 |
| Video | Tutorial Guide | Video Script |
| Troubleshoot | Complete Guide | Troubleshooting |
| Setup | Testing Guide | Pre-Test Checklist |

---

## 🚀 Quick Launch Commands

### Start Development Server
```bash
cd d:\VISHNRX\ProjectVX
python app.py
```

### Access Page
```
http://localhost:5000/admin/staff-period-assignment
```

### Test API
```bash
curl -X POST http://localhost:5000/api/timetable/staff-period/assign \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "day_of_week": 1,
    "period_number": 3
  }'
```

---

## 📋 Related Pages & Systems

### Related Features
- **Hierarchical Timetable:** `/admin/timetable` - Complex institutional setup
- **Timetable Management:** `/admin/timetable` - Full timetable system
- **Staff Management:** `/admin/staff` - Staff directory
- **Period Management:** `/admin/periods` - Period configuration

### Related APIs
- **Staff Endpoints:** `/api/timetable/staff/list`
- **Period Endpoints:** `/api/timetable/periods`
- **Timetable Endpoints:** `/api/timetable/assignments`

---

## 🎯 Navigation Best Practices

✅ **DO:**
- Use breadcrumb navigation to go back
- Check console for errors
- Use direct URL if menu item missing
- Follow documentation order
- Test with test data first

❌ **DON'T:**
- Force page refresh repeatedly
- Ignore error messages
- Modify database directly without backup
- Use production data for testing
- Skip the pre-test checklist

---

## 📞 Support Quick Links

| Issue | Link | Time |
|-------|------|------|
| Can't access page | See "Access Control" | 2 min |
| Page won't load | See "Debugging Navigation" | 5 min |
| API not working | See "API Navigation" | 5 min |
| Don't know how to use | See "Quick Launch" | 10 min |
| Need detailed help | Read "Complete Guide" | 20 min |

---

**Status:** ✅ Navigation Guide Complete  
**Last Updated:** 2024  
**Version:** 1.0
