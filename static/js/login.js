// Login Page JavaScript - Hasteo Project

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });

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
            
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
            submitBtn.disabled = true;
            
            // Re-enable after 3 seconds (simulating network delay)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 3000);
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

    // Role selector functionality
    const roleButtons = document.querySelectorAll('.role-btn');
    const loginFormsContainer = document.querySelectorAll('.login-form-container > form');
    
    if (roleButtons.length > 0) {
        roleButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                // Remove active class from all buttons
                roleButtons.forEach(b => b.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Show corresponding form
                const role = this.dataset.role;
                loginFormsContainer.forEach(form => {
                    if (form.id === `${role}-form`) {
                        form.style.display = 'block';
                    } else {
                        form.style.display = 'none';
                    }
                });
            });
        });
    }

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
        // Add focus animation
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'translateY(-2px)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'translateY(0)';
        });
    });

    // Remember me functionality
    const rememberCheckbox = document.getElementById('remember');
    if (rememberCheckbox) {
        // Check if credentials are saved
        const savedUsername = localStorage.getItem('hasteo_username');
        const savedPassword = localStorage.getItem('hasteo_password');
        
        if (savedUsername && savedPassword) {
            document.getElementById('username').value = savedUsername;
            document.getElementById('password').value = savedPassword;
            rememberCheckbox.checked = true;
        }
        
        // Save on form submit if checked
        document.querySelector('.login-form').addEventListener('submit', function() {
            if (rememberCheckbox.checked) {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                localStorage.setItem('hasteo_username', username);
                localStorage.setItem('hasteo_password', password);
            } else {
                localStorage.removeItem('hasteo_username');
                localStorage.removeItem('hasteo_password');
            }
        });
    }
});

// Utility functions
function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    button.disabled = true;
    return originalText;
}

function hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    // At least 6 characters
    return password.length >= 6;
}

// Form reset function
function resetLoginForm() {
    const form = document.querySelector('.login-form');
    if (form) {
        form.reset();
        const errors = form.querySelectorAll('.field-error');
        errors.forEach(error => error.remove());
    }
}