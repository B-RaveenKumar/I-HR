// Department Shifts Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize event listeners
    initializeEventListeners();
});

function initializeFormHandlers() {
    // Add Mapping Form
    const addMappingForm = document.getElementById('addMappingForm');
    if (addMappingForm) {
        addMappingForm.addEventListener('submit', handleAddMapping);
    }
    
    // Edit Mapping Form
    const editMappingForm = document.getElementById('editMappingForm');
    if (editMappingForm) {
        editMappingForm.addEventListener('submit', handleEditMapping);
    }
    
    // Department selection change
    const addDepartment = document.getElementById('addDepartment');
    if (addDepartment) {
        addDepartment.addEventListener('change', handleDepartmentChange);
    }
}

function initializeEventListeners() {
    // Edit buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.edit-mapping-btn')) {
            const btn = e.target.closest('.edit-mapping-btn');
            const department = btn.getAttribute('data-department');
            const shiftType = btn.getAttribute('data-shift-type');
            populateEditForm(department, shiftType);
        }
        
        if (e.target.closest('.delete-mapping-btn')) {
            const btn = e.target.closest('.delete-mapping-btn');
            const department = btn.getAttribute('data-department');
            confirmDeleteMapping(department);
        }
    });
    
    // Bulk action buttons
    const bulkUpdateBtn = document.getElementById('bulkUpdateBtn');
    if (bulkUpdateBtn) {
        bulkUpdateBtn.addEventListener('click', handleBulkUpdate);
    }
    
    const previewChangesBtn = document.getElementById('previewChangesBtn');
    if (previewChangesBtn) {
        previewChangesBtn.addEventListener('click', handlePreviewChanges);
    }
}

function handleDepartmentChange(e) {
    const customDiv = document.getElementById('customDepartmentDiv');
    const customInput = document.getElementById('customDepartment');
    
    if (e.target.value === 'custom') {
        customDiv.style.display = 'block';
        customInput.required = true;
    } else {
        customDiv.style.display = 'none';
        customInput.required = false;
        customInput.value = '';
    }
}

function handleAddMapping(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    // Determine the department name
    const selectedDept = formData.get('department');
    const customDept = formData.get('custom_department');
    const finalDepartment = selectedDept === 'custom' ? customDept : selectedDept;
    
    if (!finalDepartment || !formData.get('shift_type')) {
        showAlert('Please fill in all required fields', 'danger');
        return;
    }
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Adding...';
    
    // Create new FormData with final department name
    const finalFormData = new FormData();
    finalFormData.append('department', finalDepartment);
    finalFormData.append('shift_type', formData.get('shift_type'));
    
    fetch('/admin/add_department_shift', {
        method: 'POST',
        body: finalFormData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Department shift mapping added successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addMappingModal')).hide();
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
        submitBtn.innerHTML = 'Add Mapping';
    });
}

function populateEditForm(department, shiftType) {
    document.getElementById('editOriginalDepartment').value = department;
    document.getElementById('editDepartment').value = department;
    document.getElementById('editShiftType').value = shiftType;
}

function handleEditMapping(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
    
    fetch('/admin/update_department_shift', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Department shift mapping updated successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editMappingModal')).hide();
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
        submitBtn.innerHTML = 'Update Mapping';
    });
}

function confirmDeleteMapping(department) {
    if (confirm(`Are you sure you want to delete the shift mapping for "${department}" department? This action cannot be undone.`)) {
        deleteMapping(department);
    }
}

function deleteMapping(department) {
    const formData = new FormData();
    formData.append('department', department);
    
    fetch('/admin/delete_department_shift', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Department shift mapping deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showAlert('Error: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    });
}

function handleBulkUpdate() {
    if (confirm('This will update the shift types of all existing staff members based on their department mappings. Are you sure you want to continue?')) {
        const btn = document.getElementById('bulkUpdateBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
        
        fetch('/admin/bulk_update_staff_shifts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`Successfully updated ${data.updated_count} staff members' shift assignments!`, 'success');
            } else {
                showAlert('Error: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            showAlert('Error: ' + error.message, 'danger');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Update Existing Staff Shifts';
        });
    }
}

function handlePreviewChanges() {
    fetch('/admin/preview_staff_shift_changes', {
        method: 'GET',
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showPreviewModal(data.changes);
        } else {
            showAlert('Error: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showAlert('Error: ' + error.message, 'danger');
    });
}

function showPreviewModal(changes) {
    let modalHTML = `
        <div class="modal fade" id="previewModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title">Preview Shift Changes</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p><strong>${changes.length}</strong> staff members will be affected:</p>
                        <div class="table-responsive">
                            <table class="table table-sm table-striped">
                                <thead>
                                    <tr>
                                        <th>Staff Name</th>
                                        <th>Department</th>
                                        <th>Current Shift</th>
                                        <th>New Shift</th>
                                    </tr>
                                </thead>
                                <tbody>
    `;
    
    changes.forEach(change => {
        modalHTML += `
            <tr>
                <td>${change.staff_name}</td>
                <td>${change.department}</td>
                <td><span class="badge bg-secondary">${change.current_shift}</span></td>
                <td><span class="badge bg-primary">${change.new_shift}</span></td>
            </tr>
        `;
    });
    
    modalHTML += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing preview modal if any
    const existingModal = document.getElementById('previewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add new modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
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
