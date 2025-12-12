// Admin Dashboard JavaScript

// Global variables
let adminStats = {
    total_students: 0,
    students_with_due: 0,
    total_security: 0,
    today_scans: 0
};

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Load admin data
    loadAdminStats();
    loadRecentActivity();
    loadStudents();
    loadSecurityPersonnel();
    
    // Setup event listeners
    setupAdminEventListeners();
});

// Load admin statistics
async function loadAdminStats() {
    try {
        // Stats are already loaded server-side in the template
        // This function is for future AJAX updates
        console.log('Admin stats loaded');
    } catch (error) {
        console.error('Error loading admin stats:', error);
    }
}

// Load recent activity
async function loadRecentActivity() {
    try {
        const response = await fetch('/api/attendance?limit=5');
        const history = await response.json();
        
        const activityContainer = document.getElementById('recentActivity');
        if (!activityContainer) return;
        
        if (!response.ok) {
            activityContainer.innerHTML = `<div class="empty-state">${history.error || 'Failed to load activity'}</div>`;
            return;
        }
        
        if (history.length === 0) {
            activityContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h3>No recent activity</h3>
                    <p>Activity will appear here once scans are recorded</p>
                </div>
            `;
            return;
        }
        
        const activityHTML = `
            <div style="overflow-x: auto;">
                <table style="width: 100%;">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Student</th>
                            <th>Register No</th>
                            <th>Bus No</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${history.map(record => `
                            <tr>
                                <td>${formatTime(record.timestamp)}</td>
                                <td>${record.student_name || 'N/A'}</td>
                                <td><code>${record.register_no}</code></td>
                                <td><strong>${record.bus_no}</strong></td>
                                <td><span class="status-badge ${record.scan_type === 'entry' ? 'status-active' : 'status-inactive'}">
                                    ${record.scan_type === 'entry' ? 'Entry' : 'Exit'}
                                </span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <a href="/security/history" class="btn btn-sm">View Full History</a>
            </div>
        `;
        
        activityContainer.innerHTML = activityHTML;
        
    } catch (error) {
        const activityContainer = document.getElementById('recentActivity');
        if (activityContainer) {
            activityContainer.innerHTML = `<div class="empty-state">Failed to load activity</div>`;
        }
    }
}

// Load students
async function loadStudents() {
    try {
        const response = await fetch('/api/students');
        const students = await response.json();
        
        const container = document.getElementById('studentsList');
        if (!container) return;
        
        if (!response.ok) {
            container.innerHTML = `<div class="empty-state">${students.error || 'Failed to load'}</div>`;
            return;
        }
        
        if (students.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h3>No students</h3>
                    <p>Add students using the form</p>
                </div>
            `;
            return;
        }
        
        const tableHTML = `
            <div class="table-responsive">
                <table class="table" id="studentsTable">
                    <thead>
                        <tr>
                            <th>Reg No</th>
                            <th>Name</th>
                            <th>Course</th>
                            <th>Bus No</th>
                            <th>Fees</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${students.map(student => `
                            <tr>
                                <td><strong>${student.register_no}</strong></td>
                                <td>${student.name}</td>
                                <td>${student.course}</td>
                                <td>${student.bus_no || 'N/A'}</td>
                                <td><span class="badge ${student.bus_fees_paid ? 'badge-success' : 'badge-danger'}">${student.bus_fees_paid ? 'Paid' : 'Due'}</span></td>
                                <td class="action-buttons">
                                    <button onclick="editStudent(${student.id})" class="action-btn edit" title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button onclick="deleteStudent(${student.id}, '${student.name}')" class="action-btn delete" title="Delete">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        
    } catch (error) {
        const container = document.getElementById('studentsList');
        if (container) {
            container.innerHTML = `<div class="empty-state">Failed to load students</div>`;
        }
    }
}

// Add student
async function addStudent() {
    const registerNo = document.getElementById('register_no')?.value.trim();
    const name = document.getElementById('name')?.value.trim();
    const course = document.getElementById('course')?.value.trim();
    const admissionYear = document.getElementById('admission_year')?.value.trim();
    
    if (!registerNo || !name || !course || !admissionYear) {
        showNotification('Fill all required fields', 'error');
        return;
    }
    
    // Validate registration number format
    if (!registerNo.includes('/') || registerNo.split('/').length !== 3) {
        showNotification('Invalid format. Use: COURSE/ID/YEAR', 'error');
        return;
    }
    
    const studentData = {
        register_no: registerNo,
        name: name,
        course: course,
        admission_year: admissionYear,
        bus_no: document.getElementById('bus_no')?.value,
        department: document.getElementById('department')?.value,
        year: document.getElementById('year')?.value,
        phone: document.getElementById('phone')?.value,
        email: document.getElementById('email')?.value,
        bus_fees_paid: document.getElementById('bus_fees_paid')?.checked || false,
        monthly_fee: parseFloat(document.getElementById('monthly_fee')?.value) || 1000.00
    };
    
    try {
        const response = await fetch('/api/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(result.message, 'success');
            document.getElementById('addStudentForm')?.reset();
            loadStudents();
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to add student', 'error');
    }
}

// Edit student
function editStudent(studentId) {
    showNotification('Edit feature coming soon!', 'info');
}

// Delete student
async function deleteStudent(studentId, studentName) {
    if (!confirm(`Delete student: ${studentName}?\nThis action cannot be undone.`)) {
        return;
    }
    
    showNotification('Delete feature coming soon!', 'info');
}

// Load security personnel
async function loadSecurityPersonnel() {
    try {
        const response = await fetch('/api/security');
        const securityUsers = await response.json();
        
        const container = document.getElementById('securityList');
        if (!container) return;
        
        if (!response.ok) {
            container.innerHTML = `<div class="empty-state">${securityUsers.error || 'Failed to load'}</div>`;
            return;
        }
        
        if (securityUsers.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-user-shield"></i>
                    <h3>No security personnel</h3>
                    <p>Add security users using the form</p>
                </div>
            `;
            return;
        }
        
        const tableHTML = `
            <div class="table-responsive">
                <table class="table" id="securityTable">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Full Name</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${securityUsers.map(user => `
                            <tr>
                                <td><strong>${user.username}</strong></td>
                                <td>${user.full_name}</td>
                                <td>${formatDate(user.created_at)}</td>
                                <td>
                                    <button onclick="deleteSecurityUser(${user.id}, '${user.username}')" class="btn btn-sm btn-danger">
                                        <i class="fas fa-trash"></i> Delete
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        
    } catch (error) {
        const container = document.getElementById('securityList');
        if (container) {
            container.innerHTML = `<div class="empty-state">Failed to load</div>`;
        }
    }
}

// Add security user
async function addSecurityUser() {
    const username = document.getElementById('username')?.value.trim();
    const password = document.getElementById('password')?.value;
    const confirmPassword = document.getElementById('confirm_password')?.value;
    const fullName = document.getElementById('full_name')?.value.trim();
    
    if (!username || !password || !confirmPassword || !fullName) {
        showNotification('Fill all fields', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return;
    }
    
    if (password.length < 6) {
        showNotification('Password must be at least 6 characters', 'error');
        return;
    }
    
    const userData = {
        username: username,
        password: password,
        full_name: fullName
    };
    
    try {
        const response = await fetch('/api/security', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(result.message, 'success');
            document.getElementById('addSecurityForm')?.reset();
            loadSecurityPersonnel();
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to add user', 'error');
    }
}

// Delete security user
async function deleteSecurityUser(userId, username) {
    if (!confirm(`Delete security user: ${username}?\nThis will permanently remove their account.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/security/${userId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(result.message, 'success');
            loadSecurityPersonnel();
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to delete user', 'error');
    }
}

// Setup admin event listeners
function setupAdminEventListeners() {
    // Student form
    const addStudentForm = document.getElementById('addStudentForm');
    if (addStudentForm) {
        addStudentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addStudent();
        });
    }
    
    // Security form
    const addSecurityForm = document.getElementById('addSecurityForm');
    if (addSecurityForm) {
        addSecurityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addSecurityUser();
        });
    }
    
    // Search functionality
    const searchStudents = document.getElementById('searchStudents');
    if (searchStudents) {
        searchStudents.addEventListener('input', function() {
            setupTableSearch('searchStudents', 'studentsTable');
        });
    }
    
    const searchSecurity = document.getElementById('searchSecurity');
    if (searchSecurity) {
        searchSecurity.addEventListener('input', function() {
            setupTableSearch('searchSecurity', 'securityTable');
        });
    }
}

// Show coming soon notification
function showComingSoon() {
    showNotification('This feature is coming soon!', 'info');
}

// Export functions for global use
window.addStudent = addStudent;
window.addSecurityUser = addSecurityUser;
window.deleteSecurityUser = deleteSecurityUser;
window.editStudent = editStudent;
window.deleteStudent = deleteStudent;
window.showComingSoon = showComingSoon;