# HIERARCHICAL TIMETABLE SYSTEM - IMPLEMENTATION GUIDE

## Overview
This document provides frontend implementation guidance for the hierarchical timetable system supporting both School (Classes 1-12) and College (Years 1-4) modes with real-time conflict detection.

---

## 1. SYSTEM ARCHITECTURE

### Database Schema Hierarchy
```
Organization (School/College)
    ├── Academic Levels (Classes 1-12 OR Years 1-4)
    │   └── Sections (A, B, C, etc.)
    │       └── Timetable Slots (Day × Period)
    │           └── Staff Assignment
    └── Staff Members
        └── Availability Matrix (Day × Period)
            └── Conflict Detection
```

### Key Tables
- `timetable_organization_config` - Organization type (school/college)
- `timetable_academic_levels` - Classes/Years
- `timetable_sections` - Dynamic sections per level
- `timetable_hierarchical_assignments` - Staff-to-section assignments
- `timetable_staff_availability` - Staff unavailability tracking
- `timetable_conflict_logs` - Conflict alerts and resolutions

---

## 2. CONFLICT DETECTION LOGIC (CORE)

### The Overlap Check Query
```sql
WHERE PeriodID = X AND Day = Y AND (StaffID = Z OR SectionID = W)
```

### Three-Level Validation
1. **Staff Availability**: Is staff marked unavailable for this slot?
2. **Staff Conflicts**: Is staff already assigned elsewhere at same time?
3. **Section Conflicts**: Does section already have a teacher assigned?

### Return Conditions
```javascript
{
  success: true,
  is_available: true/false,
  conflicts: ["Class 10-A", "Class 11-B"],  // if conflicts exist
  reason: "Staff already assigned to..."
}
```

---

## 3. FRONTEND IMPLEMENTATION

### 3.1 ORGANIZATION MODE SELECTOR

**Location**: Admin Dashboard > Timetable Settings

```html
<div class="card">
  <h5>Organization Type</h5>
  <div class="btn-group">
    <button class="btn btn-outline-primary" onclick="setOrgType('school')">
      School (Classes 1-12)
    </button>
    <button class="btn btn-outline-primary" onclick="setOrgType('college')">
      College (Years 1-4)
    </button>
  </div>
</div>
```

**JavaScript Function**:
```javascript
async function setOrgType(type) {
  try {
    const response = await fetch('/api/hierarchical-timetable/organization/set-type', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ organization_type: type })
    });
    
    const result = await response.json();
    if (result.success) {
      alert(`Organization set to ${type}`);
      await loadAcademicLevels();
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

### 3.2 DYNAMIC LEVEL/SECTION MANAGEMENT

**Location**: Admin Dashboard > Academic Structure

#### Load Academic Levels
```javascript
async function loadAcademicLevels() {
  try {
    const response = await fetch('/api/hierarchical-timetable/levels');
    const result = await response.json();
    
    if (result.success) {
      const tbody = document.getElementById('levelsTableBody');
      tbody.innerHTML = '';
      
      result.data.forEach(level => {
        const row = tbody.insertRow();
        row.innerHTML = `
          <td>${level.level_name}</td>
          <td><button onclick="editLevel(${level.id})">Manage Sections</button></td>
        `;
      });
    }
  } catch (error) {
    console.error('Error loading levels:', error);
  }
}
```

#### Create Section for Level
```javascript
async function createSection(levelId) {
  const sectionName = prompt('Enter section name (e.g., A, B, Section A):');
  const capacity = prompt('Enter capacity:', '60');
  
  if (!sectionName) return;
  
  try {
    const response = await fetch('/api/hierarchical-timetable/sections/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        level_id: levelId,
        section_name: sectionName,
        capacity: parseInt(capacity)
      })
    });
    
    const result = await response.json();
    if (result.success) {
      alert(`Section ${sectionName} created!`);
      await loadSectionsForLevel(levelId);
    } else {
      alert('Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

#### Display All Sections
```javascript
async function loadAllSections() {
  try {
    const response = await fetch('/api/hierarchical-timetable/sections/all');
    const result = await response.json();
    
    if (result.success) {
      const tbody = document.getElementById('sectionsTableBody');
      tbody.innerHTML = '';
      
      result.data.forEach(section => {
        const row = tbody.insertRow();
        row.innerHTML = `
          <td>${section.level_name}</td>
          <td>${section.section_name}</td>
          <td>${section.capacity}</td>
          <td>
            <button onclick="assignStaffToSection(${section.id})">Assign Staff</button>
            <button onclick="viewSchedule(${section.id})">View Schedule</button>
          </td>
        `;
      });
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

### 3.3 CONFLICT DETECTION IN ASSIGNMENT UI

**Location**: Admin Panel > Assign Staff to Section

#### Assignment Form with Validation
```html
<div class="card">
  <h5>Assign Staff to Section</h5>
  
  <form id="assignmentForm">
    <!-- Section Selection -->
    <div class="form-group">
      <label>Section</label>
      <select id="sectionSelect" onchange="loadStaffAndPeriods()">
        <option value="">Select Section...</option>
      </select>
    </div>
    
    <!-- Staff Selection -->
    <div class="form-group">
      <label>Staff Member</label>
      <select id="staffSelect" onchange="checkAvailability()">
        <option value="">Select Staff...</option>
      </select>
    </div>
    
    <!-- Day Selection -->
    <div class="form-group">
      <label>Day</label>
      <select id="daySelect" onchange="checkAvailability()">
        <option value="">Select Day...</option>
        <option value="0">Sunday</option>
        <option value="1">Monday</option>
        <!-- ... -->
      </select>
    </div>
    
    <!-- Period Selection -->
    <div class="form-group">
      <label>Period</label>
      <select id="periodSelect" onchange="checkAvailability()">
        <option value="">Select Period...</option>
      </select>
    </div>
    
    <!-- Subject & Room (Optional) -->
    <div class="form-group">
      <label>Subject</label>
      <input type="text" id="subjectInput" placeholder="e.g., Mathematics">
    </div>
    
    <div class="form-group">
      <label>Room</label>
      <input type="text" id="roomInput" placeholder="e.g., A101">
    </div>
    
    <!-- Availability Alert -->
    <div id="availabilityAlert" class="alert alert-warning" style="display:none;"></div>
    
    <button type="button" onclick="submitAssignment()" class="btn btn-primary">
      Assign
    </button>
  </form>
</div>
```

#### Real-Time Conflict Checking
```javascript
async function checkAvailability() {
  const staffId = document.getElementById('staffSelect').value;
  const sectionId = document.getElementById('sectionSelect').value;
  const dayOfWeek = document.getElementById('daySelect').value;
  const periodNumber = document.getElementById('periodSelect').value;
  
  if (!staffId || !dayOfWeek || !periodNumber) return;
  
  try {
    // Check Staff Availability
    const staffCheck = await fetch('/api/hierarchical-timetable/check-staff-availability', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        staff_id: parseInt(staffId),
        day_of_week: parseInt(dayOfWeek),
        period_number: parseInt(periodNumber),
        section_id: parseInt(sectionId)
      })
    });
    
    const staffResult = await staffCheck.json();
    const alert = document.getElementById('availabilityAlert');
    
    if (!staffResult.is_available) {
      alert.innerHTML = `
        <strong>⚠️ Conflict Detected:</strong><br>
        ${staffResult.reason}
        ${staffResult.conflicts ? '<ul>' + staffResult.conflicts.map(c => `<li>${c}</li>`).join('') + '</ul>' : ''}
      `;
      alert.style.display = 'block';
      alert.classList.add('alert-danger');
      alert.classList.remove('alert-success');
      return false;
    }
    
    // Check Section Availability
    const sectionCheck = await fetch('/api/hierarchical-timetable/check-section-availability', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        section_id: parseInt(sectionId),
        day_of_week: parseInt(dayOfWeek),
        period_number: parseInt(periodNumber)
      })
    });
    
    const sectionResult = await sectionCheck.json();
    
    if (!sectionResult.is_available) {
      alert.innerHTML = `
        <strong>⚠️ Section Conflict:</strong><br>
        ${sectionResult.reason}
      `;
      alert.style.display = 'block';
      alert.classList.add('alert-danger');
      alert.classList.remove('alert-success');
      return false;
    }
    
    // All checks passed
    alert.innerHTML = '✅ All availability checks passed';
    alert.style.display = 'block';
    alert.classList.add('alert-success');
    alert.classList.remove('alert-danger');
    return true;
    
  } catch (error) {
    console.error('Error checking availability:', error);
  }
}
```

#### Submit Assignment
```javascript
async function submitAssignment() {
  const isAvailable = await checkAvailability();
  if (!isAvailable) {
    alert('Cannot proceed: Conflicts detected');
    return;
  }
  
  const staffId = document.getElementById('staffSelect').value;
  const sectionId = document.getElementById('sectionSelect').value;
  const dayOfWeek = document.getElementById('daySelect').value;
  const periodNumber = document.getElementById('periodSelect').value;
  const subject = document.getElementById('subjectInput').value;
  const room = document.getElementById('roomInput').value;
  
  // Get level_id from section data
  const levelId = document.getElementById('sectionSelect').options
    [document.getElementById('sectionSelect').selectedIndex].dataset.levelId;
  
  try {
    const response = await fetch('/api/hierarchical-timetable/assign-staff', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        staff_id: parseInt(staffId),
        section_id: parseInt(sectionId),
        level_id: parseInt(levelId),
        day_of_week: parseInt(dayOfWeek),
        period_number: parseInt(periodNumber),
        subject_name: subject,
        room_number: room
      })
    });
    
    const result = await response.json();
    if (result.success) {
      alert('✅ Staff assigned successfully!');
      document.getElementById('assignmentForm').reset();
      await loadAllSections();
    } else {
      alert('❌ Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

### 3.4 COLOR-CODED GRID DISPLAY

**Location**: Staff View & Admin View

#### Grid Structure (7 Days × 8 Periods)
```html
<div class="timetable-grid">
  <table class="table table-bordered">
    <thead>
      <tr>
        <th>Period</th>
        <th>Monday</th>
        <th>Tuesday</th>
        <!-- ... -->
      </tr>
    </thead>
    <tbody id="gridBody"></tbody>
  </table>
</div>
```

#### Color Coding Schema
```javascript
const CELL_COLORS = {
  free: '#90EE90',       // Light Green
  occupied: '#87CEEB',   // Sky Blue
  locked: '#FF6B6B',     // Red
  conflict: '#FFD700',   // Gold
  unavailable: '#808080' // Gray
};
```

#### Generate Grid
```javascript
async function generateColorCodedGrid(itemType, itemId) {
  try {
    const response = await fetch(`/api/hierarchical-timetable/grid/${itemType}/${itemId}`);
    const result = await response.json();
    
    if (result.success) {
      const grid = result.data;
      const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const tbody = document.getElementById('gridBody');
      tbody.innerHTML = '';
      
      for (let period = 1; period <= 8; period++) {
        let row = `<tr><td><strong>Period ${period}</strong></td>`;
        
        for (let dayIdx = 0; dayIdx < 7; dayIdx++) {
          const day = DAYS[dayIdx];
          const cell = grid[day][period];
          
          row += `
            <td style="background-color: ${cell.color}; min-height: 60px;">
              <div style="padding: 8px; font-size: 12px;">
                <strong>${cell.subject || '-'}</strong><br>
                ${cell.staff || cell.section || '-'}<br>
                <span style="font-size: 10px;">${cell.status}</span>
              </div>
            </td>
          `;
        }
        
        row += '</tr>';
        tbody.innerHTML += row;
      }
    }
  } catch (error) {
    console.error('Error generating grid:', error);
  }
}
```

---

### 3.5 STAFF-SPECIFIC VIEW

**Location**: Staff Dashboard

#### Load Staff Schedule
```javascript
async function loadStaffSchedule(staffId) {
  try {
    const response = await fetch(`/api/hierarchical-timetable/staff-schedule/${staffId}`);
    const result = await response.json();
    
    if (result.success) {
      const data = result.data;
      
      // Display schedule table
      const tbody = document.getElementById('scheduleTableBody');
      tbody.innerHTML = '';
      
      data.schedule.forEach(slot => {
        const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const row = tbody.insertRow();
        
        row.innerHTML = `
          <td>${DAYS[slot.day_of_week]}</td>
          <td>Period ${slot.period_number}</td>
          <td>${slot.start_time.slice(0,5)} - ${slot.end_time.slice(0,5)}</td>
          <td>${slot.level_name} - ${slot.section_name}</td>
          <td>${slot.subject_name || '-'}</td>
          <td>${slot.room_number || '-'}</td>
          <td>
            <span class="badge ${slot.is_locked ? 'bg-danger' : 'bg-success'}">
              ${slot.is_locked ? 'Locked' : 'Active'}
            </span>
          </td>
        `;
      });
      
      // Show conflicts if any
      if (data.conflict_count > 0) {
        document.getElementById('conflictAlert').innerHTML = `
          ⚠️ ${data.conflict_count} scheduling conflict(s) detected
        `;
        document.getElementById('conflictAlert').style.display = 'block';
      }
      
      // Generate color-coded grid
      await generateColorCodedGrid('staff', staffId);
    }
  } catch (error) {
    console.error('Error loading staff schedule:', error);
  }
}
```

---

### 3.6 CLASS/SECTION-SPECIFIC VIEW

**Location**: Class/Section Management Dashboard

#### Load Section Schedule
```javascript
async function loadSectionSchedule(sectionId) {
  try {
    const response = await fetch(`/api/hierarchical-timetable/section-schedule/${sectionId}`);
    const result = await response.json();
    
    if (result.success) {
      const data = result.data;
      
      // Display section info
      document.getElementById('sectionInfo').innerHTML = `
        <h5>${data.section_info.level_name} - ${data.section_info.section_name}</h5>
        <p>Capacity: ${data.section_info.capacity} students</p>
      `;
      
      // Display schedule table
      const tbody = document.getElementById('classScheduleTableBody');
      tbody.innerHTML = '';
      
      data.schedule.forEach(slot => {
        const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const row = tbody.insertRow();
        
        row.innerHTML = `
          <td>${DAYS[slot.day_of_week]}</td>
          <td>Period ${slot.period_number}</td>
          <td>${slot.start_time.slice(0,5)} - ${slot.end_time.slice(0,5)}</td>
          <td><strong>${slot.staff_name}</strong></td>
          <td>${slot.subject_name}</td>
          <td>${slot.room_number || '-'}</td>
        `;
      });
      
      // Generate color-coded grid
      await generateColorCodedGrid('section', sectionId);
    }
  } catch (error) {
    console.error('Error loading section schedule:', error);
  }
}
```

---

## 4. API ENDPOINTS SUMMARY

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/hierarchical-timetable/organization/set-type` | Set school/college mode |
| GET | `/api/hierarchical-timetable/organization/config` | Get organization config |
| GET | `/api/hierarchical-timetable/levels` | Get all academic levels |
| POST | `/api/hierarchical-timetable/sections/create` | Create section |
| GET | `/api/hierarchical-timetable/sections/all` | Get all sections |
| POST | `/api/hierarchical-timetable/check-staff-availability` | Check conflicts (CORE) |
| POST | `/api/hierarchical-timetable/check-section-availability` | Check section conflicts |
| POST | `/api/hierarchical-timetable/assign-staff` | Assign staff (with validation) |
| DELETE | `/api/hierarchical-timetable/assignment/<id>` | Delete assignment |
| GET | `/api/hierarchical-timetable/staff-schedule/<id>` | Get staff view |
| GET | `/api/hierarchical-timetable/section-schedule/<id>` | Get class view |
| GET | `/api/hierarchical-timetable/grid/<type>/<id>` | Get color-coded grid |

---

## 5. EXAMPLE WORKFLOW

### Step 1: Set Organization Type
```javascript
await setOrgType('school');  // Generates Class 1-12
```

### Step 2: Create Sections for Each Class
```javascript
await createSection(levelId=1, sectionName='A', capacity=60);
await createSection(levelId=1, sectionName='B', capacity=60);
```

### Step 3: Assign Staff (with Conflict Detection)
1. Select Section → Triggers `/check-staff-availability`
2. Select Staff & Time → Real-time validation
3. System prevents double-booking
4. Assignment created on approval

### Step 4: View Schedules
- **Admin**: Sees all assignments with edit/delete options
- **Staff**: Sees their own schedule + color-coded grid
- **Students**: View their class schedule

---

## 6. TESTING CHECKLIST

- [ ] Organization type toggle (School ↔ College)
- [ ] Dynamic level generation (12 vs 4)
- [ ] Section creation for each level
- [ ] Conflict detection prevents double-booking
- [ ] Staff cannot be in 2 classes same period
- [ ] Section cannot have 2 teachers same period
- [ ] Color-coded grid displays correctly
- [ ] Staff view shows only their assignments
- [ ] Class view shows only that class's schedule
- [ ] Admin can delete assignments
- [ ] Locked assignments prevent deletion
- [ ] Mobile responsiveness

---

## 7. DEPLOYMENT NOTES

1. **Database Migration**: Run `python -c "from database import init_db; from app import app; init_db(app)"`
2. **Register Routes**: Hierarchical blueprint already registered in app.py
3. **Session Management**: Requires `school_id` and `user_id` in session
4. **Permissions**: Admin endpoints use `@check_admin_auth` decorator

---

**Version**: 1.0
**Last Updated**: 2026-02-09
**Status**: Implementation Ready
