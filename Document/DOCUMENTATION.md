# VishnoRex Attendance Management System - Complete Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Installation Guide](#installation-guide)
5. [Configuration](#configuration)
6. [User Guide](#user-guide)
7. [API Documentation](#api-documentation)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

## System Overview

VishnoRex is a comprehensive attendance management system designed for educational institutions and organizations. It provides advanced features including biometric integration, Excel reporting, data visualization, and comprehensive analytics.

### Key Components
- **Core System**: Flask-based web application with SQLite database
- **Biometric Integration**: ZK Teco device support for fingerprint attendance
- **Reporting Engine**: Advanced Excel reports with charts and analytics
- **Notification System**: Email and in-app notifications
- **Analytics Dashboard**: Interactive data visualization and insights
- **Backup System**: Automated backup and data management

## Architecture

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │  Mobile Device  │    │ Biometric Device│
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴───────────┐
                    │    Flask Web Server     │
                    │   (app.py - Main App)   │
                    └─────────────┬───────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                       │                        │
┌───────┴────────┐    ┌─────────┴─────────┐    ┌─────────┴─────────┐
│   Database     │    │   File System     │    │   External APIs   │
│   (SQLite)     │    │   (Uploads/Logs)  │    │   (Email/SMS)     │
└────────────────┘    └───────────────────┘    └───────────────────┘
```

### Module Structure
```
VishnoRex/
├── Core Modules/
│   ├── app.py                    # Main Flask application
│   ├── database.py               # Database management
│   └── shift_management.py       # Shift and schedule management
├── Advanced Features/
│   ├── excel_reports.py          # Excel report generation
│   ├── staff_management_enhanced.py # Enhanced staff operations
│   ├── attendance_advanced.py    # Advanced attendance features
│   ├── notification_system.py    # Notification management
│   ├── backup_manager.py         # Backup and data management
│   ├── data_visualization.py     # Charts and analytics
│   └── reporting_dashboard.py    # Comprehensive reporting
├── Integration/
│   └── zk_biometric.py          # Biometric device integration
├── Testing/
│   └── test_system.py           # Comprehensive test suite
└── Templates & Static Files/
    ├── templates/               # HTML templates
    └── static/                  # CSS, JS, images
```

## Features

### Core Features
1. **Multi-School Management**
   - Support for multiple schools/organizations
   - Centralized company admin dashboard
   - School-specific admin access

2. **Role-Based Access Control**
   - Company Admin: System-wide access
   - School Admin: School-specific management
   - Staff: Personal attendance and leave management

3. **Attendance Management**
   - Manual attendance marking
   - Biometric device integration
   - Overtime tracking and calculation
   - Attendance regularization requests

4. **Leave Management**
   - Multiple leave types (CL, SL, EL, ML)
   - Leave application workflow
   - Approval/rejection system
   - Leave balance tracking

### Advanced Features
1. **Excel Reporting System**
   - Professional Excel reports with formatting
   - Charts and graphs integration
   - Multiple report types (daily, weekly, monthly, yearly)
   - Custom date range reports

2. **Enhanced Staff Management**
   - Bulk staff import/export
   - Advanced search and filtering
   - Staff photo management
   - Department-wise analytics

3. **Attendance Analytics**
   - Interactive dashboards
   - Data visualization with charts
   - Performance metrics and KPIs
   - Trend analysis

4. **Notification System**
   - Email notifications for alerts
   - In-app notification system
   - Attendance alerts and reminders
   - Leave approval notifications

5. **Backup & Data Management**
   - Automated database backups
   - Data export in multiple formats
   - Data archiving for old records
   - Backup scheduling and retention

## Installation Guide

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- 2GB RAM minimum
- 1GB disk space

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/vishnorex-attendance.git
   cd vishnorex-attendance
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   python database.py
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the System**
   Open your browser and navigate to `http://localhost:5000`

### Dependencies
```
Flask==2.3.3
Flask-WTF==1.1.1
openpyxl==3.1.2
pandas==2.0.3
Pillow==10.0.0
pyzk==0.9.1
schedule==1.2.0
psutil==5.9.5
requests==2.31.0
Werkzeug==2.3.7
```

## Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Application Settings
SECRET_KEY=your-secret-key-here
CSRF_SECRET_KEY=your-csrf-key-here
DEBUG=False

# Database Configuration
DATABASE_URL=sqlite:///vishnorex.db

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SYSTEM_EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
USE_TLS=True

# Biometric Device Configuration
ZK_DEVICE_IP=192.168.1.100
ZK_DEVICE_PORT=4370
ZK_DEVICE_PASSWORD=0

# File Upload Settings
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=static/uploads

# Backup Settings
BACKUP_RETENTION_DAYS=30
ARCHIVE_RETENTION_DAYS=365
```

### Application Configuration
Key configuration options in `app.py`:

```python
# Security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('CSRF_SECRET_KEY', 'csrf-secret')

# File Upload
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Database
app.config['DATABASE'] = 'vishnorex.db'
```

## User Guide

### For Company Admins

#### Dashboard Overview
- System-wide statistics and metrics
- School performance comparison
- Recent activity summary
- Quick action buttons

#### School Management
1. **Add New School**
   - Navigate to Schools → Add School
   - Fill in school details (name, address, contact)
   - Upload school logo (optional)
   - Assign school administrator

2. **Manage Schools**
   - View all schools in the system
   - Edit school information
   - Deactivate/activate schools
   - Generate school-wise reports

#### System Reports
- Company-wide attendance reports
- Cross-school performance analysis
- System usage statistics
- Data export capabilities

### For School Admins

#### Staff Management
1. **Add Staff Members**
   - Navigate to Staff → Add Staff
   - Fill in personal details
   - Assign department and position
   - Set shift and work schedule
   - Upload staff photo

2. **Bulk Operations**
   - Import staff from Excel/CSV
   - Bulk update staff information
   - Export staff data
   - Generate staff reports

#### Attendance Management
1. **Daily Attendance**
   - View daily attendance summary
   - Mark manual attendance
   - Handle attendance corrections
   - Generate daily reports

2. **Attendance Reports**
   - Daily, weekly, monthly reports
   - Department-wise analysis
   - Individual staff reports
   - Export to Excel/PDF

#### Leave Management
1. **Leave Applications**
   - Review pending applications
   - Approve/reject leave requests
   - Add admin comments
   - Track leave balances

2. **Leave Reports**
   - Leave summary reports
   - Department-wise leave analysis
   - Leave trend analysis

### For Staff Members

#### Personal Dashboard
- Today's attendance status
- Recent attendance history
- Leave balance summary
- Upcoming holidays/events

#### Attendance
1. **View Attendance**
   - Personal attendance calendar
   - Monthly attendance summary
   - Attendance statistics
   - Download attendance reports

2. **Attendance Regularization**
   - Request attendance corrections
   - Provide justification
   - Track request status

#### Leave Management
1. **Apply for Leave**
   - Select leave type and dates
   - Provide reason and details
   - Submit application
   - Track application status

2. **Leave History**
   - View past leave applications
   - Check leave balances
   - Download leave reports

## API Documentation

### Authentication Endpoints

#### POST /login
Login to the system
```json
{
  "username": "user123",
  "password": "password123",
  "user_type": "admin"
}
```

Response:
```json
{
  "success": true,
  "message": "Login successful",
  "user_type": "admin",
  "redirect_url": "/admin_dashboard"
}
```

#### POST /logout
Logout from the system
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### Staff Management Endpoints

#### GET /get_staff
Get staff list with optional filters
```
GET /get_staff?department=IT&limit=50&search=john
```

Response:
```json
{
  "success": true,
  "staff": [
    {
      "id": 1,
      "staff_id": "EMP001",
      "full_name": "John Doe",
      "department": "IT",
      "position": "Developer",
      "email": "john@example.com"
    }
  ],
  "total": 1
}
```

#### POST /add_staff
Add new staff member
```json
{
  "staff_id": "EMP002",
  "full_name": "Jane Smith",
  "email": "jane@example.com",
  "department": "HR",
  "position": "Manager"
}
```

### Attendance Endpoints

#### GET /get_attendance
Get attendance records
```
GET /get_attendance?staff_id=1&start_date=2024-01-01&end_date=2024-01-31
```

#### POST /mark_attendance
Mark attendance
```json
{
  "staff_id": 1,
  "verification_type": "check-in",
  "timestamp": "2024-01-15 09:00:00"
}
```

### Reporting Endpoints

#### GET /generate_report
Generate various reports
```
GET /generate_report?report_type=daily&date=2024-01-15
GET /generate_report?report_type=monthly&year=2024&month=1
```

#### GET /export_staff_data
Export staff data
```
GET /export_staff_data?start_date=2024-01-01&end_date=2024-01-31&format=excel
```

## Testing

### Running Tests
```bash
# Run all tests
python test_system.py

# Run specific test class
python -m unittest test_system.TestDatabaseOperations

# Run with verbose output
python test_system.py -v
```

### Test Coverage
The test suite includes:

1. **Unit Tests**
   - Database operations
   - Shift management
   - Staff management
   - Attendance processing
   - Notification system

2. **Integration Tests**
   - API endpoints
   - Database integrity
   - File operations
   - Email functionality

3. **Performance Tests**
   - Query performance
   - Memory usage
   - Response times
   - Load testing

### Test Reports
Test reports are generated in JSON format:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "tests_run": 45,
  "failures": 0,
  "errors": 0,
  "success_rate": 100.0,
  "execution_time": 12.5
}
```

## Deployment

### Production Deployment

#### 1. Server Setup (Ubuntu/Debian)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Create application user
sudo useradd -m -s /bin/bash vishnorex
sudo su - vishnorex
```

#### 2. Application Setup
```bash
# Clone repository
git clone https://github.com/your-repo/vishnorex-attendance.git
cd vishnorex-attendance

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python database.py

# Create production configuration
cp .env.example .env
# Edit .env with production settings
```

#### 3. Nginx Configuration
```nginx
# /etc/nginx/sites-available/vishnorex
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/vishnorex/vishnorex-attendance/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 4. Supervisor Configuration
```ini
# /etc/supervisor/conf.d/vishnorex.conf
[program:vishnorex]
command=/home/vishnorex/vishnorex-attendance/venv/bin/python app.py
directory=/home/vishnorex/vishnorex-attendance
user=vishnorex
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/vishnorex.log
```

#### 5. SSL Configuration (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads backups exports archives temp

# Initialize database
RUN python database.py

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  vishnorex:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
      - ./static/uploads:/app/static/uploads
    environment:
      - SECRET_KEY=your-secret-key
      - DATABASE_URL=sqlite:///data/vishnorex.db
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - vishnorex
    restart: unless-stopped
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
**Problem**: `sqlite3.OperationalError: database is locked`
**Solution**:
```bash
# Check for running processes
ps aux | grep python

# Kill any hanging processes
pkill -f "python app.py"

# Restart the application
python app.py
```

#### 2. File Upload Issues
**Problem**: File uploads failing
**Solution**:
```bash
# Check upload directory permissions
chmod 755 static/uploads/
chown -R www-data:www-data static/uploads/

# Check file size limits in nginx
# Add to nginx.conf:
client_max_body_size 16M;
```

#### 3. Email Notification Issues
**Problem**: Emails not being sent
**Solution**:
1. Check SMTP configuration in `.env`
2. Verify email credentials
3. Check firewall settings for SMTP ports
4. Test with a simple email client

#### 4. Biometric Device Connection
**Problem**: Cannot connect to ZK device
**Solution**:
1. Verify device IP and port
2. Check network connectivity
3. Ensure device is not in use by another application
4. Check device firmware compatibility

#### 5. Performance Issues
**Problem**: Slow response times
**Solution**:
```sql
-- Add database indexes
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_attendance_staff_id ON attendance(staff_id);
CREATE INDEX idx_staff_school_id ON staff(school_id);
```

### Log Files
- Application logs: `vishnorex.log`
- Nginx logs: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- System logs: `/var/log/syslog`

### Monitoring
```bash
# Check application status
sudo supervisorctl status vishnorex

# Monitor logs in real-time
tail -f /var/log/vishnorex.log

# Check system resources
htop
df -h
```

### Backup and Recovery
```bash
# Create manual backup
python -c "from backup_manager import BackupManager; BackupManager().create_database_backup()"

# Restore from backup
python -c "from backup_manager import BackupManager; BackupManager().restore_database_backup('backup_name', True)"
```

---

This documentation provides comprehensive guidance for installing, configuring, using, and maintaining the VishnoRex Attendance Management System. For additional support, please refer to the GitHub repository or contact the development team.
