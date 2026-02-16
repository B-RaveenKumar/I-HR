/**
 * Staff Timetable View JavaScript
 * Handles peer-to-peer swaps, self-allocation, and request management
 */

let staffId = null;
let schoolId = null;
let timetableData = [];
let allocationsData = [];
let requestsData = [];
let periodsConfig = [];
let swapRequestsPollingInterval = null;

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

// Helper function to get CSRF token
function getCSRFToken() {
    return document.querySelector('input[name="csrf_token"]')?.value || '';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Use window variables set by Flask session in the HTML template
    staffId = window.staffId;
    schoolId = window.schoolId;
    
    console.log('============================================');
    console.log('STAFF TIMETABLE INITIALIZATION');
    console.log('============================================');
    console.log('Staff ID (user_id from session):', staffId);
    console.log('School ID:', schoolId);
    console.log('============================================');
    
    if (!staffId || !schoolId || staffId === 0 || schoolId === 0) {
        showAlert('Missing staff or school information. Please log in again.', 'error');
        console.error('Invalid session data - staffId:', staffId, 'schoolId:', schoolId);
        return;
    }
    
    loadPeriodsConfig();
    loadTimetable();
    loadSwapRequests();
    loadAllocations();
    
    // Start auto-refresh for swap requests (every 10 seconds)
    startSwapRequestsAutoRefresh();
});

// Cleanup polling when page is unloaded
window.addEventListener('beforeunload', function() {
    stopSwapRequestsAutoRefresh();
});

// ==========================================================================
// TIMETABLE LOADING & RENDERING
// ==========================================================================

function loadPeriodsConfig() {
    const url = `/api/timetable/periods?school_id=${schoolId}`;
    console.log('Loading periods configuration from:', url);
    
    fetch(url)
        .then(r => {
            if (!r.ok) {
                throw new Error(`HTTP error! status: ${r.status}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Periods config received:', data);
            if (data.success && data.periods) {
                periodsConfig = data.periods;
            }
        })
        .catch(err => {
            console.error('Error loading periods config:', err);
            // Continue with default - will use data from assignments
        });
}

function loadTimetable() {
    const url = `/api/timetable/staff?school_id=${schoolId}&staff_id=${staffId}`;
    console.log('Loading timetable from:', url);
    console.log('Staff ID:', staffId, 'School ID:', schoolId);
    
    fetch(url)
        .then(r => {
            if (!r.ok) {
                throw new Error(`HTTP error! status: ${r.status}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Timetable data received:', data);
            if (data.success) {
                timetableData = data.timetable || data.data || [];
                console.log(`Loaded ${timetableData.length} assignments for staff ${staffId}`);
                
                if (timetableData.length === 0) {
                    console.warn('No assignments found for this staff member. Admin needs to assign periods.');
                }
                
                renderWeeklyGrid();
            } else {
                throw new Error(data.error || 'Failed to load timetable');
            }
        })
        .catch(err => {
            console.error('Error loading timetable:', err);
            showAlert('Failed to load timetable: ' + err.message, 'error');
            // Show error in table
            const tbody = document.getElementById('timetableTableBody');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="7" style="padding: 2rem; text-align: center; color: #dc3545;">
                    <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
                    <p style="margin-top: 1rem;">Failed to load timetable</p>
                    <small>${err.message}</small>
                </td></tr>`;
            }
        });
}

function renderWeeklyGrid() {
    const tbody = document.getElementById('timetableTableBody');
    if (!tbody) {
        console.error('timetableTableBody container not found');
        return;
    }
    
    console.log('=== Rendering Weekly Grid ===');
    console.log('periodsConfig:', periodsConfig);
    console.log('timetableData (assignments):', timetableData);
    console.log('allocationsData:', allocationsData);
    
    // Determine max period number dynamically
    // First check periodsConfig from institution admin settings
    let maxPeriod = 0;
    
    if (periodsConfig && periodsConfig.length > 0) {
        maxPeriod = Math.max(...periodsConfig.map(p => p.period_number));
        console.log('Max period from config:', maxPeriod);
    }
    
    // Also check actual assignments and allocations
    if (timetableData.length > 0) {
        const assignmentMax = Math.max(...timetableData.map(t => t.period_number));
        maxPeriod = Math.max(maxPeriod, assignmentMax);
        console.log('Max period from assignments:', assignmentMax);
    }
    if (allocationsData.length > 0) {
        const allocationMax = Math.max(...allocationsData.map(a => a.period_number));
        maxPeriod = Math.max(maxPeriod, allocationMax);
        console.log('Max period from allocations:', allocationMax);
    }
    
    // Default to configured periods from settings, or 8 if nothing found
    if (maxPeriod === 0) {
        maxPeriod = 8; // Default to 8 periods instead of 9
        console.warn('No period configuration found, defaulting to', maxPeriod, 'periods');
    }
    
    console.log('Final: Rendering timetable with', maxPeriod, 'periods');
    
    let html = '';
    
    // Generate rows for each period (1 to maxPeriod)
    for (let period = 1; period <= maxPeriod; period++) {
        html += '<tr>';
        
        // First column: Period number with time if available
        const periodInfo = periodsConfig.find(p => p.period_number === period);
        if (periodInfo && periodInfo.start_time && periodInfo.end_time) {
            html += `<td class="period-number">
                <div style="font-weight: 600;">${period}</div>
                <div style="font-size: 0.7rem; color: #666; margin-top: 0.2rem;">${periodInfo.start_time} - ${periodInfo.end_time}</div>
            </td>`;
        } else {
            html += `<td class="period-number">${period}</td>`;
        }
        
        // Columns for Monday (1) to Saturday (6)
        for (let day = 1; day <= 6; day++) {
            const assignment = timetableData.find(t => t.day_of_week === day && t.period_number === period);
            const allocation = allocationsData.find(a => a.day_of_week === day && a.period_number === period);
            
            if (assignment) {
                // Admin-assigned period
                const cellClass = assignment.is_locked ? 'timetable-cell assigned locked' : 'timetable-cell assigned';
                const periodDisplay = assignment.period_name || 'Period ' + assignment.period_number;
                html += `
                    <td class="${cellClass}" 
                        ${!assignment.is_locked ? `onclick="showSwapModal(${assignment.id})" style="cursor: pointer;"` : ''}>
                        <div class="cell-content">
                            <div class="cell-subject">${assignment.class_subject || periodDisplay}</div>
                            ${assignment.start_time && assignment.end_time ? `<div class="cell-time">${assignment.start_time} - ${assignment.end_time}</div>` : ''}
                            ${assignment.is_locked 
                                ? '<span class="cell-badge badge-locked">LOCKED</span>' 
                                : '<span class="cell-badge badge-swap">REQUEST SWAP</span>'
                            }
                        </div>
                    </td>
                `;
            } else if (allocation) {
                // Self-allocated period
                html += `
                    <td class="timetable-cell allocated">
                        <div class="cell-content">
                            <div class="cell-subject">${allocation.class_subject || 'Allocated'}</div>
                            ${allocation.start_time && allocation.end_time ? `<div class="cell-time">${allocation.start_time} - ${allocation.end_time}</div>` : ''}
                            ${allocation.is_admin_locked ? '<span class="cell-badge badge-locked">ADMIN LOCKED</span>' : ''}
                        </div>
                    </td>
                `;
            } else {
                // Empty cell
                html += `
                    <td class="timetable-cell empty" title="No assignment for this period">
                        <div style="text-align: center; color: #aaa; font-size: 0.8rem; padding: 0.5rem;">
                            —
                        </div>
                    </td>
                `;
            }
        }
        
        html += '</tr>';
    }
    
    tbody.innerHTML = html;
    
    // Show helpful message if no assignments at all
    const infoContainer = document.getElementById('timetableInfoMessage');
    if (infoContainer) {
        if (timetableData.length === 0 && allocationsData.length === 0) {
            infoContainer.innerHTML = `
                <div style="margin-top: 1rem; padding: 1.5rem; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; text-align: center;">
                    <i class="bi bi-info-circle" style="font-size: 1.5rem; color: #856404;"></i>
                    <p style="margin: 0.5rem 0 0 0; color: #856404; font-weight: 500;">
                        No periods assigned yet
                    </p>
                    <small style="color: #856404;">
                        Please contact your school administrator to assign your timetable periods.<br>
                        Your Staff ID: <strong>${staffId}</strong> | School ID: <strong>${schoolId}</strong>
                    </small>
                </div>
            `;
        } else {
            infoContainer.innerHTML = '';
        }
    }
}

// ==========================================================================
// SWAP REQUESTS
// ==========================================================================

// Auto-refresh swap requests every 10 seconds
function startSwapRequestsAutoRefresh() {
    // Clear any existing interval
    if (swapRequestsPollingInterval) {
        clearInterval(swapRequestsPollingInterval);
    }
    
    // Set up polling every 10 seconds
    swapRequestsPollingInterval = setInterval(() => {
        console.log('[AUTO-REFRESH] Checking for new swap requests...');
        loadSwapRequests();
    }, 10000); // 10 seconds
    
    console.log('[AUTO-REFRESH] Swap requests polling started (10s interval)');
}

// Stop auto-refresh (useful for cleanup)
function stopSwapRequestsAutoRefresh() {
    if (swapRequestsPollingInterval) {
        clearInterval(swapRequestsPollingInterval);
        swapRequestsPollingInterval = null;
        console.log('[AUTO-REFRESH] Swap requests polling stopped');
    }
}

function loadSwapRequests() {
    fetch(`/api/timetable/requests?school_id=${schoolId}&staff_id=${staffId}`)
        .then(r => {
            if (!r.ok) {
                throw new Error(`HTTP error! status: ${r.status}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Swap requests loaded:', data);
            if (data.success) {
                requestsData = data.requests || [];
                renderSwapRequests();
            } else {
                console.error('Failed to load requests:', data.error);
                requestsData = [];
                renderSwapRequests();
                // Don't show error alert for empty requests
            }
        })
        .catch(err => {
            console.error('Error loading requests:', err);
            requestsData = [];
            renderSwapRequests();
            // Show error only for actual network/server errors
            if (err.message.includes('HTTP error')) {
                showAlert('Failed to load requests: ' + err.message, 'error');
            }
        });
}

function renderSwapRequests() {
    const container = document.getElementById('swapRequestsList');
    const count = document.getElementById('requestCount');
    
    console.log('[DEBUG] renderSwapRequests called, container:', container, 'requests:', requestsData.length);
    
    if (!container) {
        console.error('[ERROR] swapRequestsList container not found!');
        return;
    }
    
    const pendingRequests = requestsData.filter(r => r.status === 'pending');
    console.log('[DEBUG] Pending requests:', pendingRequests.length);
    
    if (count) {
        count.textContent = pendingRequests.length;
    }
    
    if (pendingRequests.length === 0) {
        container.innerHTML = '<p class="text-muted text-center p-4">No pending swap requests</p>';
        return;
    }
    
    container.innerHTML = pendingRequests.map(req => `
        <div class="request-card-compact">
            <div class="request-info">
                <div class="requester-name">
                    <i class="bi bi-person-circle"></i> ${req.requester_name}
                </div>
                <div class="request-period-info">
                    ${req.class_subject || 'Unknown Class'} • ${req.period_name || `Period ${req.period_number}`} • ${req.start_time} - ${req.end_time}
                </div>
            </div>
            <div class="request-actions-compact">
                <button class="btn-icon btn-accept-icon" onclick="acceptSwapRequest(${req.id})" title="Accept">
                    <i class="bi bi-check-lg"></i>
                </button>
                <button class="btn-icon btn-reject-icon" onclick="rejectSwapRequest(${req.id})" title="Reject">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function showSwapModal(assignmentId) {
    const assignment = timetableData.find(t => t.id === assignmentId);
    if (!assignment || assignment.is_locked) {
        showAlert('Cannot request swap for locked assignments', 'warning');
        return;
    }
    
    const modal = document.getElementById('swapModal');
    modal.dataset.assignmentId = assignmentId;
    modal.dataset.dayOfWeek = assignment.day_of_week;
    modal.dataset.periodNumber = assignment.period_number;
    
    const periodDisplay = assignment.period_name || `Period ${assignment.period_number}`;
    const dayName = DAYS[assignment.day_of_week];
    const timeDisplay = assignment.start_time && assignment.end_time ? ` (${assignment.start_time} - ${assignment.end_time})` : '';
    
    document.getElementById('swapPeriod').value = `${dayName} - ${periodDisplay}${timeDisplay}`;
    document.getElementById('swapDepartmentSelect').value = '';
    document.getElementById('swapStaffSelect').value = '';
    document.getElementById('swapStaffSelect').innerHTML = '<option value="">-- First select a department --</option>';
    document.getElementById('swapMessage').value = '';
    
    // Load available departments
    loadDepartments();
    
    new bootstrap.Modal(modal).show();
}

function loadDepartments() {
    const select = document.getElementById('swapDepartmentSelect');
    select.innerHTML = '<option value="">Loading departments...</option>';
    
    fetch(`/api/departments?school_id=${schoolId}`)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.departments && data.departments.length > 0) {
                select.innerHTML = '<option value="">-- Choose a department --</option>' +
                    data.departments.map(d => `<option value="${d}">${d}</option>`).join('');
            } else {
                select.innerHTML = '<option value="">No departments found</option>';
            }
        })
        .catch(err => {
            console.error('Error loading departments:', err);
            select.innerHTML = '<option value="">Error loading departments</option>';
        });
}

function loadStaffByDepartment() {
    const modal = document.getElementById('swapModal');
    const department = document.getElementById('swapDepartmentSelect').value;
    const staffSelect = document.getElementById('swapStaffSelect');
    
    if (!department) {
        staffSelect.innerHTML = '<option value="">-- First select a department --</option>';
        return;
    }
    
    const dayOfWeek = modal.dataset.dayOfWeek;
    const periodNumber = modal.dataset.periodNumber;
    
    staffSelect.innerHTML = '<option value="">Loading available staff...</option>';
    
    // Fetch staff who are free at this time in selected department
    fetch(`/api/staff/available-for-period?school_id=${schoolId}&staff_id=${staffId}&day_of_week=${dayOfWeek}&period_number=${periodNumber}&department=${encodeURIComponent(department)}`)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.staff && data.staff.length > 0) {
                staffSelect.innerHTML = '<option value="">-- Choose a colleague --</option>' +
                    data.staff.map(s => `<option value="${s.id}">${s.full_name}</option>`).join('');
            } else {
                staffSelect.innerHTML = '<option value="">No staff available in this department at this time</option>';
            }
        })
        .catch(err => {
            console.error('Error loading available staff:', err);
            staffSelect.innerHTML = '<option value="">Error loading staff</option>';
        });
}

function submitSwapRequest() {
    const modal = document.getElementById('swapModal');
    const assignmentId = modal.dataset.assignmentId;
    const targetStaffId = document.getElementById('swapStaffSelect').value;
    const reason = document.getElementById('swapMessage').value;
    
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
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(result => {
        if (result.success) {
            showAlert('Swap request sent successfully!', 'success');
            bootstrap.Modal.getInstance(modal).hide();
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
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
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
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
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
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
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
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
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
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
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
