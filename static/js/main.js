// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Handle company admin login form
    const companyLoginForm = document.getElementById('companyLoginForm');
    if (companyLoginForm) {
        companyLoginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new URLSearchParams(new FormData(this));
            
            try {
                const response = await fetch('/company_login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    window.location.href = data.redirect;
                } else {
                    alert(data.error || 'Login failed');
                }
            } catch (error) {
                console.error('Company login error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }

    // Handle school login form
    const schoolLoginForm = document.getElementById('schoolLoginForm');
    if (schoolLoginForm) {
        schoolLoginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Validate school selection
            const schoolSelect = document.getElementById('schoolSelect');
            if (!schoolSelect.value) {
                alert('Please select a school');
                schoolSelect.focus();
                return;
            }

            // Validate username
            const username = document.getElementById('username').value.trim();
            if (!username) {
                alert('Please enter your username/staff ID');
                document.getElementById('username').focus();
                return;
            }

            // Validate password
            const password = document.getElementById('password').value.trim();
            if (!password) {
                alert('Please enter your password');
                document.getElementById('password').focus();
                return;
            }
            
            const formData = new URLSearchParams(new FormData(this));
            
            try {
                // Show loading state
                const submitBtn = this.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn.textContent;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';

                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData
                });
                
                // Restore button state
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;

                const data = await response.json();
                
                if (response.ok) {
                    window.location.href = data.redirect;
                } else {
                    alert(data.error || 'Invalid username or password');
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('An error occurred. Please try again.');
                
                // Restore button state in case of error
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Login';
                }
            }
        });
    }

    // Add event listener for the company admin login link
    const companyLoginLink = document.querySelector('a[href="/company_login"]');
    if (companyLoginLink) {
        companyLoginLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/company_login';
        });
    }
});