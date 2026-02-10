// Staff Management JavaScript - Enhanced Version
document.addEventListener('DOMContentLoaded', function() {
    // Initialize enhanced UI components
    initializeEnhancedUI();

    // Initialize search and filter functionality
    initializeSearchAndFilter();

    // Initialize form handlers
    initializeFormHandlers();

    // Initialize export functionality
    initializeExportFunctionality();

    // Initialize loading overlay
    initializeLoadingOverlay();

    // Update stats display
    updateStatsDisplay();
});

function initializeEnhancedUI() {
    // Initialize sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.enhanced-sidebar');
            sidebar.classList.toggle('show');
        });
    }

    // Initialize refresh button
    const refreshBtn = document.getElementById('refreshDataBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            showLoadingOverlay();
            setTimeout(() => {
                location.reload();
            }, 500);
        });
    }

    // Clear filters functionality is now handled in initializeSearchAndFilter()

    // Update current date in sidebar
    const currentDateElement = document.getElementById('currentDate');
    if (currentDateElement) {
        const today = new Date();
        currentDateElement.textContent = today.toLocaleDateString();
    }
}

function initializeLoadingOverlay() {
    window.showLoadingOverlay = function() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('d-none');
        }
    };

    window.hideLoadingOverlay = function() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('d-none');
        }
    };
}

function updateStatsDisplay() {
    const totalStaffElement = document.getElementById('totalStaffDisplay');
    const totalStaffCountElement = document.getElementById('totalStaffCount');
    const tableBody = document.getElementById('staffTableBody');

    if (tableBody) {
        const totalStaff = tableBody.querySelectorAll('tr').length;
        // Only update sidebar count, preserve main display count from server
        if (totalStaffCountElement) {
            totalStaffCountElement.textContent = totalStaff;
        }
        // Don't override the server-side totalStaffDisplay count unless we're showing filtered results
    }
}

function initializeSearchAndFilter() {
    const searchInput = document.getElementById('staffSearchInput');
    const departmentFilter = document.getElementById('departmentFilter');
    const positionFilter = document.getElementById('positionFilter');
    const genderFilter = document.getElementById('genderFilter');
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');

    // Debounce function to limit API calls
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Apply filters function
    function applyFilters() {
        const filters = {
            search_term: searchInput.value.trim(),
            department: departmentFilter.value,
            position: positionFilter.value,
            gender: genderFilter.value
        };

        // Remove empty filters
        Object.keys(filters).forEach(key => {
            if (!filters[key]) delete filters[key];
        });

        console.log('Applying filters:', filters);

        // Only load filtered data if there are actual filters applied
        if (Object.keys(filters).length > 0) {
            loadFilteredStaffData(filters);
        } else {
            // If no filters, reload the page to show original server-side data
            location.reload();
        }
    }

    // Clear filters function
    function clearFilters() {
        searchInput.value = '';
        departmentFilter.value = '';
        positionFilter.value = '';
        genderFilter.value = '';

        console.log('Clearing all filters');
        // Reload page to show original server-side data
        location.reload();
    }

    // Event listeners
    searchInput.addEventListener('input', debounce(applyFilters, 300));
    departmentFilter.addEventListener('change', applyFilters);
    positionFilter.addEventListener('change', applyFilters);
    genderFilter.addEventListener('change', applyFilters);
    applyFiltersBtn.addEventListener('click', applyFilters);
    clearFiltersBtn.addEventListener('click', clearFilters);

    // Don't load initial data automatically - preserve server-side data
    // Only load filtered data when filters are actually applied
    // loadFilteredStaffData({});
}

// Show loading state for table
function showTableLoadingState() {
    const tableBody = document.getElementById('staffTableBody');
    const table = document.getElementById('staffTable');

    if (table) {
        table.classList.add('loading');
    }

    const loadingRow = document.createElement('tr');
    loadingRow.innerHTML = `
        <td colspan="7" class="text-center py-4 staff-loading-state">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 mb-0 text-muted">Filtering staff members...</p>
        </td>
    `;
    tableBody.innerHTML = '';
    tableBody.appendChild(loadingRow);
}

// Hide loading state for table
function hideTableLoadingState() {
    const table = document.getElementById('staffTable');
    if (table) {
        table.classList.remove('loading');
    }
}

// Load filtered staff data from server
function loadFilteredStaffData(filters = {}) {
    const params = new URLSearchParams(filters);

    // Show loading state
    showTableLoadingState();

    fetch(`/advanced_search_staff?${params}`)
        .then(response => response.json())
        .then(data => {
            hideTableLoadingState();
            if (data.success) {
                console.log(`Found ${data.staff.length} staff members matching filters`);
                renderFilteredStaffTable(data.staff);
                updateFilteredStatsDisplay(data.staff.length);
            } else {
                showAlert('Error filtering staff: ' + data.error, 'danger');
                renderFilteredStaffTable([]);
            }
        })
        .catch(error => {
            hideTableLoadingState();
            console.error('Error filtering staff:', error);
            showAlert('Error filtering staff: ' + error.message, 'danger');
            renderFilteredStaffTable([]);
        });
}

// Render filtered staff table
function renderFilteredStaffTable(staffList) {
    const tableBody = document.getElementById('staffTableBody');
    const table = document.getElementById('staffTable');

    // Preserve table layout by maintaining structure
    tableBody.innerHTML = '';

    if (staffList.length === 0) {
        const noDataRow = document.createElement('tr');
        noDataRow.innerHTML = `
            <td colspan="7" class="text-center py-4">
                <i class="bi bi-search text-muted" style="font-size: 3rem;"></i>
                <p class="mt-3 mb-0 text-muted">No staff members found matching the current filters</p>
                <p class="text-muted small">Try adjusting your search criteria</p>
            </td>
        `;
        tableBody.appendChild(noDataRow);
        return;
    }

    staffList.forEach((staff) => {
        const row = document.createElement('tr');
        row.setAttribute('data-staff-id', staff.id);

        // Match the exact structure from the original HTML template
        row.innerHTML = `
            <td>
                <strong>${staff.staff_id || 'N/A'}</strong>
            </td>
            <td>
                <div class="d-flex align-items-center">
                    <div class="user-avatar me-2">
                        <i class="bi bi-person-circle"></i>
                    </div>
                    <div>
                        <div class="fw-bold">${staff.first_name || ''} ${staff.last_name || ''}</div>
                        <small class="text-muted">${staff.destination || 'N/A'}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-primary">${staff.department || 'N/A'}</span>
            </td>
            <td>${staff.position || staff.destination || 'N/A'}</td>
            <td>
                <div>
                    <small class="d-block"><i class="bi bi-telephone"></i> ${staff.phone || 'N/A'}</small>
                    <small class="d-block"><i class="bi bi-envelope"></i> ${staff.email || 'N/A'}</small>
                </div>
            </td>
            <td>
                <span class="badge bg-info">${staff.shift_type || 'General'}</span>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-sm btn-view-details edit-staff-btn"
                            data-staff-id="${staff.id}"
                            data-bs-toggle="modal"
                            data-bs-target="#editStaffModal"
                            title="Edit staff member">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-staff-btn"
                            data-staff-id="${staff.id}"
                            data-staff-name="${staff.full_name || 'Unknown'}"
                            title="Delete staff member">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });

    // Force table layout recalculation to prevent alignment issues
    if (table) {
        table.style.tableLayout = 'fixed';
        // Trigger reflow
        table.offsetHeight;
        table.style.tableLayout = 'auto';
    }
}

// Update stats display for filtered results
function updateFilteredStatsDisplay(filteredCount) {
    const totalStaffCountElement = document.getElementById('totalStaffCount');
    const totalStaffDisplayElement = document.getElementById('totalStaffDisplay');

    if (totalStaffCountElement) {
        totalStaffCountElement.textContent = filteredCount;
    }

    // Update main display count when showing filtered results
    if (totalStaffDisplayElement) {
        totalStaffDisplayElement.textContent = filteredCount;
    }

    // Update any other stats displays
    const statsElements = document.querySelectorAll('.staff-count-display');
    statsElements.forEach(element => {
        element.textContent = filteredCount;
    });
}

function initializeFormHandlers() {
    // Add Staff Form
    const addStaffForm = document.getElementById('addStaffForm');
    if (addStaffForm) {
        addStaffForm.addEventListener('submit', handleAddStaff);

        // Add auto-generation of full name for add form
        const addFirstName = document.getElementById('addFirstName');
        const addLastName = document.getElementById('addLastName');

        if (addFirstName && addLastName) {
            function updateAddFullName() {
                const firstName = addFirstName.value.trim();
                const lastName = addLastName.value.trim();
                // We'll send the full name as a hidden field or generate it on the server
                // For now, we just ensure the form has the required data
            }

            addFirstName.addEventListener('input', updateAddFullName);
            addLastName.addEventListener('input', updateAddFullName);
        }
    }

    // Edit Staff Form
    const editStaffForm = document.getElementById('editStaffForm');
    if (editStaffForm) {
        editStaffForm.addEventListener('submit', handleEditStaff);
    }
    
    // Edit buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-staff-btn')) {
            const btn = e.target.closest('.edit-staff-btn');
            const staffId = btn.getAttribute('data-staff-id');
            loadStaffForEdit(staffId);
        }
        
        if (e.target.closest('.delete-staff-btn')) {
            const btn = e.target.closest('.delete-staff-btn');
            const staffId = btn.getAttribute('data-staff-id');
            const staffName = btn.getAttribute('data-staff-name');
            confirmDeleteStaff(staffId, staffName);
        }
    });
}

function handleAddStaff(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Adding...';
    
    fetch('/add_staff_enhanced', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Staff member added successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addStaffModal')).hide();
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('Error: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Add Staff Member';
    });
}

function loadStaffForEdit(staffId) {
    const modalBody = document.getElementById('editStaffModalBody');

    // Show loading state
    modalBody.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Loading staff details...</p>
        </div>
    `;

    fetch(`/get_staff_details_enhanced?id=${staffId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Staff data loaded:', data.staff); // Debug log
            populateEditForm(data.staff);
        } else {
            showAlert('Error loading staff details: ' + data.error, 'danger');
            modalBody.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                    <p class="mt-3 text-danger">Failed to load staff details</p>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error loading staff details:', error);
        showAlert('Error: ' + error.message, 'danger');
        modalBody.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                <p class="mt-3 text-danger">Network error occurred</p>
            </div>
        `;
    });
}

// Load departments dynamically for edit form
async function loadDepartmentsForEdit(currentDepartment) {
    const editDepartmentSelect = document.getElementById('editDepartment');
    
    if (!editDepartmentSelect) {
        console.error('Edit department select not found');
        return;
    }
    
    try {
        const response = await fetch('/admin/get_departments_list');
        const result = await response.json();
        
        if (result.success && result.departments) {
            // Clear existing options except the first one
            editDepartmentSelect.innerHTML = '<option value="">Select Department</option>';
            
            // Add department options
            result.departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.department_name;
                option.textContent = dept.department_name;
                
                // Select the current department
                if (dept.department_name === currentDepartment) {
                    option.selected = true;
                }
                
                editDepartmentSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading departments for edit:', error);
    }
}

// Load positions dynamically for edit form
async function loadPositionsForEdit(currentPosition) {
    const editPositionSelect = document.getElementById('editDestination');
    
    if (!editPositionSelect) {
        console.error('Edit position select not found');
        return;
    }
    
    try {
        const response = await fetch('/admin/get_positions_list');
        const result = await response.json();
        
        if (result.success && result.positions) {
            // Clear existing options except the first one
            editPositionSelect.innerHTML = '<option value="">Select Position</option>';
            
            // Trim currentPosition for comparison
            const trimmedCurrentPosition = currentPosition ? currentPosition.trim() : '';
            
            // Add position options
            result.positions.forEach(pos => {
                const option = document.createElement('option');
                option.value = pos.position_name;
                option.textContent = pos.position_name;
                
                // Select the current position (case-sensitive comparison with trimming)
                if (pos.position_name.trim() === trimmedCurrentPosition) {
                    option.selected = true;
                }
                
                editPositionSelect.appendChild(option);
            });
            
            // Debug: Log if position was selected
            console.log('Current position:', trimmedCurrentPosition, 'Selected:', editPositionSelect.value);
        }
    } catch (error) {
        console.error('Error loading positions for edit:', error);
    }
}

function populateEditForm(staff) {
    const modalBody = document.getElementById('editStaffModalBody');

    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editStaffId" class="form-label">Staff ID *</label>
                    <input type="text" class="form-control" id="editStaffId" name="staff_id" value="${staff.staff_id || ''}" required>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editFirstName" class="form-label">First Name *</label>
                    <input type="text" class="form-control" id="editFirstName" name="first_name" value="${staff.first_name || ''}" required>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editLastName" class="form-label">Last Name *</label>
                    <input type="text" class="form-control" id="editLastName" name="last_name" value="${staff.last_name || ''}" required>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editDateOfBirth" class="form-label">Date of Birth</label>
                    <input type="date" class="form-control" id="editDateOfBirth" name="date_of_birth" value="${staff.date_of_birth || ''}">
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editDateOfJoining" class="form-label">Date of Joining</label>
                    <input type="date" class="form-control" id="editDateOfJoining" name="date_of_joining" value="${staff.date_of_joining || ''}">
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editDepartment" class="form-label">Department</label>
                    <select class="form-select" id="editDepartment" name="department">
                        <option value="">Select Department</option>
                        <!-- Will be populated dynamically -->
                    </select>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editDestination" class="form-label">Destination *</label>
                    <select class="form-select" id="editDestination" name="destination" required>
                        <option value="">Select Position</option>
                        <!-- Will be populated dynamically -->
                    </select>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editGender" class="form-label">Gender</label>
                    <select class="form-select" id="editGender" name="gender">
                        <option value="">Select Gender</option>
                        <option value="Male" ${staff.gender === 'Male' ? 'selected' : ''}>Male</option>
                        <option value="Female" ${staff.gender === 'Female' ? 'selected' : ''}>Female</option>
                        <option value="Other" ${staff.gender === 'Other' ? 'selected' : ''}>Other</option>
                    </select>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editPhone" class="form-label">Phone Number</label>
                    <input type="tel" class="form-control" id="editPhone" name="phone" value="${staff.phone || ''}">
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editEmail" class="form-label">Email ID</label>
                    <input type="email" class="form-control" id="editEmail" name="email" value="${staff.email || ''}">
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editShiftType" class="form-label">Shift Assign Type</label>
                    <select class="form-select" id="editShiftType" name="shift_type">
                        <option value="general" ${staff.shift_type === 'general' ? 'selected' : ''}>General</option>
                        <option value="morning" ${staff.shift_type === 'morning' ? 'selected' : ''}>Morning</option>
                        <option value="evening" ${staff.shift_type === 'evening' ? 'selected' : ''}>Evening</option>
                        <option value="night" ${staff.shift_type === 'night' ? 'selected' : ''}>Night</option>
                    </select>
                    <small class="form-text text-muted">
                        <i class="bi bi-info-circle"></i>
                        Department default: ${getDepartmentDefaultShift(staff.department) || 'Not set'}
                    </small>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="editFullName" class="form-label">Full Name (Auto-generated)</label>
                    <input type="text" class="form-control" id="editFullName" name="full_name" value="${staff.full_name || ''}" readonly>
                    <small class="form-text text-muted">This field is automatically generated from First Name + Last Name</small>
                </div>
            </div>
        </div>

        <!-- Salary Information Section -->
        <div class="rules-section">
            <h6 class="section-title">
                <i class="bi bi-currency-dollar text-success"></i> Salary Information
            </h6>
            <div class="rules-grid">
                <div class="rule-item">
                    <label for="editBasicSalary" class="form-label">
                        <i class="bi bi-cash-stack"></i> Base Monthly Salary *
                    </label>
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control" id="editBasicSalary" name="basic_salary" step="0.01" min="0" value="${staff.basic_salary || ''}" title="Enter base monthly salary">
                    </div>
                    <small class="form-text">Base monthly salary for standard working hours</small>
                </div>
                <div class="rule-item">
                    <label for="editHRA" class="form-label">
                        <i class="bi bi-house"></i> HRA
                    </label>
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control" id="editHRA" name="hra" step="0.01" min="0" value="${staff.hra || ''}" title="Enter HRA amount">
                    </div>
                    <small class="form-text">House Rent Allowance</small>
                </div>
                <div class="rule-item">
                    <label for="editTransportAllowance" class="form-label">
                        <i class="bi bi-bus-front"></i> Transport Allowance
                    </label>
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control" id="editTransportAllowance" name="transport_allowance" step="0.01" min="0" value="${staff.transport_allowance || ''}" title="Enter transport allowance">
                    </div>
                    <small class="form-text">Monthly transport allowance</small>
                </div>
                <div class="rule-item">
                    <label for="editOtherAllowances" class="form-label">
                        <i class="bi bi-plus-circle"></i> Other Allowances
                    </label>
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control" id="editOtherAllowances" name="other_allowances" step="0.01" min="0" value="${staff.other_allowances || ''}" title="Enter other allowances">
                    </div>
                    <small class="form-text">Other monthly allowances</small>
                </div>
            </div>
        </div>

        <!-- Deductions Section -->
        <div class="rules-section">
            <h6 class="section-title">
                <i class="bi bi-dash-circle text-danger"></i> Deductions
            </h6>
            <div class="rules-grid">
                <div class="rule-item">
                    <label for="editPFDeduction" class="form-label">
                        <i class="bi bi-piggy-bank"></i> PF Deduction
                    </label>
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control" id="editPFDeduction" name="pf_deduction" step="0.01" min="0" value="${staff.pf_deduction || ''}" title="Enter PF deduction amount">
                    </div>
                    <small class="form-text">Provident Fund deduction</small>
                </div>
                <div class="rule-item">
                    <label for="editESIDeduction" class="form-label">
                        <i class="bi bi-shield-plus"></i> ESI Deduction
                    </label>
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control" id="editESIDeduction" name="esi_deduction" step="0.01" min="0" value="${staff.esi_deduction || ''}" title="Enter ESI deduction amount">
                    </div>
                    <small class="form-text">Employee State Insurance deduction</small>
                </div>
                <div class="rule-item">
                    <label for="editProfessionalTax" class="form-label">
                        <i class="bi bi-receipt"></i> Professional Tax
                    </label>
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control" id="editProfessionalTax" name="professional_tax" step="0.01" min="0" value="${staff.professional_tax || ''}" title="Enter professional tax amount">
                    </div>
                    <small class="form-text">Monthly professional tax</small>
                </div>
                <div class="rule-item">
                    <label for="editOtherDeductions" class="form-label">
                        <i class="bi bi-dash-square"></i> Other Deductions
                    </label>
                    <div class="input-group">
                        <span class="input-group-text">₹</span>
                        <input type="number" class="form-control" id="editOtherDeductions" name="other_deductions" step="0.01" min="0" value="${staff.other_deductions || ''}" title="Enter other deductions">
                    </div>
                    <small class="form-text">Other monthly deductions</small>
                </div>
            </div>
        </div>
    `;

    // Set the staff ID for the form
    document.getElementById('editStaffDbId').value = staff.id;

    // Load departments dynamically for edit form
    loadDepartmentsForEdit(staff.department);
    
    // Load positions dynamically for edit form
    // Use destination field or fallback to position field
    const currentPosition = staff.destination || staff.position || '';
    loadPositionsForEdit(currentPosition);

    // Debug: Log salary field values
    console.log('Salary field values from database:');
    console.log('Basic Salary:', staff.basic_salary);
    console.log('HRA:', staff.hra);
    console.log('Transport Allowance:', staff.transport_allowance);
    console.log('Other Allowances:', staff.other_allowances);
    console.log('PF Deduction:', staff.pf_deduction);
    console.log('ESI Deduction:', staff.esi_deduction);
    console.log('Professional Tax:', staff.professional_tax);
    console.log('Other Deductions:', staff.other_deductions);

    // Verify that salary fields are populated correctly
    setTimeout(() => {
        const basicSalaryField = document.getElementById('editBasicSalary');
        const hraField = document.getElementById('editHRA');

        console.log('Form field values after population:');
        console.log('Basic Salary field value:', basicSalaryField ? basicSalaryField.value : 'Field not found');
        console.log('HRA field value:', hraField ? hraField.value : 'Field not found');

        // If basic salary field is empty but we have data, populate it manually
        if (basicSalaryField && !basicSalaryField.value && staff.basic_salary) {
            console.log('Manually setting basic salary field value');
            basicSalaryField.value = staff.basic_salary;
        }
    }, 100);

    // Add event listeners to update full name automatically
    const firstNameInput = document.getElementById('editFirstName');
    const lastNameInput = document.getElementById('editLastName');
    const fullNameInput = document.getElementById('editFullName');

    function updateFullName() {
        const firstName = firstNameInput.value.trim();
        const lastName = lastNameInput.value.trim();
        fullNameInput.value = `${firstName} ${lastName}`.trim();
    }

    firstNameInput.addEventListener('input', updateFullName);
    lastNameInput.addEventListener('input', updateFullName);
}

function handleEditStaff(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
    
    fetch('/update_staff_enhanced', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Staff member updated successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editStaffModal')).hide();
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('Error: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Update Staff Member';
    });
}

function confirmDeleteStaff(staffId, staffName) {
    if (confirm(`Are you sure you want to delete ${staffName}? This action cannot be undone.`)) {
        deleteStaff(staffId);
    }
}

function deleteStaff(staffId) {
    const formData = new FormData();
    formData.append('staff_id', staffId);
    
    fetch('/delete_staff', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Staff member deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('Error: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    });
}

function initializeExportFunctionality() {
    const exportBtn = document.getElementById('exportStaffExcelBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToExcel);
    }
}

function exportToExcel() {
    const exportBtn = document.getElementById('exportStaffExcelBtn');
    exportBtn.disabled = true;
    exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Exporting...';
    
    window.location.href = '/export_staff_excel';
    
    setTimeout(() => {
        exportBtn.disabled = false;
        exportBtn.innerHTML = '<i class="bi bi-file-earmark-excel"></i> Export to Excel';
    }, 2000);
}

function getDepartmentDefaultShift(department) {
    // This would ideally come from the server, but for now we'll use a simple lookup
    // In a real implementation, this data should be passed from the server
    const deptShiftMap = window.deptShiftMap || {};
    return deptShiftMap[department] || 'Not set';
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// Department Shift Management Functions
function initializeDepartmentShifts() {
    loadDepartmentShiftMappings();
    initializeDeptMappingForm();
}

function loadDepartmentShiftMappings() {
    const container = document.getElementById('departmentShiftMappings');
    if (!container) return;

    // Show loading state
    container.innerHTML = `
        <div class="col-12 text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading department shifts...</span>
            </div>
            <p class="text-muted mt-2">Loading department shift mappings...</p>
        </div>
    `;

    fetch('/api/department_shifts')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.mappings) {
                renderDepartmentShiftMappings(data.mappings);
            } else {
                showEmptyDepartmentShifts();
            }
        })
        .catch(error => {
            console.error('Error loading department shifts:', error);
            showDepartmentShiftsError();
        });
}

function renderDepartmentShiftMappings(mappings) {
    const container = document.getElementById('departmentShiftMappings');
    if (!container) return;

    console.log(`🔍 Rendering ${mappings.length} department shift mappings`);

    // Update count display in header
    updateMappingCount(mappings.length);

    if (mappings.length === 0) {
        showEmptyDepartmentShifts();
        return;
    }

    const mappingsHTML = mappings.map((mapping, index) => {
        console.log(`📋 Mapping ${index + 1}: ${mapping.department} -> ${mapping.default_shift_type}`);
        return `
        <div class="col-xl-4 col-lg-4 col-md-6 col-sm-12 mb-3">
            <div class="card h-100 dept-shift-card">
                <div class="card-body">
                    <div class="d-flex align-items-center mb-3">
                        <div class="dept-icon me-3">
                            <i class="bi bi-building-fill text-primary fs-4"></i>
                        </div>
                        <div>
                            <h6 class="card-title mb-1">${mapping.department}</h6>
                            <small class="text-muted">Department</small>
                        </div>
                    </div>
                    <div class="shift-info">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="text-muted">Default Shift:</span>
                            <span class="badge bg-info">${mapping.default_shift_type.charAt(0).toUpperCase() + mapping.default_shift_type.slice(1)}</span>
                        </div>
                        <div class="text-muted small">
                            <div>Created: ${mapping.created_at ? mapping.created_at.substring(0, 10) : 'N/A'}</div>
                            <div>Updated: ${mapping.updated_at ? mapping.updated_at.substring(0, 10) : 'N/A'}</div>
                        </div>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary flex-fill" onclick="editDeptMapping('${mapping.department}', '${mapping.default_shift_type}')" title="Edit mapping">
                            <i class="bi bi-pencil"></i> Edit
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteDeptMapping('${mapping.department}')" title="Delete mapping">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
    }).join('');

    container.innerHTML = mappingsHTML;
    
    console.log(`✅ Successfully rendered ${mappings.length} department shift mapping cards in rows of 3`);
}

function updateMappingCount(count) {
    const countElement = document.getElementById('mappingCount');
    const countBadge = document.getElementById('mappingCountBadge');
    const subtitle = document.getElementById('deptShiftSubtitle');
    
    if (countElement) {
        countElement.textContent = count;
    }
    
    if (countBadge) {
        if (count > 0) {
            countBadge.style.display = 'block';
        } else {
            countBadge.style.display = 'none';
        }
    }
    
    if (subtitle) {
        if (count > 0) {
            subtitle.textContent = `${count} department${count !== 1 ? 's' : ''} configured with default shift assignments`;
        } else {
            subtitle.textContent = 'Configure default shift types for departments';
        }
    }
}

function showEmptyDepartmentShifts() {
    const container = document.getElementById('departmentShiftMappings');
    if (!container) return;

    // Update count to 0
    updateMappingCount(0);

    container.innerHTML = `
        <div class="col-12">
            <div class="empty-state text-center py-4">
                <div class="empty-icon mb-3">
                    <i class="bi bi-clock-history text-muted" style="font-size: 3rem;"></i>
                </div>
                <h6 class="empty-title text-muted">No Department Mappings Found</h6>
                <p class="empty-text text-muted">Configure default shift types for departments to automate staff shift assignment during onboarding.</p>
                <button class="btn btn-success" data-bs-toggle="modal" data-bs-target="#addDeptMappingModal">
                    <i class="bi bi-plus-circle"></i> Add First Mapping
                </button>
            </div>
        </div>
    `;
}

function showDepartmentShiftsError() {
    const container = document.getElementById('departmentShiftMappings');
    if (!container) return;

    container.innerHTML = `
        <div class="col-12">
            <div class="alert alert-danger text-center">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Error loading department shifts</strong><br>
                <small>Please refresh the page or contact support if the problem persists.</small>
            </div>
        </div>
    `;
}

async function loadDepartmentsForDeptMapping() {
    const deptSelect = document.getElementById('deptAddDepartment');
    
    if (!deptSelect) {
        console.error('Department select for dept mapping not found');
        return;
    }
    
    try {
        const response = await fetch('/admin/get_departments_list');
        const result = await response.json();
        
        if (result.success && result.departments) {
            // Clear existing options
            deptSelect.innerHTML = '<option value="">Select Department</option>';
            
            // Add department options from database
            result.departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.department_name;
                option.textContent = dept.department_name;
                deptSelect.appendChild(option);
            });
            
            // Add custom department option at the end
            const customOption = document.createElement('option');
            customOption.value = 'custom';
            customOption.textContent = '+ Add Custom Department';
            deptSelect.appendChild(customOption);
            
            console.log(`✅ Loaded ${result.departments.length} departments for dept mapping dropdown`);
        }
    } catch (error) {
        console.error('Error loading departments for dept mapping:', error);
    }
}

function initializeDeptMappingForm() {
    const form = document.getElementById('addDeptMappingForm');
    if (form) {
        form.addEventListener('submit', handleDeptMappingSubmit);
    }

    // Load departments when modal is opened
    const modal = document.getElementById('addDeptMappingModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', function() {
            loadDepartmentsForDeptMapping();
        });
    }

    // Handle custom department toggle
    const deptSelect = document.getElementById('deptAddDepartment');
    const customDiv = document.getElementById('deptCustomDepartmentDiv');
    
    if (deptSelect && customDiv) {
        deptSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customDiv.style.display = 'block';
                document.getElementById('deptCustomDepartment').required = true;
            } else {
                customDiv.style.display = 'none';
                document.getElementById('deptCustomDepartment').required = false;
            }
        });
    }
}

function handleDeptMappingSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }

    // Handle custom department
    if (data.department === 'custom' && data.custom_department) {
        data.department = data.custom_department;
        delete data.custom_department;
    }

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalHTML = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Adding...';
    submitBtn.disabled = true;

    fetch('/api/department_shifts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('Department shift mapping added successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addDeptMappingModal')).hide();
            event.target.reset();
            loadDepartmentShiftMappings();
        } else {
            showAlert(result.message || 'Failed to add department mapping', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while adding the mapping', 'danger');
    })
    .finally(() => {
        submitBtn.innerHTML = originalHTML;
        submitBtn.disabled = false;
    });
}

function editDeptMapping(department, shiftType) {
    // For now, redirect to the dedicated department shifts page
    // This can be enhanced to show an inline edit modal later
    showAlert('Redirecting to Department Shift Management page...', 'info');
    setTimeout(() => {
        window.location.href = `/admin/department_shifts`;
    }, 1000);
}

function deleteDeptMapping(department) {
    if (!confirm(`Are you sure you want to delete the shift mapping for "${department}" department?`)) {
        return;
    }

    fetch('/api/department_shifts', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        },
        body: JSON.stringify({ department: department })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showAlert('Department shift mapping deleted successfully!', 'success');
            loadDepartmentShiftMappings();
        } else {
            showAlert(result.message || 'Failed to delete department mapping', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while deleting the mapping', 'danger');
    });
}

// Initialize department shifts when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add a small delay to ensure the main initialization is complete
    setTimeout(initializeDepartmentShifts, 100);
});