// PWA functionality for Hasteo

let deferredPrompt;

// Initialize PWA
function initPWA() {
    // Register service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/service-worker.js')
            .then(reg => {
                console.log('✅ Service Worker registered:', reg.scope);
                
                // Check for updates
                reg.addEventListener('updatefound', () => {
                    const newWorker = reg.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            showNotification('New version available! Refresh to update.', 'info');
                        }
                    });
                });
            })
            .catch(err => console.log('❌ Service Worker registration failed:', err));
    }
    
    // Handle install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        // Show install button after 3 seconds if not already installed
        if (!window.matchMedia('(display-mode: standalone)').matches) {
            setTimeout(() => {
                showInstallButton();
            }, 3000);
        }
    });
    
    window.addEventListener('appinstalled', () => {
        console.log('✅ App installed successfully');
        deferredPrompt = null;
        hideInstallButton();
        
        // Save installation state
        localStorage.setItem('hasteo_pwa_installed', 'true');
        
        // Show success notification
        showNotification('App installed successfully!', 'success');
    });
    
    // Check if running as PWA
    if (window.matchMedia('(display-mode: standalone)').matches) {
        document.body.classList.add('pwa-installed');
        localStorage.setItem('hasteo_pwa_installed', 'true');
        
        // Add PWA-specific styles
        const style = document.createElement('style');
        style.textContent = `
            .pwa-installed .nav-toggle {
                top: env(safe-area-inset-top, 20px);
            }
            .pwa-installed .main-content {
                padding-top: calc(80px + env(safe-area-inset-top, 0px));
            }
            .pwa-installed .main-header {
                padding-top: calc(var(--space-md) + env(safe-area-inset-top, 0px));
            }
        `;
        document.head.appendChild(style);
    }
}

// Show install button
function showInstallButton() {
    // Don't show if already installed or on login pages
    if (isPWAInstalled() || window.location.pathname.includes('login')) {
        return;
    }
    
    let installBtn = document.getElementById('installBtn');
    
    if (!installBtn) {
        installBtn = document.createElement('button');
        installBtn.id = 'installBtn';
        installBtn.className = 'pwa-install-btn';
        installBtn.innerHTML = '<i class="fas fa-download"></i> Install App';
        installBtn.style.position = 'fixed';
        installBtn.style.bottom = '20px';
        installBtn.style.right = '20px';
        installBtn.style.zIndex = '1000';
        installBtn.style.background = 'var(--primary)';
        installBtn.style.color = 'white';
        installBtn.style.border = 'none';
        installBtn.style.borderRadius = 'var(--radius-full)';
        installBtn.style.padding = 'var(--space-md) var(--space-lg)';
        installBtn.style.boxShadow = 'var(--shadow-lg)';
        installBtn.style.display = 'flex';
        installBtn.style.alignItems = 'center';
        installBtn.style.gap = 'var(--space-sm)';
        installBtn.style.cursor = 'pointer';
        installBtn.style.fontWeight = '500';
        installBtn.style.transition = 'all 0.3s ease';
        
        installBtn.addEventListener('click', installApp);
        document.body.appendChild(installBtn);
        
        // Add animation
        installBtn.style.animation = 'bounce 2s infinite';
    }
    
    installBtn.style.display = 'flex';
}

// Hide install button
function hideInstallButton() {
    const installBtn = document.getElementById('installBtn');
    if (installBtn) {
        installBtn.style.display = 'none';
    }
}

// Install app
function installApp() {
    if (!deferredPrompt) return;
    
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
            console.log('✅ User accepted install');
            localStorage.setItem('hasteo_pwa_installed', 'true');
        } else {
            console.log('❌ User dismissed install');
        }
        deferredPrompt = null;
    });
}

// Check if app is installed
function isPWAInstalled() {
    return localStorage.getItem('hasteo_pwa_installed') === 'true' || 
           window.matchMedia('(display-mode: standalone)').matches;
}

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('✅ Notification permission granted');
                localStorage.setItem('hasteo_notifications', 'enabled');
                showNotification('Notifications enabled!', 'success');
            }
        });
    }
}

// Send notification
function sendNotification(title, body, url = '/') {
    if ('Notification' in window && Notification.permission === 'granted') {
        const options = {
            body: body,
            icon: '/static/images/app_logo.png',
            badge: '/static/images/app_logo.png',
            vibrate: [100, 50, 100],
            data: { url: url },
            tag: 'hasteo-notification'
        };
        
        const notification = new Notification(title, options);
        
        notification.onclick = function(event) {
            event.preventDefault();
            window.focus();
            window.location.href = url;
            notification.close();
        };
        
        return notification;
    }
}

// Schedule background sync
function scheduleBackgroundSync() {
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
        navigator.serviceWorker.ready.then(reg => {
            reg.sync.register('sync-attendance').then(() => {
                console.log('✅ Background sync registered');
            });
        });
    }
}

// Check for updates
function checkForUpdates() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(reg => {
            reg.update();
        });
    }
}

// Initialize PWA on load
window.addEventListener('load', function() {
    // Initialize PWA
    initPWA();
    
    // Request notification permission on first visit
    const notificationsEnabled = localStorage.getItem('hasteo_notifications');
    if (!notificationsEnabled && window.location.pathname === '/') {
        setTimeout(() => {
            requestNotificationPermission();
        }, 5000);
    }
    
    // Check for updates every hour
    setInterval(checkForUpdates, 3600000);
    
    // Schedule background sync
    if (window.location.pathname.includes('/security/scan')) {
        scheduleBackgroundSync();
    }
});

// Export functions
window.initPWA = initPWA;
window.installApp = installApp;
window.isPWAInstalled = isPWAInstalled;
window.requestNotificationPermission = requestNotificationPermission;
window.sendNotification = sendNotification;