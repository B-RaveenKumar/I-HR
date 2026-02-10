# Timetable System - Quick Access Guide

## ✅ System Status
- **Database Tables**: 6 tables created ✓
- **Routes**: 15 endpoints registered ✓
- **Timetable Enabled**: School ID 4 ✓
- **Sample Periods**: 8 periods configured ✓

---

## 🔓 How to Access Timetable Features

### 1️⃣ **Admin Dashboard** (School Admin Access)
- **URL**: `http://localhost:5500/admin/timetable`
- **Required Role**: School Admin
- **Features**:
  - ✓ Configure periods (add/edit/delete)
  - ✓ Set department permissions
  - ✓ View staff assignments
  - ✓ Override assignments (admin only)

### 2️⃣ **Staff Timetable** (Staff Access)  
- **URL**: `http://localhost:5500/staff/timetable`
- **Required Role**: Staff member
- **Features**:
  - ✓ View personal weekly timetable
  - ✓ Request alteration from peers
  - ✓ Accept/reject alteration requests
  - ✓ Add self-allocation to empty slots
  - ✓ See pending requests

### 3️⃣ **Company Admin Settings** (Super Admin Access)
- **URL**: `http://localhost:5500/company/timetable_settings/<school_id>`
- **Required Role**: Company Admin
- **Features**:
  - ✓ Enable/disable timetable for schools
  - ✓ Control module access

---

## 🎯 Quick Test Scenario

### Step 1: Login as School Admin
1. Start Flask app: `python app.py`
2. Navigate to: `http://localhost:5500`
3. Login with admin credentials
4. Go to: **Sidebar → Timetable Management**

### Step 2: Configure Periods (Already Done!)
- 8 periods are already configured:
  - Period 1: 09:00-09:45
  - Period 2: 09:45-10:30
  - ... (etc)
  - Period 7: 14:15-15:00

### Step 3: Set Department Permissions
- On **"Department Permissions"** tab
- Enable alterations for departments
- Save

### Step 4: Create Staff Assignments
- On **"Staff Assignments"** tab
- Select staff member
- Assign to periods

### Step 5: Login as Staff
1. Logout from admin
2. Login as staff member
3. Go to: **Sidebar → My Timetable**
4. View your assignments
5. Try requesting alterations or adding classes

---

## 🔍 Navigation Links (Added to Sidebars)

### Admin Sidebar
```
📋 Main Menu
├── Dashboard
├── Staff Management
├── Attendance
├── ...
├── ⭐ Timetable Management  ← Click here
├── Salary Management
└── Settings
```

### Staff Sidebar
```
📋 My Menu
├── Dashboard
├── Profile
├── Attendance
├── Pay Slip
├── ⭐ My Timetable  ← Click here
└── Settings
```

---

## 🐛 Troubleshooting

### "Timetable link not showing"
**Solution**: Timetable must be enabled first
1. Login as **Company Admin**
2. Go to school details
3. Click **"Timetable Settings"**
4. Toggle **ON**
5. Save

### "Permission Denied" error
**Solution**: Check your login role
- Company Admin: Can enable/disable for schools
- School Admin: Can configure periods and settings
- Staff: Can only view and request changes

### "Period not showing in timetable"
**Solution**: Add periods first
1. Login as School Admin
2. Go to **Timetable Management**
3. Click **"Period Configuration"** tab
4. Add periods with times
5. Save

### "Can't request alteration"
**Solution**: Check department permissions
1. Go to **"Department Permissions"** tab
2. Ensure both:
   - ✓ "Can Send Requests" is checked
   - ✓ "Can Receive Requests" is checked for target department

---

## 📊 Database Status

**Current Configuration**:
- School ID: 4
- Status: ENABLED
- Periods: 8 configured
- Tables: All created and ready

**To verify in Flask shell**:
```python
flask shell
>>> from timetable_manager import TimetableManager
>>> TimetableManager.is_timetable_enabled(4)
True
>>> periods = TimetableManager.get_periods(4)
>>> len(periods)
8
```

---

## 🚀 Next Steps

1. ✅ Database initialized
2. ✅ Routes registered
3. ✅ Sample data loaded
4. **→ Start the app**: `python app.py`
5. **→ Test navigation**: Click "Timetable Management" link
6. **→ Configure staffing**: Add staff to periods
7. **→ Test workflows**: Try requesting alterations as staff

---

## 📞 Support

If timetable menu is still not visible:
1. Run: `python init_timetable.py` again
2. Check browser cache: Clear cache and refresh
3. Verify login role matches your intended access level
4. Check database: `python verify_timetable.py`

