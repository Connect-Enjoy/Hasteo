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
        flash('Student login successful! Redirecting to dashboard...', 'success')
        
        # Store in session
        session['user_type'] = 'student'
        session['user_id'] = student_id
        session['logged_in'] = True
        
        return redirect(url_for('index'))
        
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
        
        return redirect(url_for('scanner'))
        
    return render_template('security_login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'official':
            session['admin_logged_in'] = True
            session['user_type'] = 'admin'
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
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
        
        return redirect(url_for('index'))
        
    return render_template('developer_login.html')

# Admin Routes
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('user_type', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('index'))

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# API Routes
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