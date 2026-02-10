// Reporting Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the reporting dashboard
    initializeReportingDashboard();
});

let currentReportType = null;
let currentReportData = null;
let attendanceChart = null;
let trendsChart = null;

function initializeReportingDashboard() {
    // Load summary dashboard data
    loadSummaryDashboard();
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Load departments for filters
    loadDepartments();
}

function initializeEventListeners() {
    // Report generation
    document.getElementById('generateReportBtn').addEventListener('click', generateReport);
    document.getElementById('resetFiltersBtn').addEventListener('click', resetFilters);
    
    // Export options
    document.getElementById('exportExcelBtn').addEventListener('click', exportToExcel);
    document.getElementById('exportPdfBtn').addEventListener('click', exportToPdf);
    document.getElementById('printReportBtn').addEventListener('click', printReport);
    document.getElementById('shareReportBtn').addEventListener('click', shareReport);
}

function selectReportType(reportType) {
    currentReportType = reportType;
    
    // Update UI
    document.getElementById('selectedReportType').value = reportType.charAt(0).toUpperCase() + reportType.slice(1) + ' Report';
    document.getElementById('reportFilters').style.display = 'block';
    
    // Show/hide relevant filter groups
    hideAllFilterGroups();
    
    switch(reportType) {
        case 'daily':
            document.getElementById('dateFilterGroup').style.display = 'block';
            break;
        case 'weekly':
        case 'custom':
        case 'trends':
            document.getElementById('dateRangeGroup').style.display = 'block';
            document.getElementById('endDateGroup').style.display = 'block';
            if (reportType === 'custom') {
                document.getElementById('departmentGroup').style.display = 'block';
            }
            break;
        case 'monthly':
            document.getElementById('monthYearGroup').style.display = 'block';
            break;
        case 'yearly':
            document.getElementById('yearGroup').style.display = 'block';
            break;
        case 'department':
            document.getElementById('dateRangeGroup').style.display = 'block';
            document.getElementById('endDateGroup').style.display = 'block';
            document.getElementById('departmentGroup').style.display = 'block';
            break;
        case 'summary':
            // No additional filters needed
            break;
    }
    
    // Set default dates
    setDefaultDates();
}

function hideAllFilterGroups() {
    const filterGroups = [
        'dateFilterGroup', 'dateRangeGroup', 'endDateGroup', 
        'monthYearGroup', 'yearGroup', 'departmentGroup'
    ];
    
    filterGroups.forEach(groupId => {
        document.getElementById(groupId).style.display = 'none';
    });
}

function setDefaultDates() {
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const weekAgoStr = weekAgo.toISOString().split('T')[0];
    
    // Get current year and month - force to actual current year
    const currentYear = today.getFullYear();
    const currentMonth = today.toISOString().slice(0, 7); // Format: YYYY-MM
    
    console.log('Setting default dates - Current Year:', currentYear); // Debug log
    
    // Set date fields
    const reportDate = document.getElementById('reportDate');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const yearInput = document.getElementById('year');
    const monthYearInput = document.getElementById('monthYear');
    
    if (reportDate) reportDate.value = todayStr;
    if (startDate) startDate.value = weekAgoStr;
    if (endDate) endDate.value = todayStr;
    if (yearInput) {
        yearInput.value = currentYear;
        console.log('Year input set to:', yearInput.value); // Debug log
    }
    if (monthYearInput) monthYearInput.value = currentMonth;
}

function loadSummaryDashboard() {
    fetch('/get_summary_dashboard')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateSummaryCards(data.summary);
            }
        })
        .catch(error => {
            console.error('Error loading summary dashboard:', error);
        });
}

function updateSummaryCards(summary) {
    document.getElementById('totalStaffToday').textContent = summary.today_summary.total_staff || 0;
    document.getElementById('presentToday').textContent = summary.today_summary.present_today || 0;
    document.getElementById('lateToday').textContent = summary.today_summary.late_today || 0;
    document.getElementById('attendanceRateToday').textContent = summary.attendance_rate_today.toFixed(1) + '%';
}

function loadDepartments() {
    fetch('/get_departments')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const departmentSelect = document.getElementById('department');
                departmentSelect.innerHTML = '<option value="">All Departments</option>';
                
                data.departments.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept.name;
                    option.textContent = dept.name;
                    departmentSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading departments:', error);
        });
}

function generateReport() {
    if (!currentReportType) {
        showAlert('Please select a report type first', 'warning');
        return;
    }
    
    // Show loading spinner
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('reportContent').style.display = 'none';
    document.getElementById('exportOptions').style.display = 'none';
    
    // Prepare request parameters
    const params = new URLSearchParams();
    params.append('report_type', currentReportType);
    
    // Add type-specific parameters
    switch(currentReportType) {
        case 'daily':
            params.append('date', document.getElementById('reportDate').value);
            break;
        case 'weekly':
        case 'custom':
        case 'trends':
            params.append('start_date', document.getElementById('startDate').value);
            params.append('end_date', document.getElementById('endDate').value);
            if (currentReportType === 'custom' || currentReportType === 'department') {
                const dept = document.getElementById('department').value;
                if (dept) params.append('department', dept);
            }
            break;
        case 'monthly':
            const monthYear = document.getElementById('monthYear').value;
            if (monthYear) {
                const [year, month] = monthYear.split('-');
                params.append('year', year);
                params.append('month', month);
            }
            break;
        case 'yearly':
            params.append('year', document.getElementById('year').value);
            break;
        case 'department':
            params.append('start_date', document.getElementById('startDate').value);
            params.append('end_date', document.getElementById('endDate').value);
            params.append('department', document.getElementById('department').value);
            break;
    }
    
    // Make API request
    fetch(`/generate_report?${params}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('loadingSpinner').style.display = 'none';
            
            if (data.success) {
                currentReportData = data.report;
                displayReport(data.report);
                document.getElementById('exportOptions').style.display = 'block';
            } else {
                showAlert('Error generating report: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            document.getElementById('loadingSpinner').style.display = 'none';
            showAlert('Error: ' + error.message, 'danger');
        });
}

function displayReport(reportData) {
    const reportContent = document.getElementById('reportContent');
    const reportTitle = document.getElementById('reportTitle');
    const reportTimestamp = document.getElementById('reportTimestamp');
    const reportDataDiv = document.getElementById('reportData');
    
    // Update header
    reportTitle.textContent = `${reportData.report_type.charAt(0).toUpperCase() + reportData.report_type.slice(1)} Report`;
    reportTimestamp.textContent = `Generated: ${new Date().toLocaleString()}`;
    
    // Clear previous content
    reportDataDiv.innerHTML = '';
    
    // Generate report content based on type
    switch(reportData.report_type) {
        case 'daily':
            displayDailyReport(reportData, reportDataDiv);
            break;
        case 'weekly':
            displayWeeklyReport(reportData, reportDataDiv);
            break;
        case 'monthly':
            displayMonthlyReport(reportData, reportDataDiv);
            break;
        case 'yearly':
            displayYearlyReport(reportData, reportDataDiv);
            break;
        case 'department':
            displayDepartmentReport(reportData, reportDataDiv);
            break;
        case 'custom':
            displayCustomReport(reportData, reportDataDiv);
            break;
        case 'trends':
            displayTrendsReport(reportData, reportDataDiv);
            break;
        case 'summary':
            displaySummaryReport(reportData, reportDataDiv);
            break;
    }
    
    // Show report
    reportContent.style.display = 'block';
    
    // Create charts if applicable
    createCharts(reportData);
}

function displayDailyReport(data, container) {
    const stats = data.statistics;
    
    container.innerHTML = `
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h4>${stats.total_staff}</h4>
                        <p class="mb-0">Total Staff</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h4>${stats.present_count}</h4>
                        <p class="mb-0">Present</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <h4>${stats.late_count}</h4>
                        <p class="mb-0">Late</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h4>${data.attendance_rate.toFixed(1)}%</h4>
                        <p class="mb-0">Attendance Rate</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <h6>Department Breakdown</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Department</th>
                                <th>Total</th>
                                <th>Present</th>
                                <th>Rate</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.department_breakdown.map(dept => `
                                <tr>
                                    <td>${dept.department}</td>
                                    <td>${dept.total_staff}</td>
                                    <td>${dept.present_count}</td>
                                    <td>${((dept.present_count / dept.total_staff) * 100).toFixed(1)}%</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="col-md-6">
                <h6>Late Arrivals</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Staff</th>
                                <th>Department</th>
                                <th>Time In</th>
                                <th>Late By</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.late_arrivals.map(late => `
                                <tr>
                                    <td>${late.full_name}</td>
                                    <td>${late.department}</td>
                                    <td>${late.time_in}</td>
                                    <td>${late.late_duration_minutes} min</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function createCharts(reportData) {
    // Destroy existing charts
    if (attendanceChart) {
        attendanceChart.destroy();
    }
    if (trendsChart) {
        trendsChart.destroy();
    }
    
    const chartsContainer = document.getElementById('chartsContainer');
    
    if (reportData.report_type === 'daily' && reportData.department_breakdown) {
        chartsContainer.style.display = 'block';
        
        // Department breakdown pie chart
        const ctx1 = document.getElementById('attendanceChart').getContext('2d');
        attendanceChart = new Chart(ctx1, {
            type: 'pie',
            data: {
                labels: reportData.department_breakdown.map(dept => dept.department),
                datasets: [{
                    data: reportData.department_breakdown.map(dept => dept.present_count),
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
                        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Department-wise Present Staff'
                    }
                }
            }
        });
    }
}

function resetFilters() {
    currentReportType = null;
    document.getElementById('reportFilters').style.display = 'none';
    document.getElementById('reportContent').style.display = 'none';
    document.getElementById('exportOptions').style.display = 'none';
    document.getElementById('selectedReportType').value = '';
}

function exportToExcel() {
    if (!currentReportData) {
        showAlert('No report data to export', 'warning');
        return;
    }
    
    // Show loading state
    const btn = document.getElementById('exportExcelBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating Excel...';
    
    const params = new URLSearchParams();
    params.append('report_type', currentReportData.report_type);
    
    // Add date parameters based on report type
    if (currentReportData.report_type === 'daily' && currentReportData.date) {
        params.append('date', currentReportData.date);
    } else if (['weekly', 'custom', 'trends'].includes(currentReportData.report_type)) {
        if (currentReportData.start_date) params.append('start_date', currentReportData.start_date);
        if (currentReportData.end_date) params.append('end_date', currentReportData.end_date);
    } else if (currentReportData.report_type === 'monthly') {
        if (currentReportData.year) params.append('year', currentReportData.year);
        if (currentReportData.month) params.append('month', currentReportData.month);
    } else if (currentReportData.report_type === 'yearly') {
        if (currentReportData.year) params.append('year', currentReportData.year);
    }
    
    // Add department filter if exists
    if (currentReportData.department) {
        params.append('department', currentReportData.department);
    }
    
    try {
        // Use window.location.href for better file download handling
        window.location.href = `/export_report_excel?${params}`;
        
        // Reset button after a delay
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            showAlert('<i class="bi bi-check-circle me-2"></i>Excel report exported successfully!', 'success');
        }, 2000);
        
    } catch (error) {
        btn.disabled = false;
        btn.innerHTML = originalText;
        showAlert('Error exporting report: ' + error.message, 'danger');
    }
}

function exportToPdf() {
    if (!currentReportData) {
        showAlert('No report data to export', 'warning');
        return;
    }
    
    window.print();
}

function printReport() {
    window.print();
}

function shareReport() {
    if (navigator.share) {
        navigator.share({
            title: 'Attendance Report',
            text: 'Check out this attendance report',
            url: window.location.href
        });
    } else {
        // Fallback: copy URL to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            showAlert('Report URL copied to clipboard', 'success');
        });
    }
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}
