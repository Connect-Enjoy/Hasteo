// Common JavaScript functions for Hasteo

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Setup logout buttons
    setupLogoutButtons();
    
    // Update current time
    updateTime();
    setInterval(updateTime, 60000);
    
    // Check online status
    updateConnectionStatus();
    window.addEventListener('online', updateConnectionStatus);
    window.addEventListener('offline', updateConnectionStatus);
    
    // Setup search functionality
    initSearch();
});

// Notification system
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `flash-message ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to container
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        const contentArea = document.querySelector('.content-area');
        if (contentArea) {
            contentArea.prepend(container);
        } else {
            document.body.prepend(container);
        }
    }
    
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-10px)';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Format time
function formatTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins} min ago`;
    } else if (diffMins < 1440) {
        const hours = Math.floor(diffMins / 60);
        return `${hours}h ago`;
    } else {
        return date.toLocaleDateString([], { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
}

// Format date
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Setup table search
function setupTableSearch(searchInputId, tableId) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        const rows = table.querySelectorAll('tbody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const isVisible = text.includes(searchTerm);
            row.style.display = isVisible ? '' : 'none';
            if (isVisible) visibleCount++;
        });
        
        // Show no results message
        const tbody = table.querySelector('tbody');
        let noResults = table.querySelector('.no-results');
        
        if (visibleCount === 0 && searchTerm !== '') {
            if (!noResults) {
                noResults = document.createElement('tr');
                noResults.className = 'no-results';
                noResults.innerHTML = `<td colspan="100" style="text-align: center; padding: 40px; color: var(--text-light);">No results found for "${searchTerm}"</td>`;
                tbody.appendChild(noResults);
            }
        } else if (noResults) {
            noResults.remove();
        }
    });
}

// Setup logout buttons
function setupLogoutButtons() {
    document.querySelectorAll('.logout-btn, .nav-item.logout').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Clear remember me settings
            localStorage.removeItem('hasteo_remember_me');
            localStorage.removeItem('hasteo_username');
            localStorage.removeItem('hasteo_role');
            
            window.location.href = '/logout';
        });
    });
}

// Update current time
function updateTime() {
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
}

// Update connection status
function updateConnectionStatus() {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        if (navigator.onLine) {
            statusElement.className = 'status-online';
            statusElement.innerHTML = '<i class="fas fa-wifi"></i> Online';
        } else {
            statusElement.className = 'status-offline';
            statusElement.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline';
        }
    }
}

// Initialize search
function initSearch() {
    document.querySelectorAll('.search-input').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
            }
        });
    });
}

// Play scan sound
function playScanSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
        console.log('Audio play failed:', e);
    }
}

// Vibrate device
function vibrate(pattern = [200]) {
    if (navigator.vibrate) {
        navigator.vibrate(pattern);
    }
}

// Export functions for global use
window.showNotification = showNotification;
window.formatTime = formatTime;
window.formatDate = formatDate;
window.setupTableSearch = setupTableSearch;
window.playScanSound = playScanSound;
window.vibrate = vibrate;