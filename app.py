import os
import logging
import pg8000
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
import bcrypt
from datetime import datetime, date, timedelta
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'hasteo-college-bus-secret-key-2025')

# Configure for Vercel
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.config['PREFERRED_URL_SCHEME'] = 'https'
# Persistent session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # 30 days
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Neon Database Connection
def get_db_connection():
    try:
        database_url = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_bEM3iClDvFu0@ep-orange-voice-ahyaah1x-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require')
        
        from urllib.parse import urlparse
        result = urlparse(database_url)
        
        username = result.username
        password = result.password
        database = result.path[1:] if result.path.startswith('/') else result.path
        hostname = result.hostname
        port = result.port or 5432
        
        if '?' in database:
            database = database.split('?')[0]
        
        logging.info(f"🔗 Connecting to database: {hostname}:{port}/{database}")
        
        conn = pg8000.connect(
            host=hostname,
            port=port,
            user=username,
            password=password,
            database=database,
            ssl_context=True
        )
        
        conn.autocommit = True
        logging.info("✅ Database connection successful!")
        return conn
        
    except Exception as err:
        logging.error(f"❌ Database connection error: {str(err)}")
        return None

def init_db():
    """Initialize database tables - NO SAMPLE DATA"""
    logging.info("📦 Initializing database...")
    conn = get_db_connection()
    if not conn:
        logging.warning("⚠️ Database connection failed")
        return
    
    try:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'security')),
                full_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Create students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                register_no VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                course VARCHAR(50) NOT NULL,
                admission_year VARCHAR(4) NOT NULL,
                bus_no VARCHAR(10),
                department VARCHAR(100),
                year VARCHAR(10),
                phone VARCHAR(15),
                email VARCHAR(100),
                bus_fees_paid BOOLEAN DEFAULT FALSE,
                monthly_fee DECIMAL(10,2) DEFAULT 1000.00,
                total_due DECIMAL(10,2) DEFAULT 0.00,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
                register_no VARCHAR(20) NOT NULL,
                bus_no VARCHAR(10) NOT NULL,
                scan_type VARCHAR(10) CHECK (scan_type IN ('entry', 'exit')),
                location VARCHAR(100) DEFAULT 'College Campus',
                security_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );
        ''')
        
        # Create bus_timestamps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bus_timestamps (
                id SERIAL PRIMARY KEY,
                bus_no VARCHAR(10) NOT NULL,
                timestamp_type VARCHAR(10) CHECK (timestamp_type IN ('arrival', 'departure')),
                security_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                location VARCHAR(100) DEFAULT 'College Campus',
                notes TEXT
            );
        ''')
        
        # Create ONLY admin user with password 'official'
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            hashed_password = bcrypt.hashpw('official'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, %s, %s)",
                ('admin', hashed_password.decode('utf-8'), 'admin', 'System Administrator')
            )
            logging.info("✅ Created admin user (username: admin, password: official)")
        else:
            logging.info("✅ Admin user already exists")
        
        logging.info("✅ Database initialized successfully!")
        
    except Exception as e:
        logging.error(f"❌ Database initialization error: {str(e)}")
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

# Initialize database on startup
init_db()

# ==================== AUTHENTICATION DECORATORS ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('index'))
        # Make session permanent for remember me
        session.permanent = True
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('admin_login'))
        session.permanent = True
        return f(*args, **kwargs)
    return decorated_function

def security_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'security':
            flash('Security personnel access required', 'error')
            return redirect(url_for('security_login'))
        session.permanent = True
        return f(*args, **kwargs)
    return decorated_function

# ==================== STATIC FILES ====================
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# ==================== MAIN ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        
        # Check default admin credentials
        if username == 'admin' and password == 'official':
            session['user_id'] = 1
            session['username'] = 'admin'
            session['role'] = 'admin'
            session['full_name'] = 'System Administrator'
            session['logged_in'] = True
            session.permanent = remember_me
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        # Check database for other admin users
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = %s AND role = 'admin'", (username,))
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['role'] = user[3]
                    session['full_name'] = user[4]
                    session['logged_in'] = True
                    session.permanent = remember_me
                    flash('Admin login successful!', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Invalid admin credentials', 'error')
            except Exception as e:
                flash(f'Login error: {str(e)}', 'error')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Database not available', 'error')
    
    return render_template('auth/admin_login.html')

@app.route('/security-login', methods=['GET', 'POST'])
def security_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = %s AND role = 'security'", (username,))
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['role'] = user[3]
                    session['full_name'] = user[4]
                    session['logged_in'] = True
                    session.permanent = remember_me
                    flash('Security login successful!', 'success')
                    return redirect(url_for('security_dashboard'))
                else:
                    flash('Invalid security credentials', 'error')
            except Exception as e:
                flash(f'Login error: {str(e)}', 'error')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Database not available', 'error')
    
    return render_template('auth/security_login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ==================== ADMIN ROUTES ====================
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    stats = {
        'total_students': 0,
        'students_with_due': 0,
        'total_security': 0,
        'today_scans': 0
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get today's date
            today = date.today()
            
            # Total students
            cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = TRUE")
            stats['total_students'] = cursor.fetchone()[0] or 0
            
            # Students with due
            cursor.execute("SELECT COUNT(*) FROM students WHERE bus_fees_paid = FALSE AND is_active = TRUE")
            stats['students_with_due'] = cursor.fetchone()[0] or 0
            
            # Total security personnel
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'security'")
            stats['total_security'] = cursor.fetchone()[0] or 0
            
            # Today's scans
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE DATE(timestamp) = %s", (today,))
            stats['today_scans'] = cursor.fetchone()[0] or 0
            
        except Exception as e:
            logging.error(f"Error loading dashboard stats: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('admin/admin_dashboard.html', stats=stats)

@app.route('/admin/students')
@admin_required
def student_management():
    return render_template('admin/student_management.html')

@app.route('/admin/security')
@admin_required
def security_management():
    return render_template('admin/security_management.html')

# ==================== SECURITY ROUTES ====================
@app.route('/security')
@security_required
def security_dashboard():
    conn = get_db_connection()
    stats = {
        'today_entry': 0,
        'today_exit': 0,
        'total_scans': 0,
        'active_buses': 0
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get today's date
            today = date.today()
            
            # Today's entry scans
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE DATE(timestamp) = %s AND scan_type = 'entry'", (today,))
            stats['today_entry'] = cursor.fetchone()[0] or 0
            
            # Today's exit scans
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE DATE(timestamp) = %s AND scan_type = 'exit'", (today,))
            stats['today_exit'] = cursor.fetchone()[0] or 0
            
            # Total scans (all time)
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE security_id = %s", (session['user_id'],))
            stats['total_scans'] = cursor.fetchone()[0] or 0
            
            # Active buses (distinct bus numbers from today's attendance)
            cursor.execute("SELECT COUNT(DISTINCT bus_no) FROM attendance WHERE DATE(timestamp) = %s", (today,))
            stats['active_buses'] = cursor.fetchone()[0] or 0
            
        except Exception as e:
            logging.error(f"Error loading security stats: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('security/security_dashboard.html', stats=stats)

@app.route('/security/scan')
@security_required
def scan():
    return render_template('security/scan.html')

@app.route('/security/history')
@security_required
def history():
    return render_template('security/history.html')

@app.route('/security/bus-logs')
@security_required
def bus_logs():
    return render_template('security/bus_logs.html')

# ==================== API ROUTES ====================
@app.route('/api/students', methods=['GET', 'POST'])
@login_required
def handle_students():
    if request.method == 'GET':
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database not available'}), 500
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE is_active = TRUE ORDER BY created_at DESC")
            students = cursor.fetchall()
            
            student_list = []
            for student in students:
                student_list.append({
                    'id': student[0],
                    'register_no': student[1],
                    'name': student[2],
                    'course': student[3],
                    'admission_year': student[4],
                    'bus_no': student[5],
                    'department': student[6],
                    'year': student[7],
                    'phone': student[8],
                    'email': student[9],
                    'bus_fees_paid': student[10],
                    'monthly_fee': float(student[11]) if student[11] else 0,
                    'total_due': float(student[12]) if student[12] else 0,
                    'is_active': student[13]
                })
            
            return jsonify(student_list)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    
    elif request.method == 'POST':
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.json
        register_no = data.get('register_no')
        
        # Validate registration number format (e.g., SCS/10187/23)
        if not register_no or not register_no.count('/') == 2:
            return jsonify({'error': 'Invalid registration number format. Use format: COURSE/ID/YEAR'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database not available'}), 500
        
        try:
            cursor = conn.cursor()
            
            # Check if student already exists
            cursor.execute("SELECT id FROM students WHERE register_no = %s", (register_no,))
            if cursor.fetchone():
                return jsonify({'error': 'Student with this registration number already exists'}), 400
            
            cursor.execute('''
                INSERT INTO students 
                (register_no, name, course, admission_year, bus_no, department, year, phone, email, bus_fees_paid, monthly_fee)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                register_no,
                data.get('name'),
                data.get('course', ''),
                data.get('admission_year', ''),
                data.get('bus_no'),
                data.get('department', ''),
                data.get('year', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('bus_fees_paid', False),
                data.get('monthly_fee', 1000.00)
            ))
            
            student_id = cursor.fetchone()[0]
            
            return jsonify({
                'success': True, 
                'message': 'Student added successfully',
                'student_id': student_id
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()

@app.route('/api/security', methods=['GET', 'POST'])
@admin_required
def handle_security():
    if request.method == 'GET':
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database not available'}), 500
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE role = 'security' ORDER BY created_at DESC")
            security_users = cursor.fetchall()
            
            users_list = []
            for user in security_users:
                users_list.append({
                    'id': user[0],
                    'username': user[1],
                    'full_name': user[4],
                    'created_at': user[5].isoformat() if user[5] else None
                })
            
            return jsonify(users_list)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    
    elif request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name')
        
        if not username or not password or not full_name:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database not available'}), 500
        
        try:
            cursor = conn.cursor()
            
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({'error': 'Username already exists'}), 400
            
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Insert new security user
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, %s, %s) RETURNING id",
                (username, hashed_password.decode('utf-8'), 'security', full_name)
            )
            
            user_id = cursor.fetchone()[0]
            
            return jsonify({
                'success': True, 
                'message': 'Security user added successfully',
                'user_id': user_id
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()

@app.route('/api/security/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_security_user(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Don't allow deleting yourself
        if user_id == session['user_id']:
            return jsonify({'error': 'Cannot delete your own account'}), 403
        
        cursor.execute("DELETE FROM users WHERE id = %s AND role = 'security'", (user_id,))
        
        return jsonify({'success': True, 'message': 'Security user deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/scan', methods=['POST'])
@security_required
def scan_student():
    data = request.json
    register_no = data.get('register_no')
    bus_no = data.get('bus_no')
    scan_type = data.get('scan_type')
    
    if not register_no or not bus_no or not scan_type:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate registration number format
    if not register_no.count('/') == 2:
        return jsonify({'error': 'Invalid registration number format. Use format: COURSE/ID/YEAR'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute("SELECT id, name, bus_fees_paid FROM students WHERE register_no = %s AND is_active = TRUE", (register_no,))
        student = cursor.fetchone()
        
        if not student:
            return jsonify({'error': 'Student not found or inactive'}), 404
        
        student_id, student_name, fees_paid = student
        
        # Record attendance
        cursor.execute('''
            INSERT INTO attendance (student_id, register_no, bus_no, scan_type, security_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, timestamp
        ''', (student_id, register_no, bus_no, scan_type, session['user_id']))
        
        record = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'message': f'{scan_type.capitalize()} recorded for {student_name}',
            'data': {
                'name': student_name,
                'register_no': register_no,
                'bus_no': bus_no,
                'fee_status': 'paid' if fees_paid else 'due',
                'timestamp': record[1].isoformat() if record[1] else datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/attendance', methods=['GET'])
@login_required
def get_attendance():
    limit = request.args.get('limit', 100)
    security_id = request.args.get('security_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Build query based on role
        if session.get('role') == 'admin':
            query = '''
                SELECT a.id, a.register_no, s.name, a.bus_no, a.scan_type, 
                       a.timestamp, u.full_name as security_name
                FROM attendance a
                LEFT JOIN students s ON a.student_id = s.id
                LEFT JOIN users u ON a.security_id = u.id
                ORDER BY a.timestamp DESC
                LIMIT %s
            '''
            params = (int(limit),)
        else:
            query = '''
                SELECT a.id, a.register_no, s.name, a.bus_no, a.scan_type, 
                       a.timestamp, u.full_name as security_name
                FROM attendance a
                LEFT JOIN students s ON a.student_id = s.id
                LEFT JOIN users u ON a.security_id = u.id
                WHERE a.security_id = %s
                ORDER BY a.timestamp DESC
                LIMIT %s
            '''
            params = (session['user_id'], int(limit))
        
        cursor.execute(query, params)
        attendance_records = cursor.fetchall()
        
        records_list = []
        for record in attendance_records:
            records_list.append({
                'id': record[0],
                'register_no': record[1],
                'student_name': record[2],
                'bus_no': record[3],
                'scan_type': record[4],
                'timestamp': record[5].isoformat() if record[5] else None,
                'security_name': record[6]
            })
        
        return jsonify(records_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/bus/timestamp', methods=['POST'])
@security_required
def record_bus_timestamp():
    data = request.json
    bus_no = data.get('bus_no')
    timestamp_type = data.get('timestamp_type')
    
    if not bus_no or not timestamp_type:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bus_timestamps (bus_no, timestamp_type, security_id)
            VALUES (%s, %s, %s)
            RETURNING id, timestamp
        ''', (bus_no, timestamp_type, session['user_id']))
        
        record = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'message': f'Bus {bus_no} {timestamp_type} recorded',
            'data': {
                'id': record[0],
                'timestamp': record[1].isoformat() if record[1] else datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/bus/timestamps', methods=['GET'])
@login_required
def get_bus_timestamps():
    limit = request.args.get('limit', 50)
    security_id = request.args.get('security_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Build query based on role
        if session.get('role') == 'admin':
            query = '''
                SELECT bt.id, bt.bus_no, bt.timestamp_type, bt.timestamp, 
                       bt.location, u.full_name as security_name
                FROM bus_timestamps bt
                LEFT JOIN users u ON bt.security_id = u.id
                ORDER BY bt.timestamp DESC
                LIMIT %s
            '''
            params = (int(limit),)
        else:
            query = '''
                SELECT bt.id, bt.bus_no, bt.timestamp_type, bt.timestamp, 
                       bt.location, u.full_name as security_name
                FROM bus_timestamps bt
                LEFT JOIN users u ON bt.security_id = u.id
                WHERE bt.security_id = %s
                ORDER BY bt.timestamp DESC
                LIMIT %s
            '''
            params = (session['user_id'], int(limit))
        
        cursor.execute(query, params)
        timestamps = cursor.fetchall()
        
        timestamps_list = []
        for ts in timestamps:
            timestamps_list.append({
                'id': ts[0],
                'bus_no': ts[1],
                'timestamp_type': ts[2],
                'timestamp': ts[3].isoformat() if ts[3] else None,
                'location': ts[4],
                'security_name': ts[5]
            })
        
        return jsonify(timestamps_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==================== PWA ROUTES ====================
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static/js', 'service-worker.js')

@app.route('/offline')
def offline():
    return render_template('offline.html')

# ==================== UTILITY ROUTES ====================
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/test')
def test_route():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return f"✅ Database connection successful! Test query result: {result}"
        except Exception as e:
            return f"❌ Database query error: {str(e)}"
    else:
        return "⚠️ Database connection failed"

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(e):
    return render_template('error/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error/500.html'), 500

# ==================== SESSION MANAGEMENT ====================
@app.before_request
def make_session_permanent():
    # Make all sessions permanent for remember me functionality
    session.permanent = True
    # Check if user is logged in and refresh session
    if 'user_id' in session:
        session.modified = True

# Vercel requirement
application = app

if __name__ == '__main__':
    print("🚀 Starting Hasteo - College Bus Attendance System...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    print("🚀 Application started in production mode")