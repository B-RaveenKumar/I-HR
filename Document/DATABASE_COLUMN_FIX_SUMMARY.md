# Database Column Error Fix Summary

## Issue
**Error**: `Report generation failed: no such column: s.allowances`

## Root Cause
The SQL query in the `/generate_admin_report` route was trying to access columns `s.allowances` and `s.deductions` that don't exist in the database schema.

## Database Schema Analysis
The `staff` table actually has individual columns for:

**Allowances:**
- `hra` (House Rent Allowance)
- `transport_allowance` 
- `other_allowances`

**Deductions:**
- `pf_deduction` (Provident Fund)
- `esi_deduction` (Employee State Insurance)
- `professional_tax`
- `other_deductions`

## Solution Implemented
Modified the SQL query in `app.py` (around line 1278) to calculate totals from individual columns:

### Before (Broken):
```sql
SELECT s.id, s.staff_id, s.full_name, s.department, s.position,
       s.basic_salary, s.allowances, s.deductions,
       COALESCE(s.basic_salary, 0) + COALESCE(s.allowances, 0) - COALESCE(s.deductions, 0) as net_salary,
       s.date_of_joining
FROM staff s
```

### After (Fixed):
```sql
SELECT s.id, s.staff_id, s.full_name, s.department, s.position,
       s.basic_salary, 
       (COALESCE(s.hra, 0) + COALESCE(s.transport_allowance, 0) + COALESCE(s.other_allowances, 0)) as allowances,
       (COALESCE(s.pf_deduction, 0) + COALESCE(s.esi_deduction, 0) + COALESCE(s.professional_tax, 0) + COALESCE(s.other_deductions, 0)) as deductions,
       COALESCE(s.basic_salary, 0) + (COALESCE(s.hra, 0) + COALESCE(s.transport_allowance, 0) + COALESCE(s.other_allowances, 0)) - (COALESCE(s.pf_deduction, 0) + COALESCE(s.esi_deduction, 0) + COALESCE(s.professional_tax, 0) + COALESCE(s.other_deductions, 0)) as net_salary,
       s.date_of_joining
FROM staff s
```

## Files Modified
- `app.py` - Fixed the SQL query in the staff report generation function

## Testing Done
1. **Database Schema Verification**: Confirmed the problematic columns don't exist
2. **Query Testing**: Verified the corrected query executes successfully
3. **Syntax Check**: Confirmed no syntax errors in the fixed code

## Impact
- ✅ Report generation now works without database errors
- ✅ Allowances and deductions are correctly calculated from individual components
- ✅ Net salary calculation is accurate
- ✅ Excel export functionality is fully restored

## Expected Behavior Now
- Users can successfully generate staff reports from the Reports & Analytics section
- Excel files will download properly with correct salary calculations
- No more "no such column: s.allowances" errors

## Technical Details
- Uses `COALESCE()` to handle NULL values safely
- Calculates totals dynamically in the SQL query
- Maintains backward compatibility with existing code that expects `allowances` and `deductions` fields
- Preserves all existing functionality while fixing the database column mismatch
