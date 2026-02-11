# Advanced Timetable Management System - Complete Implementation Plan

## 📋 **Project Overview**

A modular, hierarchical timetable management system with three access levels:
- **Level 1 (Company Admin)**: Controls feature access per school
- **Level 2 (School Admin)**: Configures periods, manages permissions, performs overrides
- **Level 3 (Staff)**: Views schedule, handles peer swaps, self-allocates to empty slots

### **NEW FEATURE**: Many-Class Allocation
A single staff member can be assigned to **multiple classes/sections** during the same time period (e.g., combined lectures, elective groups).

---

## 🏗️ **System Architecture**

### **Database Schema (MongoDB Collections)**

#### **1. `timetable_periods`**
```javascript
{
  _id: ObjectId,
  school_id: Number,
  period_number: Number,
  period_name: String,
  start_time: String,  // "08:00"
  end_time: String,    // "08:45"
  duration_minutes: Number,
  is_active: Boolean,
  created_at: Date,
  updated_at: Date
}
```

#### **2. `timetable_assignments`** (UPDATED for Many-Class)
```javascript
{
  _id: ObjectId,
  school_id: Number,
  staff_id: Number,
  period_id: ObjectId,
  day_of_week: Number,  // 0=Monday, 6=Sunday
  
  // NEW: Support for multiple classes
  classes: [
    {
      class_id: String,      // "10-A", "11-B", etc.
      subject: String,       // "Mathematics", "Physics"
      room_number: String,   // "Room 101"
      student_count: Number  // Optional
    }
  ],
  
  assignment_type: String,  // "regular", "admin_override", "peer_swap", "self_allocated"
  is_locked: Boolean,       // For self-allocated entries
  locked_by: String,        // "admin" or "staff"
  
  // Swap/Override tracking
  original_staff_id: Number,  // If this is a swap/override
  swap_request_id: ObjectId,  // Reference to swap request
  override_notes: String,     // Admin notes for override
  
  created_at: Date,
  created_by: Number,
  updated_at: Date,
  updated_by: Number
}
```

#### **3. `timetable_department_permissions`**
```javascript
{
  _id: ObjectId,
  school_id: Number,
  department: String,
  allow_alterations: Boolean,  // Can send swap requests
  allow_inbound: Boolean,      // Can receive swap requests
  created_at: Date,
  updated_at: Date
}
```

#### **4. `timetable_swap_requests`**
```javascript
{
  _id: ObjectId,
  school_id: Number,
  requester_staff_id: Number,
  target_staff_id: Number,
  period_id: ObjectId,
  day_of_week: Number,
  reason: String,
  status: String,  // "pending", "accepted", "rejected", "cancelled"
  requested_at: Date,
  responded_at: Date,
  response_notes: String
}
```

#### **5. `timetable_self_allocations`**
```javascript
{
  _id: ObjectId,
  school_id: Number,
  staff_id: Number,
  assignment_id: ObjectId,  // Reference to timetable_assignments
  activity_name: String,
  description: String,
  is_locked: Boolean,  // Always true for self-allocations
  created_at: Date
}
```

#### **6. `timetable_settings`**
```javascript
{
  _id: ObjectId,
  school_id: Number,
  is_enabled: Boolean,  // Company admin toggle
  working_days: [Number],  // [0,1,2,3,4] = Mon-Fri
  default_period_duration: Number,  // 45 minutes
  allow_overlapping_assignments: Boolean,  // NEW: For many-class
  created_at: Date,
  updated_at: Date
}
```

---

## 🎯 **Implementation Phases**

### **Phase 1: Database & Backend Setup** (Priority: CRITICAL)

#### **Step 1.1: Create MongoDB Collections**
```python
# database.py - Add collection definitions

from mongoengine import Document, EmbeddedDocument, fields

class ClassInfo(EmbeddedDocument):
    """Embedded document for multiple class assignments"""
    class_id = fields.StringField(required=True)
    subject = fields.StringField(required=True)
    room_number = fields.StringField()
    student_count = fields.IntField()

class TimetablePeriod(Document):
    meta = {'collection': 'timetable_periods'}
    school_id = fields.IntField(required=True)
    period_number = fields.IntField(required=True)
    period_name = fields.StringField(required=True)
    start_time = fields.StringField(required=True)
    end_time = fields.StringField(required=True)
    duration_minutes = fields.IntField()
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()

class TimetableAssignment(Document):
    meta = {'collection': 'timetable_assignments'}
    school_id = fields.IntField(required=True)
    staff_id = fields.IntField(required=True)
    period_id = fields.ObjectIdField(required=True)
    day_of_week = fields.IntField(required=True)
    
    # NEW: Multiple classes support
    classes = fields.ListField(fields.EmbeddedDocumentField(ClassInfo))
    
    assignment_type = fields.StringField(
        choices=['regular', 'admin_override', 'peer_swap', 'self_allocated'],
        default='regular'
    )
    is_locked = fields.BooleanField(default=False)
    locked_by = fields.StringField()
    
    original_staff_id = fields.IntField()
    swap_request_id = fields.ObjectIdField()
    override_notes = fields.StringField()
    
    created_at = fields.DateTimeField()
    created_by = fields.IntField()
    updated_at = fields.DateTimeField()
    updated_by = fields.IntField()

class TimetableDepartmentPermission(Document):
    meta = {'collection': 'timetable_department_permissions'}
    school_id = fields.IntField(required=True)
    department = fields.StringField(required=True)
    allow_alterations = fields.BooleanField(default=True)
    allow_inbound = fields.BooleanField(default=True)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()

class TimetableSwapRequest(Document):
    meta = {'collection': 'timetable_swap_requests'}
    school_id = fields.IntField(required=True)
    requester_staff_id = fields.IntField(required=True)
    target_staff_id = fields.IntField(required=True)
    period_id = fields.ObjectIdField(required=True)
    day_of_week = fields.IntField(required=True)
    reason = fields.StringField()
    status = fields.StringField(
        choices=['pending', 'accepted', 'rejected', 'cancelled'],
        default='pending'
    )
    requested_at = fields.DateTimeField()
    responded_at = fields.DateTimeField()
    response_notes = fields.StringField()

class TimetableSelfAllocation(Document):
    meta = {'collection': 'timetable_self_allocations'}
    school_id = fields.IntField(required=True)
    staff_id = fields.IntField(required=True)
    assignment_id = fields.ObjectIdField(required=True)
    activity_name = fields.StringField(required=True)
    description = fields.StringField()
    is_locked = fields.BooleanField(default=True)
    created_at = fields.DateTimeField()

class TimetableSetting(Document):
    meta = {'collection': 'timetable_settings'}
    school_id = fields.IntField(required=True, unique=True)
    is_enabled = fields.BooleanField(default=False)
    working_days = fields.ListField(fields.IntField())
    default_period_duration = fields.IntField(default=45)
    allow_overlapping_assignments = fields.BooleanField(default=True)  # NEW
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()
```

#### **Step 1.2: Create Backend Manager Classes**

**File**: `timetable_management.py`

```python
"""
Timetable Management Backend Logic
Handles all business logic for timetable operations
"""

from datetime import datetime
from bson import ObjectId
from database import (
    TimetablePeriod, TimetableAssignment, TimetableDepartmentPermission,
    TimetableSwapRequest, TimetableSelfAllocation, TimetableSetting,
    ClassInfo
)

class TimetableManager:
    """Manages periods and basic timetable operations"""
    
    @staticmethod
    def create_period(school_id, period_number, period_name, start_time, end_time):
        """Create a new period"""
        # Calculate duration
        from datetime import datetime
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        duration = int((end - start).total_seconds() / 60)
        
        period = TimetablePeriod(
            school_id=school_id,
            period_number=period_number,
            period_name=period_name,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        period.save()
        return period
    
    @staticmethod
    def get_periods(school_id):
        """Get all periods for a school"""
        return list(TimetablePeriod.objects(school_id=school_id, is_active=True).order_by('period_number'))
    
    @staticmethod
    def update_period(period_id, **kwargs):
        """Update period details"""
        period = TimetablePeriod.objects(id=period_id).first()
        if not period:
            return None
        
        for key, value in kwargs.items():
            setattr(period, key, value)
        
        period.updated_at = datetime.now()
        period.save()
        return period
    
    @staticmethod
    def delete_period(period_id):
        """Soft delete a period"""
        period = TimetablePeriod.objects(id=period_id).first()
        if period:
            period.is_active = False
            period.save()
            return True
        return False


class TimetableAssignmentManager:
    """Manages staff assignments to periods with many-class support"""
    
    @staticmethod
    def create_assignment(school_id, staff_id, period_id, day_of_week, 
                         classes_data, assignment_type='regular', created_by=None):
        """
        Create a new assignment with support for multiple classes
        
        Args:
            classes_data: List of dicts with keys: class_id, subject, room_number, student_count
        """
        # Convert classes_data to ClassInfo objects
        classes = [ClassInfo(**cls) for cls in classes_data]
        
        assignment = TimetableAssignment(
            school_id=school_id,
            staff_id=staff_id,
            period_id=ObjectId(period_id),
            day_of_week=day_of_week,
            classes=classes,
            assignment_type=assignment_type,
            created_at=datetime.now(),
            created_by=created_by,
            updated_at=datetime.now()
        )
        assignment.save()
        return assignment
    
    @staticmethod
    def get_staff_timetable(school_id, staff_id):
        """Get complete timetable for a staff member"""
        assignments = TimetableAssignment.objects(
            school_id=school_id,
            staff_id=staff_id
        ).order_by('day_of_week', 'period_id')
        
        # Group by day and period
        timetable = {}
        for assignment in assignments:
            day = assignment.day_of_week
            if day not in timetable:
                timetable[day] = []
            
            # Get period details
            period = TimetablePeriod.objects(id=assignment.period_id).first()
            
            timetable[day].append({
                'assignment_id': str(assignment.id),
                'period': {
                    'id': str(period.id),
                    'number': period.period_number,
                    'name': period.period_name,
                    'start_time': period.start_time,
                    'end_time': period.end_time
                },
                'classes': [
                    {
                        'class_id': cls.class_id,
                        'subject': cls.subject,
                        'room_number': cls.room_number,
                        'student_count': cls.student_count
                    }
                    for cls in assignment.classes
                ],
                'assignment_type': assignment.assignment_type,
                'is_locked': assignment.is_locked
            })
        
        return timetable
    
    @staticmethod
    def add_class_to_assignment(assignment_id, class_data):
        """Add another class to an existing assignment (many-class feature)"""
        assignment = TimetableAssignment.objects(id=assignment_id).first()
        if not assignment:
            return None
        
        # Create new ClassInfo
        new_class = ClassInfo(**class_data)
        assignment.classes.append(new_class)
        assignment.updated_at = datetime.now()
        assignment.save()
        return assignment
    
    @staticmethod
    def remove_class_from_assignment(assignment_id, class_id):
        """Remove a specific class from an assignment"""
        assignment = TimetableAssignment.objects(id=assignment_id).first()
        if not assignment:
            return None
        
        # Filter out the class
        assignment.classes = [cls for cls in assignment.classes if cls.class_id != class_id]
        assignment.updated_at = datetime.now()
        assignment.save()
        return assignment
    
    @staticmethod
    def check_staff_availability(school_id, staff_id, period_id, day_of_week, exclude_assignment_id=None):
        """Check if staff is free at a specific time"""
        query = {
            'school_id': school_id,
            'staff_id': staff_id,
            'period_id': ObjectId(period_id),
            'day_of_week': day_of_week
        }
        
        if exclude_assignment_id:
            query['id__ne'] = ObjectId(exclude_assignment_id)
        
        existing = TimetableAssignment.objects(**query).first()
        return existing is None


class DepartmentPermissionManager:
    """Manages department-level permissions"""
    
    @staticmethod
    def get_or_create_permission(school_id, department):
        """Get existing permission or create with defaults"""
        perm = TimetableDepartmentPermission.objects(
            school_id=school_id,
            department=department
        ).first()
        
        if not perm:
            perm = TimetableDepartmentPermission(
                school_id=school_id,
                department=department,
                allow_alterations=True,
                allow_inbound=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            perm.save()
        
        return perm
    
    @staticmethod
    def update_permission(school_id, department, allow_alterations=None, allow_inbound=None):
        """Update department permissions"""
        perm = DepartmentPermissionManager.get_or_create_permission(school_id, department)
        
        if allow_alterations is not None:
            perm.allow_alterations = allow_alterations
        if allow_inbound is not None:
            perm.allow_inbound = allow_inbound
        
        perm.updated_at = datetime.now()
        perm.save()
        return perm
    
    @staticmethod
    def can_staff_request_swap(school_id, staff_department):
        """Check if staff from this department can request swaps"""
        perm = TimetableDepartmentPermission.objects(
            school_id=school_id,
            department=staff_department
        ).first()
        
        return perm.allow_alterations if perm else True


class AlterationManager:
    """Manages peer swaps and admin overrides"""
    
    @staticmethod
    def request_swap(school_id, requester_id, target_id, period_id, day_of_week, reason):
        """Create a swap request"""
        swap = TimetableSwapRequest(
            school_id=school_id,
            requester_staff_id=requester_id,
            target_staff_id=target_id,
            period_id=ObjectId(period_id),
            day_of_week=day_of_week,
            reason=reason,
            requested_at=datetime.now()
        )
        swap.save()
        return swap
    
    @staticmethod
    def respond_to_swap(swap_id, accept, response_notes=None):
        """Accept or reject a swap request"""
        swap = TimetableSwapRequest.objects(id=swap_id).first()
        if not swap:
            return None
        
        swap.status = 'accepted' if accept else 'rejected'
        swap.responded_at = datetime.now()
        swap.response_notes = response_notes
        swap.save()
        
        if accept:
            # Perform the swap
            AlterationManager._execute_swap(swap)
        
        return swap
    
    @staticmethod
    def _execute_swap(swap):
        """Execute the actual swap in timetable_assignments"""
        # Find requester's assignment
        requester_assignment = TimetableAssignment.objects(
            school_id=swap.school_id,
            staff_id=swap.requester_staff_id,
            period_id=swap.period_id,
            day_of_week=swap.day_of_week
        ).first()
        
        if requester_assignment:
            # Update to target staff
            requester_assignment.staff_id = swap.target_staff_id
            requester_assignment.assignment_type = 'peer_swap'
            requester_assignment.swap_request_id = swap.id
            requester_assignment.original_staff_id = swap.requester_staff_id
            requester_assignment.updated_at = datetime.now()
            requester_assignment.save()
    
    @staticmethod
    def admin_override(school_id, assignment_id, new_staff_id, notes, admin_id):
        """Admin forces a reassignment"""
        assignment = TimetableAssignment.objects(id=assignment_id).first()
        if not assignment:
            return None
        
        # Store original staff
        assignment.original_staff_id = assignment.staff_id
        assignment.staff_id = new_staff_id
        assignment.assignment_type = 'admin_override'
        assignment.override_notes = notes
        assignment.updated_at = datetime.now()
        assignment.updated_by = admin_id
        assignment.save()
        
        return assignment


class SelfAllocationManager:
    """Manages staff self-allocation to empty slots"""
    
    @staticmethod
    def allocate_empty_slot(school_id, staff_id, period_id, day_of_week, 
                           activity_name, description, classes_data):
        """Staff fills an empty slot"""
        # Create assignment
        assignment = TimetableAssignmentManager.create_assignment(
            school_id=school_id,
            staff_id=staff_id,
            period_id=period_id,
            day_of_week=day_of_week,
            classes_data=classes_data,
            assignment_type='self_allocated',
            created_by=staff_id
        )
        
        # Lock it
        assignment.is_locked = True
        assignment.locked_by = 'staff'
        assignment.save()
        
        # Create self-allocation record
        self_alloc = TimetableSelfAllocation(
            school_id=school_id,
            staff_id=staff_id,
            assignment_id=assignment.id,
            activity_name=activity_name,
            description=description,
            created_at=datetime.now()
        )
        self_alloc.save()
        
        return assignment
    
    @staticmethod
    def can_staff_delete(assignment_id, staff_id):
        """Check if staff can delete this assignment"""
        assignment = TimetableAssignment.objects(id=assignment_id).first()
        if not assignment:
            return False
        
        # Staff cannot delete locked self-allocations
        if assignment.assignment_type == 'self_allocated' and assignment.is_locked:
            return False
        
        return True
    
    @staticmethod
    def admin_delete_self_allocation(assignment_id):
        """Admin can delete any self-allocation"""
        assignment = TimetableAssignment.objects(id=assignment_id).first()
        if assignment:
            # Delete self-allocation record
            TimetableSelfAllocation.objects(assignment_id=assignment.id).delete()
            # Delete assignment
            assignment.delete()
            return True
        return False
```

---

## 📁 **File Structure**

```
I-HR/
├── database.py                          # MongoDB models (UPDATED)
├── timetable_management.py              # Backend logic (NEW)
├── timetable_api_routes.py              # API endpoints (NEW)
├── app.py                               # Register blueprint
├── templates/
│   ├── company_dashboard.html           # Add toggle (UPDATED)
│   ├── admin_dashboard.html             # Add menu item (UPDATED)
│   ├── staff_dashboard.html             # Add menu item (UPDATED)
│   ├── timetable_management.html        # Admin timetable page (NEW)
│   └── staff_timetable.html             # Staff timetable page (NEW)
└── static/
    ├── js/
    │   ├── timetable_management.js      # Admin JS (NEW)
    │   └── staff_timetable.js           # Staff JS (NEW)
    └── css/
        └── timetable.css                # Timetable styles (NEW)
```

---

## 🎯 **Next Steps**

Would you like me to:

1. **Continue with API Routes** - Create the Flask API endpoints
2. **Build Frontend UI** - Create the HTML/JS for admin and staff panels
3. **Implement Many-Class Feature** - Focus on the multi-class assignment UI
4. **Start with Company Admin Toggle** - Begin with the gatekeeper feature

Let me know which part you'd like me to implement first!
