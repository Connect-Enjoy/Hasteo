import logging
import json
import os
from datetime import datetime, timedelta, date
from db import get_db_connection

# Conditional imports so it doesn't break if dependencies are missing during early boot
try:
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import IsolationForest
    import joblib
except ImportError as e:
    logging.warning(f"ML Dependencies missing: {e}. Please install requirements.txt")
    pd = np = IsolationForest = joblib = None

logging.basicConfig(level=logging.INFO)

def fetch_student_features_for_date(target_date):
    """
    Returns a DataFrame with features for each student that was active on target_date.
    """
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
        
    try:
        cursor = conn.cursor()

        # Get all students who had scans on that date
        cursor.execute("""
            SELECT DISTINCT s.student_id, s.residence, sv.is_valid
            FROM students s
            LEFT JOIN scans sc ON s.student_id = sc.student_id AND sc.scan_date = %s
            LEFT JOIN student_validity sv ON s.registration_number = sv.registration_number
            WHERE sc.id IS NOT NULL
        """, (target_date,))
        students = cursor.fetchall()

        features = []
        for student_id, residence, is_valid in students:
            # Scan count
            cursor.execute("SELECT COUNT(*) FROM scans WHERE student_id = %s AND scan_date = %s", (student_id, target_date))
            scan_count = cursor.fetchone()[0]

            # Unique buses
            cursor.execute("SELECT COUNT(DISTINCT bus_id) FROM scans WHERE student_id = %s AND scan_date = %s", (student_id, target_date))
            unique_buses = cursor.fetchone()[0]

            # Timestamps
            cursor.execute("SELECT scan_time FROM scans WHERE student_id = %s AND scan_date = %s ORDER BY scan_time", (student_id, target_date))
            times = [row[0] for row in cursor.fetchall() if row[0] is not None]
            
            if len(times) > 1:
                intervals = [(times[i+1] - times[i]).total_seconds() / 60 for i in range(len(times)-1)]
                avg_interval = np.mean(intervals)
                std_interval = np.std(intervals)
            else:
                avg_interval = 0
                std_interval = 0

            first_hour = times[0].hour if times else -1
            last_hour = times[-1].hour if times else -1
            duration = (times[-1] - times[0]).total_seconds() / 60 if times and len(times) > 1 else 0

            # Check if any scan after pass expiry
            cursor.execute("""
                SELECT 1 FROM scans sc
                JOIN students s ON sc.student_id = s.student_id
                JOIN student_validity sv ON sv.registration_number = s.registration_number
                WHERE sc.student_id = %s AND sc.scan_date > DATE(sv.last_updated) AND sv.is_valid = FALSE AND sc.scan_date = %s
            """, (student_id, target_date))
            
            # Using fetchone since we just check existence
            scans_after_expiry = 1 if cursor.fetchone() else 0

            features.append({
                'student_id': student_id,
                'scan_count': scan_count,
                'unique_buses': unique_buses,
                'avg_time_between_scans': avg_interval,
                'std_time_between_scans': std_interval,
                'first_scan_hour': first_hour,
                'last_scan_hour': last_hour,
                'scan_duration': duration,
                'is_hosteller': 1 if residence == 'hosteller' else 0,
                'has_valid_pass': 1 if is_valid else 0,
                'scans_after_pass_expiry': scans_after_expiry
            })

        cursor.close()
        return pd.DataFrame(features)
    except Exception as e:
        logging.error(f"Error fetching student features: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def fetch_student_features_range(start_date, end_date):
    """
    Fetches student features for a range of dates.
    For simplicity, fetches for each active date and concatenates.
    """
    all_features = []
    current_date = start_date
    while current_date <= end_date:
        df = fetch_student_features_for_date(current_date)
        if not df.empty:
            all_features.append(df)
        current_date += timedelta(days=1)
    
    if all_features:
        return pd.concat(all_features, ignore_index=True)
    return pd.DataFrame()

def train_isolation_forest(data, contamination=0.05):
    """
    Train an Isolation Forest and return the trained model.
    """
    if data.empty or IsolationForest is None:
        return None
        
    X = data.select_dtypes(include=[np.number])
    if len(X) < 5:  # Not enough data points to meaningfully train
        return None
        
    model = IsolationForest(n_estimators=100, contamination=contamination, random_state=42)
    model.fit(X)
    return model

def detect_anomalies_for_date(target_date, model, data, entity_type):
    """
    Applies the model to the daily data and extracts anomalies.
    """
    if data.empty or model is None:
        return pd.DataFrame()
        
    X = data.select_dtypes(include=[np.number])
    predictions = model.predict(X)
    scores = model.decision_function(X)

    data_copy = data.copy()
    data_copy['prediction'] = predictions
    data_copy['anomaly_score'] = scores
    
    # Extract anomalies
    anomalies = data_copy[data_copy['prediction'] == -1].copy()
    anomalies['entity_type'] = entity_type
    anomalies['detection_date'] = target_date
    return anomalies

def store_anomalies(anomalies_df):
    """
    Save anomalies to database.
    """
    if anomalies_df.empty:
        return
        
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        for _, row in anomalies_df.iterrows():
            if row['entity_type'] == 'student':
                entity_id = str(row['student_id'])
            elif row['entity_type'] == 'security':
                entity_id = str(row.get('security_id', 'unknown'))
            elif row['entity_type'] == 'bus':
                entity_id = str(row.get('bus_number', 'unknown'))
            else:
                entity_id = 'system'

            # Define severity threshold mathematically (closer to -1 is worse)
            # sklearn's decision_function returns negative values for anomalies (lower is more anomalous)
            score = float(row['anomaly_score'])
            if score < -0.2:
                severity = 'high'
            elif score < -0.1:
                severity = 'medium'
            else:
                severity = 'low'
                
            description = f"Anomaly detected in {row['entity_type']} activity on {row['detection_date']}. Score: {score:.3f}"
            
            # Serialize row to JSON for details
            details_dict = {}
            for k, v in row.to_dict().items():
                if pd.isna(v):
                    details_dict[k] = None
                elif isinstance(v, (np.integer, np.floating)):
                    details_dict[k] = float(v)
                elif isinstance(v, date):
                    details_dict[k] = str(v)
                else:
                    details_dict[k] = v
                    
            details = json.dumps(details_dict)

            # Check if this anomaly was already detected today
            cursor.execute('''
                SELECT id FROM anomaly_detections 
                WHERE detection_date = %s AND entity_type = %s AND entity_id = %s
            ''', (row['detection_date'], row['entity_type'], entity_id))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO anomaly_detections 
                    (detection_date, entity_type, entity_id, anomaly_score, severity, description, details)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (row['detection_date'], row['entity_type'], entity_id, score, severity, description, details))
                
        conn.commit()
    except Exception as e:
        logging.error(f"Error storing anomalies: {e}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()
        conn.close()

def run_anomaly_detection(target_date=None):
    """
    Main orchestrator for anomaly detection.
    """
    if pd is None:
        logging.error("Dependencies missing. Cannot run anomaly detection.")
        return False
        
    if target_date is None:
        # Default to checking yesterday's full data
        target_date = date.today() - timedelta(days=1)
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

    logging.info(f"Running anomaly detection for {target_date} ...")

    # Step 1: Historical bounds (Last 30 days)
    end_train = target_date - timedelta(days=1)
    start_train = target_date - timedelta(days=31)
    
    # Check if models directory exists
    os.makedirs('models', exist_ok=True)
    
    # --- Student Anomalies ---
    student_model_path = "models/student_iso_forest.pkl"
    model_student = None
    
    # Try to load existing model
    if os.path.exists(student_model_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(student_model_path))
        if (datetime.now() - mtime).days < 7:
            try:
                model_student = joblib.load(student_model_path)
            except Exception as e:
                logging.warning(f"Failed to load model: {e}")
                
    # Train new model if needed
    if model_student is None:
        student_data_train = fetch_student_features_range(start_train, end_train)
        if not student_data_train.empty:
            model_student = train_isolation_forest(student_data_train, contamination=0.05)
            if model_student:
                try:
                    joblib.dump(model_student, student_model_path)
                except Exception as e:
                    logging.warning(f"Failed to save model: {e}")

    # Predict
    if model_student is not None:
        student_data_today = fetch_student_features_for_date(target_date)
        if not student_data_today.empty:
            anomalies_student = detect_anomalies_for_date(target_date, model_student, student_data_today, 'student')
            if not anomalies_student.empty:
                store_anomalies(anomalies_student)
                logging.info(f"Stored {len(anomalies_student)} student anomalies.")
            else:
                logging.info("No student anomalies detected.")
        else:
            logging.info("No student activity to analyze for the target date.")
    else:
        logging.warning("Insufficient historical data to train student model. Detection skipped.")

    # Other entities (security, buses) can be implemented similarly here
    # For now, we only extracted features for students as per the detailed code given.
    
    return True

if __name__ == '__main__':
    # Test run standalone
    run_anomaly_detection()
