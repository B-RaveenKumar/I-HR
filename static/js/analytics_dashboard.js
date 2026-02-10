// Analytics Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the analytics dashboard
    initializeAnalyticsDashboard();
});

let charts = {};
let currentData = {};

function initializeAnalyticsDashboard() {
    // Initialize event listeners
    initializeEventListeners();
    
    // Set default dates
    setDefaultDates();
    
    // Load initial data
    loadAnalyticsData();
    
    // Load departments
    loadDepartments();
    
    // Set current month/year for heatmap
    const now = new Date();
    document.getElementById('heatmapMonth').value = now.getMonth() + 1;
    document.getElementById('heatmapYear').value = now.getFullYear();
}

function initializeEventListeners() {
    // Update analytics button
    document.getElementById('updateAnalyticsBtn').addEventListener('click', loadAnalyticsData);
    
    // Heatmap controls
    document.getElementById('heatmapMonth').addEventListener('change', loadHeatmapData);
    document.getElementById('heatmapYear').addEventListener('change', loadHeatmapData);
    
    // Export buttons
    document.getElementById('exportChartsBtn').addEventListener('click', exportCharts);
    document.getElementById('exportDataBtn').addEventListener('click', exportData);
    document.getElementById('generateReportBtn').addEventListener('click', generateReport);
    document.getElementById('scheduleReportBtn').addEventListener('click', scheduleReport);
}

function setDefaultDates() {
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
    
    document.getElementById('startDate').value = thirtyDaysAgo.toISOString().split('T')[0];
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
}

function loadDepartments() {
    fetch('/get_departments')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const departmentSelect = document.getElementById('departmentFilter');
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

function loadAnalyticsData() {
    showLoadingOverlay(true);
    
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const department = document.getElementById('departmentFilter').value;
    
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate
    });
    
    if (department) {
        params.append('department', department);
    }
    
    // Load all analytics data
    Promise.all([
        fetch(`/get_analytics_data?${params}`).then(r => r.json()),
        fetch(`/get_performance_metrics?${params}`).then(r => r.json())
    ])
    .then(([analyticsData, metricsData]) => {
        if (analyticsData.success && metricsData.success) {
            currentData = {
                analytics: analyticsData.data,
                metrics: metricsData.data
            };
            
            updateKPICards(metricsData.data.kpis);
            createAllCharts(analyticsData.data);
            updateTopPerformers(metricsData.data.top_performers);
            loadHeatmapData();
        } else {
            showAlert('Error loading analytics data', 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading analytics:', error);
        showAlert('Error loading analytics data', 'danger');
    })
    .finally(() => {
        showLoadingOverlay(false);
    });
}

function updateKPICards(kpis) {
    document.getElementById('attendanceRate').textContent = kpis.attendance_rate + '%';
    document.getElementById('punctualityRate').textContent = kpis.punctuality_rate + '%';
    document.getElementById('avgWorkHours').textContent = kpis.avg_work_hours + 'h';
    document.getElementById('totalOvertime').textContent = kpis.total_overtime + 'h';
}

function createAllCharts(data) {
    // Destroy existing charts
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    charts = {};
    
    // Create attendance pie chart
    if (data.attendance_pie) {
        createPieChart('attendancePieChart', data.attendance_pie);
    }
    
    // Create daily trends chart
    if (data.daily_trends) {
        createLineChart('dailyTrendsChart', data.daily_trends);
    }
    
    // Create department comparison chart
    if (data.department_comparison) {
        createBarChart('departmentChart', data.department_comparison);
    }
    
    // Create weekly pattern chart
    if (data.weekly_pattern) {
        createRadarChart('weeklyPatternChart', data.weekly_pattern);
    }
    
    // Create overtime chart
    if (data.overtime_analysis) {
        createOvertimeChart('overtimeChart', data.overtime_analysis);
    }
}

function createPieChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    charts[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: chartData.labels,
            datasets: [{
                data: chartData.data,
                backgroundColor: chartData.backgroundColor,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: chartData.title
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function createLineChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    charts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: chartData.title
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

function createBarChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: chartData.title
                }
            },
            scales: chartData.options?.scales || {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createRadarChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    charts[canvasId] = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: chartData.title
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function createOvertimeChart(canvasId, chartData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: chartData.title
                }
            },
            scales: chartData.options?.scales || {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function loadHeatmapData() {
    const month = document.getElementById('heatmapMonth').value;
    const year = document.getElementById('heatmapYear').value;
    
    fetch(`/get_heatmap_data?year=${year}&month=${month}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                createHeatmap(data.data);
            }
        })
        .catch(error => {
            console.error('Error loading heatmap data:', error);
        });
}

function createHeatmap(heatmapData) {
    const container = document.getElementById('attendanceHeatmap');
    container.innerHTML = '';
    
    // Create calendar grid
    const calendar = document.createElement('div');
    calendar.style.display = 'grid';
    calendar.style.gridTemplateColumns = 'repeat(7, 1fr)';
    calendar.style.gap = '2px';
    calendar.style.maxWidth = '350px';
    
    // Add day headers
    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(day => {
        const header = document.createElement('div');
        header.textContent = day;
        header.style.textAlign = 'center';
        header.style.fontWeight = 'bold';
        header.style.padding = '5px';
        calendar.appendChild(header);
    });
    
    // Get first day of month and add empty cells
    const firstDay = new Date(heatmapData.year, heatmapData.month - 1, 1).getDay();
    for (let i = 0; i < firstDay; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.style.height = '30px';
        calendar.appendChild(emptyCell);
    }
    
    // Add data cells
    heatmapData.data.forEach(dayData => {
        const cell = document.createElement('div');
        cell.className = 'heatmap-cell';
        cell.textContent = dayData.day;
        cell.title = `${dayData.date}: ${dayData.attendance_rate}% attendance`;
        
        // Color based on attendance rate
        if (dayData.is_weekend) {
            cell.style.backgroundColor = 'white';
        } else if (dayData.attendance_rate >= 90) {
            cell.style.backgroundColor = '#28a745';
        } else if (dayData.attendance_rate >= 70) {
            cell.style.backgroundColor = '#ffc107';
            cell.style.color = '#000';
        } else if (dayData.attendance_rate > 0) {
            cell.style.backgroundColor = '#dc3545';
        } else {
            cell.style.backgroundColor = 'white';
        }
        
        calendar.appendChild(cell);
    });
    
    container.appendChild(calendar);
}

function updateTopPerformers(performers) {
    const container = document.getElementById('topPerformers');
    container.innerHTML = '';
    
    if (performers.length === 0) {
        container.innerHTML = '<p class="text-muted">No data available</p>';
        return;
    }
    
    performers.forEach((performer, index) => {
        const performerDiv = document.createElement('div');
        performerDiv.className = 'd-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded';
        performerDiv.innerHTML = `
            <div>
                <strong>${performer.full_name}</strong>
                <br>
                <small class="text-muted">${performer.department || 'N/A'}</small>
            </div>
            <span class="badge bg-success performance-badge">${performer.attendance_rate}%</span>
        `;
        container.appendChild(performerDiv);
    });
}

function showLoadingOverlay(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.style.display = 'flex';
    } else {
        overlay.style.display = 'none';
    }
}

function exportCharts() {
    // Create a new window with all charts
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Analytics Charts Export</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .chart-container { margin: 20px 0; page-break-inside: avoid; }
                    .chart-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
                </style>
            </head>
            <body>
                <h1>Attendance Analytics Charts</h1>
                <p>Generated on: ${new Date().toLocaleString()}</p>
    `);
    
    // Add each chart as image
    Object.keys(charts).forEach(chartId => {
        if (charts[chartId]) {
            const canvas = charts[chartId].canvas;
            const imgData = canvas.toDataURL('image/png');
            printWindow.document.write(`
                <div class="chart-container">
                    <div class="chart-title">${charts[chartId].options.plugins.title.text}</div>
                    <img src="${imgData}" style="max-width: 100%; height: auto;">
                </div>
            `);
        }
    });
    
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

function exportData() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const department = document.getElementById('departmentFilter').value;
    
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        export_type: 'analytics'
    });
    
    if (department) {
        params.append('department', department);
    }
    
    window.open(`/export_analytics_data?${params}`, '_blank');
}

function generateReport() {
    showAlert('Generating comprehensive analytics report...', 'info');
    // This would integrate with the reporting system
}

function scheduleReport() {
    showAlert('Report scheduling feature coming soon!', 'info');
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
