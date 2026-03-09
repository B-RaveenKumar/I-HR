# Student Portal Quick Start Guide 🚀

## 1. Run the Application
```bash
python app.py
```
The database tables will be created automatically.

## 2. Add Sample Students
```bash
python add_sample_students.py
```
This will create 5 test students with the following credentials:

### Test Student Accounts:
| Student ID | Name | Class | Password |
|------------|------|-------|----------|
| STU001 | Rahul Kumar | 10th-A | password123 |
| STU002 | Priya Sharma | 10th-A | password123 |
| STU003 | Arjun Patel | 10th-B | password123 |
| STU004 | Sneha Reddy | 10th-B | password123 |
| STU005 | Vikram Singh | 9th-A | password123 |

## 3. Access Student Portal
Open your browser and navigate to:
```
http://localhost:5500/student/login
```

## 4. Login as Student
1. Select your institution from dropdown
2. Enter Student ID (e.g., `STU001`)
3. Enter Password: `password123`
4. Click "Sign In"

## 5. Mark Student Attendance (Staff)
1. Login as admin or staff: `http://localhost:5500`
2. Navigate to "Mark Student Attendance" in the menu
3. Select a student, date, session (morning/afternoon), and status
4. Click "Mark Attendance"

## 6. View Attendance (Student)
1. Login to student portal
2. Dashboard shows today's attendance
3. Check "Attendance History" for past 30 days

## 7. Change Theme
Click any theme button in the top bar:
- 🤍 Light Theme
- 🖤 Dark Theme
- 💙 Blue Theme
- 💚 Green Theme

Theme changes instantly and saves automatically!

## Features Summary

### ✅ Student Portal
- Modern login page
- Dashboard with morning & afternoon attendance
- 4 customizable themes
- Attendance history (30 days)
- Student profile page

### ✅ Staff Interface
- Mark attendance for any student
- Choose morning or afternoon session
- Set status (present/absent/late/leave)
- Add notes for each session
- View today's marked attendance

### ✅ Database Integration
- Uses existing database (no separate DB)
- Integrated with schools and staff tables
- Dual-session attendance tracking
- Theme preference persistence

## File Locations

All student portal files are in:
```
templates/student/
├── student_login.html
├── student_dashboard.html
├── student_attendance_history.html
├── student_profile.html
└── mark_student_attendance.html
```

## URLs

| Page | URL | Access |
|------|-----|--------|
| Student Login | `/student/login` | Public |
| Student Dashboard | `/student/dashboard` | Students only |
| Attendance History | `/student/attendance-history` | Students only |
| Student Profile | `/student/profile` | Students only |
| Mark Attendance | `/staff/mark-student-attendance` | Staff/Admin |

## Need Help?

Check [STUDENT_PORTAL_IMPLEMENTATION.md](STUDENT_PORTAL_IMPLEMENTATION.md) for complete documentation.

---

**Ready to use! 🎉**
