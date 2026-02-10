document.addEventListener('DOMContentLoaded', function () {
    // Helper function to get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }

    // Helper function to enroll user on device
    function enrollUserOnDevice(deviceIP, staffId, fullName, overwrite = false) {
        return fetch('/enroll_biometric_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `device_ip=${encodeURIComponent(deviceIP)}&user_id=${encodeURIComponent(staffId)}&name=${encodeURIComponent(fullName)}&overwrite=${overwrite}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json());
    }

    // Helper function to delete user from device (simple version for promises)
    function deleteUserFromDeviceSimple(deviceIP, staffId) {
        return fetch('/delete_biometric_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `device_ip=${encodeURIComponent(deviceIP)}&user_id=${encodeURIComponent(staffId)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json());
    }

    // Helper function to create staff account from device user
    function createStaffFromDeviceUser(deviceIP, deviceUserId, deviceUserName) {
        // Show a form to collect additional staff details
        const fullName = prompt(`Create staff account for biometric user:\n\nDevice User ID: ${deviceUserId}\nDevice Name: ${deviceUserName}\n\nEnter full name for staff account:`, deviceUserName);

        if (!fullName) {
            return; // User cancelled
        }

        const email = prompt('Enter email (optional):', '') || '';
        const phone = prompt('Enter phone (optional):', '') || '';
        const department = prompt('Enter department (optional):', '') || '';
        const position = prompt('Enter position (optional):', '') || '';

        // Create the staff account
        fetch('/create_staff_from_device_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `device_ip=${encodeURIComponent(deviceIP)}&device_user_id=${encodeURIComponent(deviceUserId)}&full_name=${encodeURIComponent(fullName)}&email=${encodeURIComponent(email)}&phone=${encodeURIComponent(phone)}&department=${encodeURIComponent(department)}&position=${encodeURIComponent(position)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`✅ Success!\n\n${data.message}\n\nThe staff member can now:\n• Login to the system using Staff ID: ${deviceUserId}\n• Use biometric attendance (already enrolled)\n• Access their dashboard and profile`);
                location.reload(); // Refresh to show new staff in dashboard
            } else {
                alert(`❌ Failed to create staff account:\n\n${data.error}\n\nPlease try again or contact administrator.`);
            }
        })
        .catch(error => {
            alert(`❌ Error creating staff account:\n\n${error.message}`);
        });
    }
    // Initialize Chart
    const ctx = document.getElementById('attendanceChart')?.getContext('2d');
    if (ctx) {
        const attendanceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent', 'Late'],
                datasets: [{
                    data: [85, 10, 5], // Placeholder
                    backgroundColor: ['#198754', '#dc3545', '#ffc107'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    // Initialize weekly calendar for staff profile modal
    let adminStaffWeeklyCalendar = null;

    function initializeStaffWeeklyCalendar(staffId) {
        const calendarEl = document.getElementById('adminStaffWeeklyCalendar');
        if (calendarEl) {
            // Destroy existing calendar if it exists
            if (adminStaffWeeklyCalendar) {
                calendarEl.innerHTML = '';
            }

            // Create new weekly calendar instance
            if (typeof WeeklyAttendanceCalendar !== 'undefined') {
                try {
                    adminStaffWeeklyCalendar = new WeeklyAttendanceCalendar('adminStaffWeeklyCalendar', {
                        staffId: staffId,
                        isAdminView: true
                    });
                } catch (error) {
                    console.error('Error initializing weekly calendar:', error);
                    calendarEl.innerHTML = '<div class="alert alert-warning">Calendar could not be loaded.</div>';
                }
            } else {
                console.warn('WeeklyAttendanceCalendar class not found');
                calendarEl.innerHTML = '<div class="alert alert-info">Calendar is not available.</div>';
            }
        }
    }

    // Live Staff Search
    document.getElementById('staffSearch')?.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        const rows = document.querySelectorAll('.table tbody tr');
        rows.forEach(row => {
            const match = Array.from(row.querySelectorAll('td')).some(cell => cell.textContent.toLowerCase().includes(searchTerm));
            if (match) {
                row.classList.remove('hidden');
            } else {
                row.classList.add('hidden');
            }
        });
    });

    // View Staff Profile Handler
    document.querySelector('.table tbody')?.addEventListener('click', function (e) {
        const target = e.target.closest('.staff-profile-link, .staff-profile-btn');
        if (!target) return;
        e.preventDefault();
        const staffId = target.getAttribute('data-staff-id');
        loadComprehensiveStaffProfile(staffId);
    });

    function loadComprehensiveStaffProfile(staffId, year = null, month = null) {
        // Show loading state
        const modalContent = document.getElementById('staffProfileModalContent');
        const modalTitle = document.getElementById('staffProfileModalLabel');

        if (!modalContent) {
            console.error('Staff profile modal content element not found');
            return;
        }

        modalContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading comprehensive staff profile...</p>
            </div>
        `;

        // Build URL with optional year/month parameters
        let url = `/get_comprehensive_staff_profile?id=${staffId}`;
        if (year && month) {
            url += `&year=${year}&month=${month}`;
        }

        // Load comprehensive staff profile data
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (modalTitle) {
                        modalTitle.textContent = `Staff Profile - ${data.staff.full_name}`;
                    }
                    renderComprehensiveStaffProfile(data, staffId);

                    // Set up modal buttons
                    setupStaffProfileButtons(staffId, data.staff);
                } else {
                    modalContent.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle"></i> ${data.error}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading staff profile:', error);
                modalContent.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i> Failed to load staff profile: ${error.message}
                    </div>
                `;
            });
    }

    function renderComprehensiveStaffProfile(data, staffId) {
        const modalContent = document.getElementById('staffProfileModalContent');
        if (!modalContent) {
            console.error('Staff profile modal content element not found');
            return;
        }

        const staff = data.staff || {};
        const stats = data.attendance_stats || {
            total_days: 0,
            present_days: 0,
            late_days: 0,
            absent_days: 0,
            attendance_rate: 0
        };
        const monthInfo = data.month_info || {
            year: new Date().getFullYear(),
            month: new Date().getMonth() + 1,
            month_name: new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
        };

    modalContent.innerHTML = `
        <!-- Staff Information Section -->
        <div class="row mb-4">
            <div class="col-md-3 text-center">
                <img src="/static/${staff.photo_url || 'images/default_profile.png'}"
                     class="img-thumbnail mb-3" alt="Staff Photo" style="max-height: 200px;">
                <!-- Change Photo button removed -->
            </div>
            <div class="col-md-9">
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0"><i class="bi bi-person-badge"></i> Personal Information</h5>
                    </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Full Name:</strong> ${staff.full_name}</p>
                                    <p><strong>Staff ID:</strong> <span class="badge bg-primary">${staff.staff_id}</span></p>
                                    <p><strong>Department:</strong> ${staff.department || 'Not assigned'}</p>
                                    <p><strong>Position:</strong> ${staff.position || 'Not assigned'}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Email:</strong> ${staff.email || 'Not provided'}</p>
                                    <p><strong>Phone:</strong> ${staff.phone || 'Not provided'}</p>
                                    <p><strong>School:</strong> ${staff.school_name || 'Not assigned'}</p>
                                    <p><strong>Status:</strong> <span class="badge bg-success">Active</span></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Attendance Statistics -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-light d-flex justify-content-between align-items-center">
                            <div>
                                <h5 class="mb-0"><i class="bi bi-graph-up"></i> Attendance Statistics</h5>
                                <small class="text-muted">Comprehensive attendance overview for ${monthInfo.month_name} - Total working days (Mon-Sat): ${stats.working_days}</small>
                            </div>
                            <div class="d-flex align-items-center gap-2">
                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="navigateMonth(${staffId}, ${monthInfo.year}, ${monthInfo.month}, -1)" title="Previous Month">
                                    <i class="bi bi-chevron-left"></i>
                                </button>
                                <span class="mx-2 fw-bold">${monthInfo.month_name}</span>
                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="navigateMonth(${staffId}, ${monthInfo.year}, ${monthInfo.month}, 1)" title="Next Month">
                                    <i class="bi bi-chevron-right"></i>
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="overflow-auto" style="white-space: nowrap;">
                                <div class="d-flex gap-3 pb-2" style="min-width: max-content;">
                                    <div class="flex-shrink-0" style="min-width: 140px;">
                                        <div class="card bg-info text-white h-100">
                                            <div class="card-body text-center p-3">
                                                <h4 class="mb-1">${stats.working_days}</h4>
                                                <p class="mb-0 small">Working Days</p>
                                                <small class="text-light">This Month</small>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex-shrink-0" style="min-width: 140px;">
                                        <div class="card bg-success text-white h-100">
                                            <div class="card-body text-center p-3">
                                                <h4 class="mb-1">${stats.present_days}</h4>
                                                <p class="mb-0 small">Present</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex-shrink-0" style="min-width: 140px;">
                                        <div class="card bg-warning text-white h-100">
                                            <div class="card-body text-center p-3">
                                                <h4 class="mb-1">${stats.late_days}</h4>
                                                <p class="mb-0 small">Late</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex-shrink-0" style="min-width: 140px;">
                                        <div class="card bg-danger text-white h-100">
                                            <div class="card-body text-center p-3">
                                                <h4 class="mb-1">${stats.absent_days}</h4>
                                                <p class="mb-0 small">Absent</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex-shrink-0" style="min-width: 140px;">
                                        <div class="card bg-secondary text-white h-100">
                                            <div class="card-body text-center p-3">
                                                <h4 class="mb-1">${stats.leave_days || 0}</h4>
                                                <p class="mb-0 small">On Leave</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex-shrink-0" style="min-width: 140px;">
                                        <div class="card bg-primary text-white h-100">
                                            <div class="card-body text-center p-3">
                                                <h4 class="mb-1">${stats.on_duty_days || 0}</h4>
                                                <p class="mb-0 small">On Duty</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex-shrink-0" style="min-width: 140px;">
                                        <div class="card bg-dark text-white h-100">
                                            <div class="card-body text-center p-3">
                                                <h4 class="mb-1">${stats.holiday_days || 0}</h4>
                                                <p class="mb-0 small">Holiday</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-3">
                                <div class="d-flex justify-content-between mb-2">
                                    <span class="fw-bold">Attendance Rate:</span>
                                    <span class="fw-bold">${stats.attendance_rate}%</span>
                                </div>
                                <div class="progress" style="height: 20px;">
                                    <div class="progress-bar bg-success" role="progressbar"
                                         style="width: ${stats.attendance_rate}%"
                                         aria-valuenow="${stats.attendance_rate}" aria-valuemin="0" aria-valuemax="100">
                                        ${stats.attendance_rate}%
                                    </div>
                                </div>
                                <small class="text-muted mt-1">
                                    Based on Present + Late + On Duty days out of ${stats.working_days} total working days in current month
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tabs for detailed information -->
            <ul class="nav nav-tabs" id="staffProfileTabs" role="tablist" style="border-bottom: 2px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="attendance-tab" data-bs-toggle="tab"
                            data-bs-target="#attendance-pane" type="button" role="tab"
                            style="color: #495057; background-color: #f8f9fa; border: 1px solid #dee2e6; border-bottom-color: transparent; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-right: 2px;">
                        <i class="bi bi-calendar-check"></i> Attendance Records
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="biometric-tab" data-bs-toggle="tab"
                            data-bs-target="#biometric-pane" type="button" role="tab"
                            style="color: #495057; background-color: transparent; border: 1px solid #dee2e6; border-bottom-color: #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-right: 2px;">
                        <i class="bi bi-fingerprint"></i> Biometric Verifications
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="leaves-tab" data-bs-toggle="tab"
                            data-bs-target="#leaves-pane" type="button" role="tab"
                            style="color: #495057; background-color: transparent; border: 1px solid #dee2e6; border-bottom-color: #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-right: 2px;">
                        <i class="bi bi-calendar-x"></i> Leave Applications
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="on-duty-tab" data-bs-toggle="tab"
                            data-bs-target="#on-duty-pane" type="button" role="tab"
                            style="color: #495057; background-color: transparent; border: 1px solid #dee2e6; border-bottom-color: #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-right: 2px;">
                        <i class="bi bi-briefcase"></i> On Duty Applications
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="permissions-tab" data-bs-toggle="tab"
                            data-bs-target="#permissions-pane" type="button" role="tab"
                            style="color: #495057; background-color: transparent; border: 1px solid #dee2e6; border-bottom-color: #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.08); margin-right: 2px;">
                        <i class="bi bi-clock"></i> Permission Applications
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="weekly-calendar-tab" data-bs-toggle="tab"
                            data-bs-target="#weekly-calendar-pane" type="button" role="tab"
                            style="color: #495057; background-color: transparent; border: 1px solid #dee2e6; border-bottom-color: #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
                        <i class="bi bi-calendar-week"></i> Weekly Calendar
                    </button>
                </li>
            </ul>

            <div class="tab-content mt-3" id="staffProfileTabContent">
                <!-- Attendance Records Tab -->
                <div class="tab-pane fade show active" id="attendance-pane" role="tabpanel">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="alert alert-info mb-0 flex-grow-1 me-3">
                            <i class="bi bi-info-circle"></i> Showing comprehensive attendance records for <strong>${monthInfo.month_name}</strong> including all working days
                        </div>
                        <button type="button" class="btn btn-success" onclick="downloadAttendanceReport(${staffId}, ${monthInfo.year}, ${monthInfo.month})" title="Download Report">
                            <i class="bi bi-download"></i> Download Report
                        </button>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Date</th>
                                    <th>Day</th>
                                    <th>Time In</th>
                                    <th>Time Out</th>
                                    <th>Overtime In</th>
                                    <th>Overtime Out</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${(data.attendance || []).map(record => {
                                    const date = new Date(record.date + 'T00:00:00');
                                    const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
                                    const formattedDate = date.toLocaleDateString('en-GB');
                                    const status = record.status || 'unknown';
                                    const statusDisplay = status.charAt(0).toUpperCase() + status.slice(1);
                                    
                                    return `
                                    <tr class="${status === 'absent' ? 'table-danger' : status === 'leave' ? 'table-secondary' : ''}">
                                        <td><strong>${formattedDate}</strong></td>
                                        <td><span class="text-muted">${dayName}</span></td>
                                        <td>${record.time_in ? `<span class="text-success">${record.time_in}</span>` : '<span class="text-muted">--:--</span>'}</td>
                                        <td>${record.time_out ? `<span class="text-info">${record.time_out}</span>` : '<span class="text-muted">--:--</span>'}</td>
                                        <td>${record.overtime_in ? `<span class="text-warning">${record.overtime_in}</span>` : '<span class="text-muted">--:--</span>'}</td>
                                        <td>${record.overtime_out ? `<span class="text-warning">${record.overtime_out}</span>` : '<span class="text-muted">--:--</span>'}</td>
                                        <td>
                                            <span class="badge bg-${getStatusColor(status)}">${statusDisplay}</span>
                                            ${status === 'absent' ? '<br><small class="text-muted">No check-in recorded</small>' : ''}
                                            ${status === 'leave' ? '<br><small class="text-muted">Approved leave</small>' : ''}
                                        </td>
                                    </tr>
                                `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${(data.attendance || []).length === 0 ? '<div class="alert alert-warning"><i class="bi bi-exclamation-triangle"></i> No attendance records available for the current month</div>' : ''}
                </div>

                <!-- Biometric Verifications Tab -->
                <div class="tab-pane fade" id="biometric-pane" role="tabpanel">
                    <div class="alert alert-info mb-3">
                        <i class="bi bi-info-circle"></i> Showing biometric verification records for the <strong>current month</strong>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Date</th>
                                    <th>Check In</th>
                                    <th>Check In Status</th>
                                    <th>Check Out</th>
                                    <th>Check Out Status</th>
                                    <th>Device IP</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${(() => {
                                    // Group verifications by date
                                    const groupedByDate = {};
                                    (data.verifications || []).forEach(v => {
                                        if (v.verification_time) {
                                            const date = v.verification_time.split(' ')[0]; // Get date part
                                            if (!groupedByDate[date]) {
                                                groupedByDate[date] = { checkIn: null, checkOut: null };
                                            }
                                            if (v.verification_type === 'check-in') {
                                                groupedByDate[date].checkIn = v;
                                            } else if (v.verification_type === 'check-out') {
                                                groupedByDate[date].checkOut = v;
                                            }
                                        }
                                    });
                                    
                                    // Convert to array and sort by date descending
                                    const sortedEntries = Object.entries(groupedByDate)
                                        .sort((a, b) => b[0].localeCompare(a[0]));
                                    
                                    if (sortedEntries.length === 0) {
                                        return '<tr><td colspan="6" class="text-center text-muted">No verification records found</td></tr>';
                                    }
                                    
                                    return sortedEntries.map(([date, records]) => `
                                            <tr>
                                                <td><strong>${date}</strong></td>
                                                <td>
                                                    ${records.checkIn ? 
                                                        new Date(records.checkIn.verification_time).toLocaleTimeString() : 
                                                        '<span class="text-muted">--:--</span>'}
                                                </td>
                                                <td>
                                                    ${records.checkIn ? 
                                                        `<span class="badge bg-${records.checkIn.verification_status === 'success' ? 'success' : 'danger'}">
                                                            ${records.checkIn.verification_status || 'unknown'}
                                                        </span>` : 
                                                        '<span class="text-muted">N/A</span>'}
                                                </td>
                                                <td>
                                                    ${records.checkOut ? 
                                                        new Date(records.checkOut.verification_time).toLocaleTimeString() : 
                                                        '<span class="text-muted">--:--</span>'}
                                                </td>
                                                <td>
                                                    ${records.checkOut ? 
                                                        `<span class="badge bg-${records.checkOut.verification_status === 'success' ? 'success' : 'danger'}">
                                                            ${records.checkOut.verification_status || 'unknown'}
                                                        </span>` : 
                                                        '<span class="text-muted">N/A</span>'}
                                                </td>
                                                <td>${records.checkIn?.device_ip || records.checkOut?.device_ip || '--'}</td>
                                            </tr>
                                        `).join('');
                                })()}
                            </tbody>
                        </table>
                    </div>
                    ${(data.verifications || []).length === 0 ? '<div class="alert alert-info">No biometric verifications found</div>' : ''}
                </div>

                <!-- Leave Applications Tab -->
                <div class="tab-pane fade" id="leaves-pane" role="tabpanel">
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Leave Type</th>
                                    <th>Start Date</th>
                                    <th>End Date</th>
                                    <th>Reason</th>
                                    <th>Status</th>
                                    <th>Applied Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${(data.leaves || []).map(leave => `
                                    <tr>
                                        <td>${leave.leave_type || 'N/A'}</td>
                                        <td>${leave.start_date || '--'}</td>
                                        <td>${leave.end_date || '--'}</td>
                                        <td>${leave.reason || 'No reason provided'}</td>
                                        <td><span class="badge bg-${getLeaveStatusColor(leave.status || 'unknown')}">${leave.status || 'Unknown'}</span></td>
                                        <td>${leave.applied_at || '--'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${(data.leaves || []).length === 0 ? '<div class="alert alert-info">No leave applications found</div>' : ''}
                </div>

                <!-- On Duty Applications Tab -->
                <div class="tab-pane fade" id="on-duty-pane" role="tabpanel">
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Duty Type</th>
                                    <th>Start Date</th>
                                    <th>End Date</th>
                                    <th>Time</th>
                                    <th>Location</th>
                                    <th>Purpose</th>
                                    <th>Status</th>
                                    <th>Applied Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${(data.on_duty_applications || []).map(duty => `
                                    <tr>
                                        <td><span class="badge bg-info">${duty.duty_type || 'N/A'}</span></td>
                                        <td>${duty.start_date || '--'}</td>
                                        <td>${duty.end_date || '--'}</td>
                                        <td>
                                            ${duty.start_time && duty.end_time ?
                                                `${duty.start_time} - ${duty.end_time}` :
                                                '<span class="text-muted">All day</span>'
                                            }
                                        </td>
                                        <td>${duty.location || '<span class="text-muted">Not specified</span>'}</td>
                                        <td>
                                            <span title="${duty.purpose || ''}">
                                                ${duty.purpose ? (duty.purpose.length > 30 ? duty.purpose.substring(0, 30) + '...' : duty.purpose) : 'No purpose specified'}
                                            </span>
                                        </td>
                                        <td><span class="badge bg-${getLeaveStatusColor(duty.status || 'unknown')}">${duty.status || 'Unknown'}</span></td>
                                        <td>${duty.applied_at ? new Date(duty.applied_at).toLocaleDateString() : '--'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${(data.on_duty_applications || []).length === 0 ? '<div class="alert alert-info">No on-duty applications found</div>' : ''}
                </div>

                <!-- Permission Applications Tab -->
                <div class="tab-pane fade" id="permissions-pane" role="tabpanel">
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Permission Type</th>
                                    <th>Date</th>
                                    <th>Time</th>
                                    <th>Duration</th>
                                    <th>Reason</th>
                                    <th>Status</th>
                                    <th>Applied Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${(data.permission_applications || []).map(permission => `
                                    <tr>
                                        <td><span class="badge bg-warning text-dark">${permission.permission_type || 'N/A'}</span></td>
                                        <td>${permission.permission_date || '--'}</td>
                                        <td>${permission.start_time && permission.end_time ? `${permission.start_time} - ${permission.end_time}` : '--'}</td>
                                        <td>
                                            <span class="badge bg-secondary">
                                                ${permission.duration_hours ? permission.duration_hours.toFixed(1) : '0.0'} hrs
                                            </span>
                                        </td>
                                        <td>
                                            <span title="${permission.reason || ''}">
                                                ${permission.reason ? (permission.reason.length > 30 ? permission.reason.substring(0, 30) + '...' : permission.reason) : 'No reason provided'}
                                            </span>
                                        </td>
                                        <td><span class="badge bg-${getLeaveStatusColor(permission.status || 'unknown')}">${permission.status || 'Unknown'}</span></td>
                                        <td>${permission.applied_at ? new Date(permission.applied_at).toLocaleDateString() : '--'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ${(data.permission_applications || []).length === 0 ? '<div class="alert alert-info">No permission applications found</div>' : ''}
                </div>

                <!-- Weekly Calendar Tab -->
                <div class="tab-pane fade" id="weekly-calendar-pane" role="tabpanel">
                    <div id="adminStaffWeeklyCalendar"></div>
                </div>
            </div>
        `;

        // Initialize the weekly calendar after the modal content is rendered
        setTimeout(() => {
            if (staff && staff.id) {
                initializeStaffWeeklyCalendar(staff.id);
            } else {
                console.warn('Staff ID not available for calendar initialization');
            }
        }, 100);
    }

    // Month navigation function (make it global)
    window.navigateMonth = function(staffId, currentYear, currentMonth, direction) {
        let newYear = currentYear;
        let newMonth = currentMonth + direction;
        
        if (newMonth > 12) {
            newMonth = 1;
            newYear++;
        } else if (newMonth < 1) {
            newMonth = 12;
            newYear--;
        }
        
        // Don't allow navigation to future months
        const now = new Date();
        const currentDate = new Date(now.getFullYear(), now.getMonth(), 1);
        const targetDate = new Date(newYear, newMonth - 1, 1);
        
        if (targetDate > currentDate) {
            alert('Cannot view future months');
            return;
        }
        
        // Reload profile with new month
        loadComprehensiveStaffProfile(staffId, newYear, newMonth);
    };

    // Download attendance report function (make it global)
    window.downloadAttendanceReport = function(staffId, year, month) {
        const downloadBtn = event.target;
        const originalText = downloadBtn.innerHTML;
        
        // Show loading state
        downloadBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';
        downloadBtn.disabled = true;
        
        // Create download URL
        const url = `/download_staff_attendance_report?id=${staffId}&year=${year}&month=${month}`;
        
        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Reset button after a short delay
        setTimeout(() => {
            downloadBtn.innerHTML = originalText;
            downloadBtn.disabled = false;
        }, 2000);
    };

    function setupStaffProfileButtons(staffId, staff) {
        // Edit Profile Button
        const editBtn = document.getElementById('editStaffProfileBtn');
        if (editBtn) {
            editBtn.onclick = function() {
                // Close the profile modal and open edit modal
                const profileModal = document.getElementById('staffProfileModal');
                if (profileModal) {
                    bootstrap.Modal.getInstance(profileModal).hide();
                }

                // Populate edit form
                const editStaffId = document.getElementById('editStaffId');
                const editFullName = document.getElementById('editFullName');
                const editEmail = document.getElementById('editEmail');
                const editPhone = document.getElementById('editPhone');
                const editDepartment = document.getElementById('editDepartment');
                const editPosition = document.getElementById('editPosition');

                if (editStaffId) editStaffId.value = staffId;
                if (editFullName) editFullName.value = staff.full_name;
                if (editEmail) editEmail.value = staff.email || '';
                if (editPhone) editPhone.value = staff.phone || '';
                if (editDepartment) editDepartment.value = staff.department || '';
                if (editPosition) editPosition.value = staff.position || '';

                // Show edit modal
                const editModal = document.getElementById('editStaffModal');
                if (editModal) {
                    new bootstrap.Modal(editModal).show();
                }
            };
        }

        // Delete Staff Button
        const deleteBtn = document.getElementById('deleteStaffProfileBtn');
        if (deleteBtn) {
            deleteBtn.onclick = function() {
                if (confirm(`Are you sure you want to delete ${staff.full_name}? This action cannot be undone.`)) {
                    fetch('/delete_staff', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `staff_id=${staffId}&csrf_token=${encodeURIComponent(getCSRFToken())}`
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            alert('Staff deleted successfully');
                            const profileModal = document.getElementById('staffProfileModal');
                            if (profileModal) {
                                bootstrap.Modal.getInstance(profileModal).hide();
                            }
                            location.reload(); // Refresh the page to update the staff list
                        } else {
                            alert(data.error || 'Failed to delete staff');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while deleting staff');
                    });
                }
            };
        }
    }

    function getStatusColor(status) {
        const colors = {
            'present': 'success',
            'absent': 'danger',
            'late': 'warning',
            'leave': 'secondary',
            'on_duty': 'primary',
            'holiday': 'dark',
            'unknown': 'secondary'
        };
        return colors[status?.toLowerCase()] || 'secondary';
    }

    function getLeaveStatusColor(status) {
        const colors = {
            'approved': 'success',
            'pending': 'warning',
            'rejected': 'danger'
        };
        return colors[status] || 'secondary';
    }

    // Wire up Change Photo button to open edit modal
    document.getElementById('changeStaffPhotoBtn')?.addEventListener('click', function() {
        // Populate edit form with staff info
        document.getElementById('editStaffId').value = staffId;
        document.getElementById('editFullName').value = staff.full_name;
        document.getElementById('editEmail').value = staff.email || '';
        document.getElementById('editPhone').value = staff.phone || '';
        document.getElementById('editDepartment').value = staff.department || '';
        document.getElementById('editPosition').value = staff.position || '';
        // Show edit modal
        new bootstrap.Modal(document.getElementById('editStaffModal')).show();
    });

    // Save Edited Staff
    document.getElementById('saveEditStaff')?.addEventListener('click', function () {
        const formData = new FormData();
        formData.append('staff_id', document.getElementById('editStaffId').value);
        formData.append('full_name', document.getElementById('editFullName').value);
        formData.append('email', document.getElementById('editEmail').value);
        formData.append('phone', document.getElementById('editPhone').value);
        formData.append('department', document.getElementById('editDepartment').value);
        formData.append('position', document.getElementById('editPosition').value);
        formData.append('shift_type', document.getElementById('editShiftType').value);
        formData.append('status', document.getElementById('editStatus').checked ? 'active' : 'inactive');
        formData.append('csrf_token', getCSRFToken());

        fetch('/update_staff', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert('Staff updated');
                location.reload();
            } else alert(data.error || 'Update failed');
        });
    });

    // Staff Creation - Step Navigation
    document.getElementById('nextStepBtn')?.addEventListener('click', function () {
        const staffId = document.getElementById('staffId').value;
        const fullName = document.getElementById('fullName').value;
        const password = document.getElementById('password').value;

        if (!staffId || !fullName || !password) {
            alert('Staff ID, Name, and Password are required');
            return;
        }

        // Move to biometric enrollment step
        document.getElementById('staffDetailsStep').classList.add('hidden');
        document.getElementById('biometricEnrollmentStep').classList.remove('hidden');
        document.getElementById('nextStepBtn').classList.add('hidden');
        document.getElementById('saveStaff').classList.remove('hidden');

        // Update progress bar
        document.getElementById('staffCreationProgress').style.width = '100%';
    });

    // Start Biometric Enrollment
    document.getElementById('startEnrollmentBtn')?.addEventListener('click', function () {
        const staffId = document.getElementById('staffId').value;
        const fullName = document.getElementById('fullName').value;
        const deviceIP = '192.168.1.201'; // Default device IP

        if (!staffId || !fullName) {
            alert('Please complete staff details first');
            return;
        }

        const startBtn = document.getElementById('startEnrollmentBtn');
        const statusDiv = document.getElementById('enrollmentDeviceStatus');
        const progressDiv = document.getElementById('staffEnrollmentProgress');
        const progressBar = document.getElementById('staffEnrollmentProgressBar');
        const statusText = document.getElementById('staffEnrollmentStatus');

        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Starting...';

        statusDiv.className = 'alert alert-info';
        statusDiv.innerHTML = '<i class="bi bi-hourglass-split"></i> Preparing device for enrollment...';

        progressDiv.classList.remove('hidden');
        progressBar.style.width = '25%';
        statusText.textContent = 'Checking existing users...';

        // Step 1: Check if user already exists
        fetch('/check_biometric_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `device_ip=${encodeURIComponent(deviceIP)}&user_id=${encodeURIComponent(staffId)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.user_exists) {
                // User already exists, show conflict resolution modal
                const existingUser = data.user_data;

                // Reset enrollment UI
                startBtn.disabled = false;
                startBtn.innerHTML = '<i class="bi bi-fingerprint"></i> Start Enrollment';
                progressDiv.classList.add('hidden');

                // Show conflict resolution modal
                showUserConflictModal({
                    user_id: staffId,
                    name: fullName,
                    existing_user: existingUser
                });

                // Set up callbacks for conflict resolution
                window.continueEnrollmentCallback = function() {
                    // Continue with enrollment after overwrite
                    startBtn.click(); // Restart the enrollment process
                };

                window.updateUserIdCallback = function(newUserId) {
                    // Update the form with new user ID
                    document.getElementById('staffId').value = newUserId;
                    alert(`Staff ID updated to: ${newUserId}\nYou can now proceed with biometric enrollment.`);
                };

                return Promise.reject(new Error('User conflict - showing resolution modal'));
            } else {
                // User doesn't exist, proceed with normal enrollment
                statusText.textContent = 'Enrolling new user...';
                return enrollUserOnDevice(deviceIP, staffId, fullName, false);
            }
        })
        .then(enrollResult => {
            if (enrollResult && enrollResult.success) {
                progressBar.style.width = '50%';
                statusText.textContent = 'User enrolled. Starting enrollment mode...';

                // Step 2: Start enrollment mode
                return fetch('/start_biometric_enrollment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `device_ip=${encodeURIComponent(deviceIP)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
                });
            } else if (enrollResult) {
                throw new Error(enrollResult.message || 'Failed to enroll user');
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                progressBar.style.width = '75%';
                statusText.textContent = 'Device ready. Please capture biometric data...';

                statusDiv.className = 'alert alert-warning';
                statusDiv.innerHTML = `
                    <i class="bi bi-fingerprint"></i>
                    <strong>Device Ready!</strong><br>
                    Please ask ${fullName} to place their finger on the biometric device and follow the device prompts.<br>
                    <br><strong>✅ Biometric enrollment is now complete!</strong><br>
                    <small>You can now create the staff account.</small>
                `;

                startBtn.classList.add('hidden');
                document.getElementById('triggerEnrollmentBtn').classList.remove('hidden');

                // Mark enrollment as complete and enable staff creation
                document.getElementById('biometricEnrolled').value = 'true';
                document.getElementById('saveStaff').disabled = false;
                document.getElementById('saveStaff').innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';

                // Update status to success
                setTimeout(() => {
                    statusDiv.className = 'alert alert-success';
                    statusDiv.innerHTML = `
                        <i class="bi bi-check-circle"></i>
                        <strong>Biometric Enrollment Complete!</strong><br>
                        User ${staffId} (${fullName}) has been enrolled on the biometric device.<br>
                        <strong>✅ Ready to create staff account!</strong>
                    `;
                }, 1500);
            } else {
                throw new Error(data.message || 'Failed to start enrollment mode');
            }
        })
        .catch(error => {
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="bi bi-fingerprint"></i> Start Enrollment';
            statusDiv.className = 'alert alert-danger';
            statusDiv.innerHTML = `<i class="bi bi-x-circle"></i> Error: ${error.message}`;
            progressDiv.classList.add('hidden');
        });
    });

    // Trigger Biometric Enrollment
    document.getElementById('triggerEnrollmentBtn')?.addEventListener('click', function () {
        const staffId = document.getElementById('staffId').value;
        const fullName = document.getElementById('fullName').value;
        const deviceIP = '192.168.1.201';

        const triggerBtn = document.getElementById('triggerEnrollmentBtn');
        const verifyBtn = document.getElementById('verifyEnrollmentBtn');
        const statusDiv = document.getElementById('enrollmentDeviceStatus');
        const progressBar = document.getElementById('staffEnrollmentProgressBar');
        const statusText = document.getElementById('staffEnrollmentStatus');

        triggerBtn.disabled = true;
        triggerBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Starting...';

        statusText.textContent = 'Starting biometric enrollment...';
        progressBar.style.width = '50%';

        fetch('/verify_biometric_enrollment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `device_ip=${encodeURIComponent(deviceIP)}&user_id=${encodeURIComponent(staffId)}&name=${encodeURIComponent(fullName)}&trigger_enrollment=true&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.enrollment_started) {
                progressBar.style.width = '75%';
                statusText.textContent = 'Biometric enrollment started. Please scan fingerprint...';

                statusDiv.className = 'alert alert-info';
                statusDiv.innerHTML = `
                    <i class="bi bi-fingerprint"></i>
                    <strong>Enrollment Started!</strong><br>
                    ${data.message}<br>
                    ${data.manual_mode ? 'Please use the device interface to complete enrollment.' : 'Please follow the device prompts to scan your biometric data.'}
                `;

                triggerBtn.classList.add('hidden');
                verifyBtn.classList.remove('hidden');
                verifyBtn.disabled = false;
            } else if (data.success && data.enrolled) {
                // User already enrolled
                progressBar.style.width = '100%';
                statusText.textContent = 'Biometric enrollment verified!';

                statusDiv.className = 'alert alert-success';
                statusDiv.innerHTML = `
                    <i class="bi bi-check-circle"></i>
                    <strong>Already Enrolled!</strong><br>
                    Biometric data already exists for ${fullName}.
                `;

                document.getElementById('biometricEnrolled').value = 'true';
                triggerBtn.classList.add('hidden');
                verifyBtn.classList.add('hidden');
                document.getElementById('saveStaff').disabled = false;
                document.getElementById('saveStaff').innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';
            } else {
                throw new Error(data.message || 'Failed to start enrollment');
            }
        })
        .catch(error => {
            triggerBtn.disabled = false;
            triggerBtn.innerHTML = '<i class="bi bi-fingerprint"></i> Start Biometric Scan';
            statusDiv.className = 'alert alert-danger';
            statusDiv.innerHTML = `<i class="bi bi-x-circle"></i> Failed to start enrollment: ${error.message}`;
        });
    });

    // Verify Biometric Enrollment
    document.getElementById('verifyEnrollmentBtn')?.addEventListener('click', function () {
        const staffId = document.getElementById('staffId').value;
        const deviceIP = '192.168.1.201';

        const verifyBtn = document.getElementById('verifyEnrollmentBtn');
        const statusDiv = document.getElementById('enrollmentDeviceStatus');
        const progressBar = document.getElementById('staffEnrollmentProgressBar');
        const statusText = document.getElementById('staffEnrollmentStatus');

        verifyBtn.disabled = true;
        verifyBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Verifying...';

        statusText.textContent = 'Verifying biometric enrollment...';

        fetch('/verify_biometric_enrollment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `device_ip=${encodeURIComponent(deviceIP)}&user_id=${encodeURIComponent(staffId)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.enrolled) {
                progressBar.style.width = '100%';
                statusText.textContent = 'Biometric enrollment verified!';

                statusDiv.className = 'alert alert-success';
                statusDiv.innerHTML = `
                    <i class="bi bi-check-circle"></i>
                    <strong>Enrollment Complete!</strong><br>
                    Biometric data has been successfully captured for ${document.getElementById('fullName').value}.
                `;

                // Mark as enrolled
                document.getElementById('biometricEnrolled').value = 'true';

                verifyBtn.classList.add('hidden');

                // Enable save button
                document.getElementById('saveStaff').disabled = false;
                document.getElementById('saveStaff').innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';

            } else {
                statusDiv.className = 'alert alert-warning';
                statusDiv.innerHTML = `
                    <i class="bi bi-exclamation-triangle"></i>
                    <strong>Enrollment Not Complete</strong><br>
                    Please ensure the staff member has completed biometric capture on the device.<br>
                    <small>Try scanning again or use the device interface directly.</small>
                `;

                verifyBtn.disabled = false;
                verifyBtn.innerHTML = '<i class="bi bi-check-circle"></i> Verify Enrollment';
            }
        })
        .catch(error => {
            verifyBtn.disabled = false;
            verifyBtn.innerHTML = '<i class="bi bi-check-circle"></i> Verify Enrollment';
            statusDiv.className = 'alert alert-danger';
            statusDiv.innerHTML = `<i class="bi bi-x-circle"></i> Verification failed: ${error.message}`;
        });
    });

    // Real-time staff ID availability checking
    document.getElementById('staffId')?.addEventListener('blur', function() {
        const staffId = this.value.trim();
        const feedbackDiv = document.getElementById('staffIdFeedback');

        if (!staffId) {
            if (feedbackDiv) feedbackDiv.innerHTML = '';
            return;
        }

        if (feedbackDiv) {
            feedbackDiv.innerHTML = '<small class="text-info"><i class="bi bi-hourglass-split"></i> Checking availability...</small>';
        }

        fetch('/check_staff_id_availability', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `staff_id=${encodeURIComponent(staffId)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            if (feedbackDiv) {
                if (data.success && data.available) {
                    feedbackDiv.innerHTML = '<small class="text-success"><i class="bi bi-check-circle"></i> Staff ID is available</small>';
                } else if (data.success && !data.available) {
                    feedbackDiv.innerHTML = `<small class="text-danger"><i class="bi bi-x-circle"></i> ${data.message}</small>`;
                } else {
                    feedbackDiv.innerHTML = '<small class="text-warning"><i class="bi bi-exclamation-triangle"></i> Could not check availability</small>';
                }
            }
        })
        .catch(error => {
            if (feedbackDiv) {
                feedbackDiv.innerHTML = '<small class="text-warning"><i class="bi bi-exclamation-triangle"></i> Could not check availability</small>';
            }
        });
    });

    // Add Staff (Final Step)
    document.getElementById('saveStaff')?.addEventListener('click', function () {
        const staffId = document.getElementById('staffId').value;
        const fullName = document.getElementById('fullName').value;
        const password = document.getElementById('password').value;
        const email = document.getElementById('email').value;
        const phone = document.getElementById('phone').value;
        const department = document.getElementById('department').value;
        const position = document.getElementById('position').value;
        const biometricEnrolled = document.getElementById('biometricEnrolled').value;

        if (!staffId || !fullName || !password) {
            alert('Staff ID, Name, and Password are required');
            return;
        }

        // Check staff ID availability first
        const saveBtn = document.getElementById('saveStaff');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Checking Staff ID...';

        fetch('/check_staff_id_availability', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `staff_id=${encodeURIComponent(staffId)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(availabilityData => {
            if (availabilityData.success && !availabilityData.available) {
                alert(`❌ Cannot create staff account:\n\n${availabilityData.message}\n\n${availabilityData.suggestion}`);
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';
                return;
            }

            // Check biometric enrollment
            if (biometricEnrolled !== 'true') {
                alert('Biometric enrollment must be completed before creating staff account');
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';
                return;
            }

            // Proceed with staff creation
            proceedWithStaffCreation();
        })
        .catch(error => {
            console.error('Error checking staff ID availability:', error);
            // Continue with creation if check fails
            if (biometricEnrolled !== 'true') {
                alert('Biometric enrollment must be completed before creating staff account');
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';
                return;
            }
            proceedWithStaffCreation();
        });

        function proceedWithStaffCreation() {

            const saveBtn = document.getElementById('saveStaff');
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Creating Account...';

            // First, enroll user on biometric device
            enrollUserOnDevice('192.168.1.201', staffId, fullName, false)
                .then(bioRes => {
                    if (!bioRes.success) {
                        alert('Failed to enroll staff on biometric device: ' + (bioRes.message || bioRes.error));
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';
                        return;
                    }
                    // If biometric enrollment succeeded, create staff account
                    fetch('/add_staff', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `staff_id=${staffId}&full_name=${encodeURIComponent(fullName)}&password=${encodeURIComponent(password)}&email=${email}&phone=${phone}&department=${encodeURIComponent(department)}&position=${encodeURIComponent(position)}&biometric_enrolled=true&csrf_token=${encodeURIComponent(getCSRFToken())}`
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            alert('Staff account created successfully with biometric enrollment!');
                            bootstrap.Modal.getInstance(document.getElementById('addStaffModal')).hide();
                            location.reload();
                        } else {
                            if (data.require_biometric) {
                                alert('Biometric enrollment is required. Please complete the enrollment process.');
                            } else if (data.details && data.suggestion) {
                                alert(`❌ ${data.error}\n\n📋 Details: ${data.details}\n\n💡 ${data.suggestion}`);
                            } else {
                                alert(data.error || 'Failed to create staff account');
                            }
                            saveBtn.disabled = false;
                            saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';
                        }
                    })
                    .catch(error => {
                        alert('Error creating staff account: ' + error.message);
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';
                    });
                });
        }
    });

    // Export Staff - Updated to use new Excel export functionality
    document.getElementById('exportStaffBtn')?.addEventListener('click', function () {
        showExportModal();
    });
    
    // Add export dashboard button functionality
    document.getElementById('exportDashboardBtn')?.addEventListener('click', function () {
        showDashboardExportModal();
    });

    function showExportModal() {
        const modalHtml = `
            <div class="modal fade" id="exportModal" tabindex="-1" aria-labelledby="exportModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title" id="exportModalLabel">
                                <i class="bi bi-download me-2"></i>Export Staff Data
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="export-option-card">
                                        <div class="export-icon">
                                            <i class="bi bi-file-earmark-excel text-success" style="font-size: 2rem;"></i>
                                        </div>
                                        <h6>Excel Export</h6>
                                        <p>Download comprehensive staff data in Excel format with proper formatting</p>
                                        <button type="button" class="btn btn-success" onclick="exportStaffExcel()">
                                            <i class="bi bi-download"></i> Export to Excel
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="export-option-card">
                                        <div class="export-icon">
                                            <i class="bi bi-file-earmark-text text-primary" style="font-size: 2rem;"></i>
                                        </div>
                                        <h6>Staff with Attendance</h6>
                                        <p>Export staff data with attendance records for a specific date range</p>
                                        <div class="mb-2">
                                            <input type="date" class="form-control form-control-sm mb-1" id="startDate" placeholder="Start Date">
                                            <input type="date" class="form-control form-control-sm" id="endDate" placeholder="End Date">
                                        </div>
                                        <button type="button" class="btn btn-primary" onclick="exportStaffWithAttendance()">
                                            <i class="bi bi-download"></i> Export Report
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('exportModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('exportModal'));
        modal.show();
        
        // Set default dates
        const today = new Date();
        const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
        document.getElementById('startDate').value = lastWeek.toISOString().split('T')[0];
        document.getElementById('endDate').value = today.toISOString().split('T')[0];
    }

    function showDashboardExportModal() {
        const modalHtml = `
            <div class="modal fade" id="dashboardExportModal" tabindex="-1" aria-labelledby="dashboardExportModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title" id="dashboardExportModalLabel">
                                <i class="bi bi-download me-2"></i>Export Dashboard Data
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="export-option-card">
                                        <div class="export-icon">
                                            <i class="bi bi-speedometer2 text-info" style="font-size: 2rem;"></i>
                                        </div>
                                        <h6>Complete Dashboard</h6>
                                        <p>Export all dashboard data including attendance summary and today's records</p>
                                        <button type="button" class="btn btn-info" onclick="exportDashboardData('all')">
                                            <i class="bi bi-download"></i> Export All
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="export-option-card">
                                        <div class="export-icon">
                                            <i class="bi bi-calendar-check text-success" style="font-size: 2rem;"></i>
                                        </div>
                                        <h6>Today's Attendance</h6>
                                        <p>Export only today's attendance records with detailed status information</p>
                                        <button type="button" class="btn btn-success" onclick="exportDashboardData('attendance')">
                                            <i class="bi bi-download"></i> Export Attendance
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <div class="export-option-card">
                                        <div class="export-icon">
                                            <i class="bi bi-people text-primary" style="font-size: 2rem;"></i>
                                        </div>
                                        <h6>Staff Profiles</h6>
                                        <p>Export complete staff profiles with personal and professional details</p>
                                        <button type="button" class="btn btn-primary" onclick="exportDashboardData('staff')">
                                            <i class="bi bi-download"></i> Export Staff
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="export-option-card">
                                        <div class="export-icon">
                                            <i class="bi bi-file-earmark-text text-warning" style="font-size: 2rem;"></i>
                                        </div>
                                        <h6>Applications</h6>
                                        <p>Export leave, on-duty, and permission applications with their status</p>
                                        <button type="button" class="btn btn-warning" onclick="exportDashboardData('applications')">
                                            <i class="bi bi-download"></i> Export Applications
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('dashboardExportModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('dashboardExportModal'));
        modal.show();
    }

    // Export functions
    window.exportStaffExcel = function() {
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Exporting...';
        
        // Use the updated Excel export route
        window.location.href = '/export_staff_excel';
        
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('exportModal'));
            if (modal) modal.hide();
        }, 2000);
    };

    window.exportStaffWithAttendance = function() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (!startDate || !endDate) {
            showAlert('Please select both start and end dates', 'warning');
            return;
        }
        
        if (new Date(startDate) > new Date(endDate)) {
            showAlert('Start date cannot be later than end date', 'warning');
            return;
        }
        
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Exporting...';
        
        // Use the report export route
        const url = `/export_report_excel?report_type=custom&start_date=${startDate}&end_date=${endDate}`;
        window.location.href = url;
        
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('exportModal'));
            if (modal) modal.hide();
        }, 2000);
    };

    window.exportDashboardData = function(type) {
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Exporting...';
        
        // Use the new dashboard export route
        const url = `/admin/export_dashboard_data?type=${type}&format=excel`;
        window.location.href = url;
        
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('dashboardExportModal'));
            if (modal) modal.hide();
        }, 2000);
    };

    // Add CSS for export option cards
    const exportStyles = `
        <style>
        .export-option-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            height: 100%;
            transition: all 0.3s ease;
        }
        .export-option-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .export-option-card h6 {
            margin: 15px 0 10px 0;
            font-weight: 600;
        }
        .export-option-card p {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }
        .export-icon {
            margin-bottom: 10px;
        }
        </style>
    `;
    
    if (!document.getElementById('exportStyles')) {
        document.head.insertAdjacentHTML('beforeend', exportStyles);
        document.head.lastElementChild.id = 'exportStyles';
    }

    // Biometric Enrollment (Fake Simulation)
    const biometricModal = document.getElementById('biometricModal');
    if (biometricModal) {
        biometricModal.addEventListener('show.bs.modal', function () {
            let count = 0;
            const progressBar = document.getElementById('progressBar');
            const status = document.getElementById('enrollmentStatus');
            const done = document.getElementById('enrollmentComplete');
            const progressWrap = document.getElementById('enrollmentProgress');
            done.classList.add('hidden');
            progressWrap.classList.remove('hidden');
            const interval = setInterval(() => {
                count++;
                progressBar.style.width = `${(count / 5) * 100}%`;
                status.innerHTML = `<div class="alert alert-info">Scan ${count} of 5 completed</div>`;
                if (count >= 5) {
                    clearInterval(interval);
                    progressWrap.classList.add('hidden');
                    done.classList.remove('hidden');
                }
            }, 2000);
        });
    }

    // Leave Processing
    document.querySelectorAll('.approve-btn, .reject-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const decision = this.classList.contains('approve-btn') ? 'approve' : 'reject';
            const leaveId = this.getAttribute('data-leave-id');
            if (!confirm(`Are you sure to ${decision} this leave?`)) return;

            fetch('/process_leave', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `leave_id=${leaveId}&decision=${decision}&csrf_token=${encodeURIComponent(getCSRFToken())}`
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert(`Leave ${decision}d`);
                    location.reload();
                } else alert(data.error || `Failed to ${decision} leave`);
            });
        });
    });

    // On Duty Processing
    document.querySelectorAll('.approve-duty-btn, .reject-duty-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const decision = this.classList.contains('approve-duty-btn') ? 'approve' : 'reject';
            const dutyId = this.getAttribute('data-duty-id');

            let adminRemarks = '';
            if (decision === 'reject') {
                adminRemarks = prompt('Please provide reason for rejection (optional):') || '';
            }

            if (!confirm(`Are you sure to ${decision} this on-duty application?`)) return;

            fetch('/process_on_duty', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `application_id=${dutyId}&decision=${decision}&admin_remarks=${encodeURIComponent(adminRemarks)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || `On-duty application ${decision}d successfully`);
                    location.reload();
                } else {
                    alert(data.error || `Failed to ${decision} on-duty application`);
                }
            })
            .catch(error => {
                console.error('Error processing on-duty application:', error);
                alert('Error processing on-duty application');
            });
        });
    });

    // Permission Processing
    document.querySelectorAll('.approve-permission-btn, .reject-permission-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const decision = this.classList.contains('approve-permission-btn') ? 'approve' : 'reject';
            const permissionId = this.getAttribute('data-permission-id');

            let adminRemarks = '';
            if (decision === 'reject') {
                adminRemarks = prompt('Please provide reason for rejection (optional):') || '';
            }

            if (!confirm(`Are you sure to ${decision} this permission application?`)) return;

            fetch('/process_permission', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `application_id=${permissionId}&decision=${decision}&admin_remarks=${encodeURIComponent(adminRemarks)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || `Permission application ${decision}d successfully`);
                    location.reload();
                } else {
                    alert(data.error || `Failed to ${decision} permission application`);
                }
            })
            .catch(error => {
                console.error('Error processing permission application:', error);
                alert('Error processing permission application');
            });
        });
    });

    // Reset Add Staff Modal when closed
    document.getElementById('addStaffModal')?.addEventListener('hidden.bs.modal', function () {
        // Reset form
        document.getElementById('staffForm').reset();
        document.getElementById('biometricEnrolled').value = 'false';

        // Reset steps
        document.getElementById('staffDetailsStep').classList.remove('hidden');
        document.getElementById('biometricEnrollmentStep').classList.add('hidden');

        // Reset buttons
        document.getElementById('nextStepBtn').classList.remove('hidden');
        document.getElementById('saveStaff').classList.add('hidden');
        document.getElementById('startEnrollmentBtn').classList.remove('hidden');
        document.getElementById('triggerEnrollmentBtn').classList.add('hidden');
        document.getElementById('verifyEnrollmentBtn').classList.add('hidden');

        // Reset progress
        document.getElementById('staffCreationProgress').style.width = '50%';
        document.getElementById('staffEnrollmentProgress').classList.add('hidden');

        // Reset status
        document.getElementById('enrollmentDeviceStatus').className = 'alert alert-secondary';
        document.getElementById('enrollmentDeviceStatus').innerHTML = '<i class="bi bi-info-circle"></i> Click "Start Biometric Scan" to begin';

        // Reset button states
        document.getElementById('startEnrollmentBtn').disabled = false;
        document.getElementById('startEnrollmentBtn').innerHTML = '<i class="bi bi-fingerprint"></i> Start Enrollment';
        document.getElementById('saveStaff').disabled = false;
        document.getElementById('saveStaff').innerHTML = '<i class="bi bi-check-circle"></i> Create Staff Account';
    });

    // Biometric Device Management
    const testConnectionBtn = document.getElementById('testConnectionBtn');
    const syncAttendanceBtn = document.getElementById('syncAttendanceBtn');
    const loadUsersBtn = document.getElementById('loadUsersBtn');
    const deviceStatus = document.getElementById('deviceStatus');
    const syncResults = document.getElementById('syncResults');
    const deviceUsers = document.getElementById('deviceUsers');

    testConnectionBtn?.addEventListener('click', function() {
        const deviceIP = document.getElementById('deviceIP').value;
        testConnectionBtn.disabled = true;
        testConnectionBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Testing...';

        deviceStatus.className = 'alert alert-info';
        deviceStatus.innerHTML = '<i class="bi bi-hourglass-split"></i> Testing connection...';

        fetch('/test_biometric_connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `device_ip=${encodeURIComponent(deviceIP)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            testConnectionBtn.disabled = false;
            testConnectionBtn.innerHTML = '<i class="bi bi-wifi"></i> Test Connection';

            if (data.success) {
                deviceStatus.className = 'alert alert-success';
                deviceStatus.innerHTML = `
                    <i class="bi bi-check-circle"></i>
                    Connection successful! Device has ${data.total_users} users.
                `;
            } else {
                deviceStatus.className = 'alert alert-danger';
                deviceStatus.innerHTML = `
                    <i class="bi bi-x-circle"></i>
                    Connection failed: ${data.message}
                `;
            }
        })
        .catch(error => {
            testConnectionBtn.disabled = false;
            testConnectionBtn.innerHTML = '<i class="bi bi-wifi"></i> Test Connection';
            deviceStatus.className = 'alert alert-danger';
            deviceStatus.innerHTML = `<i class="bi bi-x-circle"></i> Error: ${error.message}`;
        });
    });

    syncAttendanceBtn?.addEventListener('click', function() {
        const deviceIP = document.getElementById('deviceIP').value;
        syncAttendanceBtn.disabled = true;
        syncAttendanceBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Syncing...';

        fetch('/sync_biometric_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `device_ip=${encodeURIComponent(deviceIP)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            syncAttendanceBtn.disabled = false;
            syncAttendanceBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Sync Attendance';

            // Update sync results
            document.getElementById('totalRecords').textContent = data.total_records || 0;
            document.getElementById('sqliteSynced').textContent = data.sqlite_synced || 0;
            document.getElementById('mysqlSynced').textContent = data.mysql_synced || 0;
            syncResults.classList.remove('hidden');

            if (data.success) {
                deviceStatus.className = 'alert alert-success';
                deviceStatus.innerHTML = `<i class="bi bi-check-circle"></i> ${data.message}`;
            } else {
                deviceStatus.className = 'alert alert-warning';
                deviceStatus.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${data.message}`;
            }
        })
        .catch(error => {
            syncAttendanceBtn.disabled = false;
            syncAttendanceBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Sync Attendance';
            deviceStatus.className = 'alert alert-danger';
            deviceStatus.innerHTML = `<i class="bi bi-x-circle"></i> Sync error: ${error.message}`;
        });
    });

    loadUsersBtn?.addEventListener('click', function() {
        const deviceIP = document.getElementById('deviceIP').value;
        loadUsersBtn.disabled = true;
        loadUsersBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading...';

        fetch(`/get_biometric_users?device_ip=${encodeURIComponent(deviceIP)}`)
        .then(response => response.json())
        .then(data => {
            loadUsersBtn.disabled = false;
            loadUsersBtn.innerHTML = '<i class="bi bi-people"></i> Load Users from Device';

            if (data.success) {
                const tbody = document.getElementById('usersTableBody');
                const userCount = document.getElementById('userCount');
                tbody.innerHTML = '';

                data.users.forEach(user => {
                    const row = tbody.insertRow();
                    row.innerHTML = `
                        <td>${user.user_id}</td>
                        <td>${user.name || 'N/A'}</td>
                        <td>${user.privilege}</td>
                        <td>${user.group_id}</td>
                        <td>
                            <button type="button" class="btn btn-sm btn-outline-success create-staff-btn me-1"
                                    data-user-id="${user.user_id}" data-user-name="${user.name || 'N/A'}"
                                    title="Create staff account for this biometric user">
                                <i class="bi bi-person-plus"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-danger delete-user-btn"
                                    data-user-id="${user.user_id}" data-user-name="${user.name || 'N/A'}"
                                    title="Delete user from biometric device">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                });

                userCount.textContent = `${data.total_users} users`;
                deviceUsers.classList.remove('hidden');
                deviceStatus.className = 'alert alert-success';
                deviceStatus.innerHTML = `<i class="bi bi-check-circle"></i> Loaded ${data.total_users} users`;

                // Add create staff account event listeners
                document.querySelectorAll('.create-staff-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const userId = this.dataset.userId;
                        const userName = this.dataset.userName;
                        createStaffFromDeviceUser(deviceIP, userId, userName);
                    });
                });

                // Add delete user event listeners
                document.querySelectorAll('.delete-user-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const userId = this.dataset.userId;
                        const userName = this.dataset.userName;

                        if (confirm(`Delete user ${userId} (${userName}) from device?`)) {
                            deleteUserFromDevice(deviceIP, userId, this);
                        }
                    });
                });

            } else {
                deviceStatus.className = 'alert alert-danger';
                deviceStatus.innerHTML = `<i class="bi bi-x-circle"></i> Failed to load users: ${data.message}`;
            }
        })
        .catch(error => {
            loadUsersBtn.disabled = false;
            loadUsersBtn.innerHTML = '<i class="bi bi-people"></i> Load Users from Device';
            deviceStatus.className = 'alert alert-danger';
            deviceStatus.innerHTML = `<i class="bi bi-x-circle"></i> Error loading users: ${error.message}`;
        });
    });

    // Real-time attendance updates
    let attendanceUpdateInterval;

    function startRealtimeUpdates() {
        // Update every 10 seconds
        attendanceUpdateInterval = setInterval(updateAttendanceTable, 10000);
        console.log('📡 Started real-time attendance updates');
    }

    function stopRealtimeUpdates() {
        if (attendanceUpdateInterval) {
            clearInterval(attendanceUpdateInterval);
            console.log('⏹️ Stopped real-time attendance updates');
        }
    }

    function updateAttendanceTable() {
        // First, poll for new device verifications and process them
        pollDeviceForNewVerifications()
            .then(() => {
                // Then update the attendance display
                return fetch('/get_realtime_attendance');
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateAttendanceDisplay(data.attendance_data);
                    updateAttendanceSummary(data.summary);

                    // Update last refresh time
                    const now = new Date();
                    const lastUpdateElement = document.getElementById('lastUpdateTime');
                    if (lastUpdateElement) {
                        lastUpdateElement.innerHTML = `<i class="bi bi-check-circle"></i> Last updated: ${now.toLocaleTimeString()}`;
                    }
                    console.log(`🔄 Attendance data updated at ${now.toLocaleTimeString()}`);
                }
            })
            .catch(error => {
                console.error('❌ Failed to update attendance data:', error);
            });
    }

    function pollDeviceForNewVerifications() {
        return fetch('/poll_device_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `device_ip=192.168.1.201&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.processed_count > 0) {
                console.log(`📱 Processed ${data.processed_count} new device verifications`);

                // Show notification for new verifications
                showNotification(`Processed ${data.processed_count} new biometric verifications`, 'info');
            }
        })
        .catch(error => {
            console.error('❌ Failed to poll device for verifications:', error);
        });
    }

    function updateAttendanceDisplay(attendanceData) {
        const tbody = document.getElementById('attendanceTableBody');
        if (!tbody) return;

        // Update each row with new data
        attendanceData.forEach(attendance => {
            const row = tbody.querySelector(`tr[data-staff-id="${attendance.staff_id}"]`);
            if (row) {
                // Update timing columns
                const timeInCell = row.querySelector('.time-in');
                const timeOutCell = row.querySelector('.time-out');
                const overtimeInCell = row.querySelector('.overtime-in');
                const overtimeOutCell = row.querySelector('.overtime-out');
                const statusCell = row.querySelector('.status');

                if (timeInCell) timeInCell.textContent = attendance.time_in || '--:--:--';
                if (timeOutCell) timeOutCell.textContent = attendance.time_out || '--:--:--';
                if (overtimeInCell) overtimeInCell.textContent = attendance.overtime_in || '--:--:--';
                if (overtimeOutCell) overtimeOutCell.textContent = attendance.overtime_out || '--:--:--';

                // Update status badge
                if (statusCell) {
                    let badgeClass = 'bg-secondary';
                    let statusText = 'Not Marked';

                    switch (attendance.status) {
                        case 'Holiday':
                            badgeClass = 'bg-dark text-white';
                            statusText = '<i class="bi bi-calendar-event"></i> Holiday';
                            break;
                        case 'present':
                            badgeClass = 'bg-success';
                            statusText = 'Present';
                            break;
                        case 'late':
                            badgeClass = 'bg-warning';
                            statusText = 'Late';
                            break;
                        case 'absent':
                            badgeClass = 'bg-danger';
                            statusText = 'Absent';
                            break;
                        case 'leave':
                        case 'On Leave':
                            badgeClass = 'bg-info';
                            statusText = 'On Leave';
                            break;
                        case 'On Duty':
                            badgeClass = 'bg-primary';
                            statusText = 'On Duty';
                            break;
                        case 'On Permission':
                            badgeClass = 'bg-warning';
                            statusText = 'On Permission';
                            break;
                    }

                    statusCell.innerHTML = `<span class="badge ${badgeClass}">${statusText}</span>`;
                }

                // Add visual feedback for recent updates
                if (attendance.time_in || attendance.time_out || attendance.overtime_in || attendance.overtime_out) {
                    // Check if this is a new update by comparing with stored data
                    const currentData = row.dataset;
                    let hasNewData = false;

                    if (currentData.timeIn !== (attendance.time_in || '') ||
                        currentData.timeOut !== (attendance.time_out || '') ||
                        currentData.overtimeIn !== (attendance.overtime_in || '') ||
                        currentData.overtimeOut !== (attendance.overtime_out || '')) {
                        hasNewData = true;
                    }

                    // Store current data for next comparison
                    row.dataset.timeIn = attendance.time_in || '';
                    row.dataset.timeOut = attendance.time_out || '';
                    row.dataset.overtimeIn = attendance.overtime_in || '';
                    row.dataset.overtimeOut = attendance.overtime_out || '';

                    if (hasNewData) {
                        // Highlight row for new updates
                        row.style.backgroundColor = '#d4edda';
                        row.style.transition = 'background-color 0.3s ease';

                        // Show notification
                        showNotification(`${attendance.full_name} updated attendance`, 'success');

                        setTimeout(() => {
                            row.style.backgroundColor = '';
                        }, 3000);
                    }
                }
            }
        });
    }

    function updateAttendanceSummary(summary) {
        // Update summary values in header only (not in modals)
        const headerStatsSection = document.querySelector('.results-stats');
        if (headerStatsSection) {
            const statItems = headerStatsSection.querySelectorAll('.stat-item');
            
            statItems.forEach(item => {
                const statValue = item.querySelector('.stat-value');
                const text = item.textContent.toLowerCase();
                
                if (text.includes('holiday') && statValue) {
                    statValue.textContent = summary.holiday || 0;
                } else if (text.includes('present') && statValue) {
                    statValue.textContent = summary.present || 0;
                } else if (text.includes('absent') && statValue) {
                    statValue.textContent = summary.absent || 0;
                } else if (text.includes('late') && statValue) {
                    statValue.textContent = summary.late || 0;
                } else if (text.includes('leave') && statValue) {
                    statValue.textContent = summary.on_leave || 0;
                } else if (text.includes('duty') && statValue) {
                    statValue.textContent = summary.on_duty || 0;
                } else if (text.includes('permission') && statValue) {
                    statValue.textContent = summary.on_permission || 0;
                }
            });
        }
    }

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    // Start real-time updates immediately (we are already inside DOMContentLoaded)
    startRealtimeUpdates();

    // Stop updates when page is hidden/minimized
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopRealtimeUpdates();
        } else {
            startRealtimeUpdates();
        }
    });

    // Stop updates when page unloads
    window.addEventListener('beforeunload', function() {
        stopRealtimeUpdates();
    });

    // User search functionality
    document.getElementById('userSearch')?.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = document.querySelectorAll('#usersTableBody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.classList.remove('hidden');
            } else {
                row.classList.add('hidden');
            }
        });
    });

    // Helper function to delete user from device
    function deleteUserFromDevice(deviceIP, userId, buttonElement) {
        buttonElement.disabled = true;
        buttonElement.innerHTML = '<i class="bi bi-hourglass-split"></i>';

        fetch('/delete_biometric_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `device_ip=${encodeURIComponent(deviceIP)}&user_id=${encodeURIComponent(userId)}&csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the row from table
                buttonElement.closest('tr').remove();

                // Update user count
                const userCount = document.getElementById('userCount');
                const currentCount = parseInt(userCount.textContent);
                userCount.textContent = `${currentCount - 1} users`;

                deviceStatus.className = 'alert alert-success';
                deviceStatus.innerHTML = `<i class="bi bi-check-circle"></i> User ${userId} deleted successfully`;
            } else {
                buttonElement.disabled = false;
                buttonElement.innerHTML = '<i class="bi bi-trash"></i>';
                deviceStatus.className = 'alert alert-danger';
                deviceStatus.innerHTML = `<i class="bi bi-x-circle"></i> Failed to delete user: ${data.message}`;
            }
        })
        .catch(error => {
            buttonElement.disabled = false;
            buttonElement.innerHTML = '<i class="bi bi-trash"></i>';
            deviceStatus.className = 'alert alert-danger';
            deviceStatus.innerHTML = `<i class="bi bi-x-circle"></i> Error deleting user: ${error.message}`;
        });
    }

    // Global functions for biometric testing
    window.syncBiometricAttendance = function() {
        const btn = document.getElementById('syncAttendanceBtn');
        const originalText = btn.innerHTML;

        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Syncing...';

        fetch('/sync_biometric_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `csrf_token=${encodeURIComponent(getCSRFToken())}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Sync completed!\nTotal Records: ${data.total_records}\nSQLite Synced: ${data.sqlite_synced}\nMySQL Synced: ${data.mysql_synced}`);
                location.reload();
            } else {
                alert(`Sync failed: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during sync');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    };

    // Work Time Assignment functionality
    function initializeWorkTimeAssignment() {
        const workTimeForm = document.getElementById('workTimeForm');
        const checkinTimeInput = document.getElementById('institutionCheckinTime');
        const checkoutTimeInput = document.getElementById('institutionCheckoutTime');
        const validationMessage = document.getElementById('timeValidationMessage');
        const successMessage = document.getElementById('timingSuccessMessage');
        const errorMessage = document.getElementById('timingErrorMessage');
        const resetBtn = document.getElementById('resetTimingBtn');
        const currentCheckinTimeDisplay = document.getElementById('currentCheckinTime');
        const currentCheckoutTimeDisplay = document.getElementById('currentCheckoutTime');

        // Load current institution timings on page load
        function loadCurrentTimings() {
            fetch('/api/get_institution_timings', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const checkinTime = data.checkin_time || '09:00';
                    const checkoutTime = data.checkout_time || '17:00';
                    
                    // Update form inputs
                    checkinTimeInput.value = checkinTime;
                    checkoutTimeInput.value = checkoutTime;
                    
                    // Update display cards
                    currentCheckinTimeDisplay.textContent = formatTimeToAMPM(checkinTime);
                    currentCheckoutTimeDisplay.textContent = formatTimeToAMPM(checkoutTime);
                }
            })
            .catch(error => {
                console.error('Error loading timings:', error);
            });
        }

        // Format time from 24-hour to 12-hour format
        function formatTimeToAMPM(time24) {
            const [hours, minutes] = time24.split(':');
            const hour = parseInt(hours);
            const ampm = hour >= 12 ? 'PM' : 'AM';
            const hour12 = hour % 12 || 12;
            return `${hour12}:${minutes} ${ampm}`;
        }

        // Validate time inputs
        function validateTimes() {
            const checkinTime = checkinTimeInput.value;
            const checkoutTime = checkoutTimeInput.value;
            
            if (checkinTime && checkoutTime) {
                const checkinMinutes = timeToMinutes(checkinTime);
                const checkoutMinutes = timeToMinutes(checkoutTime);
                
                if (checkoutMinutes <= checkinMinutes) {
                    validationMessage.style.display = 'block';
                    return false;
                } else {
                    validationMessage.style.display = 'none';
                    return true;
                }
            }
            return true;
        }

        // Convert time string to minutes for comparison
        function timeToMinutes(timeString) {
            const [hours, minutes] = timeString.split(':').map(Number);
            return hours * 60 + minutes;
        }

        // Hide all messages
        function hideAllMessages() {
            successMessage.style.display = 'none';
            errorMessage.style.display = 'none';
            validationMessage.style.display = 'none';
        }

        // Event listeners for time validation
        checkinTimeInput.addEventListener('change', validateTimes);
        checkoutTimeInput.addEventListener('change', validateTimes);

        // Form submission handler
        if (workTimeForm) {
            workTimeForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                hideAllMessages();
                
                if (!validateTimes()) {
                    return;
                }
                
                const formData = new FormData();
                formData.append('checkin_time', checkinTimeInput.value);
                formData.append('checkout_time', checkoutTimeInput.value);
                formData.append('csrf_token', getCSRFToken());
                
                // Disable submit button
                const submitBtn = document.getElementById('saveTimingBtn');
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
                
                fetch('/api/update_institution_timings', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Enhanced success message with attendance impact info
                        successMessage.innerHTML = `
                            <i class="bi bi-check-circle-fill"></i> 
                            <strong>Institution timings updated successfully!</strong>
                            <br><small class="mt-1 d-block">
                                <i class="bi bi-info-circle"></i> 
                                New attendance entries will use these timings:
                                <br>• <strong>Late</strong> if check-in after ${formatTimeToAMPM(checkinTimeInput.value)} + 10 min grace
                                <br>• <strong>Early departure</strong> if check-out before ${formatTimeToAMPM(checkoutTimeInput.value)}
                            </small>
                        `;
                        successMessage.style.display = 'block';
                        
                        // Update display cards
                        currentCheckinTimeDisplay.textContent = formatTimeToAMPM(checkinTimeInput.value);
                        currentCheckoutTimeDisplay.textContent = formatTimeToAMPM(checkoutTimeInput.value);
                        
                        // Auto-hide success message after 6 seconds (more time to read)
                        setTimeout(() => {
                            successMessage.style.display = 'none';
                        }, 6000);
                    } else {
                        errorMessage.style.display = 'block';
                        document.getElementById('errorMessageText').textContent = data.message || 'Failed to update timings. Please try again.';
                    }
                })
                .catch(error => {
                    console.error('Error updating timings:', error);
                    errorMessage.style.display = 'block';
                    document.getElementById('errorMessageText').textContent = 'Network error. Please try again.';
                })
                .finally(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                });
            });
        }

        // Reset button handler
        if (resetBtn) {
            resetBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to reset to default timings (9:00 AM - 5:00 PM)?')) {
                    checkinTimeInput.value = '09:00';
                    checkoutTimeInput.value = '17:00';
                    hideAllMessages();
                    validateTimes();
                }
            });
        }

        // Load current timings on initialization
        loadCurrentTimings();
    }

    // Initialize Work Time Assignment when DOM is loaded
    initializeWorkTimeAssignment();

});
