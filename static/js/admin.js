// admin.js - Hasteo Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initAdminDashboard();
    initUserManagement();
    initBusManagement();
    initFlashMessages();
    initModals();
});

function initAdminDashboard() {
    setupScrollBlur();
    setActiveNavLink();
}

// Scroll blur effect
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

function setActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.admin-nav a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || 
            (currentPath.includes('users') && href.includes('users')) ||
            (currentPath.includes('buses') && href.includes('buses'))) {
            link.classList.add('active');
        }
    });
}

// User Management Functions
function initUserManagement() {
    initTabs();
    initFormValidation();
    initDeleteConfirmation();
}

// Bus Management Functions
function initBusManagement() {
    initBusFilters();
    initBusFormValidation();
    initBusDeleteConfirmation();
    initBusEditButtons();
}

// Tab switching
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
    if (activeBtn) activeBtn.classList.add('active');
    
    // Update tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    const activePane = document.getElementById(`${tab}-tab`);
    if (activePane) activePane.classList.add('active');
}

// Bus filters
function initBusFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            filterBuses(filter);
            
            // Update active state
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function filterBuses(filter) {
    const rows = document.querySelectorAll('.buses-table tbody tr');
    
    rows.forEach(row => {
        if (filter === 'all') {
            row.style.display = '';
        } else {
            const status = row.querySelector('.status-badge')?.textContent.toLowerCase().trim();
            if (status === filter) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
}

// Form validation
function initFormValidation() {
    const studentForm = document.getElementById('addStudentForm');
    const securityForm = document.getElementById('addSecurityForm');
    
    if (studentForm) {
        studentForm.addEventListener('submit', validateStudentForm);
    }
    
    if (securityForm) {
        securityForm.addEventListener('submit', validateSecurityForm);
    }
    
    const deleteYearForm = document.getElementById('deleteByYearForm');
    if (deleteYearForm) {
        deleteYearForm.addEventListener('submit', validateDeleteByYear);
    }
}

function validateStudentForm(e) {
    const form = e.target;
    const password = form.querySelector('input[name="password"]').value;
    const regNumber = form.querySelector('input[name="registration_number"]').value;
    const studentId = form.querySelector('input[name="student_id"]').value;
    
    // Suggest using registration number as default password if empty
    if (password === '') {
        if (confirm('Password is empty. Use registration number as password?')) {
            form.querySelector('input[name="password"]').value = regNumber;
        } else {
            e.preventDefault();
            alert('Please enter a password');
            return false;
        }
    }
    
    // Validate student ID format
    const studentIdPattern = /^S[A-Z]{2}\/\d{5}\/\d{2}$/;
    if (!studentIdPattern.test(studentId)) {
        if (!confirm('Student ID format should be like SCS/12345/23. Continue anyway?')) {
            e.preventDefault();
            return false;
        }
    }
    
    return true;
}

function validateSecurityForm(e) {
    const securityId = e.target.querySelector('input[name="security_id"]').value;
    const securityIdPattern = /^SEC\d{3}$/;
    
    if (!securityIdPattern.test(securityId)) {
        if (!confirm('Security ID format should be like SEC001. Continue anyway?')) {
            e.preventDefault();
            return false;
        }
    }
    
    return true;
}

// Bus form validation
function initBusFormValidation() {
    const busForm = document.getElementById('addBusForm');
    if (busForm) {
        busForm.addEventListener('submit', validateBusForm);
    }
    
    const editBusForms = document.querySelectorAll('.edit-bus-form');
    editBusForms.forEach(form => {
        form.addEventListener('submit', validateBusForm);
    });
}

function validateBusForm(e) {
    const form = e.target;
    const busNumber = form.querySelector('input[name="bus_number"]').value;
    const capacity = form.querySelector('input[name="capacity"]').value;
    const driverPhone = form.querySelector('input[name="driver_phone"]').value;
    
    // Validate bus number format
    const busNumberPattern = /^[A-Z0-9-]+$/;
    if (!busNumberPattern.test(busNumber)) {
        alert('Bus number should contain only letters, numbers, and hyphens');
        e.preventDefault();
        return false;
    }
    
    // Validate capacity
    if (parseInt(capacity) <= 0) {
        alert('Capacity must be greater than 0');
        e.preventDefault();
        return false;
    }
    
    // Validate phone number (basic)
    const phonePattern = /^[0-9]{10}$/;
    if (!phonePattern.test(driverPhone.replace(/\D/g, ''))) {
        if (!confirm('Phone number format may be invalid. Continue anyway?')) {
            e.preventDefault();
            return false;
        }
    }
    
    return true;
}

// Delete confirmations
function initDeleteConfirmation() {
    // Individual delete forms
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const button = this.querySelector('.btn-delete');
            const type = button.dataset.type || 'item';
            const id = button.dataset.id || 'unknown';
            
            if (!confirm(`Are you sure you want to delete this ${type}? This action cannot be undone!`)) {
                e.preventDefault();
            }
        });
    });
}

function initBusDeleteConfirmation() {
    document.querySelectorAll('.delete-bus-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const busNumber = this.querySelector('.btn-delete')?.dataset.bus || 'this bus';
            
            if (!confirm(`Are you sure you want to delete ${busNumber}? This action cannot be undone!`)) {
                e.preventDefault();
            }
        });
    });
}

function validateDeleteByYear(e) {
    const yearSelect = document.querySelector('select[name="year"]');
    if (!yearSelect || !yearSelect.value) {
        alert('Please select a year first!');
        e.preventDefault();
        return false;
    }
    
    if (!confirm(`Are you sure you want to delete ALL students from batch ${yearSelect.value}? This action cannot be undone!`)) {
        e.preventDefault();
        return false;
    }
    
    return true;
}

// Modal handling
function initModals() {
    // Edit bus buttons
    document.querySelectorAll('.edit-bus-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const busId = this.dataset.id;
            openEditBusModal(busId);
        });
    });
    
    // Close buttons
    document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
    
    // Click outside to close
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal();
        }
    });
    
    // Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function openEditBusModal(busId) {
    const modal = document.getElementById('editBusModal');
    if (!modal) return;
    
    // Find bus data
    const busRow = document.querySelector(`tr[data-bus-id="${busId}"]`);
    if (busRow) {
        document.getElementById('edit_bus_id').value = busId;
        document.getElementById('edit_bus_number').value = busRow.dataset.number;
        document.getElementById('edit_route_name').value = busRow.dataset.route;
        document.getElementById('edit_capacity').value = busRow.dataset.capacity;
        document.getElementById('edit_driver_name').value = busRow.dataset.driver;
        document.getElementById('edit_driver_phone').value = busRow.dataset.phone;
        document.getElementById('edit_driver_license').value = busRow.dataset.license || '';
        document.getElementById('edit_status').value = busRow.dataset.status;
        document.getElementById('edit_notes').value = busRow.dataset.notes || '';
    }
    
    modal.classList.add('active');
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

// Flash message handling
function initFlashMessages() {
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

// Show notification (can be called from anywhere)
window.showAdminNotification = function(message, type = 'info') {
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }
    
    const flashDiv = document.createElement('div');
    flashDiv.className = `flash-message ${type}`;
    
    const icon = getIconForType(type);
    flashDiv.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    
    container.appendChild(flashDiv);
    
    setTimeout(() => {
        hideFlashMessage(flashDiv);
    }, 4000);
    
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

// Handle card clicks for inactive features
window.handleCardClick = function(feature) {
    if (feature === 'Daily Report') {
        alert('Daily Reports feature is coming soon!');
    }
};

// Logout confirmation
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to logout?')) {
            e.preventDefault();
        }
    });
}