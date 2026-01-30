// PWA Installation
let deferredPrompt;

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    setupPWA();
});

// Setup PWA features
function setupPWA() {
    // Register service worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/service-worker.js')
                .then(reg => console.log('Service Worker registered'))
                .catch(err => console.log('Service Worker registration failed:', err));
        });
    }
    
    // Handle install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        const installContainer = document.getElementById('installContainer');
        const installBtn = document.getElementById('installBtn');
        
        if (installContainer && installBtn) {
            installContainer.style.display = 'block';
            
            installBtn.addEventListener('click', () => {
                installContainer.style.display = 'none';
                deferredPrompt.prompt();
                
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted install');
                    }
                    deferredPrompt = null;
                });
            });
        }
    });
    
    window.addEventListener('appinstalled', () => {
        console.log('PWA installed successfully');
        const installContainer = document.getElementById('installContainer');
        if (installContainer) {
            installContainer.style.display = 'none';
        }
        deferredPrompt = null;
    });
}