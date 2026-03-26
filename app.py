import os
import pg8000
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, date
import logging
import bcrypt

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Neon Database Connection
CONNECTION_STRING = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_cWITUpDwj95q@ep-ancient-leaf-a8knkryg-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require')

def get_db_connection():
    try:
        database_url = os.environ.get('DATABASE_URL', CONNECTION_STRING)
        
        if database_url.startswith('postgresql://'):
            url_parts = database_url[13:]
            user_pass, host_db = url_parts.split('@', 1)
            username, password = user_pass.split(':', 1)
            
            if '/' in host_db:
                host_port, database = host_db.split('/', 1)
            else:
                host_port = host_db
                database = 'neondb'
            
            if ':' in host_port:
                host, port = host_port.split(':', 1)
            else:
                host = host_port
                port = '5432'
            
            if '?' in database:
                database = database.split('?')[0]
            
            conn = pg8000.connect(
                host=host,
                user=username,
                password=password,
                database=database,
                port=int(port),
                ssl_context=True
            )
            return conn
            
    except Exception as err:
        print(f"Database connection failed: {err}")
        return None

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    branch VARCHAR(50),
                    year_of_admission INTEGER,
                    registration_number VARCHAR(20) UNIQUE,
                    residence VARCHAR(20) CHECK (residence IN ('day_scholar', 'hosteller')),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    created_date DATE DEFAULT CURRENT_DATE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security (
                    id SERIAL PRIMARY KEY,
                    security_id VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buses (
                    id SERIAL PRIMARY KEY,
                    bus_number VARCHAR(20) UNIQUE NOT NULL,
                    route_name VARCHAR(100) NOT NULL,
                    driver_name VARCHAR(100) NOT NULL,
                    driver_phone VARCHAR(20) NOT NULL,
                    capacity INTEGER DEFAULT 40,
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'inactive')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bus_logs (
                    id SERIAL PRIMARY KEY,
                    log_id VARCHAR(50) UNIQUE NOT NULL,
                    bus_id INTEGER NOT NULL REFERENCES buses(id) ON DELETE CASCADE,
                    security_id VARCHAR(20) NOT NULL REFERENCES security(security_id) ON DELETE CASCADE,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    log_date DATE DEFAULT CURRENT_DATE,
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
                    total_scans INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id SERIAL PRIMARY KEY,
                    log_id VARCHAR(50) NOT NULL REFERENCES bus_logs(log_id) ON DELETE CASCADE,
                    student_id VARCHAR(20) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scan_date DATE DEFAULT CURRENT_DATE,
                    scan_type VARCHAR(20) DEFAULT 'check_in' CHECK (scan_type IN ('check_in', 'check_out')),
                    is_verified BOOLEAN DEFAULT TRUE
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_branch ON students(branch)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_active ON students(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_active ON security(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_buses_status ON buses(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bus_logs_date ON bus_logs(log_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scans_date ON scans(scan_date)')
            
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

# Public Demo Scanner
@app.route('/scan')
def scanner():
    return render_template('scan.html')

# Student Login
@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT student_id, name, password FROM students 
                    WHERE student_id = %s AND is_active = TRUE
                ''', (student_id,))
                
                student = cursor.fetchone()
                cursor.close()
                
                if student and verify_password(password, student[2]):
                    session['user_type'] = 'student'
                    session['user_id'] = student[0]
                    session['student_name'] = student[1]
                    session['logged_in'] = True
                    flash(f'Welcome {student[1]}!', 'success')
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
        flash('Please login as student.', 'warning')
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    student = None
    total_attendance = 0
    attendance_rate = 0
    monthly_attendance = 0
    recent_attendance = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT student_id, name, email, branch, year_of_admission, 
                       registration_number, residence
                FROM students 
                WHERE student_id = %s AND is_active = TRUE
            ''', (session.get('user_id'),))
            
            student_row = cursor.fetchone()
            if student_row:
                student = {
                    'student_id': student_row[0],
                    'name': student_row[1],
                    'email': student_row[2],
                    'branch': student_row[3],
                    'year_of_admission': student_row[4],
                    'registration_number': student_row[5],
                    'residence': student_row[6]
                }
            
            cursor.execute('SELECT COUNT(*) FROM scans WHERE student_id = %s', (session.get('user_id'),))
            total_attendance = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM scans 
                WHERE student_id = %s AND scan_date >= DATE_TRUNC('month', CURRENT_DATE)
            ''', (session.get('user_id'),))
            monthly_attendance = cursor.fetchone()[0]
            
            attendance_rate = round((monthly_attendance / 22) * 100) if monthly_attendance > 0 else 0
            
            cursor.execute('''
                SELECT s.scan_date, s.scan_time, b.bus_number
                FROM scans s
                JOIN bus_logs bl ON s.log_id = bl.log_id
                JOIN buses b ON bl.bus_id = b.id
                WHERE s.student_id = %s
                ORDER BY s.scan_date DESC, s.scan_time DESC
                LIMIT 5
            ''', (session.get('user_id'),))
            recent_attendance = cursor.fetchall()
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading student dashboard: {err}")
            flash('Error loading dashboard data.', 'error')
        finally:
            conn.close()
    
    return render_template('student_dashboard.html', 
                         student=student,
                         total_attendance=total_attendance,
                         attendance_rate=attendance_rate,
                         monthly_attendance=monthly_attendance,
                         recent_attendance=recent_attendance,
                         now=datetime.now())

@app.route('/student/attendance')
def student_attendance():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        flash('Please login as student.', 'warning')
        return redirect(url_for('student_login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    conn = get_db_connection()
    attendance_records = []
    total_attendance = 0
    attendance_rate = 0
    weekly_attendance = 0
    monthly_attendance = 0
    total_pages = 0
    years = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM scans WHERE student_id = %s', (session.get('user_id'),))
            total_attendance = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM scans 
                WHERE student_id = %s AND scan_date >= DATE_TRUNC('month', CURRENT_DATE)
            ''', (session.get('user_id'),))
            monthly_attendance = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM scans 
                WHERE student_id = %s AND scan_date >= DATE_TRUNC('week', CURRENT_DATE)
            ''', (session.get('user_id'),))
            weekly_attendance = cursor.fetchone()[0]
            
            attendance_rate = round((monthly_attendance / 22) * 100) if monthly_attendance > 0 else 0
            
            offset = (page - 1) * per_page
            cursor.execute('''
                SELECT s.scan_date, s.scan_time, b.bus_number, b.route_name
                FROM scans s
                JOIN bus_logs bl ON s.log_id = bl.log_id
                JOIN buses b ON bl.bus_id = b.id
                WHERE s.student_id = %s
                ORDER BY s.scan_date DESC, s.scan_time DESC
                LIMIT %s OFFSET %s
            ''', (session.get('user_id'), per_page, offset))
            attendance_records = cursor.fetchall()
            
            total_pages = (total_attendance + per_page - 1) // per_page
            
            cursor.execute('''
                SELECT DISTINCT EXTRACT(YEAR FROM scan_date) as year
                FROM scans WHERE student_id = %s
                ORDER BY year DESC
            ''', (session.get('user_id'),))
            years = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading attendance: {err}")
            flash('Error loading attendance records.', 'error')
        finally:
            conn.close()
    
    months = [
        {'value': '01', 'name': 'January'}, {'value': '02', 'name': 'February'},
        {'value': '03', 'name': 'March'}, {'value': '04', 'name': 'April'},
        {'value': '05', 'name': 'May'}, {'value': '06', 'name': 'June'},
        {'value': '07', 'name': 'July'}, {'value': '08', 'name': 'August'},
        {'value': '09', 'name': 'September'}, {'value': '10', 'name': 'October'},
        {'value': '11', 'name': 'November'}, {'value': '12', 'name': 'December'}
    ]
    
    return render_template('student_attendance.html',
                         attendance_records=attendance_records,
                         total_attendance=total_attendance,
                         attendance_rate=attendance_rate,
                         weekly_attendance=weekly_attendance,
                         monthly_attendance=monthly_attendance,
                         years=years,
                         months=months,
                         current_page=page,
                         total_pages=total_pages,
                         now=datetime.now())

@app.route('/student/profile', methods=['GET'])
def student_profile():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        flash('Please login as student.', 'warning')
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    student = None
    total_attendance = 0
    attendance_rate = 0
    
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT student_id, name, email, branch, year_of_admission, 
                       registration_number, residence
                FROM students 
                WHERE student_id = %s AND is_active = TRUE
            ''', (session.get('user_id'),))
            
            student_row = cursor.fetchone()
            if student_row:
                student = {
                    'student_id': student_row[0],
                    'name': student_row[1],
                    'email': student_row[2],
                    'branch': student_row[3],
                    'year_of_admission': student_row[4],
                    'registration_number': student_row[5],
                    'residence': student_row[6]
                }
            
            cursor.execute('SELECT COUNT(*) FROM scans WHERE student_id = %s', (session.get('user_id'),))
            total_attendance = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM scans 
                WHERE student_id = %s AND scan_date >= DATE_TRUNC('month', CURRENT_DATE)
            ''', (session.get('user_id'),))
            monthly_attendance = cursor.fetchone()[0]
            
            attendance_rate = round((monthly_attendance / 22) * 100) if monthly_attendance > 0 else 0
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading profile: {err}")
            flash('Error loading profile data.', 'error')
        finally:
            conn.close()
    
    return render_template('student_profile.html',
                         student=student,
                         total_attendance=total_attendance,
                         attendance_rate=attendance_rate,
                         now=datetime.now())

@app.route('/student/update-profile', methods=['POST'])
def student_update_profile():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    name = request.form.get('name')
    email = request.form.get('email')
    residence = request.form.get('residence')
    
    if not all([name, email, residence]):
        flash('All fields are required', 'error')
        return redirect(url_for('student_profile'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE students SET name = %s, email = %s, residence = %s
                WHERE student_id = %s
            ''', (name, email, residence, session.get('user_id')))
            conn.commit()
            cursor.close()
            
            session['student_name'] = name
            flash('Profile updated successfully!', 'success')
            
        except Exception as err:
            print(f"Error updating profile: {err}")
            flash('Error updating profile.', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('student_profile'))

@app.route('/student/change-password', methods=['POST'])
def student_change_password():
    if not session.get('logged_in') or session.get('user_type') != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('All fields are required', 'error')
        return redirect(url_for('student_profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('student_profile'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('student_profile'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM students WHERE student_id = %s AND is_active = TRUE', (session.get('user_id'),))
            student = cursor.fetchone()
            
            if not student or not verify_password(current_password, student[0]):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('student_profile'))
            
            hashed_password = hash_password(new_password)
            cursor.execute('UPDATE students SET password = %s WHERE student_id = %s', (hashed_password, session.get('user_id')))
            conn.commit()
            cursor.close()
            
            flash('Password changed successfully!', 'success')
            
        except Exception as err:
            print(f"Error changing password: {err}")
            flash('Error changing password.', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('student_profile'))

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
                    SELECT security_id, name, password FROM security 
                    WHERE security_id = %s AND is_active = TRUE
                ''', (security_id,))
                
                security = cursor.fetchone()
                cursor.close()
                
                if security and verify_password(password, security[2]):
                    session['user_type'] = 'security'
                    session['user_id'] = security[0]
                    session['security_name'] = security[1]
                    session['logged_in'] = True
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
    pending_logs = 0
    today_scans = 0
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM bus_logs WHERE security_id = %s AND status = %s', (session.get('user_id'), 'pending'))
            pending_logs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM scans WHERE scan_date = CURRENT_DATE')
            today_scans = cursor.fetchone()[0]
            cursor.close()
            
        except Exception as err:
            print(f"Error loading dashboard data: {err}")
        finally:
            conn.close()
    
    return render_template('security_dashboard.html', 
                         pending_bus_logs=pending_logs,
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
            cursor.execute('SELECT id, bus_number, route_name, driver_name FROM buses WHERE status = %s ORDER BY bus_number', ('active',))
            active_buses = cursor.fetchall()
            
            cursor.execute('''
                SELECT bl.id, b.bus_number, bl.entry_time, bl.exit_time, bl.status
                FROM bus_logs bl JOIN buses b ON bl.bus_id = b.id
                WHERE bl.security_id = %s AND bl.log_date = CURRENT_DATE ORDER BY bl.entry_time DESC
            ''', (session.get('user_id'),))
            today_logs = cursor.fetchall()
            cursor.close()
            
        except Exception as err:
            print(f"Error loading log data: {err}")
            flash('Error loading log data.', 'error')
        finally:
            conn.close()
    
    return render_template('security_bus.html', active_buses=active_buses, today_logs=today_logs)

# Record bus entry
@app.route('/security/bus/entry/<int:bus_id>', methods=['POST'])
def record_bus_entry(bus_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT bus_number FROM buses WHERE id = %s', (bus_id,))
            bus = cursor.fetchone()
            if not bus:
                return jsonify({'success': False, 'error': 'Bus not found'}), 404
            
            cursor.execute('SELECT id FROM bus_logs WHERE bus_id = %s AND status = %s', (bus_id, 'pending'))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Bus already has a pending log'}), 400
            
            log_id = f"log_{datetime.now().strftime('%Y%m%d%H%M%S')}_{bus_id}"
            cursor.execute('''
                INSERT INTO bus_logs (log_id, bus_id, security_id, entry_time, status)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s) RETURNING id
            ''', (log_id, bus_id, session.get('user_id'), 'pending'))
            
            log_db_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Entry recorded for bus {bus[0]}', 'log_id': log_db_id})
            
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
            cursor.execute('''
                UPDATE bus_logs SET exit_time = CURRENT_TIMESTAMP
                WHERE id = %s AND security_id = %s AND status = %s RETURNING bus_id
            ''', (log_id, session.get('user_id'), 'pending'))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Log not found or already completed'}), 404
            
            cursor.execute('SELECT bus_number FROM buses WHERE id = %s', (result[0],))
            bus = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Exit recorded for bus {bus[0] if bus else "Unknown"}'})
            
        except Exception as err:
            print(f"Error recording bus exit: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete bus log
@app.route('/security/bus/delete/<int:log_id>', methods=['POST'])
def delete_bus_log(log_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bus_logs WHERE id = %s AND security_id = %s RETURNING bus_id', (log_id, session.get('user_id')))
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Log not found'}), 404
            
            cursor.execute('SELECT bus_number FROM buses WHERE id = %s', (result[0],))
            bus = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Log for bus {bus[0] if bus else "Unknown"} deleted'})
            
        except Exception as err:
            print(f"Error deleting log: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Security Student Logs
@app.route('/security/student-logs')
def security_student_logs():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return redirect(url_for('security_login'))
    
    conn = get_db_connection()
    active_buses = []
    current_log_scans = []
    permanent_scans_today = []
    pending_log_id = None
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, bus_number, route_name FROM buses WHERE status = %s ORDER BY bus_number', ('active',))
            active_buses = cursor.fetchall()
            
            cursor.execute('SELECT log_id, id FROM bus_logs WHERE security_id = %s AND status = %s ORDER BY entry_time DESC LIMIT 1', (session.get('user_id'), 'pending'))
            pending_log = cursor.fetchone()
            
            if pending_log:
                pending_log_id = pending_log[1]
                cursor.execute('''
                    SELECT s.id, s.student_id, u.name, u.branch, u.residence, s.scan_time
                    FROM scans s JOIN students u ON s.student_id = u.student_id
                    WHERE s.log_id = %s ORDER BY s.scan_time DESC
                ''', (pending_log[0],))
                current_log_scans = cursor.fetchall()
            
            cursor.execute('''
                SELECT s.id, s.student_id, u.name, u.branch, u.residence, b.bus_number, s.scan_time
                FROM scans s
                JOIN students u ON s.student_id = u.student_id
                JOIN bus_logs bl ON s.log_id = bl.log_id
                JOIN buses b ON bl.bus_id = b.id
                WHERE s.scan_date = CURRENT_DATE
                ORDER BY s.scan_time DESC LIMIT 50
            ''')
            permanent_scans_today = cursor.fetchall()
            cursor.close()
            
        except Exception as err:
            print(f"Error loading data: {err}")
            flash('Error loading data.', 'error')
        finally:
            conn.close()
    
    return render_template('security_student.html', 
                         active_buses=active_buses,
                         current_scans=current_log_scans,
                         permanent_scans=permanent_scans_today,
                         pending_log_id=pending_log_id)

# Security Scanner page
@app.route('/security/scan/<int:bus_id>')
def security_scan(bus_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return redirect(url_for('security_login'))
    
    conn = get_db_connection()
    bus = None
    pending_log = None
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, bus_number, route_name FROM buses WHERE id = %s', (bus_id,))
            bus = cursor.fetchone()
            
            if bus:
                cursor.execute('SELECT log_id, id FROM bus_logs WHERE bus_id = %s AND status = %s', (bus_id, 'pending'))
                pending_log = cursor.fetchone()
                if pending_log:
                    session['pending_log_id'] = pending_log[1]
                else:
                    session.pop('pending_log_id', None)
            cursor.close()
            
        except Exception as err:
            print(f"Error loading bus: {err}")
            flash('Error loading bus details.', 'error')
        finally:
            conn.close()
    
    if not bus:
        flash('Bus not found', 'error')
        return redirect(url_for('security_student_logs'))
    
    return render_template('security_scan.html', bus=bus, has_pending_log=pending_log is not None)

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
            cursor.execute('SELECT log_id FROM bus_logs WHERE bus_id = %s AND status = %s', (bus_id, 'pending'))
            pending_log = cursor.fetchone()
            
            if not pending_log:
                return jsonify({'success': False, 'error': 'No pending log for this bus. Please record entry first.'}), 400
            
            log_id = pending_log[0]
            
            cursor.execute('SELECT student_id, name, branch, residence FROM students WHERE student_id = %s AND is_active = TRUE', (student_id,))
            student = cursor.fetchone()
            if not student:
                return jsonify({'success': False, 'error': 'Student not found or inactive'}), 404
            
            cursor.execute('SELECT id FROM scans WHERE log_id = %s AND student_id = %s', (log_id, student_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Student already scanned in this log', 'student_name': student[1]}), 400
            
            cursor.execute('INSERT INTO scans (log_id, student_id, scan_type) VALUES (%s, %s, %s) RETURNING id', (log_id, student_id, 'check_in'))
            scan_id = cursor.fetchone()[0]
            
            cursor.execute('UPDATE bus_logs SET total_scans = total_scans + 1 WHERE log_id = %s', (log_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Student {student[1]} scanned successfully', 'student': {'id': student_id, 'name': student[1], 'branch': student[2], 'residence': student[3], 'scan_id': scan_id}})
            
        except Exception as err:
            print(f"Error saving scan: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Get current scans
@app.route('/api/security/current-scans', methods=['GET'])
def get_current_scans_by_bus():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    bus_id = request.args.get('bus_id')
    if not bus_id:
        return jsonify({'success': False, 'error': 'Bus ID required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT log_id FROM bus_logs WHERE bus_id = %s AND status = %s', (bus_id, 'pending'))
            pending = cursor.fetchone()
            
            if not pending:
                return jsonify({'success': True, 'scans': []})
            
            cursor.execute('''
                SELECT s.id, s.student_id, u.name, u.branch, u.residence, s.scan_time
                FROM scans s JOIN students u ON s.student_id = u.student_id
                WHERE s.log_id = %s ORDER BY s.scan_time DESC
            ''', (pending[0],))
            
            scans = cursor.fetchall()
            cursor.close()
            
            scans_list = [{'id': s[0], 'student_id': s[1], 'student_name': s[2], 'branch': s[3], 'residence': s[4], 'scan_time': s[5].strftime('%I:%M %p') if s[5] else ''} for s in scans]
            return jsonify({'success': True, 'scans': scans_list})
            
        except Exception as err:
            print(f"Error getting scans: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete scan
@app.route('/api/security/delete-scan/<int:scan_id>', methods=['POST'])
def delete_temp_scan(scan_id):
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT log_id, student_id FROM scans WHERE id = %s', (scan_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Scan not found'}), 404
            
            log_id = result[0]
            cursor.execute('DELETE FROM scans WHERE id = %s', (scan_id,))
            cursor.execute('UPDATE bus_logs SET total_scans = total_scans - 1 WHERE log_id = %s', (log_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': 'Scan deleted successfully'})
            
        except Exception as err:
            print(f"Error deleting scan: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# API endpoint for dashboard stats
@app.route('/api/security/dashboard-stats', methods=['GET'])
def api_security_dashboard_stats():
    if not session.get('logged_in') or session.get('user_type') != 'security':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM buses WHERE status = %s', ('active',))
            active_buses = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM scans WHERE scan_time >= NOW() - INTERVAL %s', ('1 hour',))
            hourly_scans = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(CASE WHEN status = %s THEN 1 END) as completed, COUNT(*) as total FROM bus_logs WHERE log_date = CURRENT_DATE', ('completed',))
            result = cursor.fetchone()
            completed = result[0] if result else 0
            total = result[1] if result else 0
            completion_rate = round((completed / total) * 100) if total > 0 else 0
            
            cursor.execute('SELECT COUNT(*) FROM bus_logs WHERE log_date = CURRENT_DATE AND status = %s', ('completed',))
            completed_trips = cursor.fetchone()[0]
            cursor.close()
            
            return jsonify({'success': True, 'active_buses': active_buses, 'hourly_scans': hourly_scans, 'completion_rate': completion_rate, 'completed_trips': completed_trips})
            
        except Exception as err:
            print(f"Error getting stats: {err}")
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
    student_count = security_count = bus_count = total_scans = today_scans = 0
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = TRUE")
            student_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM security WHERE is_active = TRUE")
            security_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM buses WHERE status = 'active'")
            bus_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM scans")
            total_scans = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM scans WHERE scan_date = CURRENT_DATE")
            today_scans = cursor.fetchone()[0]
            cursor.close()
            
        except Exception as err:
            print(f"Error loading dashboard data: {err}")
            flash('Error loading dashboard data.', 'error')
        finally:
            conn.close()
    
    return render_template('admin.html', student_count=student_count, security_count=security_count, bus_count=bus_count, total_scans=total_scans, today_scans=today_scans, now=datetime.now())

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
    stats = {'total_students': 0, 'total_security': 0, 'students_by_branch': {}, 'students_by_year': {}}
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, student_id, name, branch, year_of_admission, registration_number, email, residence FROM students WHERE is_active = TRUE ORDER BY year_of_admission DESC, branch, name')
            students = cursor.fetchall()
            cursor.execute('SELECT id, security_id, name, email FROM security WHERE is_active = TRUE ORDER BY name')
            security_personnel = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = TRUE")
            stats['total_students'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM security WHERE is_active = TRUE")
            stats['total_security'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT branch, COUNT(*) FROM students WHERE is_active = TRUE AND branch IS NOT NULL GROUP BY branch ORDER BY branch')
            for branch, count in cursor.fetchall():
                stats['students_by_branch'][branch] = count
            
            cursor.execute('SELECT year_of_admission, COUNT(*) FROM students WHERE is_active = TRUE AND year_of_admission IS NOT NULL GROUP BY year_of_admission ORDER BY year_of_admission DESC')
            for year, count in cursor.fetchall():
                stats['students_by_year'][year] = count
                if current_year - year >= 4:
                    eligible_batches[year] = count
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading user data: {err}")
            flash('Error loading user data.', 'error')
        finally:
            conn.close()
    
    return render_template('admin_users.html', students=students, security=security_personnel, stats=stats, eligible_batches=eligible_batches, now=datetime.now())

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
    residence = request.form.get('residence', 'day_scholar')
    
    if not all([name, branch, year_of_admission, student_id, registration_number, email, residence]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    password = hash_password(registration_number)
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT student_id FROM students WHERE student_id = %s OR registration_number = %s', (student_id, registration_number))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Student ID or Registration Number already exists'}), 400
            
            cursor.execute('INSERT INTO students (student_id, name, email, password, branch, year_of_admission, registration_number, residence) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id', (student_id, name, email, password, branch, int(year_of_admission), registration_number, residence))
            new_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Student {name} added successfully. Password is: {registration_number}', 'id': new_id, 'password': registration_number})
            
        except Exception as err:
            print(f"Error adding student: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Get Student
@app.route('/admin/get-student/<int:student_id>', methods=['GET'])
def admin_get_student(student_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, student_id, name, branch, year_of_admission, registration_number, email, residence FROM students WHERE id = %s AND is_active = TRUE', (student_id,))
            student = cursor.fetchone()
            cursor.close()
            
            if student:
                return jsonify({'success': True, 'student': {'id': student[0], 'student_id': student[1], 'name': student[2], 'branch': student[3], 'year': student[4], 'registration_number': student[5], 'email': student[6], 'residence': student[7]}})
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
            cursor.execute('SELECT id FROM students WHERE registration_number = %s AND id != %s', (registration_number, student_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Registration number already exists for another student'}), 400
            
            cursor.execute('UPDATE students SET name = %s, branch = %s, year_of_admission = %s, registration_number = %s, email = %s, residence = %s WHERE id = %s', (name, branch, int(year_of_admission), registration_number, email, residence, student_id))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Student {name} updated successfully'})
            
        except Exception as err:
            print(f"Error updating student: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete Student
@app.route('/admin/delete-student/<int:student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM students WHERE id = %s', (student_id,))
            student = cursor.fetchone()
            if not student:
                return jsonify({'success': False, 'error': 'Student not found'}), 404
            
            cursor.execute('UPDATE students SET is_active = FALSE WHERE id = %s', (student_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Student {student[0]} deleted successfully'})
            
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
    
    hashed_password = hash_password(password)
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM security WHERE security_id = %s', (security_id,))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Security ID already exists'}), 400
            
            cursor.execute('INSERT INTO security (security_id, name, email, password) VALUES (%s, %s, %s, %s) RETURNING id', (security_id, name, email, hashed_password))
            new_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Security personnel {name} added successfully', 'id': new_id})
            
        except Exception as err:
            print(f"Error adding security: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Delete Security
@app.route('/admin/delete-security/<int:security_id>', methods=['POST'])
def admin_delete_security(security_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM security WHERE id = %s', (security_id,))
            security = cursor.fetchone()
            if not security:
                return jsonify({'success': False, 'error': 'Security personnel not found'}), 404
            
            cursor.execute('UPDATE security SET is_active = FALSE WHERE id = %s', (security_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Security personnel {security[0]} deleted successfully'})
            
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
            cursor.execute('SELECT COUNT(*) FROM students WHERE year_of_admission = %s AND is_active = TRUE', (year,))
            count = cursor.fetchone()[0]
            
            cursor.execute('UPDATE students SET is_active = FALSE WHERE year_of_admission = %s', (year,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'{count} students from batch {year} have been deactivated', 'count': count})
            
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
    stats = {'total_buses': 0, 'active_buses': 0}
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, bus_number, route_name, driver_name, driver_phone, status, capacity FROM buses ORDER BY status, bus_number')
            buses = cursor.fetchall()
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
    capacity = request.form.get('capacity', 40)
    status = request.form.get('status', 'active')
    
    if not all([bus_number, route_name, driver_name, driver_phone]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM buses WHERE bus_number = %s', (bus_number,))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': f'Bus number {bus_number} already exists'}), 400
            
            cursor.execute('INSERT INTO buses (bus_number, route_name, driver_name, driver_phone, capacity, status) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id', (bus_number, route_name, driver_name, driver_phone, int(capacity), status))
            new_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Bus {bus_number} added successfully', 'id': new_id})
            
        except Exception as err:
            print(f"Error adding bus: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Get Bus
@app.route('/admin/get-bus/<int:bus_id>', methods=['GET'])
def admin_get_bus(bus_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, bus_number, route_name, driver_name, driver_phone, status, capacity FROM buses WHERE id = %s', (bus_id,))
            bus = cursor.fetchone()
            cursor.close()
            
            if bus:
                return jsonify({'success': True, 'bus': {'id': bus[0], 'bus_number': bus[1], 'route_name': bus[2], 'driver_name': bus[3], 'driver_phone': bus[4], 'status': bus[5], 'capacity': bus[6]}})
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
    capacity = request.form.get('capacity', 40)
    
    if not all([bus_number, route_name, driver_name, driver_phone]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM buses WHERE bus_number = %s AND id != %s', (bus_number, bus_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': f'Bus number {bus_number} already exists for another bus'}), 400
            
            cursor.execute('UPDATE buses SET bus_number = %s, route_name = %s, driver_name = %s, driver_phone = %s, status = %s, capacity = %s WHERE id = %s', (bus_number, route_name, driver_name, driver_phone, status, int(capacity), bus_id))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Bus {bus_number} updated successfully'})
            
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
            cursor.execute('SELECT bus_number FROM buses WHERE id = %s', (bus_id,))
            bus = cursor.fetchone()
            if not bus:
                return jsonify({'success': False, 'error': 'Bus not found'}), 404
            
            cursor.execute('DELETE FROM buses WHERE id = %s', (bus_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': f'Bus {bus[0]} deleted successfully'})
            
        except Exception as err:
            print(f"Error deleting bus: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Logout Routes
@app.route('/security/logout')
def security_logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('user_type', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('index'))

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