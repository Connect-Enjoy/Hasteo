// PWA Installation and scroll effects
let deferredPrompt;

document.addEventListener('DOMContentLoaded', function() {
    setupPWA();
    setupScrollBlur();
    setupActiveNavLink();
    setupFlashMessages();
});

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
        if (installContainer) installContainer.style.display = 'none';
        deferredPrompt = null;
    });
}

function setupScrollBlur() {
    const header = document.querySelector('header');
    if (!header) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

function setupActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-center a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || 
            (currentPath.includes('student') && href.includes('student')) ||
            (currentPath.includes('security') && href.includes('security')) ||
            (currentPath.includes('admin') && href.includes('admin'))) {
            link.classList.add('active');
        }
    });
}

function setupFlashMessages() {
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease';
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentNode) {
                    message.remove();
                }
            }, 500);
        }, 5000);
    });
}

// Loading state for buttons (used in login forms)
window.showLoading = function(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    button.disabled = true;
    return originalText;
};

window.hideLoading = function(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
};