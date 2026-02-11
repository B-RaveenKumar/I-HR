document.addEventListener('DOMContentLoaded', function () {
    // Helper function to get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }
    document.getElementById('schoolSearch')?.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        const rows = document.querySelectorAll('.table tbody tr');

        rows.forEach(row => {
            const schoolName = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
            row.style.display = schoolName.includes(searchTerm) ? '' : 'none';
        });
    });

    // Delete school
    document.querySelectorAll('.delete-school').forEach(btn => {
        btn.addEventListener('click', function () {
            const schoolId = this.getAttribute('data-school-id');
            const schoolName = this.closest('tr').querySelector('td:nth-child(1)').textContent;

            if (!confirm(`Are you sure you want to delete ${schoolName}? This action cannot be undone.`)) {
                return;
            }

            fetch('/delete_school', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `school_id=${schoolId}&csrf_token=${encodeURIComponent(getCSRFToken())}`
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('School deleted successfully');
                        location.reload();
                    } else {
                        alert(data.error || 'Failed to delete school');
                    }
                });
        });
    });

    // Hide school
    document.querySelectorAll('.hide-school').forEach(btn => {
        btn.addEventListener('click', function () {
            const row = this.closest('tr');
            const schoolId = this.getAttribute('data-school-id');
            const schoolName = row.querySelector('td:nth-child(1)').textContent;

            if (!confirm(`Are you sure you want to toggle visibility for ${schoolName}?`)) {
                return;
            }

            fetch('/toggle_school_visibility', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `school_id=${schoolId}&csrf_token=${encodeURIComponent(getCSRFToken())}`
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`School visibility updated successfully`);
                        location.reload();
                    } else {
                        alert(data.error || 'Failed to update school visibility');
                    }
                });
        });
    });

    // Add new school
    const saveSchool = document.getElementById('saveSchool');
    saveSchool.addEventListener('click', function () {
        const schoolName = document.getElementById('schoolName').value;
        const schoolAddress = document.getElementById('schoolAddress').value;
        const schoolEmail = document.getElementById('schoolEmail').value;
        const schoolPhone = document.getElementById('schoolPhone').value;
        const schoolLogo = document.getElementById('schoolLogo').files[0];

        const adminUsername = document.getElementById('adminUsername').value;
        const adminPassword = document.getElementById('adminPassword').value;
        const adminFullName = document.getElementById('adminFullName').value;
        const adminEmail = document.getElementById('adminEmail').value;

        if (!schoolName || !adminUsername || !adminPassword || !adminFullName) {
            alert('School Name and Admin details are required');
            return;
        }

        const formData = new FormData();
        formData.append('name', schoolName);
        formData.append('address', schoolAddress);
        formData.append('contact_email', schoolEmail);
        formData.append('contact_phone', schoolPhone);
        formData.append('admin_username', adminUsername);
        formData.append('admin_password', adminPassword);
        formData.append('admin_full_name', adminFullName);
        formData.append('admin_email', adminEmail);
        formData.append('csrf_token', getCSRFToken());

        if (schoolLogo) {
            formData.append('logo', schoolLogo);
        }

        fetch('/add_school', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('School added successfully');
                    bootstrap.Modal.getInstance(document.getElementById('addSchoolModal')).hide();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to add school');
                }
            });
    });

    // Edit school
    document.querySelectorAll('.edit-school').forEach(btn => {
        btn.addEventListener('click', function () {
            const schoolId = this.getAttribute('data-school-id');

            // Fetch school data
            fetch(`/get_school/${schoolId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const school = data.school;

                        // Populate form
                        document.getElementById('editSchoolId').value = school.id;
                        document.getElementById('editSchoolName').value = school.name || '';
                        document.getElementById('editSchoolAddress').value = school.address || '';
                        document.getElementById('editSchoolEmail').value = school.contact_email || '';
                        document.getElementById('editSchoolPhone').value = school.contact_phone || '';
                        document.getElementById('editBrandingEnabled').checked = school.branding_enabled == 1;

                        // Show current logo
                        const logoImage = document.getElementById('currentLogoImage');
                        const noLogoText = document.getElementById('noLogoText');

                        if (school.logo_path) {
                            logoImage.src = '/' + school.logo_path;
                            logoImage.style.display = 'block';
                            noLogoText.style.display = 'none';
                        } else {
                            logoImage.style.display = 'none';
                            noLogoText.style.display = 'block';
                        }

                        // Show modal
                        const editModal = new bootstrap.Modal(document.getElementById('editSchoolModal'));
                        editModal.show();
                    } else {
                        alert(data.error || 'Failed to load school data');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to load school data');
                });
        });
    });

    // Update school
    document.getElementById('updateSchool')?.addEventListener('click', function () {
        const schoolId = document.getElementById('editSchoolId').value;
        const schoolName = document.getElementById('editSchoolName').value;
        const schoolAddress = document.getElementById('editSchoolAddress').value;
        const schoolEmail = document.getElementById('editSchoolEmail').value;
        const schoolPhone = document.getElementById('editSchoolPhone').value;
        const schoolLogo = document.getElementById('editSchoolLogo').files[0];
        const brandingEnabled = document.getElementById('editBrandingEnabled').checked ? '1' : '0';

        if (!schoolName) {
            alert('School Name is required');
            return;
        }

        const formData = new FormData();
        formData.append('name', schoolName);
        formData.append('address', schoolAddress);
        formData.append('contact_email', schoolEmail);
        formData.append('contact_phone', schoolPhone);
        formData.append('branding_enabled', brandingEnabled);
        formData.append('csrf_token', getCSRFToken());

        if (schoolLogo) {
            formData.append('logo', schoolLogo);
        }

        fetch(`/edit_school/${schoolId}`, {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('School updated successfully! Logo changes will appear when admin/staff log in again.');
                    bootstrap.Modal.getInstance(document.getElementById('editSchoolModal')).hide();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to update school');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to update school');
            });
    });

    // View school details
    document.querySelectorAll('.view-school').forEach(btn => {
        btn.addEventListener('click', function () {
            const schoolId = this.getAttribute('data-school-id');
            window.location.href = `/company/school_details/${schoolId}`;
        });
    });

    // Timetable Toggle Logic
    document.querySelectorAll('.timetable-toggle').forEach(toggle => {
        toggle.addEventListener('change', function () {
            const schoolId = this.getAttribute('data-school-id');
            const isEnabled = this.checked;
            const label = this.nextElementSibling;

            // Show loading state or disable toggle
            this.disabled = true;

            fetch('/api/timetable/toggle-school', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    school_id: parseInt(schoolId),
                    is_enabled: isEnabled
                })
            })
                .then(response => response.json())
                .then(data => {
                    this.disabled = false;
                    if (data.success) {
                        // Update label/badge
                        if (label) {
                            label.innerHTML = isEnabled
                                ? '<span class="badge bg-success">ON</span>'
                                : '<span class="badge bg-secondary">OFF</span>';
                        }
                        // Optional: show a small toast notification
                        console.log(`Timetable ${isEnabled ? 'enabled' : 'disabled'} for school ${schoolId}`);
                    } else {
                        // Revert toggle if failed
                        this.checked = !isEnabled;
                        alert(data.error || 'Failed to update timetable status');
                    }
                })
                .catch(error => {
                    this.disabled = false;
                    this.checked = !isEnabled;
                    console.error('Error:', error);
                    alert('An error occurred while updating timetable status');
                });
        });
    });

    // Enhanced company report with date range selection
    document.getElementById('exportCompanyReportBtn')?.addEventListener('click', function () {
        const modalHtml = `
            <div class="modal fade" id="reportDateModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">Generate Company Report</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="reportStartDate" class="form-label">Start Date</label>
                                <input type="date" class="form-control" id="reportStartDate" required>
                            </div>
                            <div class="mb-3">
                                <label for="reportEndDate" class="form-label">End Date</label>
                                <input type="date" class="form-control" id="reportEndDate" required>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="generateCompanyReport">Generate Report</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('reportDateModal'));
        modal.show();

        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

        document.getElementById('reportStartDate').valueAsDate = firstDay;
        document.getElementById('reportEndDate').valueAsDate = lastDay;

        document.getElementById('generateCompanyReport').addEventListener('click', function () {
            const startDate = document.getElementById('reportStartDate').value;
            const endDate = document.getElementById('reportEndDate').value;

            if (!startDate || !endDate) {
                alert('Please select both start and end dates');
                return;
            }

            if (startDate > endDate) {
                alert('Start date cannot be after end date');
                return;
            }

            fetch(`/export_company_report?start_date=${startDate}&end_date=${endDate}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `company_report_${startDate}_to_${endDate}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    modal.hide();
                    document.getElementById('reportDateModal').remove();
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to generate report');
                    modal.hide();
                    document.getElementById('reportDateModal').remove();
                });
        });

        document.getElementById('reportDateModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    });
});
