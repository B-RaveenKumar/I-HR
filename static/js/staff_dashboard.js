document.addEventListener('DOMContentLoaded', function() {
    // Helper function to get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }

    // Quota Management Functions
    function loadStaffQuotas() {
        const staffId = window.currentStaffId;
        if (!staffId) {
            console.error('No staff ID available');
            return;
        }

        fetch(`/api/staff/${staffId}/quotas`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateQuotaDisplay(data.quotas);
                } else {
                    console.error('Failed to load quotas:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading quotas:', error);
            });
    }

    function updateQuotaDisplay(quotas) {
        // Update Leave Quotas
        if (quotas.leave) {
            document.getElementById('leaveAllocatedQuota').textContent = quotas.leave.allocated || 0;
            document.getElementById('leaveUsedQuota').textContent = quotas.leave.used || 0;
            document.getElementById('leaveRemainingQuota').textContent = quotas.leave.remaining || 0;
        }

        // Update OD Quotas
        if (quotas.od) {
            document.getElementById('odAllocatedQuota').textContent = quotas.od.allocated || 0;
            document.getElementById('odUsedQuota').textContent = quotas.od.used || 0;
            document.getElementById('odRemainingQuota').textContent = quotas.od.remaining || 0;
        }

        // Update Permission Quotas (in hours)
        if (quotas.permission) {
            document.getElementById('permissionAllocatedQuota').textContent = quotas.permission.allocated || 0;
            document.getElementById('permissionUsedQuota').textContent = quotas.permission.used || 0;
            document.getElementById('permissionRemainingQuota').textContent = quotas.permission.remaining || 0;
        }
    }

    function calculateLeaveDays() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            if (end >= start) {
                const timeDiff = Math.abs(end.getTime() - start.getTime());
                const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24)) + 1;
                
                document.getElementById('leaveTotalDays').textContent = `${daysDiff} days`;
                
                // Calculate remaining after this application
                const currentRemaining = parseInt(document.getElementById('leaveRemainingQuota').textContent) || 0;
                const remainingAfter = currentRemaining - daysDiff;
                document.getElementById('leaveRemainingAfter').textContent = `${remainingAfter} days`;
                
                // Show warning if exceeding quota
                const alertDiv = document.getElementById('leaveQuotaAlert');
                if (remainingAfter < 0) {
                    alertDiv.classList.remove('d-none');
                    alertDiv.className = 'alert alert-danger mb-3';
                    document.getElementById('leaveQuotaAlertText').textContent = 
                        `This application exceeds your remaining quota by ${Math.abs(remainingAfter)} days.`;
                } else if (remainingAfter <= 2) {
                    alertDiv.classList.remove('d-none');
                    alertDiv.className = 'alert alert-warning mb-3';
                    document.getElementById('leaveQuotaAlertText').textContent = 
                        `After this application, you will have only ${remainingAfter} days remaining.`;
                } else {
                    alertDiv.classList.add('d-none');
                }
            }
        } else {
            document.getElementById('leaveTotalDays').textContent = '0 days';
            document.getElementById('leaveRemainingAfter').textContent = '-';
            document.getElementById('leaveQuotaAlert').classList.add('d-none');
        }
    }

    function calculateODDays() {
        const startDate = document.getElementById('dutyStartDate').value;
        const endDate = document.getElementById('dutyEndDate').value;
        
        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            if (end >= start) {
                const timeDiff = Math.abs(end.getTime() - start.getTime());
                const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24)) + 1;
                
                document.getElementById('odTotalDays').textContent = `${daysDiff} days`;
                
                // Calculate remaining after this application
                const currentRemaining = parseInt(document.getElementById('odRemainingQuota').textContent) || 0;
                const remainingAfter = currentRemaining - daysDiff;
                document.getElementById('odRemainingAfter').textContent = `${remainingAfter} days`;
                
                // Show warning if exceeding quota
                const alertDiv = document.getElementById('odQuotaAlert');
                if (remainingAfter < 0) {
                    alertDiv.classList.remove('d-none');
                    alertDiv.className = 'alert alert-danger mb-3';
                    document.getElementById('odQuotaAlertText').textContent = 
                        `This application exceeds your remaining quota by ${Math.abs(remainingAfter)} days.`;
                } else if (remainingAfter <= 2) {
                    alertDiv.classList.remove('d-none');
                    alertDiv.className = 'alert alert-warning mb-3';
                    document.getElementById('odQuotaAlertText').textContent = 
                        `After this application, you will have only ${remainingAfter} days remaining.`;
                } else {
                    alertDiv.classList.add('d-none');
                }
            }
        } else {
            document.getElementById('odTotalDays').textContent = '0 days';
            document.getElementById('odRemainingAfter').textContent = '-';
            document.getElementById('odQuotaAlert').classList.add('d-none');
        }
    }

    function calculatePermissionHours() {
        const startTime = document.getElementById('permissionStartTime').value;
        const endTime = document.getElementById('permissionEndTime').value;
        
        if (startTime && endTime) {
            const start = new Date(`2000-01-01 ${startTime}`);
            const end = new Date(`2000-01-01 ${endTime}`);
            
            if (end > start) {
                const timeDiff = end.getTime() - start.getTime();
                const hours = timeDiff / (1000 * 3600);
                
                document.getElementById('permissionTotalHours').textContent = `${hours.toFixed(1)} hours`;
                
                // Calculate remaining after this application
                const currentRemaining = parseFloat(document.getElementById('permissionRemainingQuota').textContent) || 0;
                const remainingAfter = currentRemaining - hours;
                document.getElementById('permissionRemainingAfter').textContent = `${remainingAfter.toFixed(1)} hours`;
                
                // Show warning if exceeding quota
                const alertDiv = document.getElementById('permissionQuotaAlert');
                if (remainingAfter < 0) {
                    alertDiv.classList.remove('d-none');
                    alertDiv.className = 'alert alert-danger mb-3';
                    document.getElementById('permissionQuotaAlertText').textContent = 
                        `This application exceeds your remaining quota by ${Math.abs(remainingAfter).toFixed(1)} hours.`;
                } else if (remainingAfter <= 2) {
                    alertDiv.classList.remove('d-none');
                    alertDiv.className = 'alert alert-warning mb-3';
                    document.getElementById('permissionQuotaAlertText').textContent = 
                        `After this application, you will have only ${remainingAfter.toFixed(1)} hours remaining.`;
                } else {
                    alertDiv.classList.add('d-none');
                }
            }
        } else {
            document.getElementById('permissionTotalHours').textContent = '0 hours';
            document.getElementById('permissionRemainingAfter').textContent = '-';
            document.getElementById('permissionQuotaAlert').classList.add('d-none');
        }
    }

    // Load quotas when modals are opened
    document.getElementById('applyLeaveModal')?.addEventListener('shown.bs.modal', function() {
        loadStaffQuotas();
    });

    document.getElementById('applyOnDutyModal')?.addEventListener('shown.bs.modal', function() {
        loadStaffQuotas();
    });

    document.getElementById('applyPermissionModal')?.addEventListener('shown.bs.modal', function() {
        loadStaffQuotas();
    });

    // Add event listeners for real-time calculation
    document.getElementById('startDate')?.addEventListener('change', calculateLeaveDays);
    document.getElementById('endDate')?.addEventListener('change', calculateLeaveDays);
    
    document.getElementById('dutyStartDate')?.addEventListener('change', calculateODDays);
    document.getElementById('dutyEndDate')?.addEventListener('change', calculateODDays);
    
    document.getElementById('permissionStartTime')?.addEventListener('change', calculatePermissionHours);
    document.getElementById('permissionEndTime')?.addEventListener('change', calculatePermissionHours);

    // Initialize attendance chart with real data
    const ctx = document.getElementById('attendanceChart')?.getContext('2d');
    if (ctx) {
        fetch('/get_attendance_summary')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const attendanceChart = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Present', 'Absent', 'Late', 'Leave'],
                            datasets: [{
                                data: [data.present, data.absent, data.late, data.leave],
                                backgroundColor: [
                                    '#198754',
                                    '#dc3545',
                                    '#ffc107',
                                    '#0dcaf0'
                                ],
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            }
                        }
                    });

                    // Update counts
                    document.getElementById('presentDays').textContent = data.present;
                    document.getElementById('absentDays').textContent = data.absent;
                    document.getElementById('lateDays').textContent = data.late;
                    document.getElementById('leaveDays').textContent = data.leave;
                }
            });
    }

    // Removed biometric authentication UI elements (no longer needed)

    // Removed biometric authentication functions (no longer needed)



    // Global variables for biometric verification
    let isVerificationInProgress = false;

    // Update current date display
    const currentDateElement = document.getElementById('currentDate');
    if (currentDateElement) {
        const today = new Date();
        const options = { 
            weekday: 'short', 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        };
        const dateStr = today.toLocaleDateString('en-US', options);
        currentDateElement.textContent = dateStr;
    }

    // Load today's attendance status on page load
    loadTodayAttendanceStatus();

    // Start automatic polling for device verifications
    startDevicePolling();

    // Refresh attendance data every minute
    setInterval(loadTodayAttendanceStatus, 60000);
    
    // Update total hours every 30 seconds for ongoing work
    setInterval(function() {
        const totalHours = document.getElementById('totalHours');
        if (totalHours && totalHours.textContent.includes('(live)')) {
            // Only update if we're showing live hours
            loadTodayAttendanceStatus();
        }
    }, 30000);

    // Add refresh button functionality
    const refreshBtn = document.getElementById('refreshDataBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Show loading state
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spinning"></i> Refreshing...';
            refreshBtn.disabled = true;

            // Reload attendance data
            loadTodayAttendanceStatus();

            // Reset button after 2 seconds
            setTimeout(() => {
                refreshBtn.innerHTML = originalText;
                refreshBtn.disabled = false;
            }, 2000);
        });
    }

    // Test functionality removed - attendance display working correctly

    // Removed device status check (no longer needed)

    function loadTodayAttendanceStatus() {
        fetch('/get_today_attendance_status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateAttendanceDisplay(data.attendance);
                    // Removed verification history and available actions (no longer needed)
                } else {
                    console.error('Failed to load attendance status:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading attendance status:', error);
            });
    }

    function updateAttendanceDisplay(attendance) {
        const currentStatus = document.getElementById('currentStatus');
        const timeIn = document.getElementById('timeIn');
        const timeOut = document.getElementById('timeOut');
        const totalHours = document.getElementById('totalHours');

        if (attendance) {
            timeIn.textContent = attendance.time_in || '--:--:--';
            timeOut.textContent = attendance.time_out || '--:--:--';

            // Calculate total hours worked
            let totalHoursText = '--:--';
            if (attendance.time_in && attendance.time_out) {
                // Both check-in and check-out times are available
                const timeInDate = new Date(`2000-01-01 ${attendance.time_in}`);
                const timeOutDate = new Date(`2000-01-01 ${attendance.time_out}`);
                const diffMs = timeOutDate - timeInDate;
                
                if (diffMs > 0) {
                    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
                    totalHoursText = `${diffHours}:${diffMinutes.toString().padStart(2, '0')} hrs`;
                } else {
                    totalHoursText = 'Invalid time';
                }
            } else if (attendance.time_in && !attendance.time_out) {
                // Only checked in, calculate hours worked so far (ongoing)
                const timeInDate = new Date(`2000-01-01 ${attendance.time_in}`);
                const now = new Date();
                const currentTimeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
                const currentTime = new Date(`2000-01-01 ${currentTimeStr}`);
                const diffMs = currentTime - timeInDate;
                
                if (diffMs > 0) {
                    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
                    totalHoursText = `${diffHours}:${diffMinutes.toString().padStart(2, '0')} (live)`;
                    
                    // Add a pulsing indicator for ongoing work
                    if (totalHours) {
                        totalHours.style.color = '#0d6efd';
                        totalHours.style.animation = 'pulse 2s infinite';
                    }
                } else {
                    totalHoursText = 'Just started';
                }
            } else {
                // No check-in yet
                totalHoursText = '--:--';
                if (totalHours) {
                    totalHours.style.color = '';
                    totalHours.style.animation = '';
                }
            }
            totalHours.textContent = totalHoursText;

            // Update status based on attendance with proper badge styling
            let statusText, badgeClass;
            if (attendance.time_out) {
                statusText = 'Work Complete';
                badgeClass = 'badge bg-success';
            } else if (attendance.time_in) {
                // Check if the person is late based on attendance status
                if (attendance.status && attendance.status.toLowerCase() === 'late') {
                    statusText = 'Present (Late)';
                    badgeClass = 'badge bg-warning';
                } else {
                    statusText = 'Present';
                    badgeClass = 'badge bg-primary';
                }
            } else {
                statusText = 'Not Marked';
                badgeClass = 'badge bg-secondary';
            }

            currentStatus.textContent = statusText;
            currentStatus.className = badgeClass;
        } else {
            currentStatus.textContent = 'Not Marked';
            currentStatus.className = 'badge bg-secondary';
            timeIn.textContent = '--:--:--';
            timeOut.textContent = '--:--:--';
            totalHours.textContent = '--:--';
            
            // Reset any styles
            if (totalHours) {
                totalHours.style.color = '';
                totalHours.style.animation = '';
            }
        }
    }

    // Removed verification history and available actions functions (no longer needed)

    function startDevicePolling() {
        // Poll for new device verifications every 30 seconds
        setInterval(() => {
            pollForDeviceVerifications();
        }, 30000);

        // Also poll immediately
        pollForDeviceVerifications();
    }

    function pollForDeviceVerifications() {
        fetch('/get_latest_device_verifications?since_minutes=1')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.verifications.length > 0) {
                    // Check if any verification is for the current user
                    const currentUserId = getCurrentUserId(); // We'll need to implement this
                    const userVerifications = data.verifications.filter(v => v.user_id === currentUserId);

                    if (userVerifications.length > 0) {
                        // Reload attendance status when new verification detected
                        setTimeout(() => {
                            loadTodayAttendanceStatus();
                        }, 1000);
                    }
                }
            })
            .catch(error => {
                console.error('Error polling for device verifications:', error);
            });
    }

    // Removed showVerificationSuccess function (no longer needed)

    function getCurrentUserId() {
        // Extract user ID from session or page data
        // For now, we'll try to get it from the page context
        // This should be set when the page loads
        return window.currentStaffId || null;
    }

    // Removed checkDeviceStatus function (no longer needed)

    // Apply leave
    const submitLeave = document.getElementById('submitLeave');
    submitLeave?.addEventListener('click', function () {
        const leaveType = document.getElementById('leaveType').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const reason = document.getElementById('leaveReason').value;

        if (!leaveType || !startDate || !endDate || !reason) {
            alert('Please fill all fields');
            return;
        }

        fetch('/apply_leave', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `leave_type=${leaveType}&start_date=${startDate}&end_date=${endDate}&reason=${encodeURIComponent(reason)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Leave application submitted successfully');
                    bootstrap.Modal.getInstance(document.getElementById('applyLeaveModal')).hide();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to submit leave application');
                }
            });
    });

    // Apply on duty
    const submitOnDuty = document.getElementById('submitOnDuty');
    submitOnDuty?.addEventListener('click', function () {
        const form = document.getElementById('onDutyForm');
        const formData = new FormData(form);

        // Basic validation
        const dutyType = formData.get('duty_type');
        const startDate = formData.get('start_date');
        const endDate = formData.get('end_date');
        const purpose = formData.get('purpose');

        if (!dutyType || !startDate || !endDate || !purpose) {
            alert('Please fill all required fields');
            return;
        }

        // Check if end date is after start date
        if (new Date(endDate) < new Date(startDate)) {
            alert('End date must be after or equal to start date');
            return;
        }

        fetch('/apply_on_duty', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || 'On-duty application submitted successfully');
                    bootstrap.Modal.getInstance(document.getElementById('applyOnDutyModal')).hide();
                    form.reset();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to submit on-duty application');
                }
            })
            .catch(error => {
                console.error('Error submitting on-duty application:', error);
                alert('Error submitting on-duty application');
            });
    });

    // Apply permission
    const submitPermission = document.getElementById('submitPermission');
    submitPermission?.addEventListener('click', function () {
        const form = document.getElementById('permissionForm');
        const formData = new FormData(form);

        // Basic validation
        const permissionType = formData.get('permission_type');
        const permissionDate = formData.get('permission_date');
        const startTime = formData.get('start_time');
        const endTime = formData.get('end_time');
        const reason = formData.get('reason');

        if (!permissionType || !permissionDate || !startTime || !endTime || !reason) {
            alert('Please fill all required fields');
            return;
        }

        // Check if end time is after start time
        if (startTime >= endTime) {
            alert('End time must be after start time');
            return;
        }

        fetch('/apply_permission', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || 'Permission application submitted successfully');
                    bootstrap.Modal.getInstance(document.getElementById('applyPermissionModal')).hide();
                    form.reset();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to submit permission application');
                }
            })
            .catch(error => {
                console.error('Error submitting permission application:', error);
                alert('Error submitting permission application');
            });
    });

    // Updated download report with date selection
// Updated download report with date selection
document.getElementById('downloadReportBtn')?.addEventListener('click', function() {
    const startDate = prompt('Enter start date (YYYY-MM-DD):');
    if (!startDate) return;

    const endDate = prompt('Enter end date (YYYY-MM-DD):');
    if (!endDate) return;

    fetch(`/export_staff_report?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance_report_${startDate}_to_${endDate}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        });
});



    function formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return `${Math.floor(diffInSeconds / 86400)}d ago`;
    }









});
