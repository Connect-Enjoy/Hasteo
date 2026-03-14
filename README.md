<img width="1536" height="1024" alt="Image" src="https://github.com/user-attachments/assets/1e08268c-d83a-49fc-868a-fce8c0ed26b2" />

# Hasteo – College Bus Attendance & Management System 🚌✨
Hasteo is a smart, web-based Progressive Web Application (PWA) designed to digitize and automate college bus attendance tracking and transportation management. It replaces manual paper-based systems with barcode scanning, real-time tracking, and ML-powered anomaly detection for efficient campus transportation operations.

---

## 🚀 Project Overview  
Hasteo transforms traditional bus attendance systems by:
- Automating student verification using barcode scanning of student IDs
- Tracking bus arrivals/departures with digital timestamps
- Distinguishing between day scholars and hostellers with category-based tracking
- Providing real-time dashboards for security and administrative oversight
- Detecting irregular attendance patterns using machine learning algorithms

**Built With:**
- Frontend: HTML5, CSS3, Vanilla JavaScript, QuaggaJS (Barcode Scanning)
- Backend: Python Flask
- Database: PostgreSQL (Neon.tech cloud database)
- UI: Modern glassmorphism design with responsive PWA capabilities
- ML Integration: scikit-learn (Isolation Forest for anomaly detection)

---

## 🔑 Key Features

### 🧑‍🎓 Student Verification & Attendance
- Barcode Scanning: Real-time student ID scanning using device cameras
- Student ID Validation: Automatic format validation (SXX/XXXXX/XX pattern)
- Duplicate Prevention: Smart detection of duplicate scans within time windows
- Offline Support: PWA capabilities for scanning without internet connectivity
- Real-time Results: Instant feedback with visual and audio cues

### 🚌 Bus Management & Tracking
- Digital Timestamps: Accurate recording of entry/exit times
- Bus Assignment: Track specific buses assigned to each student
- Category Management: Distinguish between day scholars and hostellers
- Attendance Logs: Comprehensive digital records replacing manual logbooks

### 🛡️ Security & Administration
- Role-based Access: Separate portals for security personnel and administrators
- Real-time Dashboard: Monitor attendance statistics and bus movements
- Anomaly Detection: ML-powered identification of irregular attendance patterns
- Secure Authentication: Bcrypt password hashing and session management

### 📱 Progressive Web App (PWA)
- Installable App: Add to home screen functionality for mobile devices
- Offline Operation: Service workers enable scanning without internet
- Push Notifications: Real-time alerts for administrators
- Responsive Design: Optimized for mobile, tablet, and desktop

### 🤖 Machine Learning Integration
- Pattern Analysis: Historical attendance data processing using pandas/NumPy
- Anomaly Detection: Isolation Forest algorithm for identifying unusual patterns
- Administrative Alerts: Automated reports on suspicious activities
- Data-driven Insights: Statistical analysis of bus utilization and attendance trends

### 🗄️ Database & System Architecture
PostgreSQL-powered schema with optimized tables for:
- Students & User Management
- Attendance Records & Timestamps
- Bus Assignments & Routes
- Anomaly Detection Logs
- System Audit Trails

Core System Components:
- Authentication Module: Secure role-based access control
- Barcode Scanner: Camera-based student ID verification
- Attendance Logger: Digital timestamp recording
- PWA Service Worker: Offline capability and background sync
- ML Engine: Unsupervised anomaly detection
- Admin Dashboard: Real-time monitoring and reporting

---

## 🎯 Technical Implementation

### Backend Structure
- Framework: Flask with RESTful API endpoints
- Database Driver: pg8000 for PostgreSQL connectivity
- Security: Bcrypt hashing, session-based authentication
- Deployment: Vercel serverless platform with Python runtime

### Frontend Features
- Barcode Scanning: QuaggaJS integration for 1D barcode recognition
- Real-time Updates: AJAX-based data handling with Fetch API
- Responsive UI: Glassmorphism design with fox-inspired gradient theme
- PWA Implementation: Service workers, manifest.json, install prompts

### Machine Learning Pipeline
- Data Extraction: Historical attendance data from PostgreSQL
- Feature Engineering: Scan frequency, entry-exit ratios, unique student counts
- Model Training: Isolation Forest algorithm from scikit-learn
- Anomaly Scoring: Pattern deviation detection without predefined thresholds
- Reporting: Administrative dashboards with highlighted irregularities

---

## 📸 Screenshots
1. Home Page

<img width="1919" height="869" alt="Image" src="https://github.com/user-attachments/assets/0f908dd0-d1c5-44cb-a4af-6fd14c9a8c3f" />

2. Scanner Page

<img width="1919" height="870" alt="Image" src="https://github.com/user-attachments/assets/b9d989c6-688c-4003-8dfb-b72f5a7ea935" />

---
