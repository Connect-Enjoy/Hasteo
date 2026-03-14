// Login Page JavaScript - Hasteo Project

document.addEventListener('DOMContentLoaded', function() {
    // Form validation for login forms
    const loginForms = document.querySelectorAll('.login-form');
    loginForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.style.borderColor = '#F44336';
                    
                    // Add error message if not present
                    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('field-error')) {
                        const errorMsg = document.createElement('div');
                        errorMsg.className = 'field-error';
                        errorMsg.style.color = '#F44336';
                        errorMsg.style.fontSize = '0.85rem';
                        errorMsg.style.marginTop = '5px';
                        errorMsg.textContent = 'This field is required';
                        field.parentNode.appendChild(errorMsg);
                    }
                } else {
                    field.style.borderColor = '';
                    
                    // Remove error message if exists
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('field-error')) {
                        errorMsg.remove();
                    }
                }
            });

            if (!valid) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state using global function
            if (window.showLoading) {
                const submitBtn = form.querySelector('button[type="submit"]');
                window.showLoading(submitBtn);
            }
        });
    });

    // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter to submit form
        if (e.ctrlKey && e.key === 'Enter') {
            const form = document.querySelector('.login-form');
            if (form) {
                form.submit();
            }
        }
        
        // Escape key to go back
        if (e.key === 'Escape') {
            if (document.referrer) {
                window.history.back();
            }
        }
    });

    // Input focus effects
    const inputs = document.querySelectorAll('.login-form-group input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'translateY(-2px)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'translateY(0)';
        });
    });
});