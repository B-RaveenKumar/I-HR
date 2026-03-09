# Student Management - Extended Features Documentation

## Overview
The Student Management module has been enhanced with a comprehensive multi-step wizard form and extensive additional fields for complete student record management.

## Key Features

### 1. **Mode Toggle Switch**
- **Quick Mode**: Simple one-page form with basic fields (default)
- **Advanced Mode**: Multi-step wizard with comprehensive data collection
- Toggle button at the top of the Add Student modal

### 2. **Multi-Step Wizard (Advanced Mode)**

#### **Step 1: Basic Information**
- **Admission Number** (Optional - if not provided, roll number will be used)
- **Roll Number** (Optional - at least one of admission/roll required)
- **Student Type**: Hostel or Day Scholar (radio selection)
- First Name, Last Name
- Date of Birth (with auto-age calculation)
- Gender
- Class, Section, Academic Year
- Student Mobile Number (optional)
- Residential Address

#### **Step 2: Academic Details**
- **10th Standard**:
  - Marks (e.g., 450/500)
  - Percentage
- **12th Standard**:
  - Marks (e.g., 480/500)
  - Percentage
- **Skills & Achievements**: Textarea for talents, sports, activities, etc.

#### **Step 3: Parent & Document Details**
- **Father Information**:
  - Name (required)
  - Mobile (required, 10 digits)
  - Email (optional)
- **Mother Information**:
  - Name
  - Mobile (10 digits)
- **Parent Occupation**
- **Documents**:
  - TC Number (Transfer Certificate)
  -Aadhar Number (12 digits)
- **Custom Fields**:
  - Add unlimited custom fields with "Add Field" button
  - Each field has a name and value
  - Can be removed individually
  - Stored as JSON in database

#### **Step 4: Review & Confirm**
- Complete overview of all entered data
- Organized by sections:
  - Basic Information
  - Academic History
  - Parent Information
  - Documents
  - Custom Fields (if any)
- Final "Create Student" button

### 3. **Database Schema Updates**

**New Columns Added to `students` table:**
```sql
admission_number TEXT
student_type TEXT DEFAULT 'Day Scholar'
mother_name TEXT
mother_phone TEXT
parent_occupation TEXT
tenth_marks TEXT
tenth_percentage REAL
twelfth_marks TEXT
twelfth_percentage REAL
skills TEXT
tc_number TEXT
aadhar_number TEXT
custom_fields TEXT  -- JSON formatted
```

### 4. **Form Validation**

- **Required Field Validation**: Checks all required fields before step progression
- **Admission/Roll Number Validation**: At least one must be provided
- **Phone Number Validation**: 10-digit pattern for mobile numbers
- **Aadhar Validation**: 12-digit pattern
- **Age Auto-calculation**: Automatically computed from date of birth

### 5. **Backend Processing**

The `admin_student_management` route now handles:
- All extended fields from the form
- Custom fields extraction and JSON storage
- Validation of admission/roll number requirement
- Generation of student_id based on available identifier
- Proper error handling and flash messages

## User Workflow

### Quick Mode (Default)
1. Click "Add Student" button
2. Fill basic form (all fields visible on one page)
3. Click "Create Student"
4. Done!

### Advanced Mode
1. Click "Add Student" button
2. Toggle "Advanced Mode" switch **ON**
3. **Step 1**: Fill basic student information → Click "Next"
4. **Step 2**: Enter academic records (10th, 12th marks) → Click "Next"
5. **Step 3**: Add parent details, documents, and custom fields → Click "Next"
6. **Step 4**: Review all information → Click "Create Student"
7. Student record created with comprehensive data!

## Custom Fields Feature

### Adding Custom Fields:
1. In Step 3, click "Add Field" button
2. Enter field name (e.g., "Blood Group", "Emergency Contact")
3. Field appears with input box
4. Fill in the value
5. Repeat for multiple custom fields
6. Each field can be removed with the X button

### Storage:
- Custom fields are stored as JSON in the `custom_fields` column
- Format: `{"Blood_Group": "O+", "Emergency_Contact": "9876543210"}`
- Unlimited fields supported
- No schema changes needed for new fields

## Technical Details

### JavaScript Functions:
- `changeStep(direction)`: Navigate between wizard steps
- `validateStep(step)`: Validate current step before progression
- `addCustomField()`: Add new custom field dynamically
- `removeCustomField(id)`: Remove custom field
- `populateReview()`: Generate review page content
- `showStep(step)`: Display specific wizard step
- Auto-reset on modal close

### CSS Enhancements:
- Progress indicator with step circles
- Step labels and connecting lines
- Active step highlighting (green color)
- Responsive layout for all screen sizes
- Review page with organized card layout

## Benefits

1. **Flexibility**: Choose between quick or comprehensive data entry
2. **Completeness**: Capture all relevant student information
3. **Extensibility**: Custom fields for institution-specific needs
4. **User-Friendly**: Step-by-step wizard prevents overwhelming forms
5. **Data Integrity**: Validation ensures required information is captured
6. **Future-Proof**: JSON storage allows unlimited custom attributes

## Migration Notes

For existing databases:
- Run `migrate_student_extended_fields.py` to add new columns
- Existing student records will have NULL values for new fields
- Can be updated via Edit Student functionality
- No data loss - all existing fields preserved

## API Endpoints

- `POST /admin/student-management` - Create/Edit/Delete students
- `GET /api/get-student/<id>` - Fetch student data for editing

All endpoints automatically handle the extended field set.
