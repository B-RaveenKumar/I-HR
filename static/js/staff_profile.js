document.addEventListener('DOMContentLoaded', function() {
    // Helper function to get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : '';
    }

    // Edit Staff Button Handler
    const editStaffBtn = document.getElementById('editStaffBtn');
    if (editStaffBtn) {
        editStaffBtn.addEventListener('click', function() {
            const staffId = this.getAttribute('data-staff-id');
            
            // Populate the edit form with current staff data
            document.getElementById('editStaffId').value = staffId;
            document.getElementById('editFullName').value = document.getElementById('staffName').textContent;
            document.getElementById('editEmail').value = document.getElementById('staffEmail').textContent.replace('-', '');
            document.getElementById('editPhone').value = document.getElementById('staffPhone').textContent.replace('-', '');
            document.getElementById('editDepartment').value = document.getElementById('staffDept').textContent;
            document.getElementById('editPosition').value = document.getElementById('staffPosition').textContent.replace('-', '');
            document.getElementById('editStatus').checked = true; // Assume active by default
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('editStaffModal'));
            modal.show();
        });
    }

    // Delete Staff Button Handler
    const deleteStaffBtn = document.getElementById('deleteStaffBtn');
    if (deleteStaffBtn) {
        deleteStaffBtn.addEventListener('click', function() {
            const staffId = this.getAttribute('data-staff-id');
            const staffName = document.getElementById('staffName').textContent;
            
            if (confirm(`Are you sure you want to delete ${staffName}? This action cannot be undone.`)) {
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
                        window.location.href = '/admin/dashboard';
                    } else {
                        alert(data.error || 'Failed to delete staff');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while deleting staff');
                });
            }
        });
    }

    // Save Edit Staff Button Handler
    const saveEditStaffBtn = document.getElementById('saveEditStaff');
    if (saveEditStaffBtn) {
        saveEditStaffBtn.addEventListener('click', function() {
            const formData = new FormData();
            formData.append('staff_id', document.getElementById('editStaffId').value);
            formData.append('full_name', document.getElementById('editFullName').value);
            formData.append('email', document.getElementById('editEmail').value);
            formData.append('phone', document.getElementById('editPhone').value);
            formData.append('department', document.getElementById('editDepartment').value);
            formData.append('position', document.getElementById('editPosition').value);
            formData.append('status', document.getElementById('editStatus').checked ? 'active' : 'inactive');

            const photoFile = document.getElementById('editPhoto').files[0];
            if (photoFile) {
                formData.append('photo', photoFile);
            }
            formData.append('csrf_token', getCSRFToken());

            fetch('/update_staff', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('Staff updated successfully');
                    location.reload();
                } else {
                    alert(data.error || 'Update failed');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating staff');
            });
        });
    }

    // Reset Password Button Handler
    const resetPasswordBtn = document.getElementById('resetPasswordBtn');
    if (resetPasswordBtn) {
        resetPasswordBtn.addEventListener('click', function() {
            const staffId = this.getAttribute('data-staff-id');
            const staffName = document.getElementById('staffName').textContent;

            if (confirm(`Are you sure you want to reset password for ${staffName}? The new password will be 'password123'.`)) {
                fetch('/reset_staff_password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `staff_id=${staffId}&new_password=password123&csrf_token=${encodeURIComponent(getCSRFToken())}`
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message || 'Password reset successfully');
                    } else {
                        alert(data.error || 'Failed to reset password');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while resetting password');
                });
            }
        });
    }
});
