# 📚 Timetable System - Complete Database Setup

## ✅ Database Status

**Population Complete!**

```
✅ 5 Schools (Real data)
✅ 5 Admins
✅ 120 Staff Members
✅ 40 Departments (8 per school)
✅ 48 Time Periods (8 per school)
✅ 720 Timetable Assignments
```

---

## 🏫 Schools in Database

| ID | School Name | Location | Email | Phone |
|:--:|------------|----------|-------|-------|
| 2 | Central High School | 123 Main Street, Downtown | admin@centralhs.edu | 555-0001 |
| 3 | St. Mary's Academy | 456 Oak Avenue, North Side | info@stmaryacademy.edu | 555-0002 |
| 4 | Lincoln University Prep | 789 Elm Road, East District | support@lincolnprep.edu | 555-0003 |
| 5 | Valley Middle School | 321 Pine Lane, West Valley | contact@valleymiddle.edu | 555-0004 |
| 6 | Harbor Technical Institute | 654 Beach Boulevard, Waterfront | admin@harbortech.edu | 555-0005 |

---

## 🔑 Admin Credentials

**All admins use password**: `test123`

| Username | School | Full Name |
|----------|--------|-----------|
| `admin1` | Central High School | Principal 1 |
| `admin2` | St. Mary's Academy | Principal 2 |
| `admin3` | Lincoln University Prep | Principal 3 |
| `admin4` | Valley Middle School | Principal 4 |
| `admin5` | Harbor Technical Institute | Principal 5 |

### Login as Admin
```
URL: http://localhost:5500
Username: admin1 (or admin2, admin3, admin4, admin5)
Password: test123
```

---

## 👥 Staff Members (Sample)

Each school has **120 staff members** organized by department:
- **Departments**: English, Mathematics, Science, History, Physical Education, Arts, Technology, Library
- **Positions**: Teacher, Senior Teacher, Department Head, Lecturer
- **3 staff per department per school**

### Sample Staff (Central High School)

| ID | Name | Department | Position | Email |
|----|------|-----------|----------|-------|
| 1 | Sarah Johnson | English | Senior Teacher | sarah.johnson@centralhs.edu |
| 2 | Michael Johnson | English | Department Head | michael.johnson@centralhs.edu |
| 3 | Emma Johnson | English | Lecturer | emma.johnson@centralhs.edu |
| 4 | Sarah Williams | Mathematics | Senior Teacher | sarah.williams@centralhs.edu |
| 5 | Michael Williams | Mathematics | Department Head | michael.williams@centralhs.edu |
| ... | ... | ... | ... | ... |

### Login as Staff
```
URL: http://localhost:5500
Username: Staff ID (e.g., 2-01-01, 2-02-01, etc.)
Password: test123
```

**Staff ID Format**: `{school_id}-{department_id:02d}-{staff_index:02d}`
- Example: `2-01-01` = School 2, English (dept 1), Staff 1
- Example: `3-05-02` = School 3, Science (dept 5), Staff 2

---

## 📊 Departments in Each School

All schools have these **8 departments**:

| Dept ID | Department | Staff Count |
|---------|-----------|-------------|
| 1 | English | 3 |
| 2 | Mathematics | 3 |
| 3 | Science | 3 |
| 4 | History | 3 |
| 5 | Physical Education | 3 |
| 6 | Arts | 3 |
| 7 | Technology | 3 |
| 8 | Library | 3 |

---

## ⏰ Time Periods (All Schools)

Standard schedule for all schools:

| Period | Name | Start Time | End Time | Duration |
|--------|------|-----------|----------|----------|
| 1 | Period 1 | 09:00 | 09:45 | 45 min |
| 2 | Period 2 | 09:45 | 10:30 | 45 min |
| 3 | Period 3 | 10:30 | 11:15 | 45 min |
| 4 | Period 4 | 11:15 | 12:00 | 45 min |
| 5 | Lunch | 12:00 | 12:45 | 45 min |
| 6 | Period 5 | 12:45 | 13:30 | 45 min |
| 7 | Period 6 | 13:30 | 14:15 | 45 min |
| 8 | Period 7 | 14:15 | 15:00 | 45 min |

---

## 🎯 How to Use the System

### Step 1: Start Flask Application
```bash
python app.py
```

### Step 2: Access in Browser
```
http://localhost:5500
```

### Step 3: Choose Your Role

#### As Admin
1. Login with: `admin1` / `test123`
2. Go to: **Sidebar → Timetable Management**
3. You can:
   - ✅ View/configure time periods
   - ✅ Set department permissions
   - ✅ View staff assignments
   - ✅ Override assignments (admin only)

#### As Staff
1. Login with: `2-01-01` / `test123` (English dept staff)
2. Go to: **Sidebar → My Timetable**
3. You can:
   - ✅ View personal weekly schedule
   - ✅ Request alterations from peers
   - ✅ Accept/reject requests
   - ✅ Add classes to empty slots

---

## 🔍 Database Overview

### Record Counts
- **Schools**: 5
- **Admins**: 5 (1 per school)
- **Staff**: 120 (24 per school)
- **Time Periods**: 48 (8 per school)
- **Timetable Assignments**: 720 (144 per school)
- **Department Permissions**: 40 (8 per school)

### Database File
```
Location: D:\VISHNRX\ProjectVX\instance\vishnorex.db
Size: ~250 KB
Tables: 32 (including 6 timetable tables)
```

---

## 🧪 Test Scenarios

### Scenario 1: Admin Configures Timetable
1. Login as `admin1` → Central High School
2. Go to Timetable Management
3. View 8 pre-configured periods
4. Check department permissions (all enabled)
5. View 24 staff assignments

### Scenario 2: Staff Views Schedule
1. Login as `2-01-01` (English staff at Central High)
2. Go to "My Timetable"
3. See personal weekly schedule
4. See 4-6 assigned periods

### Scenario 3: Request Alteration
1. On personal timetable
2. Click assigned period
3. Click "Request Change"
4. Select another staff member
5. Submit request
6. Admin can accept/reject or override

### Scenario 4: Multi-School Management
1. Login as `admin1` → manage Central High School timetable
2. Logout and login as `admin2` → manage St. Mary's Academy
3. Each school has isolated data

---

## 📝 Script Commands

### Show All Database Data
```bash
python show_database.py
```

### Populate Database (Already Done)
```bash
python populate_db.py
```

### Verify System Status
```bash
python verify_timetable.py
python final_status.py
```

### Check Database Health
```bash
python check_all_dbs.py
```

---

## ✨ Quick Start Command

```bash
# 1. Populate database (if not done)
python populate_db.py

# 2. Start Flask app
python app.py

# 3. In browser, go to:
http://localhost:5500

# 4. Login with:
Username: admin1
Password: test123

# 5. Access:
Sidebar → Timetable Management
```

---

## 🎓 Test Credentials Summary

### Admin Access
- **Username**: admin1 to admin5
- **Password**: test123
- **Access**: Timetable Management tab

### Staff Access
- **Username**: Format is {school_id}-{dept_id}-{staff_num}
  - Example: `2-01-01` (School 2, English, Staff 1)
  - Example: `3-05-02` (School 3, PE, Staff 2)
  - Example: `4-03-03` (School 4, Science, Staff 3)
- **Password**: test123
- **Access**: My Timetable tab

### Company Admin Access
- Currently configured for school selection
- Can enable/disable timetable module per school

---

## 🚀 System Ready!

**Everything is now in place:**
- ✅ 5 real schools with data
- ✅ 120 staff members
- ✅ 8 departments per school
- ✅ Timetable assignments created
- ✅ All permissions configured
- ✅ Ready for testing

**Start the app and login with the credentials above!**

