/**
 * Weekly Attendance Calendar Component
 * 
 * This component replaces the existing FullCalendar implementation with a custom
 * weekly view that shows detailed daily attendance information including:
 * - Present/Absent status
 * - Shift type
 * - Morning/Evening thumb timings
 * - Calculated delays and early departures
 */

class WeeklyAttendanceCalendar {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            staffId: options.staffId || null,
            isAdminView: options.isAdminView || false,
            ...options
        };
        
        this.currentWeekStart = this.getWeekStart(new Date());
        this.weeklyData = [];
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Weekly calendar container not found');
            return;
        }
        
        this.render();
        this.loadWeeklyData();
    }
    
    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
        return new Date(d.setDate(diff));
    }
    
    formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    isWeeklyOffDay(dateStr) {
        try {
            const date = new Date(dateStr + 'T00:00:00');
            const dayOfWeek = date.getDay(); // 0=Sunday, 1=Monday, ..., 6=Saturday

            // Get weekly off configuration from global variable or default
            const weeklyOffDays = window.weeklyOffDays || ['sunday'];

            // Day name mapping
            const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
            const dayName = dayNames[dayOfWeek];

            return weeklyOffDays.includes(dayName);
        } catch (error) {
            console.error('Error checking weekly off day:', error);
            return false;
        }
    }

    getWeeklyOffDayName(dateStr) {
        try {
            const date = new Date(dateStr + 'T00:00:00');
            const dayOfWeek = date.getDay(); // 0=Sunday, 1=Monday, ..., 6=Saturday
            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            return dayNames[dayOfWeek];
        } catch (error) {
            console.error('Error getting day name:', error);
            return 'Weekly Off';
        }
    }
    
    render() {
        const weekStart = new Date(this.currentWeekStart);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        
        this.container.innerHTML = `
            <div class="weekly-calendar">
                <div class="calendar-header">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="btn-group" role="group">
                            <button class="btn btn-outline-primary btn-sm" id="prevWeek" title="Previous Week (Left Arrow)">
                                <i class="bi bi-chevron-left"></i> Previous
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" id="todayWeek" title="Go to Current Week">
                                <i class="bi bi-calendar-today"></i> Today
                            </button>
                        </div>
                        <div class="text-center">
                            <h5 class="mb-0">
                                Week of ${weekStart.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}
                            </h5>
                            <small class="text-muted">${weekStart.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</small>
                        </div>
                        <button class="btn btn-outline-primary btn-sm" id="nextWeek" title="Next Week (Right Arrow)">
                            Next <i class="bi bi-chevron-right"></i>
                        </button>
                    </div>
                </div>
                <div class="calendar-body">
                    <div class="row" id="weeklyGrid">
                        <div class="col-12">
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Loading weekly attendance...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add event listeners for navigation
        document.getElementById('prevWeek').addEventListener('click', () => {
            this.navigateWeek(-1);
        });

        document.getElementById('nextWeek').addEventListener('click', () => {
            this.navigateWeek(1);
        });

        document.getElementById('todayWeek').addEventListener('click', () => {
            this.goToCurrentWeek();
        });

    }
    
    navigateWeek(direction) {
        const newWeekStart = new Date(this.currentWeekStart);
        newWeekStart.setDate(newWeekStart.getDate() + (direction * 7));
        this.currentWeekStart = newWeekStart;
        
        this.render();
        this.loadWeeklyData();
    }
    
    loadWeeklyData() {
        const weekStartStr = this.formatDate(this.currentWeekStart);
        const weekEndStr = this.formatDate(new Date(this.currentWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000));
        
        let attendanceUrl = `/get_weekly_attendance?week_start=${weekStartStr}`;
        if (this.options.staffId) {
            attendanceUrl += `&staff_id=${this.options.staffId}`;
        }
        
        // Load both attendance and holiday data simultaneously
        Promise.all([
            fetch(attendanceUrl).then(response => response.json()),
            this.loadHolidaysData(weekStartStr, weekEndStr)
        ])
            .then(([attendanceData, holidaysData]) => {
                if (attendanceData.success) {
                    this.weeklyData = attendanceData.weekly_data;
                    this.holidaysData = holidaysData;
                    
                    // Merge holiday information into weekly data
                    this.mergeHolidaysWithWeeklyData();
                    
                    this.renderWeeklyGrid(attendanceData);
                } else {
                    this.showError(attendanceData.error || 'Failed to load weekly data');
                }
            })
            .catch(error => {
                console.error('Error loading weekly data:', error);
                this.showError('Failed to load weekly attendance data');
            });
    }
    
    loadHolidaysData(startDate, endDate) {
        let holidayUrl = `/api/staff/holidays?start_date=${startDate}&end_date=${endDate}`;
        if (this.options.staffId) {
            holidayUrl += `&staff_id=${this.options.staffId}`;
        }
        
        return fetch(holidayUrl)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    return data.holidays || [];
                } else {
                    console.warn('Failed to load holidays:', data.message);
                    return [];
                }
            })
            .catch(error => {
                console.error('Error loading holidays:', error);
                return [];
            });
    }
    
    mergeHolidaysWithWeeklyData() {
        if (!this.holidaysData || !this.weeklyData) return;
        
        // Create a map of holidays by date
        const holidaysByDate = new Map();
        
        this.holidaysData.forEach(holiday => {
            const startDate = new Date(holiday.start_date);
            const endDate = new Date(holiday.end_date);
            
            // Add holiday to each date it covers
            for (let date = new Date(startDate); date <= endDate; date.setDate(date.getDate() + 1)) {
                const dateStr = this.formatDate(date);
                if (!holidaysByDate.has(dateStr)) {
                    holidaysByDate.set(dateStr, []);
                }
                holidaysByDate.get(dateStr).push({
                    id: holiday.id,
                    name: holiday.holiday_name,
                    type: holiday.holiday_type,
                    description: holiday.description,
                    isRecurring: holiday.is_recurring,
                    departments: holiday.departments
                });
            }
        });
        
        // Merge holidays into weekly data
        this.weeklyData.forEach(dayData => {
            const holidays = holidaysByDate.get(dayData.date) || [];
            dayData.holidays = holidays;

            // Check if this day is a weekly off day
            const isWeeklyOff = this.isWeeklyOffDay(dayData.date);
            dayData.is_weekly_off = isWeeklyOff;

            // If there are holidays on this day, mark it as a holiday
            if (holidays.length > 0) {
                dayData.is_holiday = true;
                dayData.holiday_types = holidays.map(h => h.type);

                // Override present status if it's a holiday and staff wasn't present
                if (dayData.present_status === 'Absent' && holidays.some(h => h.type !== 'department_specific' || dayData.present_status === 'Absent')) {
                    dayData.present_status = 'Holiday';
                    dayData.holiday_info = holidays.map(h => h.name).join(', ');
                }
            } else if (isWeeklyOff && dayData.present_status === 'Absent') {
                // Mark as weekly off if no holiday but it's a weekly off day
                dayData.present_status = 'Weekly Off';
                dayData.weekly_off_info = this.getWeeklyOffDayName(dayData.date);
            }
        });
    }
    
    renderWeeklyGrid(data) {
        const grid = document.getElementById('weeklyGrid');
        
        let html = '<div class="table-responsive">';
        html += '<table class="table table-bordered weekly-attendance-table">';
        html += '<thead class="table-light">';
        html += '<tr>';
        
        // Header row with day names
        data.weekly_data.forEach(day => {
            const isToday = day.date === new Date().toISOString().split('T')[0];
            const headerClass = isToday ? 'bg-primary text-white' : '';
            html += `<th class="text-center ${headerClass}">${day.day_name}<br><small>${new Date(day.date).toLocaleDateString()}</small></th>`;
        });
        
        html += '</tr>';
        html += '</thead>';
        html += '<tbody>';
        html += '<tr>';
        
        // Data cells for each day
        data.weekly_data.forEach(day => {
            html += '<td class="day-cell">';
            html += this.renderDayCell(day);
            html += '</td>';
        });
        
        html += '</tr>';
        html += '</tbody>';
        html += '</table>';
        html += '</div>';
        
        grid.innerHTML = html;
    }
    
    renderDayCell(dayData) {
        let html = '<div class="day-content">';

        // Check if there are holidays on this day
        if (dayData.holidays && dayData.holidays.length > 0) {
            html += this.renderHolidayInfo(dayData.holidays);
        }

        // Present/Absent/On Duty/Holiday/Weekly Off status
        let statusClass = 'text-danger'; // Default for absent
        let statusText = dayData.present_status;

        if (dayData.present_status === 'Present') {
            statusClass = 'text-success';
        } else if (dayData.present_status === 'On Duty') {
            statusClass = 'text-info';
        } else if (dayData.present_status === 'Holiday') {
            statusClass = 'text-warning';
            statusText = 'Holiday';
        } else if (dayData.present_status === 'Weekly Off') {
            statusClass = 'text-secondary';
            statusText = 'Weekly Off';
        }

        html += `<div class="status-badge"><strong class="${statusClass}">${statusText}</strong></div>`;

        // Show leave applications (approved or pending)
        if (dayData.leave_applications && dayData.leave_applications.length > 0) {
            html += '<div class="application-badges mt-2">';
            dayData.leave_applications.forEach(leave => {
                const badgeClass = leave.status === 'approved' ? 'bg-success' : 'bg-warning';
                const iconClass = leave.status === 'approved' ? 'bi-check-circle' : 'bi-clock-history';
                const statusText = leave.status === 'approved' ? 'Approved' : 'Pending';
                html += `<div class="badge ${badgeClass} d-block mb-1" title="${leave.reason}">`;
                html += `<i class="bi bi-calendar-x"></i> Leave (${leave.type})`;
                html += `<br><small><i class="bi ${iconClass}"></i> ${statusText}</small>`;
                html += `</div>`;
            });
            html += '</div>';
        }

        // Show on-duty applications (approved or pending)
        if (dayData.on_duty_applications && dayData.on_duty_applications.length > 0) {
            html += '<div class="application-badges mt-2">';
            dayData.on_duty_applications.forEach(od => {
                const badgeClass = od.status === 'approved' ? 'bg-info' : 'bg-secondary';
                const iconClass = od.status === 'approved' ? 'bi-check-circle' : 'bi-clock-history';
                const statusText = od.status === 'approved' ? 'Approved' : 'Pending';
                const locationText = od.location ? ` - ${od.location}` : '';
                html += `<div class="badge ${badgeClass} d-block mb-1" title="${od.purpose}">`;
                html += `<i class="bi bi-briefcase"></i> On Duty${locationText}`;
                html += `<br><small><i class="bi ${iconClass}"></i> ${statusText}</small>`;
                html += `</div>`;
            });
            html += '</div>';
        }

        // Show permission applications (approved or pending)
        if (dayData.permission_applications && dayData.permission_applications.length > 0) {
            html += '<div class="application-badges mt-2">';
            dayData.permission_applications.forEach(perm => {
                const badgeClass = perm.status === 'approved' ? 'bg-primary' : 'bg-light text-dark';
                const iconClass = perm.status === 'approved' ? 'bi-check-circle' : 'bi-clock-history';
                const statusText = perm.status === 'approved' ? 'Approved' : 'Pending';
                const timeText = perm.start_time && perm.end_time ? ` ${perm.start_time}-${perm.end_time}` : '';
                html += `<div class="badge ${badgeClass} d-block mb-1" title="${perm.reason}">`;
                html += `<i class="bi bi-clock"></i> Permission${timeText}`;
                html += `<br><small><i class="bi ${iconClass}"></i> ${statusText}</small>`;
                html += `</div>`;
            });
            html += '</div>';
        }

        // Holiday-specific information
        if (dayData.present_status === 'Holiday' && dayData.holiday_info) {
            html += `<div class="holiday-info">`;
            html += `<div class="holiday-details"><small class="text-warning"><i class="bi bi-calendar-event"></i> ${dayData.holiday_info}</small></div>`;
            html += `</div>`;
        }

        // Weekly off-specific information
        if (dayData.present_status === 'Weekly Off' && dayData.weekly_off_info) {
            html += `<div class="weekly-off-info">`;
            html += `<div class="weekly-off-details"><small class="text-secondary"><i class="bi bi-calendar-x"></i> ${dayData.weekly_off_info}</small></div>`;
            html += `</div>`;
        }

        // Handle On Duty status display
        else if (dayData.present_status === 'On Duty') {
            html += `<div class="on-duty-info">`;
            html += `<div class="duty-type"><small class="text-info"><strong>Type:</strong> ${dayData.on_duty_type}</small></div>`;
            if (dayData.on_duty_location && dayData.on_duty_location !== 'Not specified') {
                html += `<div class="duty-location"><small class="text-muted"><strong>Location:</strong> ${dayData.on_duty_location}</small></div>`;
            }
            if (dayData.on_duty_purpose) {
                const truncatedPurpose = dayData.on_duty_purpose.length > 30 ?
                    dayData.on_duty_purpose.substring(0, 30) + '...' :
                    dayData.on_duty_purpose;
                html += `<div class="duty-purpose"><small class="text-secondary" title="${dayData.on_duty_purpose}"><strong>Purpose:</strong> ${truncatedPurpose}</small></div>`;
            }
            html += `</div>`;
        } 
        
        // Regular attendance display (but not if it's a holiday without attendance)
        else if (dayData.present_status !== 'Holiday') {
            // Shift type and timing (only for regular attendance)
            html += `<div class="shift-info">`;
            html += `<div class="shift-type"><small class="text-muted">${dayData.shift_type_display}</small></div>`;
            if (dayData.shift_start_time && dayData.shift_end_time) {
                html += `<div class="shift-timing"><small class="text-primary"><strong>Shift:</strong> ${dayData.shift_start_time} - ${dayData.shift_end_time}</small></div>`;
            }
            html += `</div>`;
        }

        // Show attendance details only if present (regardless of holiday status)
        if (dayData.present_status === 'Present') {
            // Morning thumb timing
            if (dayData.morning_thumb) {
                html += `<div class="timing-section">`;
                html += `<div class="timing-info">`;
                html += `<span class="timing-label">Morning Thumb:</span>`;
                html += `<span class="timing-value">${dayData.morning_thumb}</span>`;
                html += `</div>`;

                // Arrived soon information (early arrival)
                if (dayData.arrived_soon_info) {
                    html += `<div class="arrived-soon-info">`;
                    html += `<small class="text-success"><i class="bi bi-clock-fill"></i> ${dayData.arrived_soon_info}</small>`;
                    html += `</div>`;
                }

                // Delay information with detailed timing
                if (dayData.delay_info) {
                    html += `<div class="delay-info">`;
                    html += `<small class="text-warning"><i class="bi bi-clock-fill"></i> ${dayData.delay_info}</small>`;
                    html += `</div>`;
                }
                html += `</div>`;
            }

            // Evening thumb timing
            if (dayData.evening_thumb) {
                html += `<div class="timing-section">`;
                html += `<div class="timing-info">`;
                html += `<span class="timing-label">Evening Thumb:</span>`;
                html += `<span class="timing-value">${dayData.evening_thumb}</span>`;
                html += `</div>`;

                // Left soon information with detailed timing
                if (dayData.left_soon_info) {
                    html += `<div class="left-soon-info">`;
                    html += `<small class="text-info"><i class="bi bi-clock-fill"></i> ${dayData.left_soon_info}</small>`;
                    html += `</div>`;
                }
                html += `</div>`;
            }

            // Overtime information
            if (dayData.overtime_in || dayData.overtime_out) {
                html += `<div class="overtime-section">`;
                html += `<div class="overtime-header"><small class="text-secondary"><strong>Overtime:</strong></small></div>`;
                if (dayData.overtime_in) {
                    html += `<div class="overtime-timing"><small>In: ${dayData.overtime_in}</small></div>`;
                }
                if (dayData.overtime_out) {
                    html += `<div class="overtime-timing"><small>Out: ${dayData.overtime_out}</small></div>`;
                }
                html += `</div>`;
            }
        }

        html += '</div>';
        return html;
    }
    
    renderHolidayInfo(holidays) {
        let html = '<div class="holiday-badges">';
        
        holidays.forEach(holiday => {
            let badgeClass = 'badge-secondary';
            let iconClass = 'bi-calendar-event';
            
            switch (holiday.type) {
                case 'institution_wide':
                    badgeClass = 'badge bg-success holiday-badge-institution';
                    iconClass = 'bi-building';
                    break;
                case 'department_specific':
                    badgeClass = 'badge bg-warning holiday-badge-department';
                    iconClass = 'bi-people';
                    break;
                case 'common_leave':
                    badgeClass = 'badge bg-primary holiday-badge-common';
                    iconClass = 'bi-calendar-heart';
                    break;
            }
            
            const holidayName = holiday.name.length > 15 ? 
                holiday.name.substring(0, 15) + '...' : 
                holiday.name;
            
            html += `<div class="${badgeClass} mb-1" title="${holiday.name}${holiday.description ? ' - ' + holiday.description : ''}">`;
            html += `<i class="bi ${iconClass}"></i> ${holidayName}`;
            html += `</div>`;
        });
        
        html += '</div>';
        return html;
    }
    
    showError(message) {
        const grid = document.getElementById('weeklyGrid');
        grid.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> ${message}
                </div>
            </div>
        `;
    }
    
    // Public method to refresh data
    refresh() {
        this.loadWeeklyData();
    }
    
    // Public method to navigate to specific week
    goToWeek(date) {
        this.currentWeekStart = this.getWeekStart(date);
        this.render();
        this.loadWeeklyData();
    }
    
    // Public method to go to current week
    goToCurrentWeek() {
        this.goToWeek(new Date());
    }

    // Add keyboard navigation support
    addKeyboardNavigation() {
        // Remove existing listener if it exists
        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler);
        }

        this.keyboardHandler = (event) => {
            // Only handle keyboard events when the calendar container is focused or visible
            if (!this.container.closest('.modal')?.classList.contains('show') &&
                !document.activeElement?.closest('.weekly-calendar')) {
                return;
            }

            switch (event.key) {
                case 'ArrowLeft':
                    event.preventDefault();
                    this.navigateWeek(-1);
                    break;
                case 'ArrowRight':
                    event.preventDefault();
                    this.navigateWeek(1);
                    break;
                case 'Home':
                    event.preventDefault();
                    this.goToCurrentWeek();
                    break;
                case 'r':
                case 'R':
                    if (event.ctrlKey || event.metaKey) {
                        event.preventDefault();
                        this.refresh();
                    }
                    break;
            }
        };

        document.addEventListener('keydown', this.keyboardHandler);
    }

    // Cleanup method to remove event listeners
    destroy() {
        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler);
        }
    }
}

// CSS styles for the weekly calendar
const weeklyCalendarStyles = `
<style>
.weekly-calendar {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.weekly-attendance-table {
    margin-bottom: 0;
}

.weekly-attendance-table th {
    vertical-align: middle;
    padding: 12px 8px;
    font-weight: 600;
}

.day-cell {
    vertical-align: top;
    padding: 12px 8px;
    min-height: 200px;
    width: 14.28%; /* 100% / 7 days */
}

.day-content {
    min-height: 180px;
}

.status-badge {
    margin-bottom: 8px;
    font-size: 14px;
}

.shift-info {
    margin-bottom: 10px;
}

.shift-type {
    margin-bottom: 4px;
    font-size: 12px;
}

.shift-timing {
    font-size: 11px;
    margin-bottom: 6px;
}

.timing-section {
    margin-bottom: 8px;
    padding: 4px 0;
    border-bottom: 1px solid #f0f0f0;
}

.timing-section:last-of-type {
    border-bottom: none;
}

.timing-info {
    margin-bottom: 4px;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.timing-label {
    font-size: 11px;
    color: white;
    font-weight: 600;
}

.timing-value {
    font-size: 12px;
    font-weight: 500;
    color: #495057;
}

.arrived-soon-info, .delay-info, .left-soon-info {
    margin-top: 4px;
    padding: 3px 6px;
    border-radius: 4px;
    background-color: rgba(255, 193, 7, 0.1);
    border-left: 3px solid #ffc107;
}

.arrived-soon-info {
    background-color: rgba(25, 135, 84, 0.1);
    border-left-color: #198754;
}

.left-soon-info {
    background-color: rgba(13, 202, 240, 0.1);
    border-left-color: #0dcaf0;
}

.overtime-section {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid #dee2e6;
}

.overtime-header {
    margin-bottom: 4px;
}

.overtime-timing {
    font-size: 11px;
    margin-bottom: 2px;
    color: white;
}

.weekly-attendance-table td:hover {
    background-color: #f8f9fa;
}

@media (max-width: 768px) {
    .day-cell {
        min-height: 150px;
        padding: 8px 4px;
    }
    
    .day-content {
        min-height: 130px;
    }
    
    .timing-info {
        font-size: 12px;
    }
}

/* Enhanced Holiday Badge Styling with Color Coding */
.holiday-badges .badge {
    font-size: 10px;
    margin-right: 4px;
    margin-bottom: 2px;
    display: inline-block;
    border-radius: 6px;
    padding: 4px 6px;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Institution-wide holiday badges - Green gradient */
.holiday-badge-institution {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
    border: 1px solid #28a745;
    color: white !important;
}

/* Department-specific holiday badges - Orange gradient */
.holiday-badge-department {
    background: linear-gradient(135deg, #fd7e14 0%, #ffc107 100%) !important;
    border: 1px solid #fd7e14;
    color: #212529 !important;
}

/* Common leave holiday badges - Blue/Purple gradient */
.holiday-badge-common {
    background: linear-gradient(135deg, #6f42c1 0%, #17a2b8 100%) !important;
    border: 1px solid #6f42c1;
    color: white !important;
}

.holiday-info {
    margin-bottom: 8px;
}

.holiday-details {
    font-size: 11px;
    margin-bottom: 2px;
}

/* Weekly off styling */
.weekly-off-info {
    margin-bottom: 8px;
}

.weekly-off-details {
    font-size: 11px;
    margin-bottom: 2px;
    font-style: italic;
}

/* Application badges styling (Leave, On Duty, Permission) */
.application-badges {
    margin-top: 8px;
    margin-bottom: 8px;
}

.application-badges .badge {
    font-size: 10px;
    padding: 6px 8px;
    border-radius: 6px;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    line-height: 1.4;
    max-width: 100%;
    word-wrap: break-word;
}

.application-badges .badge small {
    font-size: 9px;
    display: block;
    margin-top: 2px;
    opacity: 0.9;
}

.application-badges .badge i {
    font-size: 10px;
}

/* Specific application badge styles */
.application-badges .bg-success {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
    border: 1px solid #28a745;
}

.application-badges .bg-warning {
    background: linear-gradient(135deg, #ffc107 0%, #ffdd57 100%) !important;
    border: 1px solid #ffc107;
    color: #212529 !important;
}

.application-badges .bg-info {
    background: linear-gradient(135deg, #17a2b8 0%, #5bc0de 100%) !important;
    border: 1px solid #17a2b8;
}

.application-badges .bg-secondary {
    background: linear-gradient(135deg, white 0%, #9ba3aa 100%) !important;
    border: 1px solid white;
}

.application-badges .bg-primary {
    background: linear-gradient(135deg, #0d6efd 0%, #4895ff 100%) !important;
    border: 1px solid #0d6efd;
}

.application-badges .bg-light {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
    border: 1px solid #dee2e6;
}

</style>
`;

// Inject styles into the document
if (!document.getElementById('weekly-calendar-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'weekly-calendar-styles';
    styleElement.innerHTML = weeklyCalendarStyles;
    document.head.appendChild(styleElement);
}
