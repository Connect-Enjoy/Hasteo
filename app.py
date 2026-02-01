import os
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pwa-demo-key')

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# PWA Routes
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static/js', 'service-worker.js')

# Main Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scanner():
    return render_template('scan.html')

# Login Routes
@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        # TODO: Add actual authentication logic
        # For now, just redirect with success message
        flash('Student login successful! Redirecting to dashboard...', 'success')
        
        # Store in session
        session['user_type'] = 'student'
        session['user_id'] = student_id
        session['logged_in'] = True
        
        return redirect(url_for('index'))  # Change to actual student dashboard route later
        
    return render_template('student_login.html')

@app.route('/security-login', methods=['GET', 'POST'])
def security_login():
    if request.method == 'POST':
        security_id = request.form.get('security_id')
        password = request.form.get('password')
        
        # TODO: Add actual authentication logic
        flash('Security login successful!', 'success')
        
        # Store in session
        session['user_type'] = 'security'
        session['user_id'] = security_id
        session['logged_in'] = True
        
        return redirect(url_for('scanner'))  # Redirect to scanner
        
    return render_template('security_login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # TODO: Add actual authentication logic
        # Simple demo check (replace with proper authentication)
        if username == 'admin' and password == 'admin123':
            flash('Admin login successful!', 'success')
            
            # Store in session
            session['user_type'] = 'admin'
            session['user_id'] = username
            session['logged_in'] = True
            
            return redirect(url_for('index'))  # Change to admin dashboard route later
        else:
            flash('Invalid admin credentials!', 'error')
        
    return render_template('admin_login.html')

@app.route('/developer-login', methods=['GET', 'POST'])
def developer_login():
    if request.method == 'POST':
        developer_id = request.form.get('developer_id')
        password = request.form.get('password')
        
        # TODO: Add actual developer authentication logic
        flash('Developer access granted!', 'success')
        
        # Store in session
        session['user_type'] = 'developer'
        session['user_id'] = developer_id
        session['logged_in'] = True
        
        return redirect(url_for('index'))  # Or redirect to developer dashboard
        
    return render_template('developer_login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Dashboard Routes (Placeholders - to be implemented later)
@app.route('/student-dashboard')
def student_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        flash('Please login first', 'error')
        return redirect(url_for('student_login'))
    
    # TODO: Implement student dashboard
    return render_template('student_dashboard.html')  # Create this template later

@app.route('/security-dashboard')
def security_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        flash('Please login first', 'error')
        return redirect(url_for('security_login'))
    
    # TODO: Implement security dashboard
    return render_template('security_dashboard.html')  # Create this template later

@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'admin':
        flash('Please login first', 'error')
        return redirect(url_for('admin_login'))
    
    # TODO: Implement admin dashboard
    return render_template('admin_dashboard.html')  # Create this template later

# API Routes (Placeholders)
@app.route('/api/scan', methods=['POST'])
def api_scan():
    """API endpoint for barcode scanning"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    student_id = data.get('student_id')
    
    # TODO: Process the scan and save to database
    print(f"Scanned student ID: {student_id}")
    
    return jsonify({
        'success': True,
        'student_id': student_id,
        'timestamp': datetime.now().isoformat(),
        'scanned_by': session.get('user_id')
    })

@app.route('/api/attendance')
def api_attendance():
    """API endpoint for attendance data"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # TODO: Fetch attendance data from database
    sample_data = [
        {'student_id': 'SCS/12345/22', 'name': 'John Doe', 'time': '08:30 AM', 'status': 'present'},
        {'student_id': 'SCS/12346/22', 'name': 'Jane Smith', 'time': '08:45 AM', 'status': 'present'},
        {'student_id': 'SCS/12347/22', 'name': 'Bob Johnson', 'time': '09:00 AM', 'status': 'late'},
    ]
    
    return jsonify({
        'success': True,
        'data': sample_data,
        'total': len(sample_data)
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Vercel requirement
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
