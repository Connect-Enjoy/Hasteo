// Student ID Barcode Scanner with QuaggaJS - Hasteo Project

document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.scanner-minimal')) return;
    
    // Global variables
    let scanning = false;
    let lastScanned = '';
    let lastScanTimeValue = 0;
    let scanResults = [];
    let scannedIDs = new Set();
    let scannerStatus, resultsList, scanCount, lastScanTime;
    let isDesktop = false;
    
    initializeScanner();
    
    async function initializeScanner() {
        scannerStatus = document.getElementById('scannerStatus');
        resultsList = document.getElementById('resultsList');
        scanCount = document.getElementById('scanCount');
        lastScanTime = document.getElementById('lastScanTime');
        
        // Setup initial UI
        updateStatus('Initializing scanner...', 'info');
        updateResultsList();
        
        // Initialize scanner
        await initScanner();
    }
    
    async function initScanner() {
        try {
            updateStatus('Starting camera...', 'info');
            
            // Check if QuaggaJS is loaded
            if (typeof Quagga === 'undefined') {
                throw new Error('Scanner library not loaded.');
            }
            
            // Detect device type
            isDesktop = !/Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
            
            // Get camera wrapper
            const cameraWrapper = document.querySelector('.camera-wrapper');
            if (!cameraWrapper) {
                throw new Error('Camera wrapper not found');
            }
            
            // Clear any existing video
            const scannerContainer = document.getElementById('scannerContainer');
            scannerContainer.innerHTML = '';
            
            // Show camera wrapper
            cameraWrapper.style.display = 'block';
            
            // Hide placeholder
            const placeholder = document.querySelector('.camera-placeholder');
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            // SIMPLIFIED CONFIGURATION - FIXED for visibility
            const config = {
                inputStream: {
                    name: 'Live',
                    type: 'LiveStream',
                    target: scannerContainer,
                    constraints: {
                        ...(isDesktop ? { facingMode: 'user' } : { facingMode: 'environment' }),
                        width: { min: 320, ideal: 640, max: 1280 },
                        height: { min: 240, ideal: 480, max: 720 },
                        frameRate: { ideal: 30, max: 60 }
                    }
                },
                locator: {
                    patchSize: 'medium',
                    halfSample: true
                },
                numOfWorkers: 1, // Use only 1 worker for stability
                frequency: 10,
                decoder: {
                    readers: [
                        'code_128_reader',
                        'code_39_reader',
                        'i2of5_reader'
                    ]
                },
                locate: true
            };
            
            // Initialize Quagga
            Quagga.init(config, function(err) {
                if (err) {
                    handleQuaggaError(err);
                    return;
                }
                
                updateStatus('Ready - Align student ID within frame', 'success');
                
                scanning = true;
                Quagga.start();
                Quagga.onDetected(onDetected);
                
                // Force video to be visible
                setTimeout(() => {
                    const videoElement = scannerContainer.querySelector('video');
                    if (videoElement) {
                        videoElement.style.opacity = '1';
                        videoElement.style.visibility = 'visible';
                        videoElement.style.display = 'block';
                        videoElement.style.width = '100%';
                        videoElement.style.height = '100%';
                        videoElement.style.objectFit = 'cover';
                    }
                }, 100);
                
                // Add scanning animation
                addScanningAnimation();
                
                // Add scanning tips
                setTimeout(() => {
                    updateStatus('Hold student ID steady within frame', 'info');
                }, 3000);
            });
            
        } catch (error) {
            console.error('Scanner init error:', error);
            updateStatus('Failed to start scanner', 'error');
            
            // Show error in placeholder
            const placeholder = document.querySelector('.camera-placeholder');
            if (placeholder) {
                placeholder.style.display = 'flex';
                placeholder.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to start camera<br><small>${error.message || 'Unknown error'}</small></p>
                `;
            }
        }
    }
    
    function addScanningAnimation() {
        // Remove existing scan line if any
        const existingLine = document.querySelector('.scan-line');
        if (existingLine) existingLine.remove();
        
        // Create new scan line
        const scanLine = document.createElement('div');
        scanLine.className = 'scan-line';
        document.querySelector('.scan-frame-overlay').appendChild(scanLine);
    }
    
    function onDetected(result) {
        const now = Date.now();
        const rawCode = result.codeResult.code;
        
        // Validate student ID format
        if (!isValidStudentID(rawCode)) {
            showInvalidFormatWarning(rawCode);
            return;
        }
        
        // Extract clean student ID
        const studentID = cleanStudentID(rawCode);
        
        // Prevent duplicate scans within 3 seconds (same ID)
        if (studentID === lastScanned && (now - lastScanTimeValue) < 3000) {
            return;
        }
        
        // Check if this ID has already been scanned
        if (scannedIDs.has(studentID)) {
            showDuplicateWarning(studentID);
            return;
        }
        
        // Add to scanned IDs set
        scannedIDs.add(studentID);
        lastScanned = studentID;
        lastScanTimeValue = now;
        
        // Process the valid student ID
        addScanResult(studentID, result.codeResult.format);
        updateScanCount();
        updateLastScanTime();
        playScanSound();
        animateScanSuccess();
        showScanSuccess(studentID);
    }
    
    // Validate Student ID Format: S[2 letters]/[5 digits]/[2 digits]
    function isValidStudentID(code) {
        if (!code || typeof code !== 'string') return false;
        
        // Clean the code first
        const cleanCode = code.trim().toUpperCase();
        
        // Exact pattern: S + 2 letters + / + 5 digits + / + 2 digits
        const pattern = /^S(AU|CE|CV|CS|EE|CO|CT|EC|EV|ME)\/\d{5}\/\d{2}$/;
        
        return pattern.test(cleanCode);
    }
    
    // Clean and standardize student ID
    function cleanStudentID(code) {
        return code.trim().toUpperCase();
    }
    
    // Get complete branch information
    function getBranchInfo(branchCode) {
        const branches = {
            'AU': {
                name: 'Automobile Engineering',
                class: 'branch-au',
                color: '#E91E63',
                icon: 'fa-car'
            },
            'CE': {
                name: 'Civil Engineering',
                class: 'branch-ce',
                color: '#009688',
                icon: 'fa-building'
            },
            'CV': {
                name: 'Civil & Environmental Engineering',
                class: 'branch-cv',
                color: '#795548',
                icon: 'fa-tree'
            },
            'CS': {
                name: 'Computer Science & Engineering',
                class: 'branch-cs',
                color: '#2196F3',
                icon: 'fa-laptop-code'
            },
            'EE': {
                name: 'Electrical & Electronics Engineering',
                class: 'branch-ee',
                color: '#FF9800',
                icon: 'fa-bolt'
            },
            'CO': {
                name: 'Computer Science & Engineering (Data Science)',
                class: 'branch-co',
                color: '#673AB7',
                icon: 'fa-chart-line'
            },
            'CT': {
                name: 'Computer Science & Engineering (AI)',
                class: 'branch-ct',
                color: '#9C27B0',
                icon: 'fa-robot'
            },
            'EC': {
                name: 'Electronics & Communication Engineering',
                class: 'branch-ec',
                color: '#4CAF50',
                icon: 'fa-satellite-dish'
            },
            'EV': {
                name: 'Electronics & Communication Engineering (VLSI)',
                class: 'branch-ev',
                color: '#FF5722',
                icon: 'fa-microchip'
            },
            'ME': {
                name: 'Mechanical Engineering',
                class: 'branch-me',
                color: '#F44336',
                icon: 'fa-cogs'
            }
        };
        
        return branches[branchCode] || {
            name: `${branchCode} Branch`,
            class: 'branch-cs',
            color: '#2196F3',
            icon: 'fa-graduation-cap'
        };
    }
    
    // Get branch name from code
    function getBranchName(branchCode) {
        return getBranchInfo(branchCode).name;
    }
    
    // Get branch CSS class
    function getBranchClass(branchCode) {
        return getBranchInfo(branchCode).class;
    }
    
    // Show warning for invalid format
    function showInvalidFormatWarning(rawCode) {
        updateStatus('Invalid student ID format', 'warning');
        
        // Visual feedback
        const scanFrame = document.querySelector('.scan-frame-overlay');
        if (scanFrame) {
            scanFrame.style.borderColor = '#F44336';
            scanFrame.style.animation = 'scanSuccess 0.8s ease';
            setTimeout(() => {
                scanFrame.style.borderColor = '#9C27B0';
                scanFrame.style.animation = '';
            }, 800);
        }
        
        // Play error sound
        playErrorSound();
    }
    
    // Show warning for duplicate scan
    function showDuplicateWarning(studentID) {
        updateStatus('Already scanned', 'warning');
        
        // Visual feedback
        const scanFrame = document.querySelector('.scan-frame-overlay');
        if (scanFrame) {
            scanFrame.style.borderColor = '#FF9800';
            scanFrame.style.animation = 'scanSuccess 0.8s ease';
            setTimeout(() => {
                scanFrame.style.borderColor = '#9C27B0';
                scanFrame.style.animation = '';
            }, 800);
        }
        
        playDuplicateSound();
    }
    
    // Show success message
    function showScanSuccess(studentID) {
        updateStatus(`✓ ${studentID}`, 'success');
        
        // Show detailed success message
        setTimeout(() => {
            updateStatus('Ready for next scan', 'info');
        }, 1500);
        
        // Show temporary success message
        showTemporarySuccess(studentID);
    }
    
    // Show temporary success overlay
    function showTemporarySuccess(studentID) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = `
            <i class="fas fa-check-circle" style="font-size: 2rem; margin-bottom: 10px;"></i>
            <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 5px;">Scanned</div>
            <div style="font-size: 1rem; opacity: 0.9;">
                ${studentID}
            </div>
        `;
        
        document.querySelector('.scanner-viewport').appendChild(successDiv);
        
        // Remove after animation
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 2000);
    }
    
    function addScanResult(code, format) {
        const [branchCode, studentNumber, year] = code.split('/');
        const cleanBranchCode = branchCode.substring(1);
        const branchInfo = getBranchInfo(cleanBranchCode);
        
        const result = {
            text: code,
            format: format,
            type: {
                name: 'Student ID',
                icon: 'fa-id-card',
                color: '#9C27B0'
            },
            details: {
                branch: branchInfo.name,
                branchCode: cleanBranchCode,
                branchClass: branchInfo.class,
                branchIcon: branchInfo.icon,
                studentNumber: studentNumber,
                year: `20${year}`,
                shortYear: year
            },
            time: new Date(),
            id: Date.now()
        };
        
        scanResults.unshift(result);
        
        // Keep only last 10 scans
        if (scanResults.length > 10) {
            const removed = scanResults.pop();
            scannedIDs.delete(removed.text);
        }
        
        updateResultsList();
        
        // Send to backend
        sendToBackend(result);
    }
    
    function sendToBackend(result) {
        // Implement backend API call here
        console.log('Student ID scanned:', result);
    }
    
    function updateResultsList() {
        if (scanResults.length === 0) {
            resultsList.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-id-card"></i>
                    <p>Align student ID within frame</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        scanResults.forEach(result => {
            const timeString = result.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const dateString = result.time.toLocaleDateString();
            
            html += `
                <div class="result-item-minimal">
                    <div class="result-type-minimal" style="background: ${result.type.color}15; color: ${result.type.color};">
                        <i class="fas ${result.type.icon}"></i> ${result.type.name}
                    </div>
                    <div class="result-content-minimal">
                        <div class="result-text">${result.text}</div>
                        <div style="margin-top: 10px;">
                            <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                                <span class="${result.details.branchClass} branch-badge">
                                    <i class="fas ${result.details.branchIcon}"></i> ${result.details.branch}
                                </span>
                                <span style="background: rgba(0, 0, 0, 0.08); color: #555; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem;">
                                    <i class="fas fa-hashtag"></i> ${result.details.studentNumber}
                                </span>
                                <span style="background: rgba(0, 150, 136, 0.1); color: #009688; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem;">
                                    <i class="fas fa-calendar-alt"></i> ${result.details.year}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="result-time-minimal">
                        <i class="far fa-clock"></i> ${dateString} ${timeString}
                    </div>
                </div>
            `;
        });
        
        resultsList.innerHTML = html;
        resultsList.scrollTop = 0;
    }
    
    function updateScanCount() {
        scanCount.textContent = scanResults.length;
        scanCount.style.animation = 'none';
        setTimeout(() => {
            scanCount.style.animation = 'pulse 0.5s';
        }, 10);
    }
    
    function updateLastScanTime() {
        const now = new Date();
        lastScanTime.innerHTML = `<i class="far fa-clock"></i> ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
        lastScanTime.style.animation = 'none';
        setTimeout(() => {
            lastScanTime.style.animation = 'pulse 0.5s';
        }, 10);
    }
    
    function updateStatus(message, type = 'info') {
        let icon = 'fa-info-circle';
        let color = '#ffffff';
        
        switch(type) {
            case 'success':
                icon = 'fa-check-circle';
                color = '#4CAF50';
                break;
            case 'error':
                icon = 'fa-exclamation-circle';
                color = '#F44336';
                break;
            case 'warning':
                icon = 'fa-exclamation-triangle';
                color = '#FF9800';
                break;
        }
        
        scannerStatus.innerHTML = `<i class="fas ${icon}" style="color: ${color}"></i> <span>${message}</span>`;
    }
    
    function playScanSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 1200;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.15);
        } catch (e) {
            // Silent fail
        }
    }
    
    function playErrorSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 400;
            oscillator.type = 'sawtooth';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            // Silent fail
        }
    }
    
    function playDuplicateSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(400, audioContext.currentTime + 0.1);
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.05, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (e) {
            // Silent fail
        }
    }
    
    function animateScanSuccess() {
        const scanFrame = document.querySelector('.scan-frame-overlay');
        if (scanFrame) {
            scanFrame.style.borderColor = '#4CAF50';
            scanFrame.style.animation = 'scanSuccess 0.8s ease';
            setTimeout(() => {
                scanFrame.style.borderColor = '#9C27B0';
                scanFrame.style.animation = '';
            }, 800);
        }
    }
    
    function handleQuaggaError(err) {
        console.error('Quagga error:', err);
        let errorMessage = 'Scanner failed to start';
        
        if (err.name === 'NotAllowedError') {
            errorMessage = 'Camera permission denied';
        } else if (err.name === 'NotFoundError') {
            errorMessage = 'No camera found';
        } else if (err.name === 'NotReadableError') {
            errorMessage = 'Camera is in use by another application';
        } else if (err.name === 'OverconstrainedError') {
            errorMessage = 'Camera constraints could not be satisfied';
        } else {
            errorMessage = `Error: ${err.message || 'Unknown error'}`;
        }
        
        updateStatus(errorMessage, 'error');
        
        // Show error in placeholder
        const placeholder = document.querySelector('.camera-placeholder');
        if (placeholder) {
            placeholder.style.display = 'flex';
            placeholder.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <p>${errorMessage}<br><small>Refresh page to try again</small></p>
            `;
        }
        
        // Hide camera wrapper
        const cameraWrapper = document.querySelector('.camera-wrapper');
        if (cameraWrapper) {
            cameraWrapper.style.display = 'none';
        }
    }
    
    // Clean up on page unload
    window.addEventListener('beforeunload', () => {
        if (scanning) {
            Quagga.stop();
            Quagga.offDetected(onDetected);
        }
    });
    
    // Retry function
    window.retryScanner = function() {
        if (scanning) {
            Quagga.stop();
            Quagga.offDetected(onDetected);
            scanning = false;
        }
        
        updateStatus('Retrying camera...', 'info');
        initScanner();
    };
});
