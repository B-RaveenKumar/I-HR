# Advanced Timetable Management - Quick Start Guide

## For Company Admins

### Enable Timetable for a School

1. **Navigate to**: Company Dashboard → Click on School
2. **Find**: "Timetable Settings" button/link
3. **Toggle**: "Enable Timetable Module" switch
4. **Save**: Click "Save Changes"
5. **Verify**: Status shows "ENABLED"

**Result**: School administrators now see "Timetable Management" in their sidebar

---

## For School Admins

### Step 1: Configure Periods

1. **Navigate to**: Dashboard → Timetable Management
2. **Tab**: Click "Period Configuration"
3. **Add Period**:
   - Period Number: `9` (for example)
   - Period Name: `Period 9` (optional)
   - Start Time: `14:00` (2:00 PM)
   - End Time: `14:30` (2:30 PM)
4. **Click**: "Add Period"
5. **View**: Period appears in the "Current Periods" section

### Step 2: Set Department Permissions

1. **Tab**: Click "Department Permissions"
2. **For Each Department**:
   - ✓ "Can Send Requests" = Department staff can initiate alterations
   - ✓ "Can Receive Requests" = Other staff can select this dept as target
3. **Example**: 
   - Library: Uncheck both (staff cannot swap, cannot be selected)
   - Math: Check both (normal operations)
4. **Click**: "Save Permissions"

### Step 3: Assign Staff to Periods

1. **Tab**: Click "Staff Assignments"
2. **Select**: Choose a staff member from dropdown
3. **Click**: "View Timetable"
4. **The System Will**:
   - Show their current assignments
   - Allow you to add/modify periods
   - Display empty slots available for self-allocation

---

## For Staff

### View Your Timetable

1. **Navigate to**: Dashboard → "My Timetable" (in sidebar)
2. **Display**: Weekly grid with all assigned periods
3. **Period Status**:
   - **Assigned** (Blue): Regular period assigned by admin
   - **Empty** (Yellow): Unassigned slot you can claim
   - **Locked** (Red): Cannot modify
   - **Self-Added** (Cyan): You filled this empty slot

### Request Period Alteration

1. **Find**: Your assigned period (not locked)
2. **Click Button**: "Request Change"
3. **In Modal**:
   - **Target Department**: Select which department to swap with
   - **Target Staff** (Optional): Pick specific staff, or leave blank for any available
   - **Reason**: Explain why you need this change
4. **Click**: "Send Request"
5. **Notification**: Target staff receives alert and can accept/reject

### Accept/Reject Incoming Requests

1. **Check**: "Pending Alteration Requests" panel at top
2. **For Each Request**:
   - **Review**: Requester name and reason
   - **Click**: "Accept" or "Reject"
3. **If Accepted**: Your timetable updates immediately
4. **If Rejected**: Request canceled, requester keeps original period

### Fill an Empty Slot

1. **Find**: Empty period (Yellow status)
2. **Click Button**: "Add Class"
3. **In Modal**:
   - **Class Name**: Type subject (e.g., "Mathematics")
   - **Read Note**: "Admin locked - You cannot delete"
4. **Click**: "Add Class"
5. **Status**: Changes to "Self-Added" (locked)

---

## Workflow Examples

### Example 1: Simple Period Swap

**Initial State**:
- Staff A: Period 3 = Math
- Staff B: Period 3 = Empty

**Action**:
1. Staff A → Request Alteration → Target: Staff B
2. Staff B → Receives notification
3. Staff B → Click "Accept"

**Result**:
- Staff A: Period 3 = Empty
- Staff B: Period 3 = Math
- Both see updated timetables

---

### Example 2: Admin Override

**Initial State**:
- Staff C: Period 5 = Science (ABSENT)

**Admin Action**:
1. Admin → Timetable Management
2. Find Staff C's Period 5 assignment
3. Click "Re-assign"
4. Select Staff D (replacement)
5. Click "Process"

**Result**:
- Staff C: Period 5 = reverted
- Staff D: Period 5 = Science (INSTANT - no acceptance needed)
- Both receive notifications

---

### Example 3: Department Lock Impact

**Setup**:
- Library Dept: "Can Send Requests" = OFF

**Librarian's Experience**:
1. Opens Timetable
2. "Request Change" button = NOT VISIBLE
3. Can still see timetable and fill empty slots

**Math Teacher's Experience**:
1. Opens "Request Alteration"
2. "Target Department" dropdown
3. "Library" = MISSING from list
4. Cannot select library staff as swap targets

---

## Status Indicators

| Status | Color | Meaning | Action |
|--------|-------|---------|--------|
| Assigned | Blue | Regular assignment | Can request alteration (if not locked) |
| Empty | Yellow | No one assigned | Can add class to fill it |
| Locked | Red | Admin locked | Cannot modify |
| Self-Added | Cyan | You filled this slot | Locked (admin can delete) |
| Altered (Sent) | Purple | Pending your request | Waiting for target response |
| Altered (Received) | Purple | Someone requested your period | You must accept/reject |

---

## Permission Matrix

### Department Permissions

**Scenario 1**: Library with both unchecked
- Librarians: Cannot request alterations (button hidden)
- Others: Cannot select Library as target (not in dropdown)
- Result: Library completely isolated

**Scenario 2**: PE with "Send Requests" OFF, "Receive Requests" ON
- PE Staff: Cannot initiate requests
- Other Staff: Can select PE staff as swap targets
- Result: PE can accept but cannot request

**Scenario 3**: Math with both checked (normal)
- Math Staff: Can request alterations
- Other Staff: Can select Math staff as targets
- Result: Full participation in swapping

---

## Troubleshooting

### "Request Alteration button is hidden"
→ Your department has alteration requests disabled by admin

### "Cannot select Department X in dropdown"
→ Department X has inbound requests disabled

### "Cannot delete my self-added class"
→ It's admin-locked by design (prevents false attendance claims)

### "My period didn't swap after accepting"
→ Refresh page, system syncs all changes

### "Timetable menu not visible"
→ School admin must enable module in company settings first

---

## Tips & Best Practices

1. **Check Notifications**: Regularly check for pending alteration requests
2. **Plan Ahead**: Request alterations early before the day
3. **Document Reason**: Always provide reason for requests (helps admin review)
4. **Department Coordination**: Talk to staff before requesting swaps
5. **Fill Slots Early**: Claim empty slots early to avoid conflicts
6. **Admin Review**: Admins should periodically review alteration history

---

## Keyboard Shortcuts

- **Tab Key**: Navigate modals quickly
- **Enter**: Submit form in modals
- **Escape**: Close modals

---

## Contact & Support

For issues:
1. Take screenshot of the problem
2. Note the time and date
3. Contact your administrator

---

**Last Updated**: January 22, 2026
**Version**: 1.0
