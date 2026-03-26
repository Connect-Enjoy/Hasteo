// student.js - Student Specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initProfileForm();
    initPasswordForm();
    initAttendanceFilters();
    initLogoutConfirmation();
});

function initProfileForm() {
    const profileForm = document.getElementById('updateProfileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function() {
            const submitBtn = this.querySelector('.btn-update');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
            submitBtn.disabled = true;
            
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 2000);
        });
    }
}

function initPasswordForm() {
    const passwordForm = document.getElementById('changePasswordForm');
    if (!passwordForm) return;
    
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    const errorDiv = document.getElementById('passwordMatchError');
    const submitBtn = document.getElementById('changePasswordBtn');
    
    function validatePasswords() {
        if (newPassword.value !== confirmPassword.value) {
            errorDiv.style.display = 'flex';
            submitBtn.disabled = true;
            return false;
        } else {
            errorDiv.style.display = 'none';
            submitBtn.disabled = false;
            return true;
        }
    }
    
    if (newPassword && confirmPassword) {
        newPassword.addEventListener('keyup', validatePasswords);
        confirmPassword.addEventListener('keyup', validatePasswords);
    }
    
    passwordForm.addEventListener('submit', function(e) {
        if (!validatePasswords()) {
            e.preventDefault();
            return;
        }
        
        const submitBtn = this.querySelector('.btn-change-password');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Changing...';
        submitBtn.disabled = true;
    });
}

function initAttendanceFilters() {
    const searchInput = document.getElementById('attendanceSearch');
    const monthFilter = document.getElementById('filterMonth');
    const yearFilter = document.getElementById('filterYear');
    const clearBtn = document.getElementById('clearFilters');
    
    if (!searchInput) return;
    
    function filterAttendance() {
        const searchTerm = searchInput.value.toLowerCase();
        const monthValue = monthFilter?.value || '';
        const yearValue = yearFilter?.value || '';
        
        const rows = document.querySelectorAll('#attendanceTableBody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            if (row.querySelector('.empty-state')) return;
            
            const dateCell = row.cells[0]?.textContent.toLowerCase() || '';
            const busCell = row.cells[2]?.textContent.toLowerCase() || '';
            const dateAttr = row.getAttribute('data-date');
            const rowMonth = dateAttr ? parseInt(dateAttr.split('-')[1]) : null;
            const rowYear = dateAttr ? parseInt(dateAttr.split('-')[0]) : null;
            
            const matchesSearch = searchTerm === '' || dateCell.includes(searchTerm) || busCell.includes(searchTerm);
            const matchesMonth = monthValue === '' || rowMonth === parseInt(monthValue);
            const matchesYear = yearValue === '' || rowYear === parseInt(yearValue);
            
            if (matchesSearch && matchesMonth && matchesYear) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        const tbody = document.getElementById('attendanceTableBody');
        let existingMsg = document.getElementById('noResultsMsg');
        
        if (visibleCount === 0 && rows.length > 0) {
            if (!existingMsg) {
                const tr = document.createElement('tr');
                tr.id = 'noResultsMsg';
                tr.innerHTML = `<td colspan="5" class="empty-row">
                    <div class="empty-state">
                        <i class="fas fa-search"></i>
                        <p>No matching records found</p>
                    </div>
                  </td>`;
                tbody.appendChild(tr);
            }
        } else if (existingMsg) {
            existingMsg.remove();
        }
    }
    
    searchInput.addEventListener('input', filterAttendance);
    if (monthFilter) monthFilter.addEventListener('change', filterAttendance);
    if (yearFilter) yearFilter.addEventListener('change', filterAttendance);
    
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            if (monthFilter) monthFilter.value = '';
            if (yearFilter) yearFilter.value = '';
            filterAttendance();
        });
    }
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