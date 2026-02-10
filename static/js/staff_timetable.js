/**
 * Staff Timetable View JavaScript
 * Handles peer-to-peer swaps, self-allocation, and request management
 */

let staffId = null;
let schoolId = null;
let timetableData = [];
let allocationsData = [];
let requestsData = [];

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    staffId = sessionStorage.getItem('staff_id') || new URLSearchParams(window.location.search).get('staff_id');
    schoolId = sessionStorage.getItem('school_id') || new URLSearchParams(window.location.search).get('school_id');
    
    loadTimetable();
    loadSwapRequests();
    loadAllocations();
});

// ==========================================================================
// TIMETABLE LOADING & RENDERING
// ==========================================================================

function loadTimetable() {
    fetch(`/api/timetable/staff?school_id=${schoolId}&staff_id=${staffId}`)
        .then(r => r.json())
        .then(data => {
            timetableData = data.timetable || [];
            renderWeeklyGrid();
        })
        .catch(err => {
            console.error('Error loading timetable:', err);
            showAlert('Failed to load timetable', 'error');
        });
}

function renderWeeklyGrid() {
    const container = document.getElementById('weeklyGrid');
    
    // Create day columns
    let html = '';
    for (let dayNum = 0; dayNum < 7; dayNum++) {
        const dayAssignments = timetableData.filter(t => t.day_of_week === dayNum);
        const dayAllocations = allocationsData.filter(a => a.day_of_week === dayNum);
        
        html += `
            <div class="day-column">
                <div class="day-header">${DAYS[dayNum]}</div>
        `;
        
        // Get all periods for this day
        const periods = [...new Set([...dayAssignments.map(t => t.period_number), ...dayAllocations.map(a => a.period_number)])];
        
        if (periods.length === 0) {
            html += '<div style="color: white; text-align: center; padding: 1rem; font-size: 0.85rem;">No assignments</div>';
        } else {
            periods.forEach(periodNum => {
                const assignment = dayAssignments.find(t => t.period_number === periodNum);
                const allocation = dayAllocations.find(a => a.period_number === periodNum);
                
                if (assignment) {
                    // Assigned slot
                    html += `
                        <div class="period-slot assigned" onclick="showSwapModal(${assignment.id}, '${assignment.period_name}')">
                            <div class="slot-time">${assignment.start_time} - ${assignment.end_time}</div>
                            <div class="slot-content">${assignment.period_name || `Period ${assignment.period_number}`}</div>
                            ${assignment.class_subject ? `<div class="slot-content" style="font-size: 0.8rem; color: white;">${assignment.class_subject}</div>` : ''}
                            ${assignment.is_locked 
                                ? '<span class="slot-badge" style="background: #dc3545;">LOCKED</span>' 
                                : '<span class="slot-badge" style="background: #007bff;">REQUEST SWAP</span>'
                            }
                        </div>
                    `;
                } else if (allocation) {
                    // Self-allocated slot
                    html += `
                        <div class="period-slot allocated" style="background: #e8f5e9; border-color: #28a745;">
                            <div class="slot-time">${allocation.start_time} - ${allocation.end_time}</div>
                            <div class="slot-content">${allocation.period_name || `Period ${allocation.period_number}`}</div>
                            <div class="slot-content" style="font-size: 0.8rem; color: #1b5e20;">${allocation.class_subject}</div>
                            ${allocation.is_admin_locked 
                                ? '<span class="slot-badge" style="background: #ff6f00;">ADMIN LOCKED</span>'
                                : ''
                            }
                        </div>
                    `;
                } else {
                    // Empty slot - can self-allocate
                    html += `
                        <div class="period-slot empty" style="cursor: pointer;" onclick="showAllocateModal(${dayNum}, ${periodNum}, '${DAYS[dayNum]}')">
                            <div style="color: white; text-align: center;">
                                <i class="bi bi-plus-circle"></i>
                                <div style="font-size: 0.8rem; margin-top: 0.25rem;">Available</div>
                            </div>
                        </div>
                    `;
                }
            });
        }
        
        html += '</div>';
    }
    
    container.innerHTML = html;
}

// ==========================================================================
// SWAP REQUESTS
// ==========================================================================

function loadSwapRequests() {
    fetch(`/api/timetable/requests?school_id=${schoolId}&staff_id=${staffId}`)
        .then(r => r.json())
        .then(data => {
            requestsData = data.requests || [];
            renderSwapRequests();
        })
        .catch(err => {
            console.error('Error loading requests:', err);
            showAlert('Failed to load requests', 'error');
        });
}

function renderSwapRequests() {
    const container = document.getElementById('requestsContainer');
    const count = document.getElementById('requestCount');
    
    const pendingRequests = requestsData.filter(r => r.status === 'pending');
    count.textContent = pendingRequests.length;
    
    if (pendingRequests.length === 0) {
        container.innerHTML = '<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: white;"><i class="bi bi-inbox"></i> No pending requests</div>';
        return;
    }
    
    container.innerHTML = pendingRequests.map(req => `
        <div class="request-card">
            <div class="request-header">
                <div class="request-from">
                    <i class="bi bi-person-circle"></i> ${req.requester_name}
                    <small style="display: block; color: white; margin-top: 0.25rem;">${req.requester_dept}</small>
                </div>
                <span class="request-status status-pending">
                    <i class="bi bi-clock"></i> Pending
                </span>
            </div>
            
            <div class="request-details">
                <div class="detail-row">
                    <span class="detail-label">Period:</span>
                    <span class="detail-value">${req.period_name || `Period ${req.period_number}`}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span class="detail-value">${req.start_time} - ${req.end_time}</span>
                </div>
            </div>
            
            ${req.reason ? `<div class="request-reason">"${req.reason}"</div>` : ''}
            
            <div class="request-actions">
                <button class="btn-accept" onclick="acceptSwapRequest(${req.id})">
                    <i class="bi bi-check-circle"></i> Accept
                </button>
                <button class="btn-reject" onclick="rejectSwapRequest(${req.id})">
                    <i class="bi bi-x-circle"></i> Reject
                </button>
            </div>
        </div>
    `).join('');
}

function showSwapModal(assignmentId, periodName) {
    const assignment = timetableData.find(t => t.id === assignmentId);
    if (!assignment || assignment.is_locked) {
        showAlert('Cannot request swap for locked assignments', 'warning');
        return;
    }
    
    document.getElementById('swapModal').dataset.assignmentId = assignmentId;
    document.getElementById('yourPeriod').value = periodName;
    document.getElementById('targetStaffSelect').value = '';
    document.getElementById('swapReason').value = '';
    
    // Populate available staff (same school, different department allowed)
    loadAvailableStaffForSwap();
    
    new bootstrap.Modal(document.getElementById('swapModal')).show();
}

function loadAvailableStaffForSwap() {
    fetch(`/api/staff/available?school_id=${schoolId}&exclude_self=true`)
        .then(r => r.json())
        .then(data => {
            const select = document.getElementById('targetStaffSelect');
            select.innerHTML = '<option>-- Choose staff member --</option>' +
                (data.staff || []).map(s => `<option value="${s.id}">${s.full_name} (${s.department})</option>`).join('');
        })
        .catch(err => console.error('Error loading staff:', err));
}

function submitSwapRequest() {
    const assignmentId = document.getElementById('swapModal').dataset.assignmentId;
    const targetStaffId = document.getElementById('targetStaffSelect').value;
    const reason = document.getElementById('swapReason').value;
    
    if (!targetStaffId) {
        showAlert('Please select a staff member', 'error');
        return;
    }
    
    const data = {
        school_id: schoolId,
        requester_staff_id: staffId,
        assignment_id: assignmentId,
        target_staff_id: targetStaffId,
        reason: reason
    };
    
    fetch('/api/timetable/swap/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Swap request sent successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('swapModal')).hide();
            loadSwapRequests();
        } else {
            showAlert(result.error || 'Failed to send request', 'error');
        }
    })
    .catch(err => {
        console.error('Error submitting request:', err);
        showAlert('Error sending request', 'error');
    });
}

function acceptSwapRequest(requestId) {
    if (!confirm('Accept this swap request?')) return;
    
    const data = {
        school_id: schoolId,
        request_id: requestId,
        accept: true,
        response_reason: ''
    };
    
    fetch('/api/timetable/swap/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Swap request accepted!', 'success');
            loadSwapRequests();
            loadTimetable();
        } else {
            showAlert(result.error || 'Failed to accept request', 'error');
        }
    })
    .catch(err => console.error('Error accepting request:', err));
}

function rejectSwapRequest(requestId) {
    if (!confirm('Reject this swap request?')) return;
    
    const data = {
        school_id: schoolId,
        request_id: requestId,
        accept: false,
        response_reason: 'Request rejected'
    };
    
    fetch('/api/timetable/swap/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Swap request rejected', 'info');
            loadSwapRequests();
        } else {
            showAlert(result.error || 'Failed to reject request', 'error');
        }
    })
    .catch(err => console.error('Error rejecting request:', err));
}

// ==========================================================================
// SELF-ALLOCATIONS
// ==========================================================================

function loadAllocations() {
    fetch(`/api/timetable/allocations?school_id=${schoolId}&staff_id=${staffId}`)
        .then(r => r.json())
        .then(data => {
            allocationsData = data.allocations || [];
            renderAllocationsTable();
            renderWeeklyGrid(); // Re-render to show allocations
        })
        .catch(err => console.error('Error loading allocations:', err));
}

function renderAllocationsTable() {
    const tbody = document.getElementById('allocationsTable');
    
    if (allocationsData.length === 0) {
        tbody.innerHTML = '<tr style="background: #f8f9fa;"><td colspan="6" style="padding: 2rem; text-align: center; color: white;"><i class="bi bi-inbox"></i> No self-allocations yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = allocationsData.map(a => `
        <tr>
            <td style="padding: 1rem;">${DAYS[a.day_of_week]}</td>
            <td style="padding: 1rem;">${a.period_name || `Period ${a.period_number}`}</td>
            <td style="padding: 1rem; font-family: monospace;">${a.start_time} - ${a.end_time}</td>
            <td style="padding: 1rem;">${a.class_subject}</td>
            <td style="padding: 1rem;">
                ${a.is_admin_locked 
                    ? '<span class="allocation-status-locked"><i class="bi bi-lock"></i> Admin Locked</span>'
                    : '<span style="background: #d4edda; color: #155724; padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.8rem;">Editable</span>'
                }
            </td>
            <td style="padding: 1rem; text-align: center;">
                <div style="display: flex; gap: 0.5rem; justify-content: center;">
                    ${!a.is_admin_locked 
                        ? `<button class="btn btn-edit-allocation btn-sm" onclick="editAllocation(${a.id})"><i class="bi bi-pencil"></i></button>`
                        : '<button class="btn btn-disabled btn-sm" disabled><i class="bi bi-pencil"></i></button>'
                    }
                    ${!a.is_admin_locked 
                        ? `<button class="btn btn-delete-allocation btn-sm" onclick="deleteAllocation(${a.id})"><i class="bi bi-trash"></i></button>`
                        : '<button class="btn btn-disabled btn-sm" disabled><i class="bi bi-trash"></i></button>'
                    }
                </div>
            </td>
        </tr>
    `).join('');
}

function showAllocateModal(dayNum, periodNum, dayName) {
    // Get period details
    fetch(`/api/timetable/period/${periodNum}?school_id=${schoolId}`)
        .then(r => r.json())
        .then(data => {
            const period = data.period;
            document.getElementById('allocationDay').textContent = dayName;
            document.getElementById('allocationTime').textContent = `${period.start_time} - ${period.end_time}`;
            document.getElementById('allocationPeriod').textContent = periodNum;
            document.getElementById('allocateModal').dataset.dayNum = dayNum;
            document.getElementById('allocateModal').dataset.periodNum = periodNum;
            document.getElementById('classSubject').value = '';
            new bootstrap.Modal(document.getElementById('allocateModal')).show();
        })
        .catch(err => console.error('Error loading period:', err));
}

function submitAllocation() {
    const dayNum = document.getElementById('allocateModal').dataset.dayNum;
    const periodNum = document.getElementById('allocateModal').dataset.periodNum;
    const classSubject = document.getElementById('classSubject').value;
    
    if (!classSubject) {
        showAlert('Please enter class/subject name', 'error');
        return;
    }
    
    const data = {
        school_id: schoolId,
        staff_id: staffId,
        day_of_week: dayNum,
        period_number: periodNum,
        class_subject: classSubject
    };
    
    fetch('/api/timetable/allocation/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Slot allocated successfully! (Admin can now lock it)', 'success');
            bootstrap.Modal.getInstance(document.getElementById('allocateModal')).hide();
            loadAllocations();
        } else {
            showAlert(result.error || 'Failed to allocate slot', 'error');
        }
    })
    .catch(err => {
        console.error('Error allocating slot:', err);
        showAlert('Error allocating slot', 'error');
    });
}

function editAllocation(allocationId) {
    const allocation = allocationsData.find(a => a.id === allocationId);
    if (allocation.is_admin_locked) {
        showAlert('Cannot edit admin-locked allocations', 'error');
        return;
    }
    
    const newSubject = prompt('Edit class/subject:', allocation.class_subject);
    if (!newSubject) return;
    
    const data = {
        school_id: schoolId,
        allocation_id: allocationId,
        class_subject: newSubject
    };
    
    fetch('/api/timetable/allocation/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Allocation updated', 'success');
            loadAllocations();
        } else {
            showAlert('Failed to update allocation', 'error');
        }
    })
    .catch(err => console.error('Error updating:', err));
}

function deleteAllocation(allocationId) {
    const allocation = allocationsData.find(a => a.id === allocationId);
    if (allocation.is_admin_locked) {
        showAlert('Cannot delete admin-locked allocations', 'error');
        return;
    }
    
    if (!confirm('Delete this allocation?')) return;
    
    const data = {
        school_id: schoolId,
        staff_id: staffId,
        allocation_id: allocationId
    };
    
    fetch('/api/timetable/allocation/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Allocation deleted', 'success');
            loadAllocations();
        } else {
            showAlert('Failed to delete allocation', 'error');
        }
    })
    .catch(err => console.error('Error deleting:', err));
}

// ==========================================================================
// UTILITY FUNCTIONS
// ==========================================================================

function showAlert(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : type === 'success' ? 'alert-success' : type === 'warning' ? 'alert-warning' : 'alert-info';
    const iconClass = type === 'error' ? 'bi-exclamation-circle' : type === 'success' ? 'bi-check-circle' : type === 'warning' ? 'bi-exclamation-triangle' : 'bi-info-circle';
    
    const alertHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <i class="bi ${iconClass}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHTML);
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) alert.remove();
    }, 5000);
}

function refreshTimetable() {
    loadTimetable();
    loadSwapRequests();
    loadAllocations();
    showAlert('Timetable refreshed', 'success');
}
