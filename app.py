import os
import pg8000
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import logging

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
            
            print(f"🔗 Connecting to: {host}:{port}/{database}")
            
            conn = pg8000.connect(
                host=host,
                user=username,
                password=password,
                database=database,
                port=int(port),
                ssl_context=True
            )
            print("✅ Database connection successful!")
            return conn
            
    except Exception as err:
        print(f"❌ Database connection failed: {err}")
        return None

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
            
            # Create buses table (simplified)
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
            
            # Create scans table for attendance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(20) NOT NULL,
                    scanned_by VARCHAR(20) NOT NULL,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    bus_number VARCHAR(20),
                    scan_type VARCHAR(20) DEFAULT 'check_in',
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (scanned_by) REFERENCES security(security_id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_branch ON students(branch)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_year ON students(year_of_admission)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_residence ON students(residence)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_active ON students(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_active ON security(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scans_student ON scans(student_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scans_time ON scans(scan_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_buses_status ON buses(status)')
            
            conn.commit()
            cursor.close()
            print("✅ Database tables created successfully!")
            
        except Exception as err:
            print(f"❌ Database initialization error: {err}")
            conn.rollback()
        finally:
            conn.close()

# Initialize database on startup
try:
    init_db()
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# Index Route
@app.route('/')
def index():
    return render_template('index.html')

# Student Login
@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        # TODO: Add actual authentication logic
        session['user_type'] = 'student'
        session['user_id'] = student_id
        session['logged_in'] = True
        flash('Student login successful!', 'success')
        return redirect(url_for('index'))
        
    return render_template('student_login.html')

# Security Login
@app.route('/security-login', methods=['GET', 'POST'])
def security_login():
    if request.method == 'POST':
        security_id = request.form.get('security_id')
        password = request.form.get('password')
        
        # TODO: Add actual authentication logic
        session['user_type'] = 'security'
        session['user_id'] = security_id
        session['logged_in'] = True
        flash('Security login successful!', 'success')
        return redirect(url_for('scanner'))
        
    return render_template('security_login.html')

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
        
        # TODO: Add actual developer authentication logic
        session['user_type'] = 'developer'
        session['user_id'] = developer_id
        session['logged_in'] = True
        flash('Developer login successful!', 'success')
        return redirect(url_for('index'))
        
    return render_template('developer_login.html')

# Scanner Page
@app.route('/scan')
def scanner():
    if not session.get('logged_in') or session.get('user_type') not in ['security', 'admin']:
        flash('Please login as security personnel to access scanner.', 'warning')
        return redirect(url_for('security_login'))
    return render_template('scan.html')

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

# Delete Student
@app.route('/admin/delete-student/<int:student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE students SET is_active = FALSE WHERE id = %s', (student_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': 'Student deleted successfully'})
            
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

# Delete Security
@app.route('/admin/delete-security/<int:security_id>', methods=['POST'])
def admin_delete_security(security_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE security SET is_active = FALSE WHERE id = %s', (security_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': 'Security personnel deleted successfully'})
            
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
            cursor.execute('DELETE FROM buses WHERE id = %s', (bus_id,))
            conn.commit()
            cursor.close()
            
            return jsonify({'success': True, 'message': 'Bus deleted successfully'})
            
        except Exception as err:
            print(f"Error deleting bus: {err}")
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('user_type', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('index'))

# Logout
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
    bus_number = data.get('bus_number', '')
    scan_type = data.get('scan_type', 'check_in')
    
    if not student_id:
        return jsonify({'error': 'Student ID required'}), 400
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Verify student exists and is active
            cursor.execute('''
                SELECT student_id, name FROM students 
                WHERE student_id = %s AND is_active = TRUE
            ''', (student_id,))
            
            student = cursor.fetchone()
            if not student:
                return jsonify({'error': 'Student not found or inactive'}), 404
            
            # Save scan
            cursor.execute('''
                INSERT INTO scans (student_id, scanned_by, bus_number, scan_type)
                VALUES (%s, %s, %s, %s)
            ''', (student_id, session.get('user_id', 'unknown'), bus_number, scan_type))
            
            conn.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'student_id': student_id,
                'student_name': student[1],
                'timestamp': datetime.now().isoformat(),
                'scanned_by': session.get('user_id')
            })
            
        except Exception as err:
            print(f"Error saving scan: {err}")
            return jsonify({'error': 'Database error'}), 500
        finally:
            conn.close()
    
    return jsonify({'error': 'Database connection failed'}), 500

# Vercel requirement
application = app

if __name__ == '__main__':
    print("🚀 Starting Hasteo Bus Attendance System...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
