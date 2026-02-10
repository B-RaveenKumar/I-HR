document.addEventListener('DOMContentLoaded', function() {
    // Helper function to get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }

    // Toast notification function
    function showToast(message, type = 'info') {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.custom-toast');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `custom-toast alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        toast.innerHTML = `
            <i class="bi bi-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    // Enhanced form validation function
    function validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        let firstInvalidField = null;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                if (!firstInvalidField) firstInvalidField = field;
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
            }
        });

        if (!isValid && firstInvalidField) {
            firstInvalidField.focus();
            showToast('Please fill in all required fields', 'error');
        }

        return isValid;
    }

    // Function to load and update attendance summary dynamically
    let attendanceChart = null; // Store chart instance for updates

    function loadAttendanceSummary() {
        fetch('/staff/get_attendance_summary')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update stat cards
                    const statCards = document.querySelectorAll('.attendance-stat-card .stat-value');
                    if (statCards[0]) statCards[0].textContent = data.present_days;
                    if (statCards[1]) statCards[1].textContent = data.absent_days;
                    if (statCards[2]) statCards[2].textContent = data.late_days;
                    if (statCards[3]) statCards[3].textContent = data.leave_days;

                    // Update month title
                    const monthTitle = document.querySelector('.card-title');
                    if (monthTitle && data.current_month) {
                        monthTitle.textContent = `${data.current_month} Summary`;
                    }

                    // Update or create chart
                    const ctx = document.getElementById('attendanceSummaryChart')?.getContext('2d');
                    if (ctx) {
                        const chartData = {
                            labels: ['Present', 'Absent', 'Late', 'Leave'],
                            datasets: [{
                                data: [data.present_days, data.absent_days, data.late_days, data.leave_days],
                                backgroundColor: [
                                    '#198754',
                                    '#dc3545',
                                    '#ffc107',
                                    '#0dcaf0'
                                ],
                                borderWidth: 3,
                                borderColor: '#ffffff',
                                hoverBorderWidth: 4,
                                hoverOffset: 10
                            }]
                        };

                        if (attendanceChart) {
                            // Update existing chart
                            attendanceChart.data = chartData;
                            attendanceChart.update();
                        } else {
                            // Create new chart
                            attendanceChart = new Chart(ctx, {
                                type: 'doughnut',
                                data: chartData,
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: {
                                        legend: {
                                            position: 'bottom',
                                            labels: {
                                                padding: 20,
                                                usePointStyle: true,
                                                font: {
                                                    size: 12,
                                                    weight: '500'
                                                }
                                            }
                                        },
                                        tooltip: {
                                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                            titleColor: '#ffffff',
                                            bodyColor: '#ffffff',
                                            borderColor: '#ffffff',
                                            borderWidth: 1,
                                            cornerRadius: 8,
                                            padding: 12,
                                            callbacks: {
                                                label: function(context) {
                                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                                    const percentage = total > 0 ? ((context.parsed * 100) / total).toFixed(1) : 0;
                                                    return `${context.label}: ${context.parsed} days (${percentage}%)`;
                                                }
                                            }
                                        }
                                    },
                                    animation: {
                                        animateRotate: true,
                                        animateScale: true,
                                        duration: 1000,
                                        easing: 'easeOutQuart'
                                    }
                                }
                            });
                        }
                    }

                    console.log('Attendance summary loaded successfully:', data);
                } else {
                    console.error('Failed to load attendance summary:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading attendance summary:', error);
            });
    }

    // Load attendance summary on page load
    loadAttendanceSummary();

    // Add refresh button event listener
    const refreshBtn = document.getElementById('refreshAttendanceSummary');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Add spinning animation to the icon
            const icon = this.querySelector('i');
            icon.classList.add('fa-spin');
            this.disabled = true;
            
            // Load fresh data
            loadAttendanceSummary();
            
            // Remove spinning animation after a delay
            setTimeout(() => {
                icon.classList.remove('fa-spin');
                this.disabled = false;
            }, 1000);
        });
    }

    // Initialize weekly attendance calendar
    const weeklyCalendarEl = document.getElementById('weeklyAttendanceCalendar');
    if (weeklyCalendarEl) {
        // Initialize the weekly calendar component
        const weeklyCalendar = new WeeklyAttendanceCalendar('weeklyAttendanceCalendar', {
            isAdminView: false
        });

        // Store reference for potential future use
        window.weeklyAttendanceCalendar = weeklyCalendar;

        // Add calendar refresh functionality
        const addCalendarRefreshButton = () => {
            const calendarHeader = weeklyCalendarEl.querySelector('.calendar-header .d-flex');
            if (calendarHeader && !calendarHeader.querySelector('.refresh-btn')) {
                const refreshBtn = document.createElement('button');
                refreshBtn.className = 'btn btn-outline-success btn-sm refresh-btn';
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh';
                refreshBtn.title = 'Refresh attendance data';
                refreshBtn.addEventListener('click', () => {
                    weeklyCalendar.refresh();
                    showToast('Attendance data refreshed', 'success');
                });
                calendarHeader.appendChild(refreshBtn);
            }
        };

        // Add the refresh button after calendar loads
        setTimeout(addCalendarRefreshButton, 1000);

        // Auto-refresh calendar every 5 minutes
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                weeklyCalendar.refresh();
            }
        }, 300000); // 5 minutes
    }

    // Edit Profile functionality
    document.getElementById('saveProfileBtn')?.addEventListener('click', function() {
        const form = document.getElementById('editProfileForm');
        const formData = new FormData(form);

        // Basic validation
        if (!validateForm(form)) {
            return;
        }

        // Show loading state
        const btn = this;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-spinner-border spinner-border-sm"></i> Saving...';
        btn.disabled = true;

        fetch('/staff/update_profile', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Profile updated successfully!', 'success');
                bootstrap.Modal.getInstance(document.getElementById('editProfileModal')).hide();
                setTimeout(() => location.reload(), 1500); // Reload to show updated information
            } else {
                showToast(data.error || 'Failed to update profile', 'error');
            }
        })
        .catch(error => {
            console.error('Error updating profile:', error);
            showToast('Error updating profile', 'error');
        })
        .finally(() => {
            // Reset button state
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    });

    // Change Password functionality
    document.getElementById('changePasswordBtn')?.addEventListener('click', function() {
        const form = document.getElementById('changePasswordForm');
        const formData = new FormData(form);

        // Basic validation
        if (!validateForm(form)) {
            return;
        }

        // Validate passwords match
        const newPassword = formData.get('new_password');
        const confirmPassword = formData.get('confirm_password');

        if (newPassword !== confirmPassword) {
            showToast('New passwords do not match', 'error');
            document.getElementById('confirmPassword').classList.add('is-invalid');
            return;
        }

        // Validate password strength
        if (newPassword.length < 6) {
            showToast('Password must be at least 6 characters long', 'error');
            document.getElementById('newPassword').classList.add('is-invalid');
            return;
        }

        // Show loading state
        const btn = this;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-spinner-border spinner-border-sm"></i> Changing...';
        btn.disabled = true;

        fetch('/staff/change_password', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Password changed successfully!', 'success');
                bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
                form.reset();
                // Clear validation classes
                form.querySelectorAll('.is-valid, .is-invalid').forEach(field => {
                    field.classList.remove('is-valid', 'is-invalid');
                });
            } else {
                showToast(data.error || 'Failed to change password', 'error');
            }
        })
        .catch(error => {
            console.error('Error changing password:', error);
            showToast('Error changing password', 'error');
        })
        .finally(() => {
            // Reset button state
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    });

    // Apply Leave functionality
    document.getElementById('submitLeave')?.addEventListener('click', function() {
        const form = document.getElementById('leaveForm');
        const formData = new FormData(form);

        // Basic validation
        if (!validateForm(form)) {
            return;
        }

        // Additional validation
        const leaveType = formData.get('leave_type');
        const startDate = formData.get('start_date');
        const endDate = formData.get('end_date');
        const reason = formData.get('reason');

        // Check if end date is after start date
        if (new Date(endDate) < new Date(startDate)) {
            showToast('End date must be after start date', 'error');
            document.getElementById('endDate').classList.add('is-invalid');
            return;
        }

        // Check if start date is not in the past
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (new Date(startDate) < today) {
            showToast('Start date cannot be in the past', 'error');
            document.getElementById('startDate').classList.add('is-invalid');
            return;
        }

        // Show loading state
        const btn = this;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-spinner-border spinner-border-sm"></i> Submitting...';
        btn.disabled = true;

        fetch('/apply_leave', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Leave application submitted successfully!', 'success');
                bootstrap.Modal.getInstance(document.getElementById('applyLeaveModal')).hide();
                form.reset();
                // Clear validation classes
                form.querySelectorAll('.is-valid, .is-invalid').forEach(field => {
                    field.classList.remove('is-valid', 'is-invalid');
                });
                setTimeout(() => location.reload(), 1500); // Reload to show new leave application
            } else {
                showToast(data.error || 'Failed to submit leave application', 'error');
            }
        })
        .catch(error => {
            console.error('Error submitting leave:', error);
            showToast('Error submitting leave application', 'error');
        })
        .finally(() => {
            // Reset button state
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    });

    // Set minimum date for leave application to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('startDate')?.setAttribute('min', today);
    document.getElementById('endDate')?.setAttribute('min', today);

    // Update end date minimum when start date changes
    document.getElementById('startDate')?.addEventListener('change', function() {
        const endDateInput = document.getElementById('endDate');
        if (endDateInput) {
            endDateInput.setAttribute('min', this.value);
            if (endDateInput.value && endDateInput.value < this.value) {
                endDateInput.value = this.value;
            }
        }
    });

    // Real-time form validation
    document.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('input', function() {
            if (this.hasAttribute('required')) {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                }
            }
        });

        field.addEventListener('blur', function() {
            if (this.hasAttribute('required') && !this.value.trim()) {
                this.classList.add('is-invalid');
            }
        });
    });

    // Password confirmation validation
    document.getElementById('confirmPassword')?.addEventListener('input', function() {
        const newPassword = document.getElementById('newPassword')?.value;
        if (newPassword && this.value) {
            if (newPassword === this.value) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        }
    });

    // Photo upload preview
    document.getElementById('profilePhoto')?.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                // Create preview if it doesn't exist
                let preview = document.getElementById('photoPreview');
                if (!preview) {
                    preview = document.createElement('div');
                    preview.id = 'photoPreview';
                    preview.className = 'mt-2';
                    this.parentNode.appendChild(preview);
                }
                preview.innerHTML = `
                    <img src="${e.target.result}" alt="Photo Preview" 
                         style="max-width: 150px; max-height: 150px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div class="text-muted mt-1"><small>Photo preview</small></div>
                `;
            }.bind(this);
            reader.readAsDataURL(file);
        }
    });

    // Enhanced modal focus management
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = this.querySelector('input:not([type="hidden"]), select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });

        modal.addEventListener('hidden.bs.modal', function() {
            // Clear validation classes when modal is closed
            this.querySelectorAll('.is-valid, .is-invalid').forEach(field => {
                field.classList.remove('is-valid', 'is-invalid');
            });
        });
    });
});
