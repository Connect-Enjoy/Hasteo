// Minimalistic Scanner Logic
document.addEventListener('DOMContentLoaded', function() {
    // Only run on scanner page
    if (!document.querySelector('.scanner-minimal')) return;
    
    // Wait for ZXing library to load
    if (typeof ZXing === 'undefined') {
        console.error('ZXing library not loaded!');
        updateStatus('Scanner library failed to load. Please refresh the page.', 'error');
        
        // Try to load it dynamically
        loadZXingLibrary();
        return;
    }
    
    initializeScanner();
    
    async function loadZXingLibrary() {
        updateStatus('Loading scanner library...', 'info');
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.19.1';
        script.onload = () => {
            console.log('ZXing library loaded dynamically');
            initializeScanner();
        };
        script.onerror = () => {
            updateStatus('Failed to load scanner library. Check internet connection.', 'error');
        };
        
        document.head.appendChild(script);
    }
    
    async function initializeScanner() {
        const videoElement = document.getElementById('scannerVideo');
        const scannerStatus = document.getElementById('scannerStatus');
        const resultsList = document.getElementById('resultsList');
        const scanCount = document.getElementById('scanCount');
        const lastScanTime = document.getElementById('lastScanTime');
        
        let codeReader = null;
        let scannerInterval = null;
        let lastScanned = '';
        let lastScanTimeValue = 0;
        let scanResults = [];
        
        // Initialize scanner
        initScanner();
        
        async function initScanner() {
            try {
                updateStatus('Requesting camera access...', 'info');
                
                // Initialize ZXing
                if (typeof ZXing === 'undefined') {
                    throw new Error('ZXing library not available');
                }
                
                codeReader = new ZXing.BrowserMultiFormatReader();
                
                // Try back camera first, fallback to any camera
                let constraints = {
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                };
                
                // Check if we're on mobile (likely has back camera)
                const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                
                if (isMobile) {
                    // On mobile, prefer back camera
                    constraints.video.facingMode = { exact: 'environment' };
                } else {
                    // On desktop/laptop, use any camera
                    constraints.video.facingMode = 'user'; // Front camera
                }
                
                try {
                    const stream = await navigator.mediaDevices.getUserMedia(constraints);
                    videoElement.srcObject = stream;
                    
                    updateStatus('Camera ready - scanning for barcodes', 'success');
                    
                    // Start scanning
                    startScanning();
                    
                    // Handle stream ended (camera disconnected)
                    stream.getVideoTracks()[0].onended = () => {
                        updateStatus('Camera disconnected', 'error');
                        stopScanning();
                    };
                    
                } catch (cameraError) {
                    // If exact facingMode fails, try without it
                    if (cameraError.name === 'OverconstrainedError' || cameraError.name === 'ConstraintNotSatisfiedError') {
                        updateStatus('Trying alternative camera...', 'info');
                        
                        // Remove exact facingMode constraint
                        delete constraints.video.facingMode;
                        
                        try {
                            const stream = await navigator.mediaDevices.getUserMedia(constraints);
                            videoElement.srcObject = stream;
                            
                            updateStatus('Camera ready - scanning for barcodes', 'success');
                            startScanning();
                        } catch (fallbackError) {
                            handleCameraError(fallbackError);
                        }
                    } else {
                        handleCameraError(cameraError);
                    }
                }
                
            } catch (error) {
                console.error('Scanner initialization error:', error);
                updateStatus('Scanner initialization failed: ' + error.message, 'error');
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
                errorMessage = 'Camera constraints could not be satisfied';
            } else {
                errorMessage = 'Camera error: ' + error.message;
            }
            
            updateStatus(errorMessage, 'error');
            
            // Show help message for laptop users
            if (!/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
                setTimeout(() => {
                    updateStatus('Tip: Use a mobile device for best scanning experience', 'info');
                }, 2000);
            }
        }
        
        function startScanning() {
            if (!codeReader) return;
            
            scannerInterval = setInterval(scanBarcode, 300);
        }
        
        function stopScanning() {
            if (scannerInterval) {
                clearInterval(scannerInterval);
                scannerInterval = null;
            }
        }
        
        function scanBarcode() {
            if (!videoElement.videoWidth || !codeReader) return;
            
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            
            context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
            
            try {
                codeReader.decodeFromCanvas(canvas)
                    .then(result => {
                        if (result) {
                            processScanResult(result);
                        }
                    })
                    .catch(() => {
                        // No barcode detected - normal
                    });
            } catch (error) {
                // Ignore decoding errors
            }
        }
        
        function processScanResult(result) {
            const now = Date.now();
            const text = result.getText();
            
            // Prevent duplicate scans within 2 seconds
            if (text === lastScanned && (now - lastScanTimeValue) < 2000) {
                return;
            }
            
            lastScanned = text;
            lastScanTimeValue = now;
            
            // Add to results
            addScanResult(text);
            
            // Update UI
            updateScanCount();
            updateLastScanTime();
            playScanSound();
            animateScanSuccess();
        }
        
        function addScanResult(text) {
            const result = {
                text: text,
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
            if (text.startsWith('http://') || text.startsWith('https://')) {
                return { name: 'URL', icon: 'fa-link', color: '#0277BD' };
            } else if (text.includes('@') && text.includes('.')) {
                return { name: 'Email', icon: 'fa-envelope', color: '#D93E30' };
            } else if (/^\d{12,13}$/.test(text)) {
                return { name: 'EAN Barcode', icon: 'fa-barcode', color: '#FF8C42' };
            } else if (/^\d{10}$/.test(text)) {
                return { name: 'ISBN', icon: 'fa-book', color: '#5D4037' };
            } else if (/^[A-Z]{2}\d{10}$/.test(text)) {
                return { name: 'Tracking', icon: 'fa-shipping-fast', color: '#2E7D32' };
            } else if (/^\d{9}$/.test(text)) {
                return { name: 'Student ID', icon: 'fa-id-card', color: '#FF6347' };
            } else if (text.length < 50) {
                return { name: 'Text', icon: 'fa-font', color: '#8B7355' };
            } else {
                return { name: 'Data', icon: 'fa-database', color: '#6A1B9A' };
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
                            ${result.text.startsWith('http') ? `<a href="${result.text}" target="_blank" style="color: ${result.type.color}; text-decoration: none; font-size: 0.9rem;">↗ Open Link</a>` : ''}
                        </div>
                        <div class="result-time-minimal">
                            <i class="far fa-clock"></i> ${timeString}
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
            let color = 'var(--text-light)';
            
            switch(type) {
                case 'success':
                    icon = 'fa-check-circle';
                    color = 'var(--success)';
                    break;
                case 'error':
                    icon = 'fa-exclamation-circle';
                    color = 'var(--danger)';
                    break;
                case 'warning':
                    icon = 'fa-exclamation-triangle';
                    color = 'var(--warning)';
                    break;
            }
            
            scannerStatus.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
            scannerStatus.style.color = color;
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
                startScanning();
            }
        });
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            stopScanning();
            if (videoElement.srcObject) {
                videoElement.srcObject.getTracks().forEach(track => track.stop());
            }
        });
    }
});