// admin.js - Hasteo Admin Dashboard JavaScript
// Only admin-specific functionality, reusing main.js functions where possible

document.addEventListener('DOMContentLoaded', function() {
    initAdminDashboard();
});

function initAdminDashboard() {
    setupScrollBlur(); // Reuses same function from main script.js
    setupFlashMessages(); // Enhanced version of main flash messages
    setActiveNavLink();
}

// Scroll blur effect - matches main site functionality
function setupScrollBlur() {
    const header = document.querySelector('.admin-header');
    if (!header) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

// Enhanced flash message handling with positioning
function setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // Auto-hide after 4 seconds
        setTimeout(() => {
            hideFlashMessage(message);
        }, 4000);
        
        // Click to dismiss
        message.addEventListener('click', () => {
            hideFlashMessage(message);
        });
    });
}

function hideFlashMessage(message) {
    message.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    message.style.opacity = '0';
    message.style.transform = 'translateX(100%)';
    
    setTimeout(() => {
        if (message.parentNode) {
            message.remove();
        }
    }, 300);
}

// Show notification (can be called from HTML)
window.showAdminNotification = function(message, type = 'info') {
    // Check if flash container exists, if not create it
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }
    
    const flashDiv = document.createElement('div');
    flashDiv.className = `flash-message ${type}`;
    
    // Add icon based on type
    const icon = getIconForType(type);
    flashDiv.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    
    container.appendChild(flashDiv);
    
    // Auto-hide
    setTimeout(() => {
        hideFlashMessage(flashDiv);
    }, 4000);
    
    // Click to dismiss
    flashDiv.addEventListener('click', () => {
        hideFlashMessage(flashDiv);
    });
};

function getIconForType(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

function setActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.admin-nav a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
        }
    });
}

// Simple confirmation for logout
window.confirmLogout = function() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/admin/logout';
    }
    return false;
};

// Simple card click handler
window.handleCardClick = function(action) {
    window.showAdminNotification(`${action} feature coming soon!`, 'info');
};