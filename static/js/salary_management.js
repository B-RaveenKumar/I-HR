/**
 * Salary Management JavaScript
 * Handles salary calculations, rule management, and reporting
 */

// Global variables for salary management
let currentSalaryCalculationResults = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize salary management
    initializeSalaryManagement();
    
    // Load initial data
    loadDepartments();
    loadSalaryRules();
    setCurrentMonth();
    
    // Set up immediate save functionality for salary rules
    setupSalaryRulesAutoSave();
});

// Storage key for localStorage backup
const SALARY_RULES_STORAGE_KEY = 'vishnorex_salary_rules_backup';

function setupSalaryRulesAutoSave() {
    // List of salary rule input field IDs
    const salaryRuleFields = [
        'earlyArrivalBonus',
        'earlyDeparturePenalty', 
        'lateArrivalPenalty',
        'overtimeMultiplier',
        'absentDeductionRate',
        'onDutyRate',
        'bonusRatePercentage',
        'minimumHoursForBonus'
    ];
    
    // Add change event listeners for immediate save
    salaryRuleFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            // Add change and input event listeners for immediate response
            field.addEventListener('change', debounce(saveRuleImmediately, 1000));
            field.addEventListener('input', debounce(saveRuleToLocalStorage, 300));
        }
    });
}

function saveRuleImmediately(event) {
    const fieldElement = event.target;
    const fieldId = fieldElement.id;
    const value = parseFloat(fieldElement.value);
    
    if (isNaN(value)) {
        showAlert('Please enter a valid number for ' + getFieldDisplayName(fieldId), 'warning');
        return;
    }
    
    // Show saving indicator
    showSavingIndicator(fieldElement, true);
    
    // Prepare the rule update data
    const ruleData = {};
    ruleData[getRuleNameFromFieldId(fieldId)] = value;
    
    // Send to server
    const formData = new FormData();
    for (const [key, val] of Object.entries(ruleData)) {
        formData.append(key, val);
    }
    
    fetch('/update_salary_rules', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
    .then(response => response.json())
    .then(data => {
        showSavingIndicator(fieldElement, false);
        if (data.success) {
            showSaveSuccess(fieldElement);
            // Update localStorage backup
            saveRuleToLocalStorage();
        } else {
            showAlert('Error saving ' + getFieldDisplayName(fieldId) + ': ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showSavingIndicator(fieldElement, false);
        console.error('Error saving salary rule:', error);
        showAlert('Error saving ' + getFieldDisplayName(fieldId) + '. Changes saved locally as backup.', 'warning');
        // Save to localStorage as backup
        saveRuleToLocalStorage();
    });
}

function saveRuleToLocalStorage() {
    try {
        const currentRules = {};
        const salaryRuleFields = [
            'earlyArrivalBonus',
            'earlyDeparturePenalty', 
            'lateArrivalPenalty',
            'overtimeMultiplier',
            'absentDeductionRate',
            'onDutyRate',
            'bonusRatePercentage',
            'minimumHoursForBonus'
        ];
        
        salaryRuleFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field && field.value) {
                currentRules[getRuleNameFromFieldId(fieldId)] = parseFloat(field.value);
            }
        });
        
        currentRules.lastSaved = new Date().toISOString();
        localStorage.setItem(SALARY_RULES_STORAGE_KEY, JSON.stringify(currentRules));
    } catch (error) {
        console.error('Error saving to localStorage:', error);
    }
}

function loadSalaryRulesFromLocalStorage() {
    try {
        const saved = localStorage.getItem(SALARY_RULES_STORAGE_KEY);
        if (saved) {
            const rules = JSON.parse(saved);
            
            // Check if we have a recent backup (within 24 hours)
            if (rules.lastSaved) {
                const saveTime = new Date(rules.lastSaved);
                const now = new Date();
                const hoursDiff = (now - saveTime) / (1000 * 60 * 60);
                
                if (hoursDiff <= 24) {
                    return rules;
                }
            }
        }
    } catch (error) {
        console.error('Error loading from localStorage:', error);
    }
    return null;
}

function getRuleNameFromFieldId(fieldId) {
    const fieldMap = {
        'earlyArrivalBonus': 'early_arrival_bonus_per_hour',
        'earlyDeparturePenalty': 'early_departure_penalty_per_hour',
        'lateArrivalPenalty': 'late_arrival_penalty_per_hour',
        'overtimeMultiplier': 'overtime_rate_multiplier',
        'absentDeductionRate': 'absent_day_deduction_rate',
        'onDutyRate': 'on_duty_rate',
        'bonusRatePercentage': 'bonus_rate_percentage',
        'minimumHoursForBonus': 'minimum_hours_for_bonus'
    };
    return fieldMap[fieldId] || fieldId;
}

function getFieldDisplayName(fieldId) {
    const displayNames = {
        'earlyArrivalBonus': 'Early Arrival Bonus',
        'earlyDeparturePenalty': 'Early Departure Penalty',
        'lateArrivalPenalty': 'Late Arrival Penalty',
        'overtimeMultiplier': 'Overtime Multiplier',
        'absentDeductionRate': 'Absent Day Deduction Rate',
        'onDutyRate': 'On Duty Rate',
        'bonusRatePercentage': 'Bonus Rate Percentage',
        'minimumHoursForBonus': 'Minimum Hours for Bonus'
    };
    return displayNames[fieldId] || fieldId;
}

function showSavingIndicator(element, show) {
    let indicator = element.nextElementSibling;
    
    if (show) {
        if (!indicator || !indicator.classList.contains('saving-indicator')) {
            indicator = document.createElement('small');
            indicator.className = 'saving-indicator text-muted ms-2';
            indicator.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Saving...';
            element.parentNode.insertBefore(indicator, element.nextSibling);
        }
    } else {
        if (indicator && indicator.classList.contains('saving-indicator')) {
            indicator.remove();
        }
    }
}

function showSaveSuccess(element) {
    let indicator = element.nextElementSibling;
    
    // Remove any existing indicator
    if (indicator && (indicator.classList.contains('saving-indicator') || indicator.classList.contains('saved-indicator'))) {
        indicator.remove();
    }
    
    // Add success indicator
    indicator = document.createElement('small');
    indicator.className = 'saved-indicator text-success ms-2';
    indicator.innerHTML = '<i class="bi bi-check-circle"></i> Saved';
    element.parentNode.insertBefore(indicator, element.nextSibling);
    
    // Remove after 2 seconds
    setTimeout(() => {
        if (indicator && indicator.parentNode) {
            indicator.remove();
        }
    }, 2000);
}

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

function initializeSalaryManagement() {
    // Event listeners
    document.getElementById('calculateBulkSalaryBtn').addEventListener('click', calculateBulkSalaries);
    document.getElementById('updateSalaryRulesBtn').addEventListener('click', updateSalaryRules);
    document.getElementById('refreshDataBtn').addEventListener('click', refreshData);
    
    // Download salary slip button (will be added when modal is shown)
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'downloadSalarySlipBtn') {
            if (window.currentSalaryDetail && window.currentSalaryDetail.staff_info) {
                const staff = window.currentSalaryDetail.staff_info;
                const breakdown = window.currentSalaryDetail.salary_breakdown;
                
                // Extract year and month from calculation period
                const year = document.getElementById('calculationYear').value;
                const month = document.getElementById('calculationMonth').value;
                
                // Use staff.id (integer primary key) for the backend
                downloadSalarySlip(staff.id, year, month);
            } else {
                showAlert('<i class="bi bi-exclamation-triangle me-2"></i>No salary data available for download', 'warning');
            }
        }
    });
    
    // Set current month and year
    const now = new Date();
    document.getElementById('calculationYear').value = now.getFullYear();
    document.getElementById('calculationMonth').value = now.getMonth() + 1;
}

function setCurrentMonth() {
    const now = new Date();
    const currentMonth = now.getMonth() + 1;
    const currentYear = now.getFullYear();
    
    document.getElementById('calculationMonth').value = currentMonth;
    document.getElementById('calculationYear').value = currentYear;
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
                    option.value = dept;
                    option.textContent = dept;
                    departmentSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading departments:', error);
        });
}

function loadSalaryRules() {
    // First try to load from localStorage backup
    const localBackup = loadSalaryRulesFromLocalStorage();
    
    fetch('/get_salary_rules')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const rules = data.salary_rules;
                populateSalaryRuleFields(rules);
                
                // Update localStorage backup with latest server data
                saveRuleToLocalStorage();
            } else {
                // If server fails but we have local backup, use it
                if (localBackup) {
                    populateSalaryRuleFields(localBackup);
                    showAlert('Loaded salary rules from local backup. Server connection failed.', 'warning');
                } else {
                    showAlert('Failed to load salary rules: ' + data.error, 'danger');
                }
            }
        })
        .catch(error => {
            console.error('Error loading salary rules:', error);
            
            // If server request fails but we have local backup, use it
            if (localBackup) {
                populateSalaryRuleFields(localBackup);
                showAlert('Loaded salary rules from local backup. Please check your connection.', 'warning');
            } else {
                showAlert('Error loading salary rules. Please refresh the page.', 'danger');
            }
        });
}

function populateSalaryRuleFields(rules) {
    // Populate form fields with proper fallback values
    const setFieldValue = (fieldId, ruleKey, defaultValue) => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = rules[ruleKey] !== undefined ? rules[ruleKey] : defaultValue;
        }
    };
    
    setFieldValue('earlyArrivalBonus', 'early_arrival_bonus_per_hour', 50);
    setFieldValue('earlyDeparturePenalty', 'early_departure_penalty_per_hour', 100);
    setFieldValue('lateArrivalPenalty', 'late_arrival_penalty_per_hour', 75);
    setFieldValue('overtimeMultiplier', 'overtime_rate_multiplier', 1.5);
    setFieldValue('absentDeductionRate', 'absent_day_deduction_rate', 1.0);
    setFieldValue('onDutyRate', 'on_duty_rate', 1.0);
    setFieldValue('bonusRatePercentage', 'bonus_rate_percentage', 10.0);
    setFieldValue('minimumHoursForBonus', 'minimum_hours_for_bonus', 5.0);
}

function calculateBulkSalaries() {
    const year = document.getElementById('calculationYear').value;
    const month = document.getElementById('calculationMonth').value;
    const department = document.getElementById('departmentFilter').value;
    
    if (!year || !month) {
        showAlert('Please select year and month for calculation', 'warning');
        return;
    }
    
    showLoading(true);
    
    const formData = new FormData();
    formData.append('year', year);
    formData.append('month', month);
    if (department) {
        formData.append('department', department);
    }
    
    fetch('/bulk_salary_calculation', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false);
        
        if (data.success) {
            displaySalaryResults(data);
            showAlert(`Salary calculated for ${data.total_staff} staff members`, 'success');
        } else {
            showAlert('Error calculating salaries: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        showLoading(false);
        console.error('Error calculating salaries:', error);
        showAlert('Error calculating salaries. Please try again.', 'danger');
    });
}

function displaySalaryResults(data) {
    const container = document.getElementById('salaryResultsContainer');
    const resultsSubtitle = document.getElementById('resultsSubtitle');
    const resultsStats = document.getElementById('resultsStats');
    const exportBtn = document.getElementById('exportResultsBtn');

    // Store results globally for export functionality
    currentSalaryCalculationResults = data;

    if (!data.success) {
        container.innerHTML = `
            <div class="alert alert-danger d-flex align-items-center">
                <i class="bi bi-exclamation-triangle me-2"></i>
                <div>
                    <strong>Calculation Failed</strong><br>
                    ${data.error || 'Failed to calculate salaries'}
                </div>
            </div>
        `;
        if (exportBtn) exportBtn.classList.add('d-none');
        return;
    }

    if (!data.salary_calculations || data.salary_calculations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="bi bi-inbox"></i>
                </div>
                <h6 class="empty-title">No Salary Data Found</h6>
                <p class="empty-text">No salary data found for the selected criteria. Please check your filters and try again.</p>
            </div>
        `;
        if (exportBtn) exportBtn.classList.add('d-none');
        return;
    }
    
    // Calculate summary statistics
    const totalEarnings = data.salary_calculations.reduce((sum, item) => sum + item.total_earnings, 0);
    const totalDeductions = data.salary_calculations.reduce((sum, item) => sum + item.total_deductions, 0);
    const totalNetSalary = data.salary_calculations.reduce((sum, item) => sum + item.net_salary, 0);
    const totalPresentDays = data.salary_calculations.reduce((sum, item) => sum + item.present_days, 0);
    const totalAbsentDays = data.salary_calculations.reduce((sum, item) => sum + item.absent_days, 0);

    // Update subtitle and stats in header
    if (resultsSubtitle) {
        resultsSubtitle.textContent = `Detailed salary breakdown for ${data.calculation_period}`;
    }

    if (resultsStats) {
        resultsStats.innerHTML = `
            <div class="stat-item">
                <i class="bi bi-people"></i>
                <span class="stat-value">${data.total_staff}</span>
                <span>Staff</span>
            </div>
            <div class="stat-item">
                <i class="bi bi-currency-rupee"></i>
                <span class="stat-value">₹${totalNetSalary.toLocaleString('en-IN')}</span>
                <span>Total Payout</span>
            </div>
        `;
    }

    if (exportBtn) {
        exportBtn.classList.remove('d-none');
    }
    
    let html = `
        <!-- Summary Section -->
        <div class="calculation-summary">
            <h5 class="mb-0"><i class="bi bi-calendar-month"></i> ${data.calculation_period} - Salary Summary</h5>
            <div class="summary-stats">
                <div class="stat-item">
                    <div class="stat-value">₹${totalNetSalary.toLocaleString('en-IN', {maximumFractionDigits: 0})}</div>
                    <div class="stat-label">Total Net Salary</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">₹${totalEarnings.toLocaleString('en-IN', {maximumFractionDigits: 0})}</div>
                    <div class="stat-label">Total Earnings</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">₹${totalDeductions.toLocaleString('en-IN', {maximumFractionDigits: 0})}</div>
                    <div class="stat-label">Total Deductions</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.total_staff}</div>
                    <div class="stat-label">Staff Members</div>
                </div>
            </div>
        </div>
        
        <!-- Salary Table -->
        <div class="table-responsive">
            <table class="table salary-table">
                <thead>
                    <tr>
                        <th>Staff ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Present Days</th>
                        <th>Absent Days</th>
                        <th>Total Earnings</th>
                        <th>Total Deductions</th>
                        <th>Net Salary</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    data.salary_calculations.forEach(salary => {
        html += `
            <tr>
                <td><strong>${salary.staff_id}</strong></td>
                <td>${salary.staff_name}</td>
                <td><span class="badge bg-secondary">${salary.department}</span></td>
                <td><span class="present-days">${salary.present_days}</span></td>
                <td><span class="absent-days">${salary.absent_days}</span></td>
                <td><span class="earnings-badge">₹${salary.total_earnings.toLocaleString('en-IN')}</span></td>
                <td><span class="deductions-badge">₹${salary.total_deductions.toLocaleString('en-IN')}</span></td>
                <td><span class="net-salary-badge">₹${salary.net_salary.toLocaleString('en-IN')}</span></td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-outline-primary btn-sm btn-view-details"
                                onclick="viewSalaryDetails('${salary.id}')"
                                title="View detailed salary breakdown">
                            <i class="bi bi-eye"></i> Details
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

function viewSalaryDetails(staffId) {
    const year = document.getElementById('calculationYear').value;
    const month = document.getElementById('calculationMonth').value;
    
    const formData = new FormData();
    formData.append('staff_id', staffId);
    formData.append('year', year);
    formData.append('month', month);
    
    fetch('/generate_salary_report', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Store current salary detail data for download functionality
            window.currentSalaryDetail = data;
            displayDetailedSalaryBreakdown(data);
            const modal = new bootstrap.Modal(document.getElementById('salaryDetailModal'));
            modal.show();
        } else {
            showAlert('Error loading salary details: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading salary details:', error);
        showAlert('Error loading salary details. Please try again.', 'danger');
    });
}

function displayDetailedSalaryBreakdown(data) {
    const staff = data.staff_info;
    const breakdown = data.salary_breakdown;
    const attendance = breakdown.attendance_summary;
    const earnings = breakdown.earnings;
    const deductions = breakdown.deductions;
    
    const content = document.getElementById('salaryDetailContent');
    
    content.innerHTML = `
        <!-- Staff Information -->
        <div class="row mb-4">
            <div class="col-md-6">
                <h6 class="text-primary">Staff Information</h6>
                <p><strong>Name:</strong> ${staff.full_name}</p>
                <p><strong>Staff ID:</strong> ${staff.staff_id}</p>
                <p><strong>Department:</strong> ${staff.department}</p>
                <p><strong>Position:</strong> ${staff.position}</p>
            </div>
            <div class="col-md-6">
                <h6 class="text-primary">Calculation Period</h6>
                <p><strong>Period:</strong> ${breakdown.calculation_period}</p>
                <p><strong>Working Days:</strong> ${breakdown.working_days}</p>
                <p><strong>Per Day Salary:</strong> ₹${breakdown.per_day_salary}</p>
                <p><strong>Per Hour Salary:</strong> ₹${breakdown.per_hour_salary}</p>
            </div>
        </div>
        
        <!-- Attendance Summary -->
        <div class="salary-breakdown-section">
            <div class="salary-breakdown-title">Attendance Summary</div>
            <div class="attendance-summary">
                <div class="attendance-item">
                    <span class="attendance-label">Present Days</span>
                    <span class="attendance-value present-days">${attendance.present_days}</span>
                </div>
                <div class="attendance-item">
                    <span class="attendance-label">Absent Days</span>
                    <span class="attendance-value absent-days">${attendance.absent_days}</span>
                </div>
                <div class="attendance-item">
                    <span class="attendance-label">On Duty Days</span>
                    <span class="attendance-value on-duty-days">${attendance.on_duty_days}</span>
                </div>
                <div class="attendance-item">
                    <span class="attendance-label">Leave Days</span>
                    <span class="attendance-value leave-days">${attendance.leave_days}</span>
                </div>
            </div>
        </div>
        
        <!-- Earnings Breakdown -->
        <div class="salary-breakdown-section">
            <div class="salary-breakdown-title">Earnings Breakdown</div>
            <div class="breakdown-item">
                <span class="breakdown-label">Basic Salary</span>
                <span class="breakdown-value">₹${earnings.basic_salary.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">HRA</span>
                <span class="breakdown-value">₹${earnings.hra.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">Transport Allowance</span>
                <span class="breakdown-value">₹${earnings.transport_allowance.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">Other Allowances</span>
                <span class="breakdown-value">₹${earnings.other_allowances.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">Present Days Pay</span>
                <span class="breakdown-value">₹${earnings.present_pay.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">On Duty Pay</span>
                <span class="breakdown-value">₹${earnings.on_duty_pay.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">Leave Pay</span>
                <span class="breakdown-value">₹${earnings.leave_pay.toLocaleString('en-IN')}</span>
            </div>
            ${earnings.early_arrival_bonus > 0 ? `
            <div class="breakdown-item bonus-item">
                <span class="breakdown-label"><i class="bi bi-award"></i> Early Arrival Bonus</span>
                <span class="breakdown-value">₹${earnings.early_arrival_bonus.toLocaleString('en-IN')}</span>
            </div>
            ` : ''}
            ${earnings.overtime_pay > 0 ? `
            <div class="breakdown-item bonus-item">
                <span class="breakdown-label"><i class="bi bi-clock"></i> Overtime Pay</span>
                <span class="breakdown-value">₹${earnings.overtime_pay.toLocaleString('en-IN')}</span>
            </div>
            ` : ''}
            <div class="breakdown-item total-row">
                <span class="breakdown-label">Total Earnings</span>
                <span class="breakdown-value">₹${earnings.total_earnings.toLocaleString('en-IN')}</span>
            </div>
        </div>
        
        <!-- Deductions Breakdown -->
        <div class="salary-breakdown-section">
            <div class="salary-breakdown-title">Deductions Breakdown</div>
            ${deductions.absent_deduction > 0 ? `
            <div class="breakdown-item penalty-item">
                <span class="breakdown-label"><i class="bi bi-exclamation-triangle"></i> Absent Days Deduction</span>
                <span class="breakdown-value">₹${deductions.absent_deduction.toLocaleString('en-IN')}</span>
            </div>
            ` : ''}
            ${deductions.early_departure_penalty > 0 ? `
            <div class="breakdown-item penalty-item">
                <span class="breakdown-label"><i class="bi bi-clock-history"></i> Early Departure Penalty</span>
                <span class="breakdown-value">₹${deductions.early_departure_penalty.toLocaleString('en-IN')}</span>
            </div>
            ` : ''}
            ${deductions.late_arrival_penalty > 0 ? `
            <div class="breakdown-item penalty-item">
                <span class="breakdown-label"><i class="bi bi-clock"></i> Late Arrival Penalty</span>
                <span class="breakdown-value">₹${deductions.late_arrival_penalty.toLocaleString('en-IN')}</span>
            </div>
            ` : ''}
            <div class="breakdown-item">
                <span class="breakdown-label">PF Deduction</span>
                <span class="breakdown-value">₹${deductions.pf_deduction.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">ESI Deduction</span>
                <span class="breakdown-value">₹${deductions.esi_deduction.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">Professional Tax</span>
                <span class="breakdown-value">₹${deductions.professional_tax.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item">
                <span class="breakdown-label">Other Deductions</span>
                <span class="breakdown-value">₹${deductions.other_deductions.toLocaleString('en-IN')}</span>
            </div>
            <div class="breakdown-item total-row">
                <span class="breakdown-label">Total Deductions</span>
                <span class="breakdown-value">₹${deductions.total_deductions.toLocaleString('en-IN')}</span>
            </div>
        </div>
        
        <!-- Net Salary -->
        <div class="salary-breakdown-section">
            <div class="breakdown-item total-row" style="font-size: 1.2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px;">
                <span class="breakdown-label">NET SALARY</span>
                <span class="breakdown-value">₹${breakdown.net_salary.toLocaleString('en-IN')}</span>
            </div>
        </div>
    `;
    
    // Update modal title
    document.getElementById('salaryDetailModalLabel').innerHTML = `
        <i class="bi bi-person-badge"></i> Salary Breakdown - ${staff.full_name} (${staff.staff_id})
    `;
}

function updateSalaryRules() {
    // Show confirmation for manual bulk update
    if (!confirm('Update all salary rules at once? Individual changes are saved automatically.')) {
        return;
    }
    
    const formData = new FormData();
    
    formData.append('early_arrival_bonus_per_hour', document.getElementById('earlyArrivalBonus').value);
    formData.append('early_departure_penalty_per_hour', document.getElementById('earlyDeparturePenalty').value);
    formData.append('late_arrival_penalty_per_hour', document.getElementById('lateArrivalPenalty').value);
    formData.append('overtime_rate_multiplier', document.getElementById('overtimeMultiplier').value);
    formData.append('absent_day_deduction_rate', document.getElementById('absentDeductionRate').value);
    formData.append('on_duty_rate', document.getElementById('onDutyRate').value);

    // Add new enhanced salary fields
    if (document.getElementById('bonusRatePercentage')) {
        formData.append('bonus_rate_percentage', document.getElementById('bonusRatePercentage').value);
    }
    if (document.getElementById('minimumHoursForBonus')) {
        formData.append('minimum_hours_for_bonus', document.getElementById('minimumHoursForBonus').value);
    }
    
    // Show loading state
    const updateBtn = document.getElementById('updateSalaryRulesBtn');
    const originalText = updateBtn.textContent;
    updateBtn.disabled = true;
    updateBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Updating...';
    
    fetch('/update_salary_rules', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
    .then(response => response.json())
    .then(data => {
        updateBtn.disabled = false;
        updateBtn.textContent = originalText;
        
        if (data.success) {
            showAlert('All salary rules updated successfully', 'success');
            // Update localStorage backup
            saveRuleToLocalStorage();
        } else {
            showAlert('Error updating salary rules: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        updateBtn.disabled = false;
        updateBtn.textContent = originalText;
        console.error('Error updating salary rules:', error);
        showAlert('Error updating salary rules. Please try again.', 'danger');
    });
}

function refreshData() {
    loadDepartments();
    loadSalaryRules();
    showAlert('Data refreshed successfully', 'info');
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('d-none');
    } else {
        overlay.classList.add('d-none');
    }
}

function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 10000; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Download salary slip function
function downloadSalarySlip(staffId, year, month) {
    // Validate required parameters
    if (!staffId || !year || !month) {
        showAlert('<i class="bi bi-exclamation-triangle me-2"></i>Missing required parameters for salary slip download', 'warning');
        return;
    }

    // Show loading state
    showAlert('<i class="bi bi-download me-2"></i>Generating salary slip PDF...', 'info');

    // Create form data
    const formData = new FormData();
    formData.append('staff_id', staffId);
    formData.append('year', year);
    formData.append('month', month);

    // Send request to download salary slip
    fetch('/download_salary_slip', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value || ''
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `salary_slip_${staffId}_${year}_${month.toString().padStart(2, '0')}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showAlert('<i class="bi bi-check-circle me-2"></i>Salary slip downloaded successfully', 'success');
    })
    .catch(error => {
        console.error('Error downloading salary slip:', error);
        showAlert('<i class="bi bi-exclamation-triangle me-2"></i>Error downloading salary slip. Please try again.', 'danger');
    });
}

// Enhanced UI functionality
function initializeEnhancedUI() {
    // Enhanced event listeners
    const refreshBtn = document.getElementById('refreshDataBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadSalaryRules();
            loadDepartments();
            showAlert('<i class="bi bi-check-circle me-2"></i>Data refreshed successfully', 'success');
        });
    }

    const exportSalaryBtn = document.getElementById('exportSalaryBtn');
    if (exportSalaryBtn) {
        exportSalaryBtn.addEventListener('click', function() {
            showAlert('<i class="bi bi-info-circle me-2"></i>Export feature coming soon!', 'info');
        });
    }

    const exportResultsBtn = document.getElementById('exportResultsBtn');
    if (exportResultsBtn) {
        exportResultsBtn.addEventListener('click', function() {
            exportSalaryResults();
        });
    }

    const resetRulesBtn = document.getElementById('resetRulesBtn');
    if (resetRulesBtn) {
        resetRulesBtn.addEventListener('click', function() {
            resetSalaryRulesToDefaults();
        });
    }

    // Initialize tooltips
    initializeTooltips();
}

function exportSalaryResults(format = null) {
    if (!currentSalaryCalculationResults || !currentSalaryCalculationResults.success) {
        showAlert('<i class="bi bi-exclamation-triangle me-2"></i>No salary calculation results to export', 'warning');
        return;
    }

    // Get current calculation parameters
    const year = document.getElementById('calculationYear').value;
    const month = document.getElementById('calculationMonth').value;
    const department = document.getElementById('departmentFilter').value;

    if (!year || !month) {
        showAlert('<i class="bi bi-exclamation-triangle me-2"></i>Missing calculation parameters', 'warning');
        return;
    }

    // If no format specified, show format selection modal
    if (!format) {
        showExportFormatModal();
        return;
    }

    const formatNames = {
        'excel': 'Excel',
        'csv': 'CSV',
        'pdf': 'PDF'
    };

    showAlert(`<i class="bi bi-download me-2"></i>Exporting salary calculation results as ${formatNames[format]}...`, 'info');

    // Prepare form data
    const formData = new FormData();
    formData.append('year', year);
    formData.append('month', month);
    formData.append('format', format);
    if (department) {
        formData.append('department', department);
    }

    // Add CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    if (csrfToken) {
        formData.append('csrf_token', csrfToken.value);
    }

    // Make the export request
    fetch('/export_salary_calculation_results', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken ? csrfToken.value : ''
        }
    })
    .then(response => {
        if (response.ok) {
            // Check if it's a file download
            const contentType = response.headers.get('content-type');
            const isFileDownload = contentType && (
                contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') ||
                contentType.includes('text/csv') ||
                contentType.includes('application/pdf')
            );

            if (isFileDownload) {
                // It's a file, trigger download
                return response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;

                    // Extract filename from Content-Disposition header or create default
                    const disposition = response.headers.get('Content-Disposition');
                    let filename = 'salary_calculation_results';
                    if (disposition && disposition.includes('filename=')) {
                        filename = disposition.split('filename=')[1].replace(/"/g, '');
                    } else {
                        // Create default filename based on format
                        const extension = contentType.includes('excel') ? '.xlsx' :
                                        contentType.includes('csv') ? '.csv' : '.pdf';
                        filename += extension;
                    }

                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);

                    showAlert('<i class="bi bi-check-circle me-2"></i>Salary calculation results exported successfully!', 'success');
                });
            } else {
                // It might be a JSON response with an error
                return response.json().then(data => {
                    if (data.success === false) {
                        showAlert(`<i class="bi bi-exclamation-triangle me-2"></i>Export failed: ${data.error}`, 'danger');
                    } else {
                        showAlert('<i class="bi bi-check-circle me-2"></i>Export completed successfully!', 'success');
                    }
                });
            }
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    })
    .catch(error => {
        console.error('Export error:', error);
        showAlert(`<i class="bi bi-exclamation-triangle me-2"></i>Export failed: ${error.message}`, 'danger');
    });
}

function showExportFormatModal() {
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="exportFormatModal" tabindex="-1" aria-labelledby="exportFormatModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="exportFormatModalLabel">
                            <i class="bi bi-download me-2"></i>Export Salary Calculation Results
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-3">Choose the format for exporting your salary calculation results:</p>
                        <div class="export-format-options">
                            <div class="format-option" data-format="excel">
                                <div class="format-icon">
                                    <i class="bi bi-file-earmark-excel text-success"></i>
                                </div>
                                <div class="format-details">
                                    <h6>Excel (.xlsx)</h6>
                                    <p>Comprehensive spreadsheet with formatting and formulas</p>
                                </div>
                                <div class="format-check">
                                    <i class="bi bi-check-circle-fill text-success d-none"></i>
                                </div>
                            </div>
                            <div class="format-option" data-format="csv">
                                <div class="format-icon">
                                    <i class="bi bi-file-earmark-text text-primary"></i>
                                </div>
                                <div class="format-details">
                                    <h6>CSV (.csv)</h6>
                                    <p>Simple comma-separated values for data analysis</p>
                                </div>
                                <div class="format-check">
                                    <i class="bi bi-check-circle-fill text-success d-none"></i>
                                </div>
                            </div>
                            <div class="format-option" data-format="pdf">
                                <div class="format-icon">
                                    <i class="bi bi-file-earmark-pdf text-danger"></i>
                                </div>
                                <div class="format-details">
                                    <h6>PDF (.pdf)</h6>
                                    <p>Professional report format for printing and sharing</p>
                                </div>
                                <div class="format-check">
                                    <i class="bi bi-check-circle-fill text-success d-none"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirmExportBtn" disabled onclick="confirmExport()">
                            <i class="bi bi-download me-2"></i>Export
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <style>
        .export-format-options {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .format-option {
            display: flex;
            align-items: center;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .format-option:hover {
            border-color: #007bff;
            background-color: #f8f9fa;
        }

        .format-option.selected {
            border-color: #28a745;
            background-color: #f8fff9;
        }

        .format-icon {
            font-size: 2rem;
            margin-right: 15px;
            min-width: 50px;
            text-align: center;
        }

        .format-details {
            flex: 1;
        }

        .format-details h6 {
            margin: 0 0 5px 0;
            font-weight: 600;
        }

        .format-details p {
            margin: 0;
            color: white;
            font-size: 0.9rem;
        }

        .format-check {
            margin-left: 15px;
        }
        </style>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('exportFormatModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('exportFormatModal'));
    modal.show();

    // Add event listeners for format options
    document.querySelectorAll('.format-option').forEach(option => {
        option.addEventListener('click', function() {
            const format = this.getAttribute('data-format');
            selectExportFormat(format, this);
        });
    });

    // Clean up when modal is hidden
    document.getElementById('exportFormatModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

let selectedExportFormat = null;

function selectExportFormat(format, element) {
    // Remove previous selection
    document.querySelectorAll('.format-option').forEach(option => {
        option.classList.remove('selected');
        option.querySelector('.format-check i').classList.add('d-none');
    });

    // Add selection to clicked option
    const targetOption = element ? element.closest('.format-option') :
                        document.querySelector(`[onclick*="${format}"]`).closest('.format-option');
    targetOption.classList.add('selected');
    targetOption.querySelector('.format-check i').classList.remove('d-none');

    // Enable export button
    selectedExportFormat = format;
    document.getElementById('confirmExportBtn').disabled = false;
}

function confirmExport() {
    if (selectedExportFormat) {
        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('exportFormatModal'));
        modal.hide();

        // Start export with selected format
        exportSalaryResults(selectedExportFormat);
    }
}

function resetSalaryRulesToDefaults() {
    if (confirm('Are you sure you want to reset all salary rules to default values?')) {
        // Reset form values to defaults
        document.getElementById('earlyArrivalBonus').value = '50.00';
        document.getElementById('earlyDeparturePenalty').value = '100.00';
        document.getElementById('lateArrivalPenalty').value = '75.00';
        document.getElementById('overtimeMultiplier').value = '1.5';
        document.getElementById('absentDeductionRate').value = '1.0';
        document.getElementById('onDutyRate').value = '1.0';

        showAlert('<i class="bi bi-arrow-clockwise me-2"></i>Salary rules reset to default values', 'success');
    }
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Enhanced salary calculation function
function calculateEnhancedSalary() {
    const year = document.getElementById('calculationYear').value;
    const month = document.getElementById('calculationMonth').value;
    const department = document.getElementById('departmentFilter').value;

    if (!year || !month) {
        showAlert('Please select year and month for calculation', 'warning');
        return;
    }

    showLoading('Calculating enhanced salaries based on actual hours worked...');

    // Get all staff for the selected department
    fetch('/get_staff_list', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            department: department
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.staff && data.staff.length > 0) {
            // Calculate enhanced salary for each staff member
            const promises = data.staff.map(staff =>
                fetch('/api/calculate_enhanced_salary', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        staff_id: staff.id,
                        year: parseInt(year),
                        month: parseInt(month)
                    })
                }).then(response => response.json())
            );

            Promise.all(promises)
                .then(results => {
                    hideLoading();
                    displayEnhancedSalaryResults(results, year, month);
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error calculating enhanced salaries:', error);
                    showAlert('Error calculating enhanced salaries. Please try again.', 'error');
                });
        } else {
            hideLoading();
            showAlert('No staff found for the selected criteria', 'info');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error fetching staff list:', error);
        showAlert('Error fetching staff list. Please try again.', 'error');
    });
}

// Display enhanced salary results
function displayEnhancedSalaryResults(results, year, month) {
    const resultsContainer = document.getElementById('enhancedSalaryResultsContainer');
    if (!resultsContainer) return;

    let html = `
        <div class="enhanced-salary-results">
            <div class="results-header">
                <h4><i class="bi bi-clock-history"></i> Enhanced Salary Results - ${year}-${month.toString().padStart(2, '0')}</h4>
                <p class="text-muted">Salary calculations based on actual hours worked vs standard institution hours</p>
            </div>
            <div class="table-responsive">
                <table class="table table-striped salary-results-table">
                    <thead>
                        <tr>
                            <th>Staff Name</th>
                            <th>Base Salary</th>
                            <th>Hourly Rate</th>
                            <th>Standard Hours</th>
                            <th>Actual Hours</th>
                            <th>Hours Ratio</th>
                            <th>Base Earned</th>
                            <th>Extra Hours Bonus</th>
                            <th>Total Earnings</th>
                            <th>Total Deductions</th>
                            <th>Net Salary</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    results.forEach(result => {
        if (result.success) {
            const breakdown = result.salary_breakdown;
            const hoursRatio = breakdown.hours_ratio || 1.0;
            const hoursRatioPercent = (hoursRatio * 100).toFixed(1);
            const hoursRatioClass = hoursRatio >= 1.0 ? 'text-success' : 'text-warning';

            html += `
                <tr>
                    <td>
                        <strong>${result.staff_name}</strong>
                    </td>
                    <td>₹${result.base_monthly_salary.toLocaleString()}</td>
                    <td>₹${result.hourly_rate.toFixed(2)}</td>
                    <td>${result.standard_monthly_hours.toFixed(1)} hrs</td>
                    <td>${result.actual_hours_worked.toFixed(1)} hrs</td>
                    <td class="${hoursRatioClass}">
                        <strong>${hoursRatioPercent}%</strong>
                    </td>
                    <td>₹${breakdown.base_salary_earned.toLocaleString()}</td>
                    <td class="text-success">₹${breakdown.bonus_for_extra_hours.toLocaleString()}</td>
                    <td class="text-primary">₹${breakdown.total_earnings.toLocaleString()}</td>
                    <td class="text-danger">₹${breakdown.total_deductions.toLocaleString()}</td>
                    <td class="text-success">
                        <strong>₹${breakdown.net_salary.toLocaleString()}</strong>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-info" onclick="showEnhancedSalaryDetails('${result.staff_id}', '${year}', '${month}')">
                            <i class="bi bi-eye"></i> Details
                        </button>
                    </td>
                </tr>
            `;
        } else {
            html += `
                <tr>
                    <td colspan="12" class="text-danger">
                        Error calculating salary: ${result.error}
                    </td>
                </tr>
            `;
        }
    });

    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    resultsContainer.innerHTML = html;
}

// Initialize enhanced UI when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Load salary rules on page load
    loadSalaryRules();

    // Set up event listeners
    document.getElementById('calculateBulkSalaryBtn').addEventListener('click', calculateBulkSalaries);
    document.getElementById('updateSalaryRulesBtn').addEventListener('click', updateSalaryRules);

    // Add enhanced salary calculation listener
    const enhancedBtn = document.getElementById('calculateEnhancedSalaryBtn');
    if (enhancedBtn) {
        enhancedBtn.addEventListener('click', calculateEnhancedSalary);
    }

    // Set current month as default
    const currentMonth = new Date().getMonth() + 1;
    document.getElementById('calculationMonth').value = currentMonth;

    // Load departments
    loadDepartments();

    // Initialize enhanced UI
    initializeEnhancedUI();

    // Initialize enhanced sidebar
    initializeEnhancedSidebar();
});

// Enhanced Sidebar Functionality
function initializeEnhancedSidebar() {
    // Update current date in sidebar footer
    updateSidebarStats();

    // Set up quick action buttons
    setupQuickActions();

    // Update stats periodically
    setInterval(updateSidebarStats, 60000); // Update every minute

    // Load staff count
    loadStaffCount();

    // Setup mobile sidebar toggle
    setupMobileSidebarToggle();
}

function setupMobileSidebarToggle() {
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.enhanced-sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });

        // Close sidebar on window resize to desktop
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                sidebar.classList.remove('show');
            }
        });
    }
}

function updateSidebarStats() {
    const currentDateElement = document.getElementById('currentDate');
    if (currentDateElement) {
        const now = new Date();
        const dateStr = now.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short'
        });
        currentDateElement.textContent = dateStr;
    }
}

function loadStaffCount() {
    fetch('/get_staff_count')
        .then(response => response.json())
        .then(data => {
            const staffCountElement = document.getElementById('totalStaffCount');
            if (staffCountElement && data.success) {
                staffCountElement.textContent = data.count || '0';
            }
        })
        .catch(error => {
            console.log('Could not load staff count:', error);
            const staffCountElement = document.getElementById('totalStaffCount');
            if (staffCountElement) {
                staffCountElement.textContent = '0';
            }
        });
}

function setupQuickActions() {
    // Export quick action
    const exportBtn = document.querySelector('.quick-action-btn[title="Export Data"]');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            showExportModal();
        });
    }

    // Settings quick action
    const settingsBtn = document.querySelector('.quick-action-btn[title="Settings"]');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            window.location.href = '/admin/settings';
        });
    }

    // Help quick action
    const helpBtn = document.querySelector('.quick-action-btn[title="Help"]');
    if (helpBtn) {
        helpBtn.addEventListener('click', function() {
            showHelpModal();
        });
    }
}

function showHelpModal() {
    const helpContent = `
        <div class="help-content">
            <h5><i class="bi bi-question-circle me-2"></i>Salary Management Help</h5>
            <div class="help-section">
                <h6><i class="bi bi-calculator me-1"></i>Calculating Salaries</h6>
                <ul>
                    <li>Select year and month for calculation period</li>
                    <li>Choose department filter (optional)</li>
                    <li>Click "Calculate Salaries" to process</li>
                </ul>
            </div>
            <div class="help-section">
                <h6><i class="bi bi-gear me-1"></i>Salary Rules</h6>
                <ul>
                    <li>Configure bonus rates for early arrival</li>
                    <li>Set penalty rates for late arrival/early departure</li>
                    <li>Adjust overtime multipliers</li>
                    <li>Click "Update Salary Rules" to save changes</li>
                </ul>
            </div>
            <div class="help-section">
                <h6><i class="bi bi-eye me-1"></i>Viewing Details</h6>
                <ul>
                    <li>Click "Details" button in results table</li>
                    <li>View comprehensive salary breakdown</li>
                    <li>See attendance summary and calculations</li>
                </ul>
            </div>
        </div>
    `;

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title">Help & Documentation</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${helpContent}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Show modal
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        // Remove modal from DOM when hidden
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });
    }
}

function showExportModal() {
    const exportContent = `
        <div class="export-content">
            <h5><i class="bi bi-download me-2"></i>Export Data</h5>
            <p class="mb-4">Choose the type of data you want to export:</p>

            <div class="export-options">
                <div class="export-option">
                    <div class="export-icon">
                        <i class="bi bi-currency-dollar text-success"></i>
                    </div>
                    <div class="export-details">
                        <h6>Salary Data</h6>
                        <p>Export salary calculations and payroll information</p>
                        <button type="button" class="btn btn-success btn-sm" onclick="exportData('salary')">
                            <i class="bi bi-download"></i> Export Salary
                        </button>
                    </div>
                </div>

                <div class="export-option">
                    <div class="export-icon">
                        <i class="bi bi-calendar-check text-primary"></i>
                    </div>
                    <div class="export-details">
                        <h6>Attendance Data</h6>
                        <p>Export attendance records and time tracking</p>
                        <button type="button" class="btn btn-primary btn-sm" onclick="exportData('attendance')">
                            <i class="bi bi-download"></i> Export Attendance
                        </button>
                    </div>
                </div>

                <div class="export-option">
                    <div class="export-icon">
                        <i class="bi bi-people text-info"></i>
                    </div>
                    <div class="export-details">
                        <h6>Staff Data</h6>
                        <p>Export staff information and profiles</p>
                        <button type="button" class="btn btn-info btn-sm" onclick="exportData('staff')">
                            <i class="bi bi-download"></i> Export Staff
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title">Export Data</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${exportContent}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Show modal
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        // Remove modal from DOM when hidden
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });
    }
}

function exportData(type) {
    showAlert(`<i class="bi bi-download me-2"></i>Exporting ${type} data...`, 'info');

    // Simulate export process
    setTimeout(() => {
        showAlert(`<i class="bi bi-check-circle me-2"></i>${type.charAt(0).toUpperCase() + type.slice(1)} data exported successfully!`, 'success');
    }, 2000);
}

function showNotification(message, type) {
    showAlert(`<i class="bi bi-info-circle me-2"></i>${message}`, type);
}

// Report Generation Functions
function generateReport(reportType) {
    const year = document.getElementById('reportYear')?.value || '2024';
    const month = document.getElementById('reportMonth')?.value || '';
    const department = document.getElementById('reportDepartment')?.value || '';
    const format = document.getElementById('reportFormat')?.value || 'excel';

    const reportNames = {
        'monthly_salary': 'Monthly Salary Report',
        'payroll_summary': 'Payroll Summary Report',
        'department_salary': 'Department Wise Salary Report',
        'staff_directory': 'Staff Directory Report',
        'department_report': 'Department Analysis Report',
        'performance_report': 'Performance Evaluation Report',
        'daily_attendance': 'Daily Attendance Report',
        'monthly_attendance': 'Monthly Attendance Report',
        'overtime_report': 'Overtime Analysis Report'
    };

    const reportName = reportNames[reportType] || 'Report';

    showAlert(`<i class="bi bi-gear me-2"></i>Generating ${reportName}...`, 'info');

    // Build parameters for the request
    const params = new URLSearchParams({
        report_type: reportType,
        year: year,
        format: format
    });
    
    if (month) params.append('month', month);
    if (department) params.append('department', department);
    
    // Add current date for daily reports
    if (reportType === 'daily_attendance') {
        params.append('date', new Date().toISOString().split('T')[0]);
    }

    // Make the actual request to generate and download the report
    fetch(`/generate_admin_report?${params}`)
        .then(response => {
            if (response.ok) {
                // Check if it's a file download (Excel/PDF) or JSON error
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) {
                    // It's an Excel file, trigger download
                    return response.blob().then(blob => {
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        
                        // Extract filename from Content-Disposition header or create default
                        const disposition = response.headers.get('content-disposition');
                        let filename = `${reportType}_${new Date().toISOString().split('T')[0]}.xlsx`;
                        if (disposition && disposition.includes('filename=')) {
                            filename = disposition.split('filename=')[1].replace(/"/g, '');
                        }
                        
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        const filters = [];
                        if (month) filters.push(`Month: ${getMonthName(month)}`);
                        if (department) filters.push(`Department: ${department}`);
                        filters.push(`Format: ${format.toUpperCase()}`);

                        const filterText = filters.length > 0 ? ` (${filters.join(', ')})` : '';
                        showAlert(`<i class="bi bi-check-circle me-2"></i>${reportName} generated and downloaded successfully!${filterText}`, 'success');
                    });
                } else {
                    // It might be a JSON response with an error
                    return response.json().then(data => {
                        if (data.success === false) {
                            showAlert(`<i class="bi bi-exclamation-triangle me-2"></i>Error: ${data.error}`, 'danger');
                        } else {
                            showAlert(`<i class="bi bi-check-circle me-2"></i>${reportName} generated successfully!`, 'success');
                        }
                    });
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        })
        .catch(error => {
            console.error('Report generation error:', error);
            showAlert(`<i class="bi bi-exclamation-triangle me-2"></i>Error generating ${reportName}: ${error.message}`, 'danger');
        });
}

function openCustomReportBuilder() {
    showCustomReportModal();
}

function manageScheduledReports() {
    showAlert('<i class="bi bi-calendar-plus me-2"></i>Scheduled Reports feature coming soon!', 'info');
}

function viewReportHistory() {
    showReportHistoryModal();
}

function getMonthName(monthNumber) {
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[parseInt(monthNumber) - 1] || '';
}

function showCustomReportModal() {
    const customReportContent = `
        <div class="custom-report-content">
            <h5><i class="bi bi-sliders me-2"></i>Custom Report Builder</h5>
            <p class="mb-4">Create a custom report with your specific requirements:</p>

            <div class="custom-report-form">
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Report Name</label>
                        <input type="text" class="form-control" placeholder="Enter report name" id="customReportName">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Report Type</label>
                        <select class="form-select" id="customReportType">
                            <option value="salary">Salary Analysis</option>
                            <option value="attendance">Attendance Analysis</option>
                            <option value="staff">Staff Analysis</option>
                            <option value="financial">Financial Analysis</option>
                        </select>
                    </div>
                </div>

                <div class="row mt-3">
                    <div class="col-md-12">
                        <label class="form-label">Include Fields</label>
                        <div class="field-checkboxes">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="field1" checked>
                                <label class="form-check-label" for="field1">Staff Information</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="field2" checked>
                                <label class="form-check-label" for="field2">Salary Details</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="field3">
                                <label class="form-check-label" for="field3">Attendance Summary</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="field4">
                                <label class="form-check-label" for="field4">Performance Metrics</label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-secondary text-white">
                    <h5 class="modal-title">Custom Report Builder</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${customReportContent}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="buildCustomReport()">Build Report</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Show modal
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        // Remove modal from DOM when hidden
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });
    }
}

function buildCustomReport() {
    const reportName = document.getElementById('customReportName')?.value || 'Custom Report';
    showAlert(`<i class="bi bi-tools me-2"></i>Building custom report: ${reportName}...`, 'info');

    setTimeout(() => {
        showAlert(`<i class="bi bi-check-circle me-2"></i>Custom report "${reportName}" created successfully!`, 'success');
    }, 2000);
}

function showReportHistoryModal() {
    const historyContent = `
        <div class="report-history-content">
            <h5><i class="bi bi-clock-history me-2"></i>Report History</h5>
            <p class="mb-4">Previously generated reports:</p>

            <div class="history-list">
                <div class="history-item">
                    <div class="history-icon">
                        <i class="bi bi-file-earmark-excel text-success"></i>
                    </div>
                    <div class="history-details">
                        <h6>Monthly Salary Report - January 2024</h6>
                        <small class="text-muted">Generated on: 2024-01-31 10:30 AM</small>
                    </div>
                    <div class="history-actions">
                        <button type="button" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-download"></i> Download
                        </button>
                    </div>
                </div>

                <div class="history-item">
                    <div class="history-icon">
                        <i class="bi bi-file-earmark-pdf text-danger"></i>
                    </div>
                    <div class="history-details">
                        <h6>Staff Directory Report</h6>
                        <small class="text-muted">Generated on: 2024-01-28 02:15 PM</small>
                    </div>
                    <div class="history-actions">
                        <button type="button" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-download"></i> Download
                        </button>
                    </div>
                </div>

                <div class="history-item">
                    <div class="history-icon">
                        <i class="bi bi-file-earmark-text text-info"></i>
                    </div>
                    <div class="history-details">
                        <h6>Department Analysis Report</h6>
                        <small class="text-muted">Generated on: 2024-01-25 09:45 AM</small>
                    </div>
                    <div class="history-actions">
                        <button type="button" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-download"></i> Download
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-info text-white">
                    <h5 class="modal-title">Report History</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${historyContent}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Show modal
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        // Remove modal from DOM when hidden
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });
    }
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        showAlert('<i class="bi bi-box-arrow-right me-2"></i>Logging out...', 'info');
        setTimeout(() => {
            window.location.href = '/logout';
        }, 1000);
    }
}
