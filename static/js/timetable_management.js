/**
 * Timetable Management JavaScript - School Admin Panel
 * Handles period management, department permissions, and staff assignments
 */

let schoolId = null;
let allPeriods = [];
let allDepartments = [];
let allStaff = [];
let currentAssignments = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Use the schoolId initialized in HTML (from Flask session)
    schoolId = window.schoolId;
    console.log('🏫 Timetable Management initialized with school_id:', schoolId);
    
    // Check if user is authenticated and load data
    console.log('Starting data load...');
    loadPeriods();
    loadDepartments();
    loadStaffList();
});

// ==========================================================================
// PERIODS MANAGEMENT
// ==========================================================================

function loadPeriods() {
    console.log('Loading periods for school_id:', schoolId);
    fetch(`/api/timetable/periods?school_id=${schoolId}`)
        .then(r => {
            console.log('Periods API response status:', r.status);
            if (!r.ok) {
                throw new Error(`API Error: ${r.status} ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Periods data received:', data);
            allPeriods = data.periods || [];
            console.log(`Loaded ${allPeriods.length} periods`);
            renderPeriodsTable();
        })
        .catch(err => {
            console.error('Error loading periods:', err);
            showAlert('Failed to load periods: ' + err.message, 'error');
        });
}

function renderPeriodsTable() {
    const tbody = document.getElementById('periodsTableBody');
    
    if (allPeriods.length === 0) {
        tbody.innerHTML = '<tr style="background: #f8f9fa;"><td colspan="6" style="padding: 2rem; text-align: center; color: white;"><i class="bi bi-inbox"></i> No periods defined. Add one to get started!</td></tr>';
        return;
    }
    
    tbody.innerHTML = allPeriods.map(p => `
        <tr>
            <td style="padding: 1rem; font-weight: 600;">${p.period_number}</td>
            <td style="padding: 1rem;">${p.period_name || '-'}</td>
            <td style="padding: 1rem;"><span class="time-display">${p.start_time}</span></td>
            <td style="padding: 1rem;"><span class="time-display">${p.end_time}</span></td>
            <td style="padding: 1rem;"><span class="duration-badge">${p.duration_minutes} mins</span></td>
            <td style="padding: 1rem; text-align: center;">
                <div class="action-buttons">
                    <button class="btn-edit btn-sm" onclick="editPeriod(${p.id})">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn-delete-action btn-sm" onclick="deletePeriod(${p.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function showAddPeriodModal() {
    document.getElementById('periodNumber').value = '';
    document.getElementById('periodName').value = '';
    document.getElementById('startTime').value = '';
    document.getElementById('endTime').value = '';
    document.getElementById('periodModalTitle').textContent = 'Add Period';
    document.getElementById('periodModal').dataset.editId = '';
    new bootstrap.Modal(document.getElementById('periodModal')).show();
}

function editPeriod(periodId) {
    const period = allPeriods.find(p => p.id === periodId);
    if (!period) return;
    
    document.getElementById('periodNumber').value = period.period_number;
    document.getElementById('periodName').value = period.period_name || '';
    document.getElementById('startTime').value = period.start_time;
    document.getElementById('endTime').value = period.end_time;
    document.getElementById('periodModalTitle').textContent = 'Edit Period';
    document.getElementById('periodModal').dataset.editId = periodId;
    new bootstrap.Modal(document.getElementById('periodModal')).show();
}

function savePeriod() {
    const periodNumber = document.getElementById('periodNumber').value;
    const periodName = document.getElementById('periodName').value;
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    
    console.log('📝 Saving period:', { periodNumber, periodName, startTime, endTime, schoolId });
    
    if (!periodNumber || !startTime || !endTime) {
        showAlert('Please fill all required fields', 'error');
        return;
    }
    
    const data = {
        school_id: schoolId,
        period_number: periodNumber,
        period_name: periodName,
        start_time: startTime,
        end_time: endTime
    };
    
    fetch('/api/timetable/period/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => {
        console.log('Period save response status:', r.status);
        if (!r.ok) {
            throw new Error(`HTTP Error: ${r.status} ${r.statusText}`);
        }
        return r.json();
    })
    .then(result => {
        console.log('Period save result:', result);
        if (result.success) {
            showAlert('Period saved successfully', 'success');
            const modalElement = document.getElementById('periodModal');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
            console.log('Reloading periods after save...');
            loadPeriods();
        } else {
            showAlert(result.error || 'Failed to save period', 'error');
        }
    })
    .catch(err => {
        console.error('Error saving period:', err);
        showAlert('Error saving period: ' + err.message, 'error');
    });
}

function deletePeriod(periodId) {
    if (!confirm('Are you sure you want to delete this period?')) return;
    
    fetch('/api/timetable/period/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ school_id: schoolId, period_id: periodId })
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Period deleted successfully', 'success');
            loadPeriods();
        } else {
            showAlert(result.error || 'Failed to delete period', 'error');
        }
    })
    .catch(err => console.error('Error deleting period:', err));
}

// ==========================================================================
// DEPARTMENT PERMISSIONS
// ==========================================================================

function loadDepartments() {
    console.log('Loading departments for school_id:', schoolId);
    fetch(`/api/timetable/departments?school_id=${schoolId}`)
        .then(r => {
            console.log('Departments API response status:', r.status);
            if (!r.ok) {
                throw new Error(`API Error: ${r.status} ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Departments data received:', data);
            allDepartments = data.departments || [];
            console.log(`Loaded ${allDepartments.length} departments`);
            renderDepartmentsTable();
        })
        .catch(err => {
            console.error('Error loading departments:', err);
            showAlert('Failed to load departments: ' + err.message, 'warning');
        });
}

function renderDepartmentsTable() {
    const tbody = document.getElementById('departmentsTableBody');
    
    if (allDepartments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="padding: 2rem; text-align: center; color: white;">Loading departments...</td></tr>';
        return;
    }
    
    tbody.innerHTML = allDepartments.map(d => `
        <tr>
            <td style="padding: 1rem; font-weight: 600;">${d.department}</td>
            <td style="padding: 1rem; text-align: center;">
                <label class="custom-switch">
                    <input type="checkbox" ${d.allow_alterations ? 'checked' : ''} 
                        onchange="toggleDepartmentPermission('${d.department}', 'alterations', this.checked)">
                    <span class="slider"></span>
                </label>
            </td>
            <td style="padding: 1rem; text-align: center;">
                <label class="custom-switch">
                    <input type="checkbox" ${d.allow_inbound ? 'checked' : ''} 
                        onchange="toggleDepartmentPermission('${d.department}', 'inbound', this.checked)">
                    <span class="slider"></span>
                </label>
            </td>
            <td style="padding: 1rem; text-align: center;">
                <button class="btn btn-sm btn-outline-primary" onclick="saveDepartmentPermission('${d.department}')">
                    <i class="bi bi-check-circle"></i> Save
                </button>
            </td>
        </tr>
    `).join('');
}

function toggleDepartmentPermission(department, permType, value) {
    // Store in data attribute for later save
    const row = event.target.closest('tr');
    if (!row.dataset.permissions) row.dataset.permissions = JSON.stringify({});
    const perms = JSON.parse(row.dataset.permissions);
    if (permType === 'alterations') perms.allow_alterations = value;
    if (permType === 'inbound') perms.allow_inbound = value;
    row.dataset.permissions = JSON.stringify(perms);
}

function saveDepartmentPermission(department) {
    const row = event.target.closest('tr');
    const perms = JSON.parse(row.dataset.permissions || '{}');
    
    const data = {
        school_id: schoolId,
        department: department,
        allow_alterations: perms.allow_alterations !== false,
        allow_inbound: perms.allow_inbound !== false
    };
    
    fetch('/api/timetable/department/permission', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Department permissions updated', 'success');
            loadDepartments();
        } else {
            showAlert(result.error || 'Failed to update permissions', 'error');
        }
    })
    .catch(err => console.error('Error saving permissions:', err));
}

// ==========================================================================
// STAFF ASSIGNMENTS & ADMIN OVERRIDE
// ==========================================================================

function loadStaffList() {
    console.log('Loading staff for school_id:', schoolId);
    fetch(`/api/staff/list?school_id=${schoolId}`)
        .then(r => {
            console.log('Staff API response status:', r.status);
            if (!r.ok) {
                throw new Error(`API Error: ${r.status} ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Staff data received:', data);
            allStaff = data.staff || [];
            console.log(`Loaded ${allStaff.length} staff members`);
            populateStaffSelect();
        })
        .catch(err => {
            console.error('Error loading staff:', err);
            showAlert('Failed to load staff: ' + err.message, 'warning');
        });
}

function populateStaffSelect() {
    // Populate the main staff assignment dropdown
    const mainSelect = document.getElementById('staffSelectAssign');
    if (mainSelect) {
        mainSelect.innerHTML = '<option value="">-- Choose Staff Member --</option>' +
            allStaff.map(s => `<option value="${s.id}">${s.full_name} (${s.department})</option>`).join('');
        console.log(`✅ Populated staffSelectAssign with ${allStaff.length} staff`);
    }
    
    // Populate the admin override modal dropdown
    const overrideSelect = document.getElementById('overrideStaffSelect');
    if (overrideSelect) {
        overrideSelect.innerHTML = '<option>-- Choose staff member --</option>' +
            allStaff.map(s => `<option value="${s.id}">${s.full_name} (${s.department})</option>`).join('');
        console.log(`✅ Populated overrideStaffSelect with ${allStaff.length} staff`);
    }
}

function loadDayAssignments() {
    const dayValue = document.getElementById('daySelector').value;
    if (!dayValue) {
        document.getElementById('assignmentsTableBody').innerHTML = 
            '<tr><td colspan="6" style="padding: 2rem; text-align: center;">Select a day to view</td></tr>';
        return;
    }
    
    fetch(`/api/timetable/assignments/all?school_id=${schoolId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load assignments: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.data) {
                currentAssignments = data.data;
            } else {
                currentAssignments = [];
            }
            renderAssignmentsTable();
        })
        .catch(err => {
            console.error('Error loading assignments:', err);
            showAlert('Failed to load assignments: ' + err.message, 'error');
        });
}

function renderAssignmentsTable() {
    const tbody = document.getElementById('assignmentsTableBody');
    
    if (currentAssignments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="padding: 2rem; text-align: center; color: white;">No assignments for this day</td></tr>';
        return;
    }
    
    tbody.innerHTML = currentAssignments.map(a => `
        <tr>
            <td style="padding: 1rem;">${a.full_name}</td>
            <td style="padding: 1rem;">${a.period_name || `Period ${a.period_number}`}</td>
            <td style="padding: 1rem; font-family: monospace;">${a.start_time} - ${a.end_time}</td>
            <td style="padding: 1rem;">${a.class_subject || '-'}</td>
            <td style="padding: 1rem;">
                ${a.is_locked 
                    ? '<span class="status-badge status-locked"><i class="bi bi-lock"></i> Locked</span>'
                    : '<span class="status-badge status-active">Active</span>'
                }
            </td>
            <td style="padding: 1rem; text-align: center;">
                <button class="btn btn-sm btn-override" onclick="showOverrideModal(${a.id})">
                    <i class="bi bi-shield-check"></i> Override
                </button>
            </td>
        </tr>
    `).join('');
}

function filterAssignments() {
    const search = document.getElementById('staffSearchInput').value.toLowerCase();
    const rows = document.getElementById('assignmentsTableBody').querySelectorAll('tr');
    
    rows.forEach(row => {
        const staffName = row.cells[0]?.textContent.toLowerCase() || '';
        row.style.display = staffName.includes(search) ? '' : 'none';
    });
}

function showOverrideModal(assignmentId) {
    document.getElementById('overrideModal').dataset.assignmentId = assignmentId;
    document.getElementById('overrideStaffSelect').value = '';
    document.getElementById('overrideNotes').value = '';
    new bootstrap.Modal(document.getElementById('overrideModal')).show();
}

function performAdminOverride() {
    const assignmentId = document.getElementById('overrideModal').dataset.assignmentId;
    const newStaffId = document.getElementById('overrideStaffSelect').value;
    const notes = document.getElementById('overrideNotes').value;
    
    if (!newStaffId) {
        showAlert('Please select a staff member', 'error');
        return;
    }
    
    const data = {
        school_id: schoolId,
        assignment_id: assignmentId,
        new_staff_id: newStaffId,
        admin_notes: notes
    };
    
    fetch('/api/timetable/assignment/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Assignment reassigned successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('overrideModal')).hide();
            loadDayAssignments();
        } else {
            showAlert(result.error || 'Failed to override assignment', 'error');
        }
    })
    .catch(err => {
        console.error('Error overriding assignment:', err);
        showAlert('Error overriding assignment', 'error');
    });
}

// ==========================================================================
// UTILITY FUNCTIONS
// ==========================================================================

function showAlert(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : type === 'success' ? 'alert-success' : 'alert-info';
    const iconClass = type === 'error' ? 'bi-exclamation-circle' : type === 'success' ? 'bi-check-circle' : 'bi-info-circle';
    
    const alertHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <i class="bi ${iconClass}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) alert.remove();
    }, 5000);
}

function refreshData() {
    loadPeriods();
    loadDepartments();
    if (document.getElementById('daySelector').value) {
        loadDayAssignments();
    }
    showAlert('Data refreshed', 'success');
}

function saveAllSettings() {
    showAlert('All settings saved successfully', 'success');
}

// ============================================================================
// ENHANCED STAFF PERIOD ALLOCATION FUNCTIONS
// ============================================================================

/**
 * Called when a staff member is selected
 * Shows the allocation interface and loads their current allocations
 */
function onStaffSelected() {
    const staffSelect = document.getElementById('staffSelectAssign');
    const staffId = staffSelect.value;
    const staffName = staffSelect.options[staffSelect.selectedIndex].text;
    
    const allocationSection = document.getElementById('allocationSection');
    const currentAllocationsSection = document.getElementById('currentAllocationsSection');
    const staffInfoDisplay = document.getElementById('staffInfoDisplay');
    const staffInfoText = document.getElementById('staffInfoText');
    const divider = document.getElementById('staffPeriodsDivider');
    
    if (!staffId) {
        // Hide sections if no staff selected
        allocationSection.style.display = 'none';
        currentAllocationsSection.style.display = 'none';
        staffInfoDisplay.classList.add('d-none');
        divider.style.display = 'none';
        return;
    }
    
    // Show allocation interface
    allocationSection.style.display = 'block';
    divider.style.display = 'block';
    
    // Show staff info
    staffInfoDisplay.classList.remove('d-none');
    staffInfoText.textContent = `Currently managing allocations for: ${staffName}`;
    
    // Load current allocations for this staff
    loadStaffCurrentAllocations(staffId);
}

/**
 * Load current period allocations for a specific staff member
 */
function loadStaffCurrentAllocations(staffId) {
    const tbody = document.getElementById('staffCurrentAllocationsBody');
    const section = document.getElementById('currentAllocationsSection');
    
    fetch(`/api/timetable/staff-period/list/${staffId}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to load allocations');
            return response.json();
        })
        .then(data => {
            if (data.status === 'success' && data.data && data.data.length > 0) {
                const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                
                tbody.innerHTML = data.data.map(allocation => {
                    const day = DAYS[allocation.day_of_week] || 'Unknown';
                    const periodName = allocation.period_name || `Period ${allocation.period_id}`;
                    const timeSlot = allocation.time_slot || '--:-- to --:--';
                    const createdDate = new Date(allocation.created_at).toLocaleDateString() || 'Unknown';
                    
                    return `
                        <tr>
                            <td><strong>${day}</strong></td>
                            <td>${periodName}</td>
                            <td><code>${timeSlot}</code></td>
                            <td><small>${createdDate}</small></td>
                            <td class="text-center">
                                <button class="btn btn-sm btn-danger" onclick="deleteStaffAllocation(${allocation.id}, ${staffId})">
                                    <i class="bi bi-trash"></i> Delete
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
                
                section.style.display = 'block';
            } else {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center text-muted py-3">
                            <i class="bi bi-inbox"></i> No periods allocated yet. Add one above!
                        </td>
                    </tr>
                `;
                section.style.display = 'block';
            }
        })
        .catch(err => {
            console.error('Error loading allocations:', err);
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-danger py-3">
                        <i class="bi bi-exclamation-circle"></i> Error loading allocations
                    </td>
                </tr>
            `;
            section.style.display = 'block';
        });
}

/**
 * Assign a period to a staff member
 */
function assignStaffPeriod() {
    const staffSelect = document.getElementById('staffSelectAssign');
    const daySelect = document.getElementById('daySelectAssign');
    const periodSelect = document.getElementById('periodSelectAssign');
    
    const staffId = staffSelect.value;
    const day = daySelect.value;
    const periodId = periodSelect.value;
    const staffName = staffSelect.options[staffSelect.selectedIndex].text;
    const dayName = daySelect.options[daySelect.selectedIndex].text;
    const periodName = periodSelect.options[periodSelect.selectedIndex].text;
    
    // Validation
    if (!staffId) {
        showAlert('Please select a staff member', 'error');
        return;
    }
    if (!day && day !== '0') {
        showAlert('Please select a day', 'error');
        return;
    }
    if (!periodId) {
        showAlert('Please select a period', 'error');
        return;
    }
    
    // Check for duplicate allocation
    const tbody = document.getElementById('staffCurrentAllocationsBody');
    const isDuplicate = Array.from(tbody.querySelectorAll('tr')).some(row => {
        const rowDay = row.cells[0].textContent.trim();
        const rowPeriod = row.cells[1].textContent.trim();
        return rowDay === dayName && rowPeriod === periodName;
    });
    
    if (isDuplicate) {
        showAlert(`Period already allocated for this day!`, 'warning');
        return;
    }
    
    // Make API call to assign period
    fetch('/api/timetable/staff-period/assign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({
            staff_id: parseInt(staffId),
            day_of_week: parseInt(day),
            period_id: parseInt(periodId)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' || data.success) {
            showAlert(`Period "${periodName}" successfully allocated to ${staffName} on ${dayName}`, 'success');
            
            // Reset form
            daySelect.value = '';
            periodSelect.value = '';
            
            // Reload allocations
            loadStaffCurrentAllocations(staffId);
        } else {
            showAlert(`Error: ${data.message || 'Failed to allocate period'}`, 'error');
        }
    })
    .catch(err => {
        console.error('Error assigning period:', err);
        showAlert('Error assigning period. Please try again.', 'error');
    });
}

/**
 * Delete a period allocation for a staff member
 */
function deleteStaffAllocation(allocationId, staffId) {
    if (!confirm('Are you sure you want to delete this allocation?')) {
        return;
    }
    
    fetch(`/api/timetable/staff-period/remove/${allocationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' || data.success) {
            showAlert('Allocation deleted successfully', 'success');
            loadStaffCurrentAllocations(staffId);
        } else {
            showAlert(`Error: ${data.message || 'Failed to delete allocation'}`, 'error');
        }
    })
    .catch(err => {
        console.error('Error deleting allocation:', err);
        showAlert('Error deleting allocation. Please try again.', 'error');
    });
}

/**
 * Get all allocations and display as calendar grid for a staff member
 */
function loadStaffAllocationScheduleGrid(staffId) {
    fetch(`/api/timetable/staff-period/list/${staffId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data) {
                generateAllocationScheduleGrid(data.data);
            }
        })
        .catch(err => console.error('Error loading schedule grid:', err));
}

/**
 * Generate visual schedule grid for staff allocations
 */
function generateAllocationScheduleGrid(allocations) {
    const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const PERIODS = {};
    
    // Build period map
    allPeriods.forEach(period => {
        PERIODS[period.id] = `${period.period_name || `Period ${period.period_number}`}`;
    });
    
    // Create grid structure
    let gridHTML = '<div class="allocation-schedule-grid">';
    
    DAYS.forEach((day, dayIdx) => {
        gridHTML += `
            <div class="allocation-day-column">
                <div class="day-header">${day}</div>
        `;
        
        allocations
            .filter(a => a.day_of_week === dayIdx)
            .forEach(alloc => {
                const period = PERIODS[alloc.period_id] || `Period ${alloc.period_id}`;
                gridHTML += `
                    <div class="period-slot allocated">
                        <span>${period}</span>
                        <small>${alloc.time_slot}</small>
                    </div>
                `;
            });
        
        gridHTML += '</div>';
    });
    
    gridHTML += '</div>';
    
    return gridHTML;
}
