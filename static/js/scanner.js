// Enhanced Scanner Logic with ZXing Integration
document.addEventListener('DOMContentLoaded', function() {
    // Only run on scanner page
    if (!document.querySelector('.scanner-minimal')) return;
    
    // Initialize scanner
    initializeScanner();
    
    async function initializeScanner() {
        const videoElement = document.getElementById('scannerVideo');
        const scannerStatus = document.getElementById('scannerStatus');
        const resultsList = document.getElementById('resultsList');
        const scanCount = document.getElementById('scanCount');
        const lastScanTime = document.getElementById('lastScanTime');
        
        let codeReader = null;
        let isScanning = false;
        let lastScanned = '';
        let lastScanTimeValue = 0;
        let scanResults = [];
        
        // Initialize scanner
        initScanner();
        
        async function initScanner() {
            try {
                updateStatus('Initializing scanner...', 'info');
                
                // Initialize ZXing
                if (typeof ZXing === 'undefined') {
                    throw new Error('ZXing library not available');
                }
                
                codeReader = new ZXing.BrowserMultiFormatReader();
                
                // Camera constraints
                let constraints = {
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                        facingMode: 'environment' // Prefer back camera
                    }
                };
                
                // Get camera stream
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                videoElement.srcObject = stream;
                
                // Start playing video
                await videoElement.play();
                
                updateStatus('Camera ready - point at barcode', 'success');
                
                // Start continuous scanning
                startContinuousScanning();
                
                // Handle camera disconnection
                stream.getVideoTracks()[0].onended = () => {
                    updateStatus('Camera disconnected', 'error');
                    stopScanning();
                };
                
            } catch (error) {
                handleCameraError(error);
            }
        }
        
        function handleCameraError(error) {
            console.error('Camera error:', error);
            let errorMessage = 'Camera error';
            
            if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                errorMessage = 'No camera found on device';
            } else if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                errorMessage = 'Camera permission denied. Please allow camera access.';
            } else if (error.name === 'NotSupportedError') {
                errorMessage = 'Camera not supported';
            } else if (error.name === 'OverconstrainedError') {
                // Try without facingMode constraint
                errorMessage = 'Trying alternative camera...';
                setTimeout(() => tryAlternativeCamera(), 1000);
                return;
            } else {
                errorMessage = 'Camera error: ' + error.message;
            }
            
            updateStatus(errorMessage, 'error');
            
            // Show help message for desktop users
            if (!/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
                setTimeout(() => {
                    updateStatus('Tip: Use a mobile device for best scanning experience', 'info');
                }, 2000);
            }
        }
        
        async function tryAlternativeCamera() {
            try {
                const constraints = {
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                        // No facingMode constraint
                    }
                };
                
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                const videoElement = document.getElementById('scannerVideo');
                videoElement.srcObject = stream;
                await videoElement.play();
                
                updateStatus('Camera ready - point at barcode', 'success');
                startContinuousScanning();
            } catch (error) {
                updateStatus('Failed to access camera: ' + error.message, 'error');
            }
        }
        
        function startContinuousScanning() {
            if (isScanning || !codeReader) return;
            
            isScanning = true;
            scanFrame();
        }
        
        function stopScanning() {
            isScanning = false;
        }
        
        async function scanFrame() {
            if (!isScanning || !videoElement.videoWidth) return;
            
            try {
                const result = await codeReader.decodeFromVideoElement(videoElement);
                
                if (result) {
                    processScanResult(result);
                }
            } catch (error) {
                // No barcode detected - this is normal
            }
            
            // Continue scanning
            if (isScanning) {
                requestAnimationFrame(() => scanFrame());
            }
        }
        
        function processScanResult(result) {
            const now = Date.now();
            const text = result.getText();
            
            // Prevent duplicate scans within 1 second
            if (text === lastScanned && (now - lastScanTimeValue) < 1000) {
                return;
            }
            
            lastScanned = text;
            lastScanTimeValue = now;
            
            // Add to results
            addScanResult(text, result.getBarcodeFormat());
            
            // Update UI
            updateScanCount();
            updateLastScanTime();
            playScanSound();
            animateScanSuccess();
        }
        
        function addScanResult(text, format) {
            const result = {
                text: text,
                format: format,
                type: getBarcodeType(text),
                time: new Date(),
                id: Date.now()
            };
            
            // Add to beginning of array
            scanResults.unshift(result);
            
            // Keep only last 10 scans
            if (scanResults.length > 10) {
                scanResults.pop();
            }
            
            // Update UI
            updateResultsList();
        }
        
        function getBarcodeType(text) {
            if (/^https?:\/\//i.test(text)) {
                return { name: 'URL', icon: 'fa-link', color: '#0277BD' };
            } else if (/^WIFI:/i.test(text)) {
                return { name: 'Wi-Fi Config', icon: 'fa-wifi', color: '#4CAF50' };
            } else if (/^BEGIN:VCARD/i.test(text)) {
                return { name: 'Contact', icon: 'fa-address-card', color: '#FF9800' };
            } else if (/^\d{12,13}$/.test(text)) {
                return { name: 'Product (EAN/UPC)', icon: 'fa-barcode', color: '#FF6347' };
            } else if (/^\d{10}$/.test(text)) {
                return { name: 'ISBN', icon: 'fa-book', color: '#795548' };
            } else if (/^[A-Z]{2}\d{10}$/.test(text)) {
                return { name: 'Tracking', icon: 'fa-shipping-fast', color: '#2196F3' };
            } else if (/^\d{9}$/.test(text)) {
                return { name: 'Student ID', icon: 'fa-id-card', color: '#9C27B0' };
            } else if (text.length < 50) {
                return { name: 'Text', icon: 'fa-font', color: '#607D8B' };
            } else {
                return { name: 'Data', icon: 'fa-database', color: '#3F51B5' };
            }
        }
        
        function updateResultsList() {
            if (scanResults.length === 0) {
                resultsList.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-qrcode"></i>
                        <p>Point your camera at a barcode to scan</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            scanResults.forEach(result => {
                const timeString = result.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const displayText = result.text.length > 80 ? result.text.substring(0, 80) + '...' : result.text;
                
                html += `
                    <div class="result-item-minimal">
                        <div class="result-type-minimal" style="background: ${result.type.color}15; color: ${result.type.color};">
                            <i class="fas ${result.type.icon}"></i> ${result.type.name}
                        </div>
                        <div class="result-content-minimal">
                            <div class="result-text">${displayText}</div>
                            ${result.text.startsWith('http') ? 
                                `<a href="${result.text}" target="_blank" style="color: ${result.type.color}; text-decoration: none; font-size: 0.9rem;">
                                    <i class="fas fa-external-link-alt"></i> Open Link
                                </a>` : 
                                ''}
                        </div>
                        <div class="result-time-minimal">
                            <i class="far fa-clock"></i> ${timeString}
                            <span style="margin-left: 10px; font-size: 0.8rem; color: #999;">${result.format}</span>
                        </div>
                    </div>
                `;
            });
            
            resultsList.innerHTML = html;
            
            // Smooth scroll to top of results
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
            
            // Highlight
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
                // Simple beep sound
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = 800;
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.1);
            } catch (e) {
                // Audio not supported - silent fail
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
        
        // Handle page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                stopScanning();
            } else {
                startContinuousScanning();
            }
        });
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            stopScanning();
            if (videoElement.srcObject) {
                videoElement.srcObject.getTracks().forEach(track => track.stop());
            }
        });
        
        // Clean up on page hide (for PWA)
        window.addEventListener('pagehide', () => {
            stopScanning();
            if (videoElement.srcObject) {
                videoElement.srcObject.getTracks().forEach(track => track.stop());
            }
        });
    }
});
