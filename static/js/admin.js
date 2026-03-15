// admin.js - Hasteo Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initAdminDashboard();
    initUserManagement();
    initBusManagement();
    initFlashMessages();
    initModals();
    initSearchAndFilters();
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
    
    // Check hash for tab navigation
    if (window.location.hash === '#security') {
        setTimeout(() => switchTab('security'), 100);
    } else if (window.location.hash === '#students') {
        setTimeout(() => switchTab('students'), 100);
    }
}

// User Management Functions
function initUserManagement() {
    initTabs();
    initAddStudentForm();
    initAddSecurityForm();
    initStudentDeleteButtons();
    initSecurityDeleteButtons();
    initStudentEditButtons();
    initBatchDelete();
}

// Bus Management Functions
function initBusManagement() {
    initAddBusForm();
    initBusDeleteButtons();
    initBusEditButtons();
}

// Tab switching
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
            window.location.hash = tab;
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

// Search and Filter Functions
function initSearchAndFilters() {
    // Student search
    const studentSearch = document.getElementById('studentSearch');
    if (studentSearch) {
        studentSearch.addEventListener('input', filterStudents);
    }
    
    // Student filters
    const filterBranch = document.getElementById('filterBranch');
    const filterYear = document.getElementById('filterYear');
    const filterResidence = document.getElementById('filterResidence');
    
    if (filterBranch) filterBranch.addEventListener('change', filterStudents);
    if (filterYear) filterYear.addEventListener('change', filterStudents);
    if (filterResidence) filterResidence.addEventListener('change', filterStudents);
    
    // Clear filters button
    const clearFilters = document.getElementById('clearFilters');
    if (clearFilters) {
        clearFilters.addEventListener('click', clearStudentFilters);
    }
    
    // Bus search
    const busSearch = document.getElementById('busSearch');
    if (busSearch) {
        busSearch.addEventListener('input', filterBuses);
    }
    
    // Bus status filter
    const filterBusStatus = document.getElementById('filterBusStatus');
    if (filterBusStatus) {
        filterBusStatus.addEventListener('change', filterBuses);
    }
    
    // Clear bus filters
    const clearBusFilters = document.getElementById('clearBusFilters');
    if (clearBusFilters) {
        clearBusFilters.addEventListener('click', clearBusFiltersFunction);
    }
}

function filterStudents() {
    const searchTerm = document.getElementById('studentSearch')?.value.toLowerCase() || '';
    const branchFilter = document.getElementById('filterBranch')?.value || '';
    const yearFilter = document.getElementById('filterYear')?.value || '';
    const residenceFilter = document.getElementById('filterResidence')?.value || '';
    
    const rows = document.querySelectorAll('#studentsTable tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const studentId = row.cells[0]?.textContent.toLowerCase() || '';
        const name = row.cells[1]?.textContent.toLowerCase() || '';
        const branch = row.cells[2]?.textContent.trim() || '';
        const year = row.cells[3]?.textContent || '';
        const residence = row.cells[4]?.textContent.toLowerCase() || '';
        
        const matchesSearch = searchTerm === '' || 
            studentId.includes(searchTerm) || 
            name.includes(searchTerm) ||
            branch.toLowerCase().includes(searchTerm);
        
        const matchesBranch = branchFilter === '' || branch.includes(branchFilter);
        const matchesYear = yearFilter === '' || year === yearFilter;
        const matchesResidence = residenceFilter === '' || 
            (residenceFilter === 'day_scholar' && residence.includes('day')) ||
            (residenceFilter === 'hosteller' && residence.includes('hosteller'));
        
        if (matchesSearch && matchesBranch && matchesYear && matchesResidence) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    showNoResults('studentsTable', visibleCount);
}

function filterBuses() {
    const searchTerm = document.getElementById('busSearch')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('filterBusStatus')?.value || '';
    
    const rows = document.querySelectorAll('#busesTable tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const busNumber = row.cells[0]?.textContent.toLowerCase() || '';
        const route = row.cells[1]?.textContent.toLowerCase() || '';
        const driver = row.cells[2]?.textContent.toLowerCase() || '';
        const statusElement = row.querySelector('.status-badge');
        const status = statusElement ? statusElement.textContent.toLowerCase().trim() : '';
        
        const matchesSearch = searchTerm === '' || 
            busNumber.includes(searchTerm) || 
            route.includes(searchTerm) ||
            driver.includes(searchTerm);
        
        const matchesStatus = statusFilter === '' || status.includes(statusFilter);
        
        if (matchesSearch && matchesStatus) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    showNoResults('busesTable', visibleCount);
}

function showNoResults(tableId, visibleCount) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const existingMsg = document.getElementById(`no${tableId}Results`);
    
    if (visibleCount === 0) {
        if (!existingMsg) {
            const tr = document.createElement('tr');
            tr.id = `no${tableId}Results`;
            tr.innerHTML = `<td colspan="8" style="text-align: center; padding: 30px;">
                <i class="fas fa-search" style="font-size: 2rem; opacity: 0.5; margin-bottom: 10px; display: block;"></i>
                No records match your search criteria
            </td>`;
            tbody.appendChild(tr);
        }
    } else {
        if (existingMsg) existingMsg.remove();
    }
}

function clearStudentFilters() {
    const searchInput = document.getElementById('studentSearch');
    const branchFilter = document.getElementById('filterBranch');
    const yearFilter = document.getElementById('filterYear');
    const residenceFilter = document.getElementById('filterResidence');
    
    if (searchInput) searchInput.value = '';
    if (branchFilter) branchFilter.value = '';
    if (yearFilter) yearFilter.value = '';
    if (residenceFilter) residenceFilter.value = '';
    
    filterStudents();
}

function clearBusFiltersFunction() {
    const searchInput = document.getElementById('busSearch');
    const statusFilter = document.getElementById('filterBusStatus');
    
    if (searchInput) searchInput.value = '';
    if (statusFilter) statusFilter.value = '';
    
    filterBuses();
}

// Add Student Form
function initAddStudentForm() {
    const form = document.getElementById('addStudentForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitBtn = document.getElementById('addStudentBtn');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        submitBtn.disabled = true;
        
        fetch('/admin/add-student', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                form.reset();
                // Reload the page to show new student
                setTimeout(() => location.reload(), 1500);
            } else {
                showNotification(data.error || 'Error adding student', 'error');
            }
        })
        .catch(error => {
            showNotification('Network error. Please try again.', 'error');
            console.error('Error:', error);
        })
        .finally(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });
}

// Add Security Form
function initAddSecurityForm() {
    const form = document.getElementById('addSecurityForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitBtn = document.getElementById('addSecurityBtn');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        submitBtn.disabled = true;
        
        fetch('/admin/add-security', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                form.reset();
                // Reload the page to show new security personnel
                setTimeout(() => location.reload(), 1500);
            } else {
                showNotification(data.error || 'Error adding security', 'error');
            }
        })
        .catch(error => {
            showNotification('Network error. Please try again.', 'error');
            console.error('Error:', error);
        })
        .finally(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });
}

// Add Bus Form
function initAddBusForm() {
    const form = document.getElementById('addBusForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitBtn = document.getElementById('addBusBtn');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        submitBtn.disabled = true;
        
        fetch('/admin/add-bus', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                form.reset();
                // Reload the page to show new bus
                setTimeout(() => location.reload(), 1500);
            } else {
                showNotification(data.error || 'Error adding bus', 'error');
            }
        })
        .catch(error => {
            showNotification('Network error. Please try again.', 'error');
            console.error('Error:', error);
        })
        .finally(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    });
}

// Delete Student
function initStudentDeleteButtons() {
    document.querySelectorAll('.btn-delete-student').forEach(btn => {
        btn.addEventListener('click', function() {
            const studentId = this.dataset.id;
            const row = this.closest('tr');
            
            showDeleteConfirmation(
                'Are you sure you want to delete this student?',
                function() {
                    fetch(`/admin/delete-student/${studentId}`, {
                        method: 'POST'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showNotification(data.message, 'success');
                            row.remove();
                            closeModal();
                        } else {
                            showNotification(data.error || 'Error deleting student', 'error');
                        }
                    })
                    .catch(error => {
                        showNotification('Network error. Please try again.', 'error');
                        console.error('Error:', error);
                    });
                }
            );
        });
    });
}

// Delete Security
function initSecurityDeleteButtons() {
    document.querySelectorAll('.btn-delete-security').forEach(btn => {
        btn.addEventListener('click', function() {
            const securityId = this.dataset.id;
            const row = this.closest('tr');
            
            showDeleteConfirmation(
                'Are you sure you want to delete this security personnel?',
                function() {
                    fetch(`/admin/delete-security/${securityId}`, {
                        method: 'POST'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showNotification(data.message, 'success');
                            row.remove();
                            closeModal();
                        } else {
                            showNotification(data.error || 'Error deleting security', 'error');
                        }
                    })
                    .catch(error => {
                        showNotification('Network error. Please try again.', 'error');
                        console.error('Error:', error);
                    });
                }
            );
        });
    });
}

// Delete Bus
function initBusDeleteButtons() {
    document.querySelectorAll('.btn-delete-bus').forEach(btn => {
        btn.addEventListener('click', function() {
            const busId = this.dataset.id;
            const row = this.closest('tr');
            
            showDeleteConfirmation(
                'Are you sure you want to delete this bus?',
                function() {
                    fetch(`/admin/delete-bus/${busId}`, {
                        method: 'POST'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showNotification(data.message, 'success');
                            row.remove();
                            closeModal();
                        } else {
                            showNotification(data.error || 'Error deleting bus', 'error');
                        }
                    })
                    .catch(error => {
                        showNotification('Network error. Please try again.', 'error');
                        console.error('Error:', error);
                    });
                }
            );
        });
    });
}

// Edit Student
function initStudentEditButtons() {
    document.querySelectorAll('.btn-edit-student').forEach(btn => {
        btn.addEventListener('click', function() {
            const studentId = this.dataset.id;
            
            // Fetch student details
            fetch(`/admin/get-student/${studentId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const student = data.student;
                        document.getElementById('editStudentId').value = student.id;
                        document.getElementById('editStudentName').value = student.name;
                        document.getElementById('editStudentBranch').value = student.branch;
                        document.getElementById('editStudentYear').value = student.year;
                        document.getElementById('editStudentResidence').value = student.residence;
                        document.getElementById('editStudentReg').value = student.registration_number;
                        document.getElementById('editStudentEmail').value = student.email;
                        
                        document.getElementById('editStudentModal').classList.add('active');
                    } else {
                        showNotification('Error loading student data', 'error');
                    }
                })
                .catch(error => {
                    showNotification('Network error. Please try again.', 'error');
                    console.error('Error:', error);
                });
        });
    });
    
    // Handle edit form submission
    const editForm = document.getElementById('editStudentForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const studentId = document.getElementById('editStudentId').value;
            const formData = new FormData(editForm);
            const submitBtn = editForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
            submitBtn.disabled = true;
            
            fetch(`/admin/update-student/${studentId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    closeModal();
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification(data.error || 'Error updating student', 'error');
                }
            })
            .catch(error => {
                showNotification('Network error. Please try again.', 'error');
                console.error('Error:', error);
            })
            .finally(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });
    }
}

// Edit Bus
function initBusEditButtons() {
    document.querySelectorAll('.btn-edit-bus').forEach(btn => {
        btn.addEventListener('click', function() {
            const busId = this.dataset.id;
            
            // Fetch bus details
            fetch(`/admin/get-bus/${busId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const bus = data.bus;
                        document.getElementById('editBusId').value = bus.id;
                        document.getElementById('editBusNumber').value = bus.bus_number;
                        document.getElementById('editBusRoute').value = bus.route_name;
                        document.getElementById('editBusDriver').value = bus.driver_name;
                        document.getElementById('editBusPhone').value = bus.driver_phone;
                        document.getElementById('editBusStatus').value = bus.status;
                        
                        document.getElementById('editBusModal').classList.add('active');
                    } else {
                        showNotification('Error loading bus data', 'error');
                    }
                })
                .catch(error => {
                    showNotification('Network error. Please try again.', 'error');
                    console.error('Error:', error);
                });
        });
    });
    
    // Handle edit form submission
    const editForm = document.getElementById('editBusForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const busId = document.getElementById('editBusId').value;
            const formData = new FormData(editForm);
            const submitBtn = editForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
            submitBtn.disabled = true;
            
            fetch(`/admin/update-bus/${busId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    closeModal();
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification(data.error || 'Error updating bus', 'error');
                }
            })
            .catch(error => {
                showNotification('Network error. Please try again.', 'error');
                console.error('Error:', error);
            })
            .finally(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });
    }
}

// Batch Delete
function initBatchDelete() {
    document.querySelectorAll('.btn-delete-batch').forEach(btn => {
        btn.addEventListener('click', function() {
            const year = this.dataset.year;
            const count = this.dataset.count;
            
            showDeleteConfirmation(
                `Are you sure you want to delete ALL ${count} students from batch ${year}?`,
                function() {
                    fetch('/admin/delete-students-by-year', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ year: year })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showNotification(data.message, 'success');
                            // Remove the batch item
                            document.querySelector(`.batch-item[data-year="${year}"]`).remove();
                            // Reload after a delay
                            setTimeout(() => location.reload(), 1500);
                        } else {
                            showNotification(data.error || 'Error deleting batch', 'error');
                        }
                    })
                    .catch(error => {
                        showNotification('Network error. Please try again.', 'error');
                        console.error('Error:', error);
                    });
                }
            );
        });
    });
}

// Delete Confirmation Modal
let deleteCallback = null;

function showDeleteConfirmation(message, callback) {
    const modal = document.getElementById('deleteConfirmModal');
    const messageEl = document.getElementById('deleteConfirmMessage');
    
    messageEl.textContent = message;
    deleteCallback = callback;
    
    modal.classList.add('active');
}

// Modal handling
function initModals() {
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
    
    // Confirm delete button
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (deleteCallback) {
                deleteCallback();
            }
        });
    }
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
    deleteCallback = null;
}

// Notification system
function showNotification(message, type = 'info') {
    const container = document.querySelector('.flash-messages');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `flash-message ${type}`;
    
    const icon = getIconForType(type);
    notification.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    
    container.appendChild(notification);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
    
    // Click to dismiss
    notification.addEventListener('click', () => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    });
}

function getIconForType(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

function initFlashMessages() {
    // Auto-hide existing flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            message.style.opacity = '0';
            message.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                if (message.parentNode) {
                    message.remove();
                }
            }, 300);
        }, 3000);
    });
}

// Logout confirmation
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to logout?')) {
            e.preventDefault();
        }
    });
}