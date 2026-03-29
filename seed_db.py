import random
from datetime import datetime, timedelta, date
from db import get_db_connection

def seed_database():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database. Cannot seed data.")
        return

    try:
        cursor = conn.cursor()
        print("Creating dummy students, security, and buses...")

        # 1. Create a security personnel
        cursor.execute("INSERT INTO security (security_id, name, email, password) VALUES ('SEC999', 'Test Security', 'sec@test.com', 'pass') ON CONFLICT DO NOTHING RETURNING id")
        sec_id = 'SEC999'

        # 2. Create buses
        buses = [
            ('BUS-A1', 'Route A', 'Driver Bob'),
            ('BUS-B2', 'Route B', 'Driver Tom')
        ]
        
        bus_ids = {}
        for b in buses:
            cursor.execute("INSERT INTO buses (bus_number, route_name, driver_name, driver_phone, status) VALUES (%s, %s, %s, '1234567890', 'active') ON CONFLICT (bus_number) DO NOTHING RETURNING id", (b[0], b[1], b[2]))
            res = cursor.fetchone()
            if res:
                bus_ids[b[0]] = res[0]
            else:
                cursor.execute("SELECT id FROM buses WHERE bus_number = %s", (b[0],))
                bus_ids[b[0]] = cursor.fetchone()[0]

        # 3. Create students
        students = []
        for i in range(1, 11):
            s_id = f"STU00{i}"
            reg = f"REG20{i}"
            residence = 'day_scholar' if i <= 8 else 'hosteller'
            is_valid = True if residence == 'day_scholar' else False
            
            cursor.execute("""
                INSERT INTO students (student_id, name, branch, year_of_admission, registration_number, email, password, residence)
                VALUES (%s, %s, 'CS', 2023, %s, %s, 'pass', %s)
                ON CONFLICT (student_id) DO NOTHING
            """, (s_id, f"Student {i}", reg, f"stu{i}@test.com", residence))
            
            cursor.execute("""
                INSERT INTO student_validity (registration_number, is_valid)
                VALUES (%s, %s)
                ON CONFLICT (registration_number) DO UPDATE SET is_valid = EXCLUDED.is_valid
            """, (reg, is_valid))
            
            students.append({
                'id': s_id, 'name': f"Student {i}", 'residence': residence, 'reg': reg
            })

        print("Generating historical normal scans (last 15 days)...")
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=14)
        
        # Batch normal scans
        normal_scans = []
        curr_date = start_date
        while curr_date <= end_date:
            for s in students:
                morning_time = datetime.combine(curr_date, datetime.min.time()) + timedelta(hours=8, minutes=random.randint(0, 30))
                evening_time = datetime.combine(curr_date, datetime.min.time()) + timedelta(hours=16, minutes=random.randint(0, 30))
                
                b_num = 'BUS-A1' if int(s['id'][-1]) % 2 == 0 else 'BUS-B2'
                b_id = bus_ids[b_num]
                
                if s['residence'] == 'hosteller':
                    if random.random() > 0.8:
                        normal_scans.extend([
                            (s['id'], s['name'], s['residence'], sec_id, b_id, b_num, morning_time, curr_date),
                            (s['id'], s['name'], s['residence'], sec_id, b_id, b_num, evening_time, curr_date)
                        ])
                else:
                    normal_scans.extend([
                        (s['id'], s['name'], s['residence'], sec_id, b_id, b_num, morning_time, curr_date),
                        (s['id'], s['name'], s['residence'], sec_id, b_id, b_num, evening_time, curr_date)
                    ])
            curr_date += timedelta(days=1)
            
        if normal_scans:
            cursor.executemany("INSERT INTO scans (student_id, student_name, branch, residence, scanned_by, bus_id, bus_number, scan_time, scan_date) VALUES (%s, %s, 'CS', %s, %s, %s, %s, %s, %s)", normal_scans)

        print("Injecting ANOMALOUS scans for today/yesterday...")
        target_anomaly_date = date.today()
        anomalous_scans = []
        
        # Anomaly 1: A day scholar who scanned 12 times in a single day
        anomaly_stu1 = students[0] # STU001
        for i in range(12):
            weird_time = datetime.combine(target_anomaly_date, datetime.min.time()) + timedelta(hours=random.randint(1, 23), minutes=random.randint(0, 59))
            anomalous_scans.append((anomaly_stu1['id'], anomaly_stu1['name'], anomaly_stu1['residence'], sec_id, bus_ids['BUS-A1'], 'BUS-A1', weird_time, target_anomaly_date))

        # Anomaly 2: A hosteller (STU009) scanning without a valid pass
        anomaly_stu2 = students[8] # STU009
        cursor.execute("UPDATE student_validity SET is_valid = FALSE, last_updated = %s WHERE registration_number = %s", (target_anomaly_date - timedelta(days=2), anomaly_stu2['reg']))
        for i in range(3):
            weird_time = datetime.combine(target_anomaly_date, datetime.min.time()) + timedelta(hours=8 + i, minutes=random.randint(0, 59))
            anomalous_scans.append((anomaly_stu2['id'], anomaly_stu2['name'], anomaly_stu2['residence'], sec_id, bus_ids['BUS-B2'], 'BUS-B2', weird_time, target_anomaly_date))

        if anomalous_scans:
            cursor.executemany("INSERT INTO scans (student_id, student_name, branch, residence, scanned_by, bus_id, bus_number, scan_time, scan_date) VALUES (%s, %s, 'CS', %s, %s, %s, %s, %s, %s)", anomalous_scans)

        conn.commit()
        cursor.close()
        print("Database seeding completed successfully! You can now test the Isolation Forest model.")

    except Exception as e:
        print(f"Error seeding database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
