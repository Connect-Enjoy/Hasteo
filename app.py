import os
import pg8000
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, date
import logging
from db import get_db_connection

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Create students table with residence field
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    branch VARCHAR(50) NOT NULL,
                    year_of_admission INTEGER NOT NULL,
                    registration_number VARCHAR(20) UNIQUE NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    residence VARCHAR(20) DEFAULT 'day_scholar',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Create student_validity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_validity (
                    registration_number VARCHAR(20) PRIMARY KEY,
                    is_valid BOOLEAN DEFAULT FALSE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (registration_number) REFERENCES students(registration_number)
                )
            ''')
            
            # Populate student_validity for existing students
            cursor.execute('''
                INSERT INTO student_validity (registration_number, is_valid)
                SELECT registration_number, CASE WHEN residence = 'day_scholar' THEN TRUE ELSE FALSE END
                FROM students
                ON CONFLICT (registration_number) DO NOTHING
            ''')
            
            # Create security table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security (
                    id SERIAL PRIMARY KEY,
                    security_id VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Create buses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buses (
                    id SERIAL PRIMARY KEY,
                    bus_number VARCHAR(20) UNIQUE NOT NULL,
                    route_name VARCHAR(100) NOT NULL,
                    driver_name VARCHAR(100) NOT NULL,
                    driver_phone VARCHAR(20) NOT NULL,
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'inactive')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create bus_logs table for entry/exit times
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bus_logs (
                    id SERIAL PRIMARY KEY,
                    bus_id INTEGER NOT NULL,
                    bus_number VARCHAR(20) NOT NULL,
                    security_id VARCHAR(20) NOT NULL,
                    entry_time TIMESTAMP,
                    exit_time TIMESTAMP,
                    log_date DATE DEFAULT CURRENT_DATE,
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed')),
                    FOREIGN KEY (bus_id) REFERENCES buses(id),
                    FOREIGN KEY (security_id) REFERENCES security(security_id)
                )
            ''')
            
            # Create scans table for attendance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(20) NOT NULL,
                    student_name VARCHAR(100) NOT NULL,
                    branch VARCHAR(50) NOT NULL,
                    residence VARCHAR(20) NOT NULL,
                    scanned_by VARCHAR(20) NOT NULL,
                    bus_id INTEGER,
                    bus_number VARCHAR(20),
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scan_date DATE DEFAULT CURRENT_DATE,
                    scan_type VARCHAR(20) DEFAULT 'check_in',
                    session_id VARCHAR(50),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (scanned_by) REFERENCES security(security_id),
                    FOREIGN KEY (bus_id) REFERENCES buses(id)
                )
            ''')
            
            # Create temporary_scans table for current session
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temp_scans (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(50) NOT NULL,
                    student_id VARCHAR(20) NOT NULL,
                    student_name VARCHAR(100) NOT NULL,
                    branch VARCHAR(50) NOT NULL,
                    residence VARCHAR(20) NOT NULL,
                    bus_id INTEGER,
                    bus_number VARCHAR(20),
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scanned_by VARCHAR(20) NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students(student_id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_branch ON students(branch)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_year ON students(year_of_admission)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_residence ON students(residence)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_active ON students(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_active ON security(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scans_student ON scans(student_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scans_date ON scans(scan_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bus_logs_date ON bus_logs(log_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_temp_scans_session ON temp_scans(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_buses_status ON buses(status)')
            
            # Create anomaly_detections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anomaly_detections (
                    id SERIAL PRIMARY KEY,
                    detection_date DATE NOT NULL,
                    entity_type VARCHAR(20) NOT NULL,
                    entity_id VARCHAR(50) NOT NULL,
                    anomaly_score FLOAT NOT NULL,
                    severity VARCHAR(20) DEFAULT 'medium',
                    description TEXT,
                    details JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_anomaly_date ON anomaly_detections(detection_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_anomaly_entity ON anomaly_detections(entity_type, entity_id)')
            
            conn.commit()
            cursor.close()
            print("Database tables created successfully!")
            
        except Exception as err:
            print(f"Database initialization error: {err}")
            conn.rollback()
        finally:
            conn.close()

# Initialize database on startup
try:
    init_db()
except Exception as e:
    print(f"Database initialization warning: {e}")

# Index Route
@app.route('/')
def index():
    return render_template('index.html')

# Public Demo Scanner (No login required)
@app.route('/scan')
def scanner():
    return render_template('scan.html')

# Student Login
@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        if student_id:
            student_id = student_id.strip()
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT student_id, name FROM students 
                    WHERE student_id = %s AND password = %s AND is_active = TRUE
                ''', (student_id, password))
                
                student = cursor.fetchone()
                cursor.close()
                
                if student:
                    session['user_type'] = 'student'
                    session['user_id'] = student[0]
                    session['student_name'] = student[1]
                    session['logged_in'] = True
                    flash(f'Welcome back, {student[1]}! 👋', 'success')
                    return redirect(url_for('student_dashboard'))
                else:
                    flash('Invalid student ID or password', 'error')
            except Exception as err:
                print(f"Student login error: {err}")
                flash('Login error. Please try again.', 'error')
            finally:
                conn.close()
        else:
            flash('Database connection error', 'error')
        
    return render_template('student_login.html')

# Student Dashboard
@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        flash('Please login as a student.', 'warning')
        return redirect(url_for('student_login'))
    
    student_id = session.get('user_id')
    conn = get_db_connection()
    student = None
    total_scans = 0
    today_scans = 0
    recent_scans = []
    last_bus = None
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get full student profile
            cursor.execute('''
                SELECT student_id, name, branch, year_of_admission,
                       registration_number, email, residence
                FROM students 
                WHERE student_id = %s AND is_active = TRUE
            ''', (student_id,))
            row = cursor.fetchone()
            if row:
                student = {
                    'student_id': row[0],
                    'name': row[1],
                    'branch': row[2],
                    'year_of_admission': row[3],
                    'registration_number': row[4],
                    'email': row[5],
                    'residence': row[6]
                }
            
            # Total scans count
            cursor.execute('SELECT COUNT(*) FROM scans WHERE student_id = %s', (student_id,))
            total_scans = cursor.fetchone()[0]
            
            # Today scans count
            cursor.execute('''
                SELECT COUNT(*) FROM scans 
                WHERE student_id = %s AND scan_date = CURRENT_DATE
            ''', (student_id,))
            today_scans = cursor.fetchone()[0]
            
            # Recent scans (last 5)
            cursor.execute('''
                SELECT id, student_id, student_name, branch, residence, bus_number, scan_time
                FROM scans 
                WHERE student_id = %s
                ORDER BY scan_time DESC
                LIMIT 5
            ''', (student_id,))
            recent_scans = cursor.fetchall()
            
            # Last bus used
            cursor.execute('''
                SELECT bus_number FROM scans 
                WHERE student_id = %s AND bus_number IS NOT NULL
                ORDER BY scan_time DESC LIMIT 1
            ''', (student_id,))
            last_bus_row = cursor.fetchone()
            if last_bus_row:
                last_bus = last_bus_row[0]
            
            cursor.close()
        except Exception as err:
            print(f"Student dashboard error: {err}")
        finally:
            conn.close()
    
    if not student:
        flash('Student record not found.', 'error')
        return redirect(url_for('student_login'))
    
    return render_template('student_dashboard.html',
                           student=student,
                           total_scans=total_scans,
                           today_scans=today_scans,
                           recent_scans=recent_scans,
                           last_bus=last_bus,
                           now=datetime.now())

# One-Day Pass Selection
@app.route('/student/one-day-pass')
def one_day_pass():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        flash('Please login as a student.', 'warning')
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    buses = []
    student_residence = 'day_scholar'
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT residence FROM students WHERE student_id = %s', (session.get('user_id'),))
            res = cursor.fetchone()
            if res:
                student_residence = res[0]
            
            if student_residence == 'hosteller':
                cursor.execute("SELECT id, bus_number, route_name FROM buses WHERE status = 'active' ORDER BY bus_number")
                buses = cursor.fetchall()
            cursor.close()
        except Exception as err:
            print(f"Error fetching buses: {err}")
        finally:
            conn.close()
            
    if student_residence != 'hosteller':
        flash('One-Day Passes are only available for hostellers.', 'error')
        return redirect(url_for('student_dashboard'))
        
    return render_template('one_day_pass.html', buses=buses)

# Dummy Payment Page
@app.route('/student/payment', methods=['GET', 'POST'])
def dummy_payment():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
        
    if request.method == 'POST':
        bus_id = request.form.get('bus_id')
        bus_number = request.form.get('bus_number')
        return render_template('payment.html', bus_id=bus_id, bus_number=bus_number)
        
    return redirect(url_for('one_day_pass'))

# Process Payment
@app.route('/student/payment/process', methods=['POST'])
def process_payment():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
        
    bus_number = request.form.get('bus_number')
    
    # Store the pass in session (simulating a DB record for the 1-day pass)
    session['has_one_day_pass'] = True
    session['pass_bus'] = bus_number
    
    # Update student_validity in database
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT registration_number FROM students WHERE student_id = %s', (session.get('user_id'),))
            result = cursor.fetchone()
            if result:
                reg_no = result[0]
                cursor.execute('UPDATE student_validity SET is_valid = TRUE, last_updated = CURRENT_TIMESTAMP WHERE registration_number = %s', (reg_no,))
                conn.commit()
            cursor.close()
        except Exception as err:
            print(f"Error updating pass validity: {err}")
        finally:
            conn.close()
    
    flash(f'Payment successful! 1-Day Pass active for Bus {bus_number}.', 'success')
    return redirect(url_for('student_dashboard'))

# Student Logout
@app.route('/student/logout')
def student_logout():
    session.pop('user_type', None)
    session.pop('user_id', None)
    session.pop('student_name', None)
    session.pop('logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('student_login'))

# Student Attendance API
@app.route('/api/student/attendance')
def student_attendance_api():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    student_id = session.get('user_id')
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, student_id, student_name, branch, bus_number, scan_time, scan_date
                FROM scans 
                WHERE student_id = %s
                ORDER BY scan_time DESC
                LIMIT 60
            ''', (student_id,))
            rows = cursor.fetchall()
            
            cursor.execute('SELECT COUNT(*) FROM scans WHERE student_id = %s', (student_id,))
            total = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM scans 
                WHERE student_id = %s AND scan_date = CURRENT_DATE
            ''', (student_id,))
            today = cursor.fetchone()[0]
            
            cursor.close()
            
            scans = []
            for row in rows:
                scans.append({
                    'id': row[0],
                    'student_id': row[1],
                    'student_name': row[2],
                    'branch': row[3],
                    'bus_number': row[4],
                    'scan_time': row[5].isoformat() if row[5] else None,
                    'scan_date': row[6].isoformat() if row[6] else None
                })
            
            return jsonify({'success': True, 'scans': scans, 'total': total, 'today': today})
            
        except Exception as err:
            print(f"Attendance API error: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Security Login
@app.route('/security-login', methods=['GET', 'POST'])
def security_login():
    if request.method == 'POST':
        security_id = request.form.get('security_id')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT security_id, name FROM security 
                    WHERE security_id = %s AND password = %s AND is_active = TRUE
                ''', (security_id, password))
                
                security = cursor.fetchone()
                cursor.close()
                
                if security:
                    session['user_type'] = 'security'
                    session['user_id'] = security[0]
                    session['security_name'] = security[1]
                    session['logged_in'] = True
                    session['session_id'] = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{security_id}"
                    flash(f'Welcome {security[1]}!', 'success')
                    return redirect(url_for('security_dashboard'))
                else:
                    flash('Invalid security ID or password', 'error')
            except Exception as err:
                print(f"Security login error: {err}")
                flash('Login error. Please try again.', 'error')
            finally:
                conn.close()
        else:
            flash('Database connection error', 'error')
        
    return render_template('security_login.html')

# Security Dashboard
@app.route('/security/dashboard')
def security_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        flash('Please login as security personnel.', 'warning')
        return redirect(url_for('security_login'))
    
    conn = get_db_connection()
    pending_bus_logs = 0
    today_scans = 0
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get pending bus logs count
            cursor.execute('''
                SELECT COUNT(*) FROM bus_logs 
                WHERE security_id = %s AND status = 'pending' AND log_date = CURRENT_DATE
            ''', (session.get('user_id'),))
            pending_bus_logs = cursor.fetchone()[0]
            
            # Get today's scans count (from permanent scans)
            cursor.execute('''
                SELECT COUNT(*) FROM scans 
                WHERE scanned_by = %s AND scan_date = CURRENT_DATE
            ''', (session.get('user_id'),))
            today_scans = cursor.fetchone()[0]
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading dashboard data: {err}")
        finally:
            conn.close()
    
    return render_template('security_dashboard.html', 
                         pending_bus_logs=pending_bus_logs,
                         today_scans=today_scans,
                         now=datetime.now())

# Security Bus Logs
@app.route('/security/bus-logs')
def security_bus_logs():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return redirect(url_for('security_login'))
    
    conn = get_db_connection()
    active_buses = []
    today_logs = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get all active buses
            cursor.execute('''
                SELECT id, bus_number, route_name, driver_name 
                FROM buses 
                WHERE status = 'active' 
                ORDER BY bus_number
            ''')
            active_buses = cursor.fetchall()
            
            # Get today's bus logs
            cursor.execute('''
                SELECT id, bus_number, entry_time, exit_time, status 
                FROM bus_logs 
                WHERE security_id = %s AND log_date = CURRENT_DATE 
                ORDER BY entry_time DESC
            ''', (session.get('user_id'),))
            today_logs = cursor.fetchall()
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading bus data: {err}")
            flash('Error loading bus data.', 'error')
        finally:
            conn.close()
    
    return render_template('security_bus.html', 
                         active_buses=active_buses,
                         today_logs=today_logs)

# Record bus entry
@app.route('/security/bus/entry/<int:bus_id>', methods=['POST'])
def record_bus_entry(bus_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get bus details
            cursor.execute('SELECT bus_number FROM buses WHERE id = %s', (bus_id,))
            bus = cursor.fetchone()
            if not bus:
                return jsonify({'success': False, 'error': 'Bus not found'}), 404
            
            bus_number = bus[0]
            
            # Check if there's already a pending log for this bus today
            cursor.execute('''
                SELECT id FROM bus_logs 
                WHERE bus_id = %s AND log_date = CURRENT_DATE AND status = 'pending'
            ''', (bus_id,))
            
            existing = cursor.fetchone()
            if existing:
                return jsonify({'success': False, 'error': 'Bus already has a pending log today'}), 400
            
            # Create new bus log
            cursor.execute('''
                INSERT INTO bus_logs (bus_id, bus_number, security_id, entry_time, status)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, 'pending')
                RETURNING id
            ''', (bus_id, bus_number, session.get('user_id')))
            
            log_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Entry recorded for bus {bus_number}',
                'log_id': log_id,
                'entry_time': datetime.now().strftime('%I:%M %p')
            })
            
        except Exception as err:
            print(f"Error recording bus entry: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Record bus exit
@app.route('/security/bus/exit/<int:log_id>', methods=['POST'])
def record_bus_exit(log_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Update bus log with exit time
            cursor.execute('''
                UPDATE bus_logs 
                SET exit_time = CURRENT_TIMESTAMP
                WHERE id = %s AND security_id = %s AND status = 'pending'
                RETURNING bus_number
            ''', (log_id, session.get('user_id')))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Log not found or already completed'}), 404
            
            bus_number = result[0]
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Exit recorded for bus {bus_number}',
                'exit_time': datetime.now().strftime('%I:%M %p')
            })
            
        except Exception as err:
            print(f"Error recording bus exit: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Complete bus log (finalize)
@app.route('/security/bus/complete/<int:log_id>', methods=['POST'])
def complete_bus_log(log_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Check if both entry and exit exist
            cursor.execute('''
                UPDATE bus_logs 
                SET status = 'completed'
                WHERE id = %s AND security_id = %s AND entry_time IS NOT NULL 
                AND exit_time IS NOT NULL AND status = 'pending'
                RETURNING bus_number
            ''', (log_id, session.get('user_id')))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Log cannot be completed. Both entry and exit required.'}), 400
            
            bus_number = result[0]
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Bus log for {bus_number} completed successfully'
            })
            
        except Exception as err:
            print(f"Error completing bus log: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete bus log (for accidental entries)
@app.route('/security/bus/delete/<int:log_id>', methods=['POST'])
def delete_bus_log(log_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Only allow deletion of pending logs
            cursor.execute('''
                DELETE FROM bus_logs 
                WHERE id = %s AND security_id = %s AND status = 'pending'
                RETURNING bus_number
            ''', (log_id, session.get('user_id')))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Log not found or cannot be deleted'}), 404
            
            bus_number = result[0]
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Log for bus {bus_number} deleted successfully'
            })
            
        except Exception as err:
            print(f"Error deleting bus log: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Security Student Logs (Scanning page)
@app.route('/security/student-logs')
def security_student_logs():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return redirect(url_for('security_login'))
    
    conn = get_db_connection()
    active_buses = []
    current_session_scans = []
    permanent_scans_today = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get all active buses
            cursor.execute('''
                SELECT id, bus_number, route_name 
                FROM buses 
                WHERE status = 'active' 
                ORDER BY bus_number
            ''')
            active_buses = cursor.fetchall()
            
            # Get current session scans
            cursor.execute('''
                SELECT id, student_id, student_name, branch, residence, bus_number, scan_time
                FROM temp_scans 
                WHERE session_id = %s
                ORDER BY scan_time DESC
            ''', (session.get('session_id'),))
            current_session_scans = cursor.fetchall()
            
            # Get today's permanent scans
            cursor.execute('''
                SELECT id, student_id, student_name, branch, residence, bus_number, scan_time
                FROM scans 
                WHERE scanned_by = %s AND scan_date = CURRENT_DATE
                ORDER BY scan_time DESC
                LIMIT 20
            ''', (session.get('user_id'),))
            permanent_scans_today = cursor.fetchall()
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading data: {err}")
            flash('Error loading data.', 'error')
        finally:
            conn.close()
    
    return render_template('security_student.html', 
                         active_buses=active_buses,
                         current_scans=current_session_scans,
                         permanent_scans=permanent_scans_today)

# Security Scanner page (actual scanning interface)
@app.route('/security/scan/<int:bus_id>')
def security_scan(bus_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return redirect(url_for('security_login'))
    
    conn = get_db_connection()
    bus = None
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, bus_number, route_name FROM buses WHERE id = %s', (bus_id,))
            bus = cursor.fetchone()
            cursor.close()
            
        except Exception as err:
            print(f"Error loading bus: {err}")
            flash('Error loading bus details.', 'error')
        finally:
            conn.close()
    
    if not bus:
        flash('Bus not found', 'error')
        return redirect(url_for('security_student_logs'))
    
    return render_template('security_scan.html', bus=bus)

# API endpoint for security scanning
@app.route('/api/security/scan', methods=['POST'])
def api_security_scan():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    student_id = data.get('student_id')
    bus_id = data.get('bus_id')
    
    if not student_id or not bus_id:
        return jsonify({'success': False, 'error': 'Student ID and Bus ID required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get bus details
            cursor.execute('SELECT bus_number FROM buses WHERE id = %s', (bus_id,))
            bus = cursor.fetchone()
            if not bus:
                return jsonify({'success': False, 'error': 'Bus not found'}), 404
            bus_number = bus[0]
            
            # Verify student exists and is active - FETCH ALL DETAILS FROM DATABASE
            cursor.execute('''
                SELECT student_id, name, branch, residence, year_of_admission, registration_number 
                FROM students 
                WHERE student_id = %s AND is_active = TRUE
            ''', (student_id,))
            
            student = cursor.fetchone()
            if not student:
                return jsonify({'success': False, 'error': 'Student not found or inactive'}), 404
            
            student_id_db = student[0]
            student_name = student[1]
            branch = student[2]
            residence = student[3]
            year = student[4]
            reg_number = student[5]
            
            # Check validity in database
            cursor.execute('SELECT is_valid FROM student_validity WHERE registration_number = %s', (reg_number,))
            validity = cursor.fetchone()
            if not validity or not validity[0]:
                return jsonify({
                    'success': False, 
                    'error': f'Student {student_name} ({reg_number}) is not valid for boarding (No active pass).',
                    'student_name': student_name
                }), 400
            
            # Check if already scanned in this session
            cursor.execute('''
                SELECT id FROM temp_scans 
                WHERE session_id = %s AND student_id = %s
            ''', (session.get('session_id'), student_id))
            
            if cursor.fetchone():
                return jsonify({
                    'success': False, 
                    'error': 'Student already scanned in this session',
                    'student_name': student_name
                }), 400
            
            # Save to temp scans
            cursor.execute('''
                INSERT INTO temp_scans 
                (session_id, student_id, student_name, branch, residence, bus_id, bus_number, scanned_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (session.get('session_id'), student_id, student_name, branch, 
                  residence, bus_id, bus_number, session.get('user_id')))
            
            scan_id = cursor.fetchone()[0]
            
            # Invalidate if hosteller
            if residence == 'hosteller':
                cursor.execute('UPDATE student_validity SET is_valid = FALSE, last_updated = CURRENT_TIMESTAMP WHERE registration_number = %s', (reg_number,))
                
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Student {student_name} scanned successfully',
                'student': {
                    'id': student_id,
                    'name': student_name,
                    'branch': branch,
                    'residence': residence,
                    'bus': bus_number,
                    'scan_id': scan_id,
                    'time': datetime.now().strftime('%I:%M %p'),
                    'year': year,
                    'reg_number': reg_number
                }
            })
            
        except Exception as err:
            print(f"Error saving scan: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Get current session scans
@app.route('/api/security/current-scans', methods=['GET'])
def get_current_scans():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, student_id, student_name, branch, residence, bus_number, scan_time
                FROM temp_scans 
                WHERE session_id = %s
                ORDER BY scan_time DESC
            ''', (session.get('session_id'),))
            
            scans = cursor.fetchall()
            cursor.close()
            
            scans_list = []
            for scan in scans:
                scans_list.append({
                    'id': scan[0],
                    'student_id': scan[1],
                    'student_name': scan[2],
                    'branch': scan[3],
                    'residence': scan[4],
                    'bus_number': scan[5],
                    'scan_time': scan[6].strftime('%I:%M %p')
                })
            
            return jsonify({'success': True, 'scans': scans_list})
            
        except Exception as err:
            print(f"Error getting scans: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete scan from current session (for accidental scans)
@app.route('/api/security/delete-scan/<int:scan_id>', methods=['POST'])
def delete_temp_scan(scan_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM temp_scans 
                WHERE id = %s AND session_id = %s
                RETURNING student_name
            ''', (scan_id, session.get('session_id')))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Scan not found'}), 404
            
            student_name = result[0]
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Scan for {student_name} deleted'
            })
            
        except Exception as err:
            print(f"Error deleting scan: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Clear current session (when starting fresh)
@app.route('/api/security/clear-session', methods=['POST'])
def clear_session():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM temp_scans 
                WHERE session_id = %s
            ''', (session.get('session_id'),))
            
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': 'Session cleared'})
            
        except Exception as err:
            print(f"Error clearing session: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Submit all scans to permanent database
@app.route('/api/security/submit-scans', methods=['POST'])
def submit_scans():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # First check if there are any scans to submit
            cursor.execute('''
                SELECT COUNT(*) FROM temp_scans WHERE session_id = %s
            ''', (session.get('session_id'),))
            count = cursor.fetchone()[0]
            
            if count == 0:
                return jsonify({'success': False, 'error': 'No scans to submit'}), 400
            
            # Move all temp scans to permanent scans table
            cursor.execute('''
                INSERT INTO scans 
                (student_id, student_name, branch, residence, scanned_by, bus_id, bus_number, scan_time, scan_date, session_id)
                SELECT student_id, student_name, branch, residence, scanned_by, bus_id, bus_number, scan_time, CURRENT_DATE, session_id
                FROM temp_scans
                WHERE session_id = %s
            ''', (session.get('session_id'),))
            
            # Clear temp scans after successful insertion
            cursor.execute('DELETE FROM temp_scans WHERE session_id = %s', (session.get('session_id'),))
            
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'{count} scans submitted successfully',
                'count': count
            })
            
        except Exception as err:
            print(f"Error submitting scans: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Get today's permanent scans
@app.route('/api/security/today-scans', methods=['GET'])
def get_today_scans():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, student_id, student_name, branch, residence, bus_number, scan_time
                FROM scans 
                WHERE scanned_by = %s AND scan_date = CURRENT_DATE
                ORDER BY scan_time DESC
                LIMIT 50
            ''', (session.get('user_id'),))
            
            scans = cursor.fetchall()
            cursor.close()
            
            scans_list = []
            for scan in scans:
                scans_list.append({
                    'id': scan[0],
                    'student_id': scan[1],
                    'student_name': scan[2],
                    'branch': scan[3],
                    'residence': scan[4],
                    'bus_number': scan[5],
                    'scan_time': scan[6].strftime('%I:%M %p')
                })
            
            return jsonify({'success': True, 'scans': scans_list})
            
        except Exception as err:
            print(f"Error getting today's scans: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Admin Login
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

# Developer Login
@app.route('/developer-login', methods=['GET', 'POST'])
def developer_login():
    if request.method == 'POST':
        developer_id = request.form.get('developer_id')
        password = request.form.get('password')
        
        # Simple check for demo
        if developer_id == 'dev' and password == 'dev123':
            session['user_type'] = 'developer'
            session['user_id'] = developer_id
            session['logged_in'] = True
            flash('Developer login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid developer credentials', 'error')
        
    return render_template('developer_login.html')

# Admin Dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Default values
    student_count = 0
    security_count = 0
    bus_count = 0
    total_scans = 0
    today_scans = 0
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get student count
            cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = TRUE")
            student_count = cursor.fetchone()[0]
            
            # Get security count
            cursor.execute("SELECT COUNT(*) FROM security WHERE is_active = TRUE")
            security_count = cursor.fetchone()[0]
            
            # Get active buses count
            cursor.execute("SELECT COUNT(*) FROM buses WHERE status = 'active'")
            bus_count = cursor.fetchone()[0]
            
            # Get total scan count
            cursor.execute("SELECT COUNT(*) FROM scans")
            total_scans = cursor.fetchone()[0]
            
            # Get today's scan count
            cursor.execute("SELECT COUNT(*) FROM scans WHERE DATE(scan_time) = CURRENT_DATE")
            today_scans = cursor.fetchone()[0]
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading dashboard data: {err}")
            flash('Error loading dashboard data.', 'error')
        finally:
            conn.close()
    
    return render_template('admin.html', 
                         student_count=student_count,
                         security_count=security_count,
                         bus_count=bus_count,
                         total_scans=total_scans,
                         today_scans=today_scans,
                         now=datetime.now())

# Admin User Management
@app.route('/admin/users')
def admin_users():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    students = []
    security_personnel = []
    eligible_batches = {}
    current_year = datetime.now().year
    stats = {
        'total_students': 0,
        'total_security': 0,
        'students_by_branch': {},
        'students_by_year': {}
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get all active students with residence
            cursor.execute('''
                SELECT id, student_id, name, branch, year_of_admission, 
                       registration_number, email, residence
                FROM students 
                WHERE is_active = TRUE 
                ORDER BY year_of_admission DESC, branch, name
            ''')
            students = cursor.fetchall()
            
            # Get all active security personnel
            cursor.execute('''
                SELECT id, security_id, name, email
                FROM security 
                WHERE is_active = TRUE 
                ORDER BY name
            ''')
            security_personnel = cursor.fetchall()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = TRUE")
            stats['total_students'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM security WHERE is_active = TRUE")
            stats['total_security'] = cursor.fetchone()[0]
            
            # Students by branch
            cursor.execute('''
                SELECT branch, COUNT(*) 
                FROM students 
                WHERE is_active = TRUE 
                GROUP BY branch 
                ORDER BY branch
            ''')
            for branch, count in cursor.fetchall():
                stats['students_by_branch'][branch] = count
            
            # Students by year and calculate eligible batches
            cursor.execute('''
                SELECT year_of_admission, COUNT(*) 
                FROM students 
                WHERE is_active = TRUE 
                GROUP BY year_of_admission 
                ORDER BY year_of_admission DESC
            ''')
            for year, count in cursor.fetchall():
                stats['students_by_year'][year] = count
                # Calculate eligible batches (4+ years old)
                if current_year - year >= 4:
                    eligible_batches[year] = count
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading user data: {err}")
            flash('Error loading user data.', 'error')
        finally:
            conn.close()
    
    return render_template('admin_users.html', 
                         students=students, 
                         security=security_personnel, 
                         stats=stats,
                         eligible_batches=eligible_batches,
                         now=datetime.now())

# Admin Anomaly Detection routes
from ml_anomaly_detection import run_anomaly_detection

@app.route('/admin/detect-anomalies', methods=['POST'])
def admin_detect_anomalies():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # Optionally pass a date from request
        target_date = None
        if request.is_json:
            target_date = request.json.get('date')
            
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            
        # Run detection
        run_anomaly_detection(target_date)
        return jsonify({'success': True, 'message': 'Anomaly detection completed.'})
    except Exception as e:
        logging.error(f"Anomaly detection failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/anomalies')
def admin_anomalies():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    anomalies = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, detection_date, entity_type, entity_id, anomaly_score, severity, description, details, resolved
                FROM anomaly_detections
                ORDER BY detection_date DESC, anomaly_score ASC
                LIMIT 100
            """)
            anomalies = cursor.fetchall()
            cursor.close()
        except Exception as e:
            logging.error(f"Error fetching anomalies: {e}")
        finally:
            conn.close()
            
    return render_template('admin_anomalies.html', anomalies=anomalies)

# Add Student
@app.route('/admin/add-student', methods=['POST'])
def admin_add_student():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    name = request.form.get('name')
    branch = request.form.get('branch')
    year_of_admission = request.form.get('year_of_admission')
    student_id = request.form.get('student_id')
    registration_number = request.form.get('registration_number')
    email = request.form.get('email')
    password = request.form.get('password')
    residence = request.form.get('residence', 'day_scholar')
    
    if not all([name, branch, year_of_admission, student_id, registration_number, email, password, residence]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT student_id FROM students 
                WHERE student_id = %s OR registration_number = %s
            ''', (student_id, registration_number))
            
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Student ID or Registration Number already exists'}), 400
            
            cursor.execute('''
                INSERT INTO students (student_id, name, branch, year_of_admission, 
                                     registration_number, email, password, residence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (student_id, name, branch, int(year_of_admission), 
                  registration_number, email, password, residence))
            
            new_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO student_validity (registration_number, is_valid)
                VALUES (%s, %s)
            ''', (registration_number, residence == 'day_scholar'))
            
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True, 
                'message': f'Student {name} added successfully',
                'id': new_id
            })
            
        except Exception as err:
            print(f"Error adding student: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Get Student Details for Edit
@app.route('/admin/get-student/<int:student_id>', methods=['GET'])
def admin_get_student(student_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, student_id, name, branch, year_of_admission, 
                       registration_number, email, residence
                FROM students 
                WHERE id = %s AND is_active = TRUE
            ''', (student_id,))
            
            student = cursor.fetchone()
            cursor.close()
            
            if student:
                return jsonify({
                    'success': True,
                    'student': {
                        'id': student[0],
                        'student_id': student[1],
                        'name': student[2],
                        'branch': student[3],
                        'year': student[4],
                        'registration_number': student[5],
                        'email': student[6],
                        'residence': student[7]
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Student not found'}), 404
                
        except Exception as err:
            print(f"Error getting student: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Update Student
@app.route('/admin/update-student/<int:student_id>', methods=['POST'])
def admin_update_student(student_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    name = request.form.get('name')
    branch = request.form.get('branch')
    year_of_admission = request.form.get('year_of_admission')
    registration_number = request.form.get('registration_number')
    email = request.form.get('email')
    residence = request.form.get('residence', 'day_scholar')
    
    if not all([name, branch, year_of_admission, registration_number, email, residence]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Check if registration number already exists for another student
            cursor.execute('''
                SELECT id FROM students 
                WHERE registration_number = %s AND id != %s
            ''', (registration_number, student_id))
            
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Registration number already exists for another student'}), 400
            
            cursor.execute('''
                UPDATE students SET 
                    name = %s,
                    branch = %s,
                    year_of_admission = %s,
                    registration_number = %s,
                    email = %s,
                    residence = %s
                WHERE id = %s
            ''', (name, branch, int(year_of_admission), registration_number, email, residence, student_id))
            
            # Update validity based on new residence if needed
            cursor.execute('''
                INSERT INTO student_validity (registration_number, is_valid)
                VALUES (%s, %s)
                ON CONFLICT (registration_number) DO UPDATE SET is_valid = EXCLUDED.is_valid
            ''', (registration_number, residence == 'day_scholar'))
            
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Student {name} updated successfully'
            })
            
        except Exception as err:
            print(f"Error updating student: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete Student (soft delete)
@app.route('/admin/delete-student/<int:student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # First get student name for message
            cursor.execute('SELECT name FROM students WHERE id = %s', (student_id,))
            student = cursor.fetchone()
            
            if not student:
                return jsonify({'success': False, 'error': 'Student not found'}), 404
            
            student_name = student[0]
            
            # Soft delete
            cursor.execute('UPDATE students SET is_active = FALSE WHERE id = %s', (student_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Student {student_name} deleted successfully'})
            
        except Exception as err:
            print(f"Error deleting student: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Add Security
@app.route('/admin/add-security', methods=['POST'])
def admin_add_security():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    security_id = request.form.get('security_id')
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not all([security_id, name, email, password]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM security WHERE security_id = %s', (security_id,))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Security ID already exists'}), 400
            
            cursor.execute('''
                INSERT INTO security (security_id, name, email, password)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (security_id, name, email, password))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Security personnel {name} added successfully',
                'id': new_id
            })
            
        except Exception as err:
            print(f"Error adding security: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete Security (soft delete)
@app.route('/admin/delete-security/<int:security_id>', methods=['POST'])
def admin_delete_security(security_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # First get security name for message
            cursor.execute('SELECT name FROM security WHERE id = %s', (security_id,))
            security = cursor.fetchone()
            
            if not security:
                return jsonify({'success': False, 'error': 'Security personnel not found'}), 404
            
            security_name = security[0]
            
            # Soft delete
            cursor.execute('UPDATE security SET is_active = FALSE WHERE id = %s', (security_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Security personnel {security_name} deleted successfully'})
            
        except Exception as err:
            print(f"Error deleting security: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete Students by Year
@app.route('/admin/delete-students-by-year', methods=['POST'])
def admin_delete_students_by_year():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    year = data.get('year')
    current_year = datetime.now().year
    
    if not year:
        return jsonify({'success': False, 'error': 'Year is required'}), 400
    
    try:
        year = int(year)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid year format'}), 400
    
    if current_year - year < 4:
        return jsonify({'success': False, 'error': 'Can only delete students from batches 4 or more years old'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM students 
                WHERE year_of_admission = %s AND is_active = TRUE
            ''', (year,))
            count = cursor.fetchone()[0]
            
            cursor.execute('''
                UPDATE students SET is_active = FALSE 
                WHERE year_of_admission = %s
            ''', (year,))
            
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'{count} students from batch {year} have been deactivated',
                'count': count
            })
            
        except Exception as err:
            print(f"Error deleting students by year: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Admin Bus Management
@app.route('/admin/buses')
def admin_buses():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    buses = []
    stats = {
        'total_buses': 0,
        'active_buses': 0
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get all buses with simplified fields
            cursor.execute('''
                SELECT id, bus_number, route_name, driver_name, 
                       driver_phone, status
                FROM buses 
                ORDER BY status, bus_number
            ''')
            buses = cursor.fetchall()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM buses")
            stats['total_buses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM buses WHERE status = 'active'")
            stats['active_buses'] = cursor.fetchone()[0]
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading bus data: {err}")
            flash('Error loading bus data.', 'error')
        finally:
            conn.close()
    
    return render_template('admin_buses.html', buses=buses, stats=stats)

# Add Bus
@app.route('/admin/add-bus', methods=['POST'])
def admin_add_bus():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    bus_number = request.form.get('bus_number')
    route_name = request.form.get('route_name')
    driver_name = request.form.get('driver_name')
    driver_phone = request.form.get('driver_phone')
    status = request.form.get('status', 'active')
    
    if not all([bus_number, route_name, driver_name, driver_phone]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Check if bus number already exists
            cursor.execute('SELECT id FROM buses WHERE bus_number = %s', (bus_number,))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': f'Bus number {bus_number} already exists'}), 400
            
            cursor.execute('''
                INSERT INTO buses (bus_number, route_name, driver_name, driver_phone, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (bus_number, route_name, driver_name, driver_phone, status))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Bus {bus_number} added successfully',
                'id': new_id
            })
            
        except Exception as err:
            print(f"Error adding bus: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Get Bus Details for Edit
@app.route('/admin/get-bus/<int:bus_id>', methods=['GET'])
def admin_get_bus(bus_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, bus_number, route_name, driver_name, driver_phone, status
                FROM buses 
                WHERE id = %s
            ''', (bus_id,))
            
            bus = cursor.fetchone()
            cursor.close()
            
            if bus:
                return jsonify({
                    'success': True,
                    'bus': {
                        'id': bus[0],
                        'bus_number': bus[1],
                        'route_name': bus[2],
                        'driver_name': bus[3],
                        'driver_phone': bus[4],
                        'status': bus[5]
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Bus not found'}), 404
                
        except Exception as err:
            print(f"Error getting bus: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Update Bus
@app.route('/admin/update-bus/<int:bus_id>', methods=['POST'])
def admin_update_bus(bus_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    bus_number = request.form.get('bus_number')
    route_name = request.form.get('route_name')
    driver_name = request.form.get('driver_name')
    driver_phone = request.form.get('driver_phone')
    status = request.form.get('status')
    
    if not all([bus_number, route_name, driver_name, driver_phone]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Check if bus number already exists for another bus
            cursor.execute('''
                SELECT id FROM buses WHERE bus_number = %s AND id != %s
            ''', (bus_number, bus_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': f'Bus number {bus_number} already exists for another bus'}), 400
            
            cursor.execute('''
                UPDATE buses SET 
                    bus_number = %s,
                    route_name = %s,
                    driver_name = %s,
                    driver_phone = %s,
                    status = %s,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (bus_number, route_name, driver_name, driver_phone, status, bus_id))
            
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'Bus {bus_number} updated successfully'
            })
            
        except Exception as err:
            print(f"Error updating bus: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete Bus
@app.route('/admin/delete-bus/<int:bus_id>', methods=['POST'])
def admin_delete_bus(bus_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # First get bus number for message
            cursor.execute('SELECT bus_number FROM buses WHERE id = %s', (bus_id,))
            bus = cursor.fetchone()
            
            if not bus:
                return jsonify({'success': False, 'error': 'Bus not found'}), 404
            
            bus_number = bus[0]
            
            # Delete bus
            cursor.execute('DELETE FROM buses WHERE id = %s', (bus_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Bus {bus_number} deleted successfully'})
            
        except Exception as err:
            print(f"Error deleting bus: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Security Logout
@app.route('/security/logout')
def security_logout():
    # Clear temp scans on logout
    if session.get('session_id'):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM temp_scans WHERE session_id = %s', (session.get('session_id'),))
                conn.commit()
                cursor.close()
            except Exception as err:
                print(f"Error clearing temp scans: {err}")
            finally:
                conn.close()
    
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('user_type', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('index'))

# General Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Vercel requirement
application = app

if __name__ == '__main__':
    print("🚀 Starting Hasteo Bus Attendance System...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
