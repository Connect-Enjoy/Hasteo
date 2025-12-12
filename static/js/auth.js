// Authentication JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Set remember me if previously saved
    const rememberMe = localStorage.getItem('hasteo_remember_me');
    const username = localStorage.getItem('hasteo_username');
    
    if (rememberMe === 'true' && username) {
        const rememberMeCheckbox = document.getElementById('remember_me');
        const usernameInput = document.getElementById('username');
        
        if (rememberMeCheckbox) {
            rememberMeCheckbox.checked = true;
        }
        
        if (usernameInput) {
            usernameInput.value = username;
        }
    }
    
    // Save remember me on form submit
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function() {
            const rememberMe = document.getElementById('remember_me')?.checked || false;
            const username = document.getElementById('username')?.value || '';
            const role = document.body.classList.contains('admin-login') ? 'admin' : 'security';
            
            if (rememberMe) {
                localStorage.setItem('hasteo_remember_me', 'true');
                localStorage.setItem('hasteo_username', username);
                localStorage.setItem('hasteo_role', role);
            } else {
                localStorage.removeItem('hasteo_remember_me');
                localStorage.removeItem('hasteo_username');
                localStorage.removeItem('hasteo_role');
            }
        });
    }
    
    // Toggle password visibility
    document.querySelectorAll('.password-toggle button').forEach(button => {
        button.addEventListener('click', function() {
            const fieldId = this.dataset.target || 'password';
            const field = document.getElementById(fieldId);
            
            if (field.type === 'password') {
                field.type = 'text';
                this.innerHTML = '<i class="fas fa-eye-slash"></i> Hide';
            } else {
                field.type = 'password';
                this.innerHTML = '<i class="fas fa-eye"></i> Show';
            }
        });
    });
    
    // Auto-focus username field
    const usernameInput = document.getElementById('username');
    if (usernameInput && !usernameInput.value) {
        usernameInput.focus();
    }
});

// Toggle password visibility
function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    const button = event.target.closest('button');
    
    if (!field || !button) return;
    
    if (field.type === 'password') {
        field.type = 'text';
        button.innerHTML = '<i class="fas fa-eye-slash"></i> Hide';
    } else {
        field.type = 'password';
        button.innerHTML = '<i class="fas fa-eye"></i> Show';
    }
}

// Auto-login if remembered
function checkAutoLogin() {
    const rememberMe = localStorage.getItem('hasteo_remember_me');
    const username = localStorage.getItem('hasteo_username');
    const role = localStorage.getItem('hasteo_role');
    
    if (rememberMe === 'true' && username && role) {
        // Check if we're on a login page
        if (window.location.pathname.includes('login')) {
            // Auto-fill the form
            document.getElementById('username').value = username;
            document.getElementById('remember_me').checked = true;
            
            // Show auto-login notification
            showNotification(`Auto-login enabled for ${username}`, 'info');
        }
    }
}

// Check if user should be redirected
function checkRedirect() {
    const rememberMe = localStorage.getItem('hasteo_remember_me');
    const role = localStorage.getItem('hasteo_role');
    
    if (rememberMe === 'true' && role) {
        // If on home page, redirect to appropriate dashboard
        if (window.location.pathname === '/') {
            if (role === 'admin') {
                window.location.href = '/admin';
            } else if (role === 'security') {
                window.location.href = '/security';
            }
        }
    }
}

// Export functions
window.togglePassword = togglePassword;
window.checkAutoLogin = checkAutoLogin;
window.checkRedirect = checkRedirect;

// Initialize on load
window.addEventListener('load', function() {
    checkAutoLogin();
    checkRedirect();
});