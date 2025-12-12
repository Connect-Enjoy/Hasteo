// Security Dashboard JavaScript

// Global variables
let scanner = null;
let currentScanType = 'entry';
let batchCounter = 0;
let isScanning = false;

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Setup scanner if on scan page
    if (document.getElementById('preview')) {
        initScanner();
    }
    
    // Load data for specific pages
    if (window.location.pathname.includes('/security/history')) {
        loadAttendanceHistory();
    }
    
    if (window.location.pathname.includes('/security/bus-logs')) {
        loadBusTimestamps();
    }
    
    // Setup event listeners
    setupSecurityEventListeners();
});

// Initialize barcode scanner
function initScanner() {
    if (!('Instascan' in window)) {
        showNotification('Scanner library not loaded. Please refresh.', 'error');
        return;
    }
    
    Instascan.Camera.getCameras().then(function(cameras) {
        if (cameras.length > 0) {
            scanner = new Instascan.Scanner({
                video: document.getElementById('preview'),
                mirror: false,
                backgroundScan: true,
                refractoryPeriod: 1000,
                scanPeriod: 3
            });
            
            scanner.addListener('scan', function(content) {
                if (!isScanning) {
                    isScanning = true;
                    handleBarcodeScan(content);
                    setTimeout(() => { isScanning = false; }, 1000);
                }
            });
            
            // Start with back camera if available
            const backCamera = cameras.find(c => c.name.toLowerCase().includes('back'));
            const selectedCamera = backCamera || cameras[0];
            
            scanner.start(selectedCamera).then(() => {
                console.log('Scanner started with camera:', selectedCamera.name);
                updateScanStatus(true);
            }).catch(function(e) {
                console.error('Camera error:', e);
                showNotification('Camera access failed. Please check permissions.', 'error');
                updateScanStatus(false);
            });
        } else {
            showNotification('No cameras found on this device.', 'error');
            updateScanStatus(false);
        }
    }).catch(function(e) {
        console.error('Camera error:', e);
        showNotification('Cannot access camera. Please check permissions.', 'error');
        updateScanStatus(false);
    });
}

// Update scan status
function updateScanStatus(isActive) {
    const statusElement = document.getElementById('scanStatus');
    if (statusElement) {
        if (isActive) {
            statusElement.className = 'scan-status';
            statusElement.innerHTML = '<i class="fas fa-check-circle"></i> Scanner Ready';
        } else {
            statusElement.className = 'scan-status offline';
            statusElement.innerHTML = '<i class="fas fa-times-circle"></i> Scanner Offline';
        }
    }
}

// Set scan type
function setScanType(type) {
    currentScanType = type;
    
    // Update UI
    document.querySelectorAll('.scan-type-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(type)) {
            btn.classList.add('active');
        }
    });
    
    // Update manual scan button
    const manualBtn = document.querySelector('#manualScanBtn');
    if (manualBtn) {
        manualBtn.innerHTML = `<i class="fas fa-check"></i> Record ${type.charAt(0).toUpperCase() + type.slice(1)}`;
    }
}

// Handle barcode scan
async function handleBarcodeScan(registerNo) {
    const busNo = document.getElementById('busNo')?.value;
    
    if (!busNo) {
        showNotification('Please select bus number first', 'warning');
        return;
    }
    
    // Validate registration number format
    if (!registerNo || !registerNo.includes('/') || registerNo.split('/').length !== 3) {
        showNotification('Invalid format. Expected: COURSE/ID/YEAR', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                register_no: registerNo,
                bus_no: busNo,
                scan_type: currentScanType
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Increment batch counter
            batchCounter++;
            updateBatchCounter();
            
            // Show success notification
            const studentName = result.data?.name || 'Student';
            showNotification(`${studentName} - ${currentScanType.toUpperCase()} recorded`, 'success');
            
            // Play success sound
            playScanSound();
            
            // Vibrate if supported
            vibrate([200]);
            
            // Add visual feedback
            addScanSuccessEffect();
            
        } else {
            showNotification(result.error, 'error');
            vibrate([100, 50, 100]); // Error vibration pattern
        }
    } catch (error) {
        showNotification('Scan failed. Check connection.', 'error');
        vibrate([100, 50, 100]); // Error vibration pattern
        
        // Save scan offline if network error
        if (error.message.includes('Network')) {
            saveScanOffline(registerNo, busNo, currentScanType);
        }
    }
}

// Add visual success effect
function addScanSuccessEffect() {
    const scannerContainer = document.querySelector('.scanner-video-container');
    if (scannerContainer) {
        scannerContainer.classList.add('scan-success');
        setTimeout(() => {
            scannerContainer.classList.remove('scan-success');
        }, 300);
    }
}

// Save scan offline
function saveScanOffline(registerNo, busNo, scanType) {
    const offlineScan = {
        register_no: registerNo,
        bus_no: busNo,
        scan_type: scanType,
        timestamp: new Date().toISOString()
    };
    
    // Save to localStorage for offline sync
    let offlineScans = JSON.parse(localStorage.getItem('hasteo_offline_scans') || '[]');
    offlineScans.push(offlineScan);
    localStorage.setItem('hasteo_offline_scans', JSON.stringify(offlineScans));
    
    showNotification('Scan saved offline. Will sync when online.', 'warning');
}

// Sync offline scans
async function syncOfflineScans() {
    let offlineScans = JSON.parse(localStorage.getItem('hasteo_offline_scans') || '[]');
    
    if (offlineScans.length === 0) return;
    
    for (const scan of offlineScans) {
        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(scan)
            });
            
            if (response.ok) {
                // Remove from offline storage
                offlineScans = offlineScans.filter(s => s !== scan);
                localStorage.setItem('hasteo_offline_scans', JSON.stringify(offlineScans));
                console.log('Synced offline scan:', scan.register_no);
            }
        } catch (error) {
            console.log('Failed to sync offline scan:', scan.register_no);
        }
    }
    
    if (offlineScans.length === 0) {
        showNotification('All offline scans synced successfully', 'success');
    }
}

// Manual scan
async function manualScan() {
    const registerNo = document.getElementById('manualRegisterNo')?.value.trim();
    if (!registerNo) {
        showNotification('Enter registration number', 'warning');
        return;
    }
    
    // Validate format
    if (!registerNo.includes('/') || registerNo.split('/').length !== 3) {
        showNotification('Invalid format. Use: COURSE/ID/YEAR', 'error');
        return;
    }
    
    const busNo = document.getElementById('busNo')?.value;
    if (!busNo) {
        showNotification('Select bus number first', 'warning');
        return;
    }
    
    await handleBarcodeScan(registerNo);
    document.getElementById('manualRegisterNo').value = '';
    document.getElementById('manualRegisterNo').focus();
}

// Update batch counter
function updateBatchCounter() {
    const counter = document.getElementById('batchCounter');
    const count = document.getElementById('batchCount');
    
    if (counter && count) {
        counter.style.display = 'flex';
        count.textContent = batchCounter;
        
        // Auto-hide after 5 seconds of inactivity
        clearTimeout(window.batchCounterTimeout);
        window.batchCounterTimeout = setTimeout(() => {
            counter.style.display = 'none';
        }, 5000);
    }
}

// Reset batch counter
function resetBatchCounter() {
    batchCounter = 0;
    const counter = document.getElementById('batchCounter');
    if (counter) {
        counter.style.display = 'none';
    }
}

// Record bus timestamp
async function recordBusTimestamp(timestampType) {
    const busNo = document.getElementById('busNo')?.value;
    
    if (!busNo) {
        showNotification('Select bus number first', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/bus/timestamp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bus_no: busNo,
                timestamp_type: timestampType
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(result.message, 'success');
            vibrate([100]);
            
            // Refresh bus timestamps if on that page
            if (window.location.pathname.includes('/security/bus-logs')) {
                loadBusTimestamps();
            }
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to record timestamp', 'error');
    }
}

// Load attendance history
async function loadAttendanceHistory() {
    try {
        const response = await fetch('/api/attendance?limit=50');
        const history = await response.json();
        
        const container = document.getElementById('attendanceHistory');
        if (!container) return;
        
        if (!response.ok) {
            container.innerHTML = `<div class="empty-state">${history.error || 'Failed to load'}</div>`;
            return;
        }
        
        if (history.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h3>No scan history</h3>
                    <p>Start scanning to see records here</p>
                </div>
            `;
            return;
        }
        
        const tableHTML = `
            <div class="table-responsive">
                <table class="table" id="attendanceTable">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Student</th>
                            <th>Reg No</th>
                            <th>Bus</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${history.map(record => `
                            <tr>
                                <td class="time-cell">${formatTime(record.timestamp)}</td>
                                <td>${record.student_name || 'N/A'}</td>
                                <td class="reg-no-cell">${record.register_no}</td>
                                <td>${record.bus_no}</td>
                                <td><span class="badge ${record.scan_type === 'entry' ? 'badge-success' : 'badge-info'}">${record.scan_type.toUpperCase()}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        
    } catch (error) {
        const container = document.getElementById('attendanceHistory');
        if (container) {
            container.innerHTML = `<div class="empty-state">Failed to load</div>`;
        }
    }
}

// Load bus timestamps
async function loadBusTimestamps() {
    try {
        const response = await fetch('/api/bus/timestamps?limit=30');
        const timestamps = await response.json();
        
        const container = document.getElementById('busTimestamps');
        if (!container) return;
        
        if (!response.ok) {
            container.innerHTML = `<div class="empty-state">${timestamps.error || 'Failed to load'}</div>`;
            return;
        }
        
        if (timestamps.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bus"></i>
                    <h3>No bus logs</h3>
                    <p>Record bus arrivals/departures to see logs</p>
                </div>
            `;
            return;
        }
        
        const tableHTML = `
            <div class="table-responsive">
                <table class="table" id="busLogsTable">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Bus No</th>
                            <th>Type</th>
                            <th>Location</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${timestamps.map(record => `
                            <tr>
                                <td class="timestamp-cell">${formatTime(record.timestamp)}</td>
                                <td class="bus-no-cell">${record.bus_no}</td>
                                <td><span class="badge ${record.timestamp_type === 'arrival' ? 'badge-success' : 'badge-info'}">${record.timestamp_type.toUpperCase()}</span></td>
                                <td>${record.location}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        
    } catch (error) {
        const container = document.getElementById('busTimestamps');
        if (container) {
            container.innerHTML = `<div class="empty-state">Failed to load</div>`;
        }
    }
}

// Refresh data
function refreshData() {
    if (window.location.pathname.includes('/security/history')) {
        loadAttendanceHistory();
        showNotification('Attendance history refreshed', 'success');
    } else if (window.location.pathname.includes('/security/bus-logs')) {
        loadBusTimestamps();
        showNotification('Bus logs refreshed', 'success');
    }
}

// Setup security event listeners
function setupSecurityEventListeners() {
    // Manual scan input
    const manualInput = document.getElementById('manualRegisterNo');
    if (manualInput) {
        manualInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                manualScan();
            }
        });
    }
    
    // Manual scan button
    const manualScanBtn = document.getElementById('manualScanBtn');
    if (manualScanBtn) {
        manualScanBtn.addEventListener('click', manualScan);
    }
    
    // Refresh buttons
    document.querySelectorAll('.refresh-btn').forEach(btn => {
        btn.addEventListener('click', refreshData);
    });
    
    // Sync offline scans when online
    window.addEventListener('online', function() {
        syncOfflineScans();
    });
}

// Export functions for global use
window.handleBarcodeScan = handleBarcodeScan;
window.manualScan = manualScan;
window.setScanType = setScanType;
window.recordBusTimestamp = recordBusTimestamp;
window.resetBatchCounter = resetBatchCounter;
window.refreshData = refreshData;