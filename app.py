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
            
            # Create students table
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
            
            # Create buses table (no sample data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buses (
                    id SERIAL PRIMARY KEY,
                    bus_number VARCHAR(20) UNIQUE NOT NULL,
                    route_name VARCHAR(100) NOT NULL,
                    capacity INTEGER NOT NULL CHECK (capacity > 0),
                    driver_name VARCHAR(100) NOT NULL,
                    driver_phone VARCHAR(20) NOT NULL,
                    driver_license VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'inactive')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
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
    stats = {
        'total_students': 0,
        'total_security': 0,
        'students_by_branch': {},
        'students_by_year': {}
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get all active students
            cursor.execute('''
                SELECT student_id, name, branch, year_of_admission, 
                       registration_number, email, created_at
                FROM students 
                WHERE is_active = TRUE 
                ORDER BY year_of_admission DESC, branch, name
            ''')
            students = cursor.fetchall()
            
            # Get all active security personnel
            cursor.execute('''
                SELECT security_id, name, email, created_at
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
            
            # Students by year
            cursor.execute('''
                SELECT year_of_admission, COUNT(*) 
                FROM students 
                WHERE is_active = TRUE 
                GROUP BY year_of_admission 
                ORDER BY year_of_admission DESC
            ''')
            for year, count in cursor.fetchall():
                stats['students_by_year'][year] = count
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading user data: {err}")
            flash('Error loading user data.', 'error')
        finally:
            conn.close()
    
    return render_template('admin_users.html', students=students, security=security_personnel, stats=stats)

# Add Student
@app.route('/admin/users/add-student', methods=['POST'])
def admin_add_student():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    name = request.form.get('name')
    branch = request.form.get('branch')
    year_of_admission = request.form.get('year_of_admission')
    student_id = request.form.get('student_id')
    registration_number = request.form.get('registration_number')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not all([name, branch, year_of_admission, student_id, registration_number, email, password]):
        flash('All fields are required!', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT student_id FROM students 
                WHERE student_id = %s OR registration_number = %s
            ''', (student_id, registration_number))
            
            if cursor.fetchone():
                flash('Student ID or Registration Number already exists!', 'error')
                cursor.close()
                conn.close()
                return redirect(url_for('admin_users'))
            
            cursor.execute('''
                INSERT INTO students (student_id, name, branch, year_of_admission, 
                                     registration_number, email, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (student_id, name, branch, int(year_of_admission), 
                  registration_number, email, password))
            
            conn.commit()
            cursor.close()
            flash(f'Student {name} added successfully!', 'success')
            
        except Exception as err:
            print(f"Error adding student: {err}")
            flash('Error adding student. Please try again.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_users'))

# Add Security
@app.route('/admin/users/add-security', methods=['POST'])
def admin_add_security():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    security_id = request.form.get('security_id')
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not all([security_id, name, email, password]):
        flash('All fields are required!', 'error')
        return redirect(url_for('admin_users'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute('SELECT security_id FROM security WHERE security_id = %s', (security_id,))
            if cursor.fetchone():
                flash('Security ID already exists!', 'error')
                cursor.close()
                conn.close()
                return redirect(url_for('admin_users'))
            
            cursor.execute('''
                INSERT INTO security (security_id, name, email, password)
                VALUES (%s, %s, %s, %s)
            ''', (security_id, name, email, password))
            
            conn.commit()
            cursor.close()
            flash(f'Security personnel {name} added successfully!', 'success')
            
        except Exception as err:
            print(f"Error adding security: {err}")
            flash('Error adding security personnel. Please try again.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_users'))

# Delete Student
@app.route('/admin/users/delete-student/<student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE students SET is_active = FALSE WHERE student_id = %s', (student_id,))
            conn.commit()
            cursor.close()
            flash('Student deactivated successfully!', 'success')
            
        except Exception as err:
            print(f"Error deleting student: {err}")
            flash('Error deleting student.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_users'))

# Delete Security
@app.route('/admin/users/delete-security/<security_id>', methods=['POST'])
def admin_delete_security(security_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE security SET is_active = FALSE WHERE security_id = %s', (security_id,))
            conn.commit()
            cursor.close()
            flash('Security personnel deactivated successfully!', 'success')
            
        except Exception as err:
            print(f"Error deleting security: {err}")
            flash('Error deleting security personnel.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_users'))

# Delete Students by Year
@app.route('/admin/users/delete-students-by-year', methods=['POST'])
def admin_delete_students_by_year():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    year = request.form.get('year')
    current_year = datetime.now().year
    
    if not year:
        flash('Please select a year!', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        year = int(year)
    except ValueError:
        flash('Invalid year format!', 'error')
        return redirect(url_for('admin_users'))
    
    if current_year - year < 4:
        flash('Can only delete students from batches 4 or more years old!', 'error')
        return redirect(url_for('admin_users'))
    
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
            flash(f'{count} students from batch {year} have been deactivated!', 'success')
            
        except Exception as err:
            print(f"Error deleting students by year: {err}")
            flash('Error deleting students. Please try again.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_users'))

# Admin Bus Management
@app.route('/admin/buses')
def admin_buses():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    buses = []
    stats = {
        'total_buses': 0,
        'active_buses': 0,
        'maintenance_buses': 0,
        'inactive_buses': 0,
        'total_capacity': 0
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get all buses
            cursor.execute('''
                SELECT id, bus_number, route_name, capacity, driver_name, 
                       driver_phone, driver_license, status, created_at, notes
                FROM buses 
                ORDER BY status, bus_number
            ''')
            buses = cursor.fetchall()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM buses")
            stats['total_buses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM buses WHERE status = 'active'")
            stats['active_buses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM buses WHERE status = 'maintenance'")
            stats['maintenance_buses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM buses WHERE status = 'inactive'")
            stats['inactive_buses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(capacity), 0) FROM buses WHERE status = 'active'")
            stats['total_capacity'] = cursor.fetchone()[0]
            
            cursor.close()
            
        except Exception as err:
            print(f"Error loading bus data: {err}")
            flash('Error loading bus data.', 'error')
        finally:
            conn.close()
    
    return render_template('admin_buses.html', buses=buses, stats=stats)

# Add Bus
@app.route('/admin/buses/add', methods=['POST'])
def admin_add_bus():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    bus_number = request.form.get('bus_number')
    route_name = request.form.get('route_name')
    capacity = request.form.get('capacity')
    driver_name = request.form.get('driver_name')
    driver_phone = request.form.get('driver_phone')
    driver_license = request.form.get('driver_license')
    status = request.form.get('status', 'active')
    notes = request.form.get('notes')
    
    if not all([bus_number, route_name, capacity, driver_name, driver_phone]):
        flash('Bus Number, Route, Capacity, Driver Name, and Driver Phone are required!', 'error')
        return redirect(url_for('admin_buses'))
    
    try:
        capacity = int(capacity)
        if capacity <= 0:
            flash('Capacity must be a positive number!', 'error')
            return redirect(url_for('admin_buses'))
    except ValueError:
        flash('Capacity must be a valid number!', 'error')
        return redirect(url_for('admin_buses'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Check if bus number already exists
            cursor.execute('SELECT bus_number FROM buses WHERE bus_number = %s', (bus_number,))
            if cursor.fetchone():
                flash(f'Bus number {bus_number} already exists!', 'error')
                cursor.close()
                conn.close()
                return redirect(url_for('admin_buses'))
            
            cursor.execute('''
                INSERT INTO buses (bus_number, route_name, capacity, driver_name, 
                                 driver_phone, driver_license, status, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (bus_number, route_name, capacity, driver_name, 
                  driver_phone, driver_license, status, notes))
            
            conn.commit()
            cursor.close()
            flash(f'Bus {bus_number} added successfully!', 'success')
            
        except Exception as err:
            print(f"Error adding bus: {err}")
            flash('Error adding bus. Please try again.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_buses'))

# Update Bus
@app.route('/admin/buses/update/<int:bus_id>', methods=['POST'])
def admin_update_bus(bus_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    bus_number = request.form.get('bus_number')
    route_name = request.form.get('route_name')
    capacity = request.form.get('capacity')
    driver_name = request.form.get('driver_name')
    driver_phone = request.form.get('driver_phone')
    driver_license = request.form.get('driver_license')
    status = request.form.get('status')
    notes = request.form.get('notes')
    
    if not all([bus_number, route_name, capacity, driver_name, driver_phone]):
        flash('All required fields must be filled!', 'error')
        return redirect(url_for('admin_buses'))
    
    try:
        capacity = int(capacity)
        if capacity <= 0:
            flash('Capacity must be a positive number!', 'error')
            return redirect(url_for('admin_buses'))
    except ValueError:
        flash('Capacity must be a valid number!', 'error')
        return redirect(url_for('admin_buses'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Check if bus number already exists for another bus
            cursor.execute('''
                SELECT id FROM buses WHERE bus_number = %s AND id != %s
            ''', (bus_number, bus_id))
            if cursor.fetchone():
                flash(f'Bus number {bus_number} already exists for another bus!', 'error')
                cursor.close()
                conn.close()
                return redirect(url_for('admin_buses'))
            
            cursor.execute('''
                UPDATE buses SET 
                    bus_number = %s,
                    route_name = %s,
                    capacity = %s,
                    driver_name = %s,
                    driver_phone = %s,
                    driver_license = %s,
                    status = %s,
                    notes = %s,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (bus_number, route_name, capacity, driver_name, 
                  driver_phone, driver_license, status, notes, bus_id))
            
            conn.commit()
            cursor.close()
            flash(f'Bus {bus_number} updated successfully!', 'success')
            
        except Exception as err:
            print(f"Error updating bus: {err}")
            flash('Error updating bus. Please try again.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_buses'))

# Delete Bus
@app.route('/admin/buses/delete/<int:bus_id>', methods=['POST'])
def admin_delete_bus(bus_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM buses WHERE id = %s', (bus_id,))
            conn.commit()
            cursor.close()
            flash('Bus deleted successfully!', 'success')
            
        except Exception as err:
            print(f"Error deleting bus: {err}")
            flash('Error deleting bus. Please try again.', 'error')
            conn.rollback()
        finally:
            conn.close()
    
    return redirect(url_for('admin_buses'))

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
