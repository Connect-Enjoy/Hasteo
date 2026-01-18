// 1D Barcode Scanner with QuaggaJS - Laptop Compatible
document.addEventListener('DOMContentLoaded', function() {
    if (!document.querySelector('.scanner-minimal')) return;
    
    initializeScanner();
    
    async function initializeScanner() {
        const videoElement = document.getElementById('scannerVideo');
        const scannerStatus = document.getElementById('scannerStatus');
        const resultsList = document.getElementById('resultsList');
        const scanCount = document.getElementById('scanCount');
        const lastScanTime = document.getElementById('lastScanTime');
        
        let scanning = false;
        let lastScanned = '';
        let lastScanTimeValue = 0;
        let scanResults = [];
        
        initScanner();
        
        async function initScanner() {
            try {
                updateStatus('Initializing scanner...', 'info');
                
                // Check if QuaggaJS is loaded
                if (typeof Quagga === 'undefined') {
                    throw new Error('Scanner library not loaded');
                }
                
                // Detect device type for camera selection
                const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
                const isDesktop = !isMobile;
                
                // Configuration - SIMPLIFIED FOR LAPTOPS
                const config = {
                    inputStream: {
                        name: 'Live',
                        type: 'LiveStream',
                        target: videoElement,
                        constraints: {
                            // CRITICAL FIX: Different constraints for mobile vs desktop
                            facingMode: isMobile ? 'environment' : 'user', // 'user' for laptop front camera
                            width: { min: 640, ideal: 1280, max: 1920 },
                            height: { min: 480, ideal: 720, max: 1080 },
                            frameRate: { ideal: 30, max: 60 }
                        },
                        area: { // Define scan area
                            top: '30%',
                            right: '10%',
                            left: '10%',
                            bottom: '30%'
                        }
                    },
                    locator: {
                        patchSize: 'medium',
                        halfSample: true
                    },
                    numOfWorkers: isDesktop ? 2 : 4, // Fewer workers on desktop
                    frequency: isDesktop ? 5 : 10,   // Slower scan on desktop
                    decoder: {
                        readers: [
                            'ean_reader',
                            'ean_8_reader',
                            'upc_reader',
                            'upc_e_reader',
                            'code_128_reader',
                            'code_39_reader',
                            'codabar_reader',
                            'i2of5_reader'
                        ]
                    },
                    locate: true
                };
                
                updateStatus('Requesting camera access...', 'info');
                
                // Initialize Quagga
                Quagga.init(config, function(err) {
                    if (err) {
                        handleQuaggaError(err, isDesktop);
                        return;
                    }
                    
                    updateStatus(isDesktop ? 
                        'Camera ready - point barcode at camera' : 
                        'Camera ready - point at barcode', 
                        'success'
                    );
                    
                    scanning = true;
                    Quagga.start();
                    Quagga.onDetected(onDetected);
                    
                    // Add device-specific tips
                    if (isDesktop) {
                        setTimeout(() => {
                            updateStatus('Desktop tip: Hold barcode steady about 6-12 inches from camera', 'info');
                        }, 3000);
                    }
                });
                
            } catch (error) {
                handleCameraError(error);
            }
        }
        
        function onDetected(result) {
            const now = Date.now();
            const code = result.codeResult.code;
            
            // Prevent duplicate scans within 1 second
            if (code === lastScanned && (now - lastScanTimeValue) < 1000) {
                return;
            }
            
            lastScanned = code;
            lastScanTimeValue = now;
            
            addScanResult(code, result.codeResult.format);
            updateScanCount();
            updateLastScanTime();
            playScanSound();
            animateScanSuccess();
        }
        
        function addScanResult(code, format) {
            const result = {
                text: code,
                format: format,
                type: getBarcodeType(code),
                time: new Date(),
                id: Date.now()
            };
            
            scanResults.unshift(result);
            if (scanResults.length > 10) {
                scanResults.pop();
            }
            
            updateResultsList();
        }
        
        function getBarcodeType(code) {
            if (/^\d{12,13}$/.test(code)) {
                return { name: 'EAN-13', icon: 'fa-barcode', color: '#FF6347' };
            } else if (/^\d{8}$/.test(code)) {
                return { name: 'EAN-8', icon: 'fa-barcode', color: '#FF8C42' };
            } else if (/^\d{6,12}$/.test(code)) {
                return { name: 'UPC', icon: 'fa-barcode', color: '#FFB347' };
            } else if (/^\d{9}$/.test(code)) {
                return { name: 'Student ID', icon: 'fa-id-card', color: '#9C27B0' };
            } else if (/^[A-Z0-9]{10,}$/i.test(code)) {
                return { name: 'Code 128/39', icon: 'fa-barcode', color: '#4CAF50' };
            } else {
                return { name: '1D Barcode', icon: 'fa-barcode', color: '#607D8B' };
            }
        }
        
        function handleQuaggaError(err, isDesktop) {
            console.error('Quagga error:', err);
            let errorMessage = 'Scanner error';
            
            if (err.name === 'NotAllowedError') {
                errorMessage = 'Camera permission denied. Please allow camera access.';
            } else if (err.name === 'NotFoundError') {
                errorMessage = 'No camera found. ' + 
                    (isDesktop ? 'Check if webcam is connected.' : 'Please use a device with camera.');
            } else if (err.name === 'NotReadableError') {
                errorMessage = 'Camera is in use by another application.';
            } else if (err.message && err.message.includes('environment')) {
                errorMessage = isDesktop ? 
                    'Using front camera. Hold barcode towards the camera.' :
                    'Camera configuration error.';
            } else {
                errorMessage = `Error: ${err.message || 'Unknown'}`;
            }
            
            updateStatus(errorMessage, 'error');
            
            // Show troubleshooting
            showTroubleshooting(isDesktop);
        }
        
        function showTroubleshooting(isDesktop) {
            const resultsList = document.getElementById('resultsList');
            resultsList.innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    <h3 style="color: var(--orange-medium); margin-bottom: 15px;">
                        <i class="fas fa-exclamation-triangle"></i> Camera Issue
                    </h3>
                    <div style="background: rgba(255, 140, 66, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <p style="margin-bottom: 10px;"><strong>Troubleshooting steps:</strong></p>
                        ${isDesktop ? 
                            `<p>1. Ensure webcam is connected</p>
                             <p>2. Check browser camera permissions</p>
                             <p>3. Close other apps using camera</p>
                             <p>4. Try Chrome or Firefox browser</p>` :
                            `<p>1. Allow camera permissions</p>
                             <p>2. Clean camera lens</p>
                             <p>3. Ensure good lighting</p>
                             <p>4. Restart app</p>`
                        }
                    </div>
                    <button onclick="location.reload()" class="btn" style="background: var(--orange-medium);">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                </div>
            `;
        }
        
        function handleCameraError(error) {
            updateStatus('Error: ' + error.message, 'error');
        }
        
        function updateResultsList() {
            if (scanResults.length === 0) {
                resultsList.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-barcode"></i>
                        <p>Point camera at a 1D barcode</p>
                        <p class="supported-formats">EAN • UPC • Code 128 • Code 39</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            scanResults.forEach(result => {
                const timeString = result.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const displayText = result.text;
                
                html += `
                    <div class="result-item-minimal">
                        <div class="result-type-minimal" style="background: ${result.type.color}15; color: ${result.type.color};">
                            <i class="fas ${result.type.icon}"></i> ${result.type.name}
                        </div>
                        <div class="result-content-minimal">
                            <div class="result-text">${displayText}</div>
                            <div style="font-size: 0.85rem; color: #666; margin-top: 5px;">
                                Format: <strong>${result.format}</strong>
                            </div>
                        </div>
                        <div class="result-time-minimal">
                            <i class="far fa-clock"></i> ${timeString}
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
                
                oscillator.frequency.value = 1000;
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.1);
            } catch (e) {
                // Silent fail
            }
        }
        
        function animateScanSuccess() {
            const scanFrame = document.querySelector('.scan-frame-minimal');
            if (scanFrame) {
                scanFrame.style.animation = 'scanSuccess 0.8s ease';
                setTimeout(() => {
                    scanFrame.style.animation = '';
                }, 800);
            }
        }
        
        // Clean up
        window.addEventListener('beforeunload', () => {
            if (scanning) {
                Quagga.stop();
                Quagga.offDetected(onDetected);
            }
        });
        
        window.addEventListener('pagehide', () => {
            if (scanning) {
                Quagga.stop();
                Quagga.offDetected(onDetected);
            }
        });
    }
});
