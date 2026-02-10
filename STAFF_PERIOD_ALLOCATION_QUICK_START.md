# STAFF PERIOD ALLOCATION MANAGER - QUICK START GUIDE

## 🚀 Getting Started

### Location
**Admin Dashboard → Timetable Management → Staff Period Allocation Manager**

### Access Requirements
- Admin or Timetable Manager role
- Valid school login
- Permission to manage staff allocations

---

## 📋 Step-by-Step Usage

### Step 1️⃣: SELECT STAFF MEMBER

```
1. Look for "Step 1: Select Staff Member" section
2. Click the "Staff Member" dropdown
3. Choose a staff member from the list
4. Wait 1 second for interface to enable
5. You'll see staff info appear above
```

**What You'll See**:
```
┌─────────────────────────────────┐
│ Step 1: Select Staff Member  🔵 │
├─────────────────────────────────┤
│ Staff Member: [John Smith ▼]    │
├─────────────────────────────────┤
│ Info: John Smith (ID: 45)       │
│ Department: Science             │
│ Position: Teacher               │
└─────────────────────────────────┘
```

---

### Step 2️⃣: ALLOCATE PERIOD

```
1. Look for "Step 2: Allocate Period" section
2. Select a Day from dropdown
   - Choose: Monday, Tuesday, Wednesday, etc.
3. Select a Period from dropdown
   - Choose: Period 1, Period 2, Period 3, etc.
4. Click "Add Period" button
5. You'll see success message
```

**What You'll See**:
```
┌─────────────────────────────────┐
│ Step 2: Allocate Period      🔵 │
├─────────────────────────────────┤
│ Day: [Monday ▼]                 │
│ Period: [Period 1 ▼]            │
│ [Add Period]                    │
│                                 │
│ ✓ Period successfully allocated │
│   to John Smith                 │
└─────────────────────────────────┘
```

---

### Step 3️⃣: MANAGE ALLOCATIONS

```
1. Look for "Step 3: Current Period Allocations" section
2. View all allocated periods in table
3. To Delete:
   - Click "Delete" button for that period
   - Confirm deletion in popup
   - Period is immediately removed
```

**What You'll See**:
```
┌────────────────────────────────┐
│ Step 3: Current Allocations 🔵 │
├────────────────────────────────┤
│ Day         │ Period    │ Del  │
├─────────────┼───────────┼──────┤
│ Monday      │ Period 1  │ [X]  │
│ Monday      │ Period 3  │ [X]  │
│ Wednesday   │ Period 2  │ [X]  │
│ Friday      │ Period 4  │ [X]  │
└────────────────────────────────┘
```

---

## ⚡ Quick Examples

### Example 1: Allocate Single Period
```
Scenario: Add Period 1 (9 AM) on Monday for teacher John

Steps:
1. Select Staff: John Smith
2. Day: Monday
3. Period: Period 1 (09:00-10:00)
4. Click "Add Period"
5. Table shows: Monday | Period 1 | [Delete]
```

### Example 2: Allocate Multiple Periods
```
Scenario: Set full schedule for teacher Sarah (4 periods/day)

Steps:
1. Select Staff: Sarah Johnson
2. Add Monday Period 1 → Success
3. Add Monday Period 2 → Success
4. Add Monday Period 3 → Success
5. Add Monday Period 4 → Success
6. Repeat for other days as needed
```

### Example 3: Remove Period Allocation
```
Scenario: Remove Thursday Period 3 from teacher Mike

Steps:
1. Select Staff: Mike Brown
2. Scroll to "Step 3: Current Allocations"
3. Find row: Thursday | Period 3
4. Click [Delete] button
5. Click "Yes" in confirmation dialog
6. Row disappears from table
```

---

## ✓ Validation Rules

### Required Fields
- ✅ Staff member MUST be selected
- ✅ Day MUST be selected
- ✅ Period MUST be selected

### Duplicate Prevention
```
❌ Cannot allocate same period twice
   Example: Monday Period 1 + Monday Period 1 = ERROR
   
✅ Different periods same day is OK
   Example: Monday Period 1 + Monday Period 2 = OK

✅ Same period different days is OK
   Example: Monday Period 1 + Tuesday Period 1 = OK
```

### Constraints
- Can allocate max 8 periods per day (if 8 periods exist)
- Can allocate to multiple different staff
- Can allocate same period to different staff

---

## 🔔 Messages Guide

### Success Messages ✓
```
"✓ Period successfully allocated to John Smith"
→ Action completed successfully
→ Table will auto-refresh
```

### Warning Messages ⚠️
```
"⚠ Period already allocated for this day!"
→ You tried to add same period twice
→ Choose a different period

"⚠ Please select all required fields"
→ You forgot to select staff, day, or period
→ Check all dropdowns are filled
```

### Error Messages ✗
```
"✗ Failed to save allocation"
→ Server error occurred
→ Check your connection
→ Refresh page if problem persists

"✗ Staff member not found"
→ Selected staff doesn't exist
→ Choose another staff member
```

---

## 🎯 Common Tasks

### Task 1: Set Weekly Schedule
**Goal**: Allocate 5 periods for entire week

```
Staff: Teacher A
Monday:   Period 1 (Add) ✓
Tuesday:  Period 2 (Add) ✓
Wednesday: Period 3 (Add) ✓
Thursday:  Period 4 (Add) ✓
Friday:    Period 5 (Add) ✓

View in Step 3 table - all 5 periods show
```

### Task 2: Switch Staff Allocations
**Goal**: Change allocations for different staff

```
Current: John (Staff A)
1. Look at John's allocations in Step 3
2. Click [Delete] for each period
3. Select different staff: Jane (Staff B)
4. Add her periods using Step 2
5. Confirm Jane's allocations in Step 3
```

### Task 3: View All Allocations
**Goal**: See current allocations for a teacher

```
1. Select Staff Member from dropdown
2. Automatically loads Step 3 table
3. Table shows all periods for that staff
4. No additional action needed
```

### Task 4: Clear All Allocations
**Goal**: Remove all periods for a staff member

```
1. Select Staff Member
2. See all allocations in Step 3
3. Click [Delete] for FIRST period
4. Confirm deletion
5. Repeat for each period
6. When done: "No allocations found"
```

---

## 🔍 Troubleshooting

### Problem: Dropdown is Empty
**Solution**:
```
1. Refresh page (Ctrl+F5)
2. Check your internet connection
3. Logout and login again
4. Contact admin if issue persists
```

### Problem: "Period already allocated" message
**Solution**:
```
1. Check Step 3 table
2. You already added this period
3. Choose a different period
4. Or delete the existing allocation first
```

### Problem: Changes Not Saving
**Solution**:
```
1. Check internet connection
2. Refresh page (Ctrl+F5)
3. Try again
4. If still failing: Check with IT support
```

### Problem: Table Not Updating
**Solution**:
```
1. Wait 2 seconds (auto-refresh)
2. If still not updated: Refresh page
3. Select staff member again
4. Table should reload
```

### Problem: Delete Not Working
**Solution**:
```
1. Confirm popup appeared (click "Yes")
2. Check deletion succeeded (message shown)
3. Refresh page if needed
4. Select staff again to see updated list
```

---

## ⏱️ Timing Tips

| Action | Time | Notes |
|--------|------|-------|
| Select staff | Instant | Interface enables immediately |
| Add period | < 1 sec | Table refreshes automatically |
| Delete period | < 1 sec | Confirmation popup appears first |
| Load allocations | < 2 sec | Shows current allocations |
| Page load | < 3 sec | Full interface ready |

---

## 📱 Mobile Usage

**Supported**: Yes (Responsive design)
**Screen Sizes**: 320px to 2560px

### Mobile Tips
```
✓ Use portrait orientation (better)
✓ Tap dropdown to open options
✓ Scroll table to see all columns
✓ Pinch to zoom if needed
✓ All features work on mobile
```

---

## 🔐 Permissions

**Who Can Use**:
- ✅ Admin
- ✅ Timetable Manager
- ✅ Head of Department (with permission)

**Who Cannot Use**:
- ❌ Teachers
- ❌ Staff (non-admin)
- ❌ Students
- ❌ Parents

**To Request Access**: Contact your administrator

---

## 💡 Best Practices

### ✓ DO's
```
✓ Allocate periods at start of semester
✓ Review allocations weekly
✓ Update when staff availability changes
✓ Use consistent scheduling patterns
✓ Document allocation decisions
✓ Test with backup/demo staff first
```

### ✗ DON'Ts
```
✗ Don't allocate same period to one staff twice
✗ Don't forget to save changes (auto-saved)
✗ Don't close browser during allocation
✗ Don't allocate without thinking
✗ Don't assign impossible schedules
✗ Don't modify during active classes
```

---

## 📞 Support

### Common Issues
- **Can't see feature?** → Check admin permissions
- **Allocations not saving?** → Check internet connection
- **Data looks wrong?** → Refresh page and try again
- **Feature crashed?** → Close and reopen browser

### Getting Help
```
1. Check this guide first
2. Review error message carefully
3. Try refreshing page
4. Contact IT Support
5. Provide: Screenshot + Steps to reproduce
```

---

## 📊 Keyboard Shortcuts

```
Tab           → Move between fields
Enter         → Confirm/Submit
Escape        → Cancel
Ctrl+F5       → Hard refresh
Space         → Toggle dropdown
Arrow keys    → Navigate dropdown
```

---

## Version & Support

| Item | Details |
|------|---------|
| Feature Name | Staff Period Allocation Manager |
| Version | 1.0 |
| Last Updated | 2026-02-10 |
| Status | Production Ready |
| Browser | All modern browsers |

---

## Quick Reference Card

```
┌──────────────────────────────────┐
│   STAFF PERIOD ALLOCATION        │
│   Quick Reference Card           │
├──────────────────────────────────┤
│ Step 1: Select Staff             │
│   └─ Choose from dropdown        │
│                                  │
│ Step 2: Allocate Period          │
│   ├─ Choose Day                  │
│   ├─ Choose Period               │
│   └─ Click "Add Period"          │
│                                  │
│ Step 3: View/Edit Allocations    │
│   ├─ See all allocations         │
│   ├─ Click "Delete" to remove    │
│   └─ Confirm in popup            │
│                                  │
│ Messages:                        │
│   ✓ = Success (Green)            │
│   ⚠ = Warning (Yellow)           │
│   ✗ = Error (Red)                │
│                                  │
│ Tips:                            │
│   • Use Tab to navigate          │
│   • Refresh (Ctrl+F5) if stuck   │
│   • Contact support for issues   │
└──────────────────────────────────┘
```

---

**Need more help?** Check the full [STAFF_PERIOD_ALLOCATION_ADMIN_GUIDE.md](STAFF_PERIOD_ALLOCATION_ADMIN_GUIDE.md) for detailed documentation.

*Quick Start Guide v1.0 - VishnoRex Staff Management*
