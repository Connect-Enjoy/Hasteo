// security.js - Hasteo Security Dashboard JavaScript

// Global variables
let currentLogId = null;
let currentScanId = null;
let selectedBusId = null;
let deleteCallback = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initSecurityDashboard();
    initBusLogs();
    initStudentLogs();
    initModals();
    initFlashMessages();
    initSecurityScanner(); // Initialize scanner if on scanner page
    
    // Load today's scans on student logs page
    if (document.querySelector('.student-logs-container')) {
        loadTodayScans();
    }
});

// Initialize Security Dashboard
function initSecurityDashboard() {
    setupScrollBlur();
    setActiveNavLink();
}

// Scroll blur effect
function setupScrollBlur() {
    const header = document.querySelector('.security-header');
    if (!header) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

// Set active navigation link
function setActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.security-nav a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
        }
    });
}

// Initialize Bus Logs functionality
function initBusLogs() {
    // Only run on bus logs page
    if (!document.querySelector('.bus-logs-container')) return;
    
    // Add event listeners to entry buttons
    document.querySelectorAll('.btn-entry').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const busId = this.closest('.bus-item').dataset.busId;
            recordEntry(busId);
        });
    });
    
    // Add event listeners to exit buttons
    document.querySelectorAll('.btn-exit').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const logId = this.closest('.log-item').dataset.logId;
            recordExit(logId);
        });
    });
    
    // Add event listeners to complete buttons
    document.querySelectorAll('.btn-complete').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const logId = this.closest('.log-item').dataset.logId;
            completeLog(logId);
        });
    });
    
    // Add event listeners to delete buttons
    document.querySelectorAll('.btn-delete-log').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const logId = this.closest('.log-item').dataset.logId;
            confirmDeleteLog(logId);
        });
    });
}

// Initialize Student Logs functionality
function initStudentLogs() {
    // Only run on student logs page
    if (!document.querySelector('.student-logs-container')) return;
    
    // Add event listeners to bus sidebar items
    document.querySelectorAll('.bus-sidebar-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const busId = this.dataset.busId;
            selectBus(busId, this);
        });
    });
    
    // Add event listeners to delete scan buttons
    document.querySelectorAll('.btn-delete-scan').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const scanId = this.dataset.scanId;
            const row = this.closest('tr');
            confirmDeleteScan(scanId, row);
        });
    });
    
    // Add submit scans button
    const submitBtn = document.getElementById('submitScansBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitScans();
        });
    }
    
    // Add clear session button
    const clearBtn = document.getElementById('clearSessionBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function(e) {
            e.preventDefault();
            clearSession();
        });
    }
}

// Load today's permanent scans
function loadTodayScans() {
    fetch('/api/security/today-scans')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePermanentScansTable(data.scans);
            }
        })
        .catch(error => console.error('Error loading today scans:', error));
}

// Update permanent scans table
function updatePermanentScansTable(scans) {
    const tbody = document.getElementById('permanentScansTableBody');
    const countSpan = document.getElementById('permanentScanCount');
    
    if (!tbody) return;
    
    if (countSpan) {
        countSpan.textContent = scans.length;
    }
    
    if (scans.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="no-scans">
                    <i class="fas fa-history"></i>
                    <p>No submitted scans for today</p>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    scans.forEach(scan => {
        html += `
            <tr>
                <td><strong>${scan.student_id}</strong></td>
                <td>${scan.student_name}</td>
                <td>${scan.branch}</td>
                <td>
                    <span class="residence-badge-small ${scan.residence}">
                        ${scan.residence === 'day_scholar' ? 'Day Scholar' : 'Hosteller'}
                    </span>
                </td>
                <td>${scan.bus_number}</td>
                <td>${scan.scan_time}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// Record bus entry
function recordEntry(busId) {
    fetch(`/security/bus/entry/${busId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        showNotification('Network error. Please try again.', 'error');
        console.error('Error:', error);
    });
}

// Record bus exit
function recordExit(logId) {
    fetch(`/security/bus/exit/${logId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        showNotification('Network error. Please try again.', 'error');
        console.error('Error:', error);
    });
}

// Complete bus log
function completeLog(logId) {
    fetch(`/security/bus/complete/${logId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        showNotification('Network error. Please try again.', 'error');
        console.error('Error:', error);
    });
}

// Confirm delete log
function confirmDeleteLog(logId) {
    currentLogId = logId;
    showDeleteConfirmation(
        'Are you sure you want to delete this bus log?',
        function() {
            fetch(`/security/bus/delete/${currentLogId}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification(data.error, 'error');
                }
            })
            .catch(error => {
                showNotification('Network error. Please try again.', 'error');
                console.error('Error:', error);
            })
            .finally(() => {
                closeModal();
            });
        }
    );
}

// Select bus for scanning
function selectBus(busId, element) {
    selectedBusId = busId;
    
    // Update UI
    document.querySelectorAll('.bus-sidebar-item').forEach(item => {
        item.classList.remove('active');
    });
    element.classList.add('active');
    
    // Get bus name
    const busName = element.querySelector('h4').textContent;
    const selectedBusName = document.getElementById('selectedBusName');
    const selectedBusInfo = document.getElementById('selectedBusInfo');
    
    if (selectedBusName) selectedBusName.textContent = busName;
    if (selectedBusInfo) selectedBusInfo.style.display = 'block';
    
    // Enable scan button
    const scanBtn = document.getElementById('scanButton');
    if (scanBtn) {
        scanBtn.href = `/security/scan/${busId}`;
        scanBtn.style.pointerEvents = 'auto';
        scanBtn.style.opacity = '1';
    }
}

// Confirm delete scan
function confirmDeleteScan(scanId, row) {
    currentScanId = scanId;
    showDeleteConfirmation(
        'Are you sure you want to delete this scan?',
        function() {
            fetch(`/api/security/delete-scan/${currentScanId}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    // Remove the row
                    if (row) row.remove();
                    updateScanCount();
                } else {
                    showNotification(data.error, 'error');
                }
            })
            .catch(error => {
                showNotification('Network error. Please try again.', 'error');
                console.error('Error:', error);
            })
            .finally(() => {
                closeModal();
            });
        }
    );
}

// Update scan count
function updateScanCount() {
    const rows = document.querySelectorAll('#scansTableBody tr:not(.no-scans)').length;
    const scanCount = document.getElementById('scanCount');
    if (scanCount) scanCount.textContent = rows;
    
    // Enable/disable buttons based on scan count
    const submitBtn = document.getElementById('submitScansBtn');
    const clearBtn = document.getElementById('clearSessionBtn');
    
    if (rows === 0) {
        if (submitBtn) {
            submitBtn.disabled = true;
        }
        if (clearBtn) {
            clearBtn.disabled = true;
        }
        
        // Show no scans message if table is empty
        const tbody = document.getElementById('scansTableBody');
        if (tbody && tbody.children.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="no-scans">
                        <i class="fas fa-qrcode"></i>
                        <p>No scans in current session. Select a bus and start scanning.</p>
                    </td>
                </tr>
            `;
        }
    } else {
        if (submitBtn) {
            submitBtn.disabled = false;
        }
        if (clearBtn) {
            clearBtn.disabled = false;
        }
    }
}

// Clear current session
function clearSession() {
    showDeleteConfirmation(
        'Are you sure you want to clear all scans from this session?',
        function() {
            fetch('/api/security/clear-session', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    // Clear the table
                    const tbody = document.getElementById('scansTableBody');
                    if (tbody) {
                        tbody.innerHTML = `
                            <tr>
                                <td colspan="7" class="no-scans">
                                    <i class="fas fa-qrcode"></i>
                                    <p>No scans in current session. Select a bus and start scanning.</p>
                                </td>
                            </tr>
                        `;
                    }
                    updateScanCount();
                    closeModal();
                } else {
                    showNotification(data.error, 'error');
                }
            })
            .catch(error => {
                showNotification('Network error. Please try again.', 'error');
                console.error('Error:', error);
            });
        }
    );
}

// Submit all scans
function submitScans() {
    showDeleteConfirmation(
        'Are you sure you want to submit all scans to the permanent database?',
        function() {
            fetch('/api/security/submit-scans', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    // Clear the table
                    const tbody = document.getElementById('scansTableBody');
                    if (tbody) {
                        tbody.innerHTML = `
                            <tr>
                                <td colspan="7" class="no-scans">
                                    <i class="fas fa-qrcode"></i>
                                    <p>No scans in current session. Select a bus and start scanning.</p>
                                </td>
                            </tr>
                        `;
                    }
                    updateScanCount();
                    // Reload today's scans
                    loadTodayScans();
                    closeModal();
                } else {
                    showNotification(data.error || 'Error submitting scans', 'error');
                }
            })
            .catch(error => {
                showNotification('Network error. Please try again.', 'error');
                console.error('Error:', error);
            });
        }
    );
}

// ======================
// SECURITY SCANNER FUNCTIONS
// ======================

// Initialize scanner specific functionality
function initSecurityScanner() {
    // Only run on scanner page
    if (!document.querySelector('.scanner-minimal')) return;
    
    // Override the scanner's sendToBackend function
    if (typeof window.sendToBackend === 'undefined') {
        window.sendToBackend = function(result) {
            const busId = document.getElementById('busId')?.value;
            
            if (!busId) {
                showNotification('Bus ID not found', 'error');
                return;
            }
            
            // Send to security-specific API
            fetch('/api/security/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    student_id: result.text,
                    bus_id: busId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success with student details
                    showStudentDetails(data.student);
                    // Add to results with enhanced details
                    addEnhancedScanResult(data.student);
                } else {
                    // Show error
                    showNotification(data.error || 'Scan failed', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Network error. Please try again.', 'error');
            });
        };
    }
}

// Show student details in success message
function showStudentDetails(student) {
    const detailsDiv = document.createElement('div');
    detailsDiv.className = 'student-details';
    detailsDiv.innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Name:</span>
            <span class="detail-value">${student.name}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">ID:</span>
            <span class="detail-value">${student.id}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Branch:</span>
            <span class="detail-value">${student.branch}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Residence:</span>
            <span class="detail-value"><span class="residence-badge-small ${student.residence}">${student.residence === 'day_scholar' ? 'Day Scholar' : 'Hosteller'}</span></span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Time:</span>
            <span class="detail-value">${student.time}</span>
        </div>
    `;
    
    // Show temporary success message with details
    const successMsg = document.createElement('div');
    successMsg.className = 'success-message';
    successMsg.innerHTML = `
        <i class="fas fa-check-circle" style="font-size: 2.5rem; margin-bottom: 15px;"></i>
        <div style="font-size: 1.4rem; font-weight: 700; margin-bottom: 10px;">✓ Student Scanned</div>
        ${detailsDiv.outerHTML}
    `;
    
    const viewport = document.querySelector('.scanner-viewport');
    if (viewport) {
        viewport.appendChild(successMsg);
        
        setTimeout(() => {
            if (successMsg.parentNode) {
                successMsg.remove();
            }
        }, 3500);
    }
}

// Add enhanced scan result to list
function addEnhancedScanResult(student) {
    const resultsList = document.getElementById('resultsList');
    if (!resultsList) return;
    
    const noResults = resultsList.querySelector('.no-results');
    if (noResults) noResults.remove();
    
    // Get first letter for avatar
    const firstLetter = student.name.charAt(0).toUpperCase();
    
    const resultItem = document.createElement('div');
    resultItem.className = 'result-item-minimal';
    resultItem.innerHTML = `
        <div class="result-header">
            <div class="student-avatar">${firstLetter}</div>
            <div class="student-main-info">
                <div class="student-name">${student.name}</div>
                <div class="student-id">${student.id}</div>
            </div>
        </div>
        
        <div class="student-details-grid">
            <div class="detail-chip branch-chip">
                <i class="fas fa-code-branch"></i>
                <span>${student.branch}</span>
            </div>
            <div class="detail-chip residence-chip ${student.residence}">
                <i class="fas ${student.residence === 'day_scholar' ? 'fa-sun' : 'fa-moon'}"></i>
                <span>${student.residence === 'day_scholar' ? 'Day Scholar' : 'Hosteller'}</span>
            </div>
        </div>
        
        <div class="detail-chip" style="background: rgba(0,188,212,0.1); width: fit-content;">
            <i class="fas fa-bus"></i>
            <span>Bus: ${student.bus}</span>
        </div>
        
        <div class="scan-time">
            <i class="far fa-clock"></i>
            <span>Scanned at ${student.time}</span>
        </div>
    `;
    
    resultsList.prepend(resultItem);
    
    // Update scan count
    const scanCount = document.getElementById('scanCount');
    if (scanCount) {
        scanCount.textContent = parseInt(scanCount.textContent) + 1;
        scanCount.style.animation = 'none';
        setTimeout(() => {
            scanCount.style.animation = 'pulse 0.5s';
        }, 10);
    }
    
    // Update last scan time
    const lastScanTime = document.getElementById('lastScanTime');
    if (lastScanTime) {
        lastScanTime.innerHTML = `<i class="far fa-clock"></i> ${student.time}`;
    }
}

// ======================
// MODAL FUNCTIONS - FIXED POSITIONING
// ======================

// Show delete confirmation modal
function showDeleteConfirmation(message, callback) {
    const modal = document.getElementById('deleteConfirmModal');
    const messageEl = document.getElementById('deleteConfirmMessage');
    
    if (!modal || !messageEl) return;
    
    console.log('Showing delete confirmation modal'); // Debug log
    
    messageEl.textContent = message;
    deleteCallback = callback;
    
    modal.classList.add('active');
    modal.style.display = 'flex'; // Ensure flex display for centering
    
    // Prevent body scrolling when modal is open
    document.body.style.overflow = 'hidden';
}

// Initialize modals
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

// Close modal
function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
        modal.style.display = 'none';
    });
    deleteCallback = null;
    currentLogId = null;
    currentScanId = null;
    
    // Restore body scrolling
    document.body.style.overflow = '';
}

// ======================
// NOTIFICATION FUNCTIONS
// ======================

// Initialize flash messages
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            hideFlashMessage(message);
        }, 3000);
        
        message.addEventListener('click', () => {
            hideFlashMessage(message);
        });
    });
}

// Hide flash message
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

// Show notification
function showNotification(message, type = 'info') {
    // Create container if it doesn't exist
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }
    
    const notification = document.createElement('div');
    notification.className = `flash-message ${type}`;
    
    const icon = getIconForType(type);
    notification.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        hideFlashMessage(notification);
    }, 3000);
    
    notification.addEventListener('click', () => {
        hideFlashMessage(notification);
    });
}

// Get icon for notification type
function getIconForType(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
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