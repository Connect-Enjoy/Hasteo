// security.js - Security Specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initBusEntryButtons();
    initBusExitButtons();
    initBusDeleteButtons();
    initBusSelection();
    initDeleteScanButtons();
    initModals();
    initLogoutConfirmation();
    initScrollBlur();
});

function initScrollBlur() {
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

function initLogoutConfirmation() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    }
}

function initBusEntryButtons() {
    document.querySelectorAll('.btn-record-entry').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            const busId = this.dataset.busId || this.closest('.bus-card')?.dataset.busId;
            if (!busId) return;
            
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            this.disabled = true;
            
            try {
                const response = await fetch(`/security/bus/entry/${busId}`, { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    showNotification(data.message, 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification(data.error, 'error');
                    this.innerHTML = originalText;
                    this.disabled = false;
                }
            } catch (error) {
                showNotification('Network error', 'error');
                this.innerHTML = originalText;
                this.disabled = false;
            }
        });
    });
}

function initBusExitButtons() {
    document.querySelectorAll('.btn-exit-trip').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            const logId = this.dataset.logId || this.closest('.log-card')?.dataset.logId;
            if (!logId) return;
            
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            this.disabled = true;
            
            try {
                const response = await fetch(`/security/bus/exit/${logId}`, { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    showNotification(data.message, 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification(data.error, 'error');
                    this.innerHTML = originalText;
                    this.disabled = false;
                }
            } catch (error) {
                showNotification('Network error', 'error');
                this.innerHTML = originalText;
                this.disabled = false;
            }
        });
    });
}

function initBusDeleteButtons() {
    document.querySelectorAll('.btn-delete-log').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const logId = this.dataset.logId || this.closest('.log-card')?.dataset.logId;
            if (logId) showDeleteModal(logId, 'log');
        });
    });
}

function initBusSelection() {
    document.querySelectorAll('.bus-list-item').forEach(item => {
        item.addEventListener('click', function() {
            const busId = this.dataset.busId;
            const busNumber = this.querySelector('.bus-list-number')?.textContent;
            
            document.querySelectorAll('.bus-list-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            const selectedBusInfo = document.getElementById('selectedBusInfo');
            const selectedBusName = document.getElementById('selectedBusName');
            if (selectedBusInfo && selectedBusName) {
                selectedBusName.textContent = busNumber;
                selectedBusInfo.style.display = 'flex';
            }
            
            const scanBtn = document.getElementById('scanButton');
            if (scanBtn) {
                scanBtn.href = `/security/scan/${busId}`;
                scanBtn.style.pointerEvents = 'auto';
                scanBtn.style.opacity = '1';
            }
            
            loadCurrentScans(busId);
        });
    });
}

async function loadCurrentScans(busId) {
    try {
        const response = await fetch(`/api/security/current-scans?bus_id=${busId}`);
        const data = await response.json();
        
        if (data.success) {
            updateScansTable(data.scans);
        }
    } catch (error) {
        console.error('Error loading scans:', error);
    }
}

function updateScansTable(scans) {
    const tbody = document.getElementById('scansTableBody');
    const countSpan = document.getElementById('currentScanCount');
    
    if (!tbody) return;
    if (countSpan) countSpan.textContent = scans.length;
    
    if (scans.length === 0) {
        tbody.innerHTML = `<tr class="empty-row"><td colspan="6"><div class="empty-state"><i class="fas fa-qrcode"></i><p>No students scanned</p></div></td></tr>`;
        return;
    }
    
    tbody.innerHTML = scans.map(scan => `
        <tr data-scan-id="${scan.id}">
            <td><strong>${scan.student_id}</strong></td>
            <td>${scan.student_name}</td>
            <td>${scan.branch}</td>
            <td><span class="residence-badge ${scan.residence}">${scan.residence === 'day_scholar' ? 'Day Scholar' : 'Hosteller'}</span></td>
            <td>${scan.scan_time}</td>
            <td><button class="delete-scan-btn" data-scan-id="${scan.id}"><i class="fas fa-trash-alt"></i></button></td>
        </tr>
    `).join('');
    
    initDeleteScanButtons();
}

function initDeleteScanButtons() {
    document.querySelectorAll('.delete-scan-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const scanId = this.dataset.scanId;
            if (scanId) showDeleteModal(scanId, 'scan');
        });
    });
}

let pendingDeleteId = null;
let deleteType = null;

function showDeleteModal(id, type) {
    pendingDeleteId = id;
    deleteType = type;
    const modal = document.getElementById('deleteConfirmModal');
    if (modal) modal.classList.add('active');
}

function initModals() {
    const modal = document.getElementById('deleteConfirmModal');
    if (!modal) return;
    
    document.querySelectorAll('.modal-close, .btn-cancel').forEach(btn => {
        btn.addEventListener('click', () => modal.classList.remove('active'));
    });
    
    document.getElementById('confirmDeleteBtn')?.addEventListener('click', async () => {
        if (!pendingDeleteId) return;
        
        const url = deleteType === 'log' ? `/security/bus/delete/${pendingDeleteId}` : `/api/security/delete-scan/${pendingDeleteId}`;
        
        try {
            const response = await fetch(url, { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                showNotification(data.message, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showNotification(data.error, 'error');
            }
        } catch (error) {
            showNotification('Network error', 'error');
        }
        
        modal.classList.remove('active');
        pendingDeleteId = null;
    });
}

function showNotification(message, type = 'info') {
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        const mainContainer = document.querySelector('.security-container');
        if (mainContainer) {
            mainContainer.insertBefore(container, mainContainer.firstChild);
        } else {
            document.body.appendChild(container);
        }
    }
    
    const notification = document.createElement('div');
    notification.className = `flash-message ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    const icon = icons[type] || 'fa-info-circle';
    notification.innerHTML = `<i class="fas ${icon}"></i> ${message}`;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) notification.remove();
        }, 300);
    }, 3000);
    
    notification.addEventListener('click', () => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) notification.remove();
        }, 300);
    });
}