// Enhanced Staff Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the enhanced staff management system
    initializeEnhancedStaffManagement();
});

let currentStaffData = [];
let selectedStaff = new Set();

function initializeEnhancedStaffManagement() {
    // Load initial data
    loadDepartmentAnalytics();
    loadStaffData();
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Initialize filters
    initializeFilters();
}

function initializeEventListeners() {
    // Search and filter events
    document.getElementById('advancedSearch').addEventListener('input', debounce(applyFilters, 300));
    document.getElementById('departmentFilter').addEventListener('change', applyFilters);
    document.getElementById('positionFilter').addEventListener('change', applyFilters);
    document.getElementById('genderFilter').addEventListener('change', applyFilters);
    document.getElementById('dateFromFilter').addEventListener('change', applyFilters);
    document.getElementById('applyFiltersBtn').addEventListener('click', applyFilters);
    
    // Bulk operations
    document.getElementById('selectAllStaff').addEventListener('change', toggleSelectAll);
    document.getElementById('bulkUpdateBtn').addEventListener('click', showBulkUpdateModal);
    document.getElementById('bulkDeleteBtn').addEventListener('click', confirmBulkDelete);
    document.getElementById('exportAllStaffBtn').addEventListener('click', exportAllStaff);
    
    // Staff management
    document.getElementById('refreshStaffBtn').addEventListener('click', loadStaffData);
    document.getElementById('generateStaffIdBtn').addEventListener('click', generateStaffId);
    
    // Form submissions
    document.getElementById('addStaffForm').addEventListener('submit', handleAddStaff);
    document.getElementById('bulkImportForm').addEventListener('submit', handleBulkImport);
    
    // Department change for staff ID generation
    document.getElementById('newStaffDepartment').addEventListener('change', function() {
        if (this.value) {
            generateStaffId();
        }
    });
}

function loadDepartmentAnalytics() {
    fetch('/get_department_analytics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateAnalyticsCards(data.analytics);
                populateFilterOptions(data.analytics);
            }
        })
        .catch(error => {
            console.error('Error loading analytics:', error);
        });
}

function updateAnalyticsCards(analytics) {
    document.getElementById('totalStaff').textContent = analytics.total_staff;
    document.getElementById('recentJoinings').textContent = analytics.recent_joinings;
    document.getElementById('departmentCount').textContent = analytics.department_stats.length;
    
    // Calculate average tenure
    const avgTenure = analytics.department_stats.reduce((sum, dept) => 
        sum + (dept.avg_tenure_years || 0), 0) / analytics.department_stats.length;
    document.getElementById('avgTenure').textContent = avgTenure ? avgTenure.toFixed(1) : '0';
}

function populateFilterOptions(analytics) {
    const departmentFilter = document.getElementById('departmentFilter');
    const newStaffDepartment = document.getElementById('newStaffDepartment');
    
    // Clear existing options
    departmentFilter.innerHTML = '<option value="">All Departments</option>';
    newStaffDepartment.innerHTML = '<option value="">Select Department</option>';
    
    // Add department options
    analytics.department_stats.forEach(dept => {
        if (dept.department !== 'Unassigned') {
            const option1 = new Option(dept.department, dept.department);
            const option2 = new Option(dept.department, dept.department);
            departmentFilter.add(option1);
            newStaffDepartment.add(option2);
        }
    });
}

function loadStaffData(filters = {}) {
    const params = new URLSearchParams(filters);
    
    fetch(`/advanced_search_staff?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentStaffData = data.staff;
                renderStaffTable(data.staff);
            } else {
                showAlert('Error loading staff data: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error loading staff data:', error);
            showAlert('Error loading staff data', 'danger');
        });
}

function renderStaffTable(staffData) {
    const tbody = document.getElementById('staffTableBody');
    tbody.innerHTML = '';
    
    if (staffData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center text-muted py-4">
                    <i class="bi bi-people fs-1"></i>
                    <p class="mt-2">No staff members found</p>
                </td>
            </tr>
        `;
        return;
    }
    
    staffData.forEach(staff => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input staff-checkbox" 
                       value="${staff.id}" onchange="updateSelectedCount()">
            </td>
            <td>
                ${staff.photo_data ? 
                    `<img src="data:image/jpeg;base64,${staff.photo_data}" class="staff-photo" alt="Photo">` :
                    `<div class="staff-photo bg-secondary d-flex align-items-center justify-content-center text-white">
                        <i class="bi bi-person"></i>
                    </div>`
                }
            </td>
            <td><strong>${staff.staff_id}</strong></td>
            <td>${staff.full_name}</td>
            <td>
                <span class="badge bg-primary">${staff.department || 'Unassigned'}</span>
            </td>
            <td>${staff.position || 'N/A'}</td>
            <td>${staff.email || 'N/A'}</td>
            <td>${staff.phone || 'N/A'}</td>
            <td>${staff.date_of_joining || 'N/A'}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-primary" onclick="editStaff(${staff.id})" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-info" onclick="uploadPhoto(${staff.id})" title="Upload Photo">
                        <i class="bi bi-camera"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteStaff(${staff.id}, '${staff.full_name}')" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function applyFilters() {
    const filters = {
        search_term: document.getElementById('advancedSearch').value,
        department: document.getElementById('departmentFilter').value,
        position: document.getElementById('positionFilter').value,
        gender: document.getElementById('genderFilter').value,
        date_from: document.getElementById('dateFromFilter').value
    };
    
    // Remove empty filters
    Object.keys(filters).forEach(key => {
        if (!filters[key]) delete filters[key];
    });
    
    loadStaffData(filters);
}

function toggleSelectAll() {
    const selectAll = document.getElementById('selectAllStaff');
    const checkboxes = document.querySelectorAll('.staff-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll.checked;
    });
    
    updateSelectedCount();
}

function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.staff-checkbox:checked');
    const count = checkboxes.length;
    
    document.getElementById('selectedCount').textContent = `${count} selected`;
    
    // Enable/disable bulk action buttons
    const bulkUpdateBtn = document.getElementById('bulkUpdateBtn');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    
    bulkUpdateBtn.disabled = count === 0;
    bulkDeleteBtn.disabled = count === 0;
    
    // Update selected staff set
    selectedStaff.clear();
    checkboxes.forEach(checkbox => {
        selectedStaff.add(parseInt(checkbox.value));
    });
}

function generateStaffId() {
    const department = document.getElementById('newStaffDepartment').value;
    
    fetch(`/generate_staff_id?department=${encodeURIComponent(department)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('newStaffId').value = data.staff_id;
            }
        })
        .catch(error => {
            console.error('Error generating staff ID:', error);
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
            loadStaffData();
            loadDepartmentAnalytics();
            e.target.reset();
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

function handleBulkImport(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Importing...';
    
    fetch('/bulk_import_staff', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let message = `Successfully imported ${data.imported_count} out of ${data.total_rows} staff members.`;
            if (data.errors.length > 0) {
                message += `\n\nErrors:\n${data.errors.slice(0, 5).join('\n')}`;
                if (data.errors.length > 5) {
                    message += `\n... and ${data.errors.length - 5} more errors.`;
                }
            }
            showAlert(message, data.errors.length > 0 ? 'warning' : 'success');
            bootstrap.Modal.getInstance(document.getElementById('bulkImportModal')).hide();
            loadStaffData();
            loadDepartmentAnalytics();
            e.target.reset();
        } else {
            showAlert('Import failed: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Import Staff';
    });
}

function exportAllStaff() {
    window.open('/export_staff_excel', '_blank');
}

function uploadPhoto(staffId) {
    // Create file input dynamically
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('staff_id', staffId);
            formData.append('photo', file);
            
            fetch('/upload_staff_photo', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Photo uploaded successfully!', 'success');
                    loadStaffData();
                } else {
                    showAlert('Error uploading photo: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                showAlert('Error: ' + error.message, 'danger');
            });
        }
    };
    fileInput.click();
}

// Utility functions
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

function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}
