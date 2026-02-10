# VishnoRex Staff Attendance System

A comprehensive web-based staff attendance management system built with Flask.

## 🚀 Features

- **Multi-School Support**: Manage multiple schools/institutions from one system
- **Role-Based Access**: Company Admin, School Admin, and Staff roles
- **Attendance Tracking**: Clock in/out functionality with time tracking
- **Leave Management**: Apply for and approve leave applications
- **Staff Management**: Add, edit, and manage staff profiles
- **Reporting**: Export attendance and staff reports in CSV format
- **File Uploads**: Support for staff photos and school logos
- **Security**: CSRF protection, secure password hashing, file upload validation

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vishnorex-attendance
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up demo data (optional)**
   ```bash
   python setup_demo_data.py
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and go to `http://127.0.0.1:5000`

## 🔐 Demo Login Credentials

After running `setup_demo_data.py`:

- **Company Admin**: `company_admin` / `admin123`
- **School Admin**: `school_admin` / `admin123`  
- **Staff**: `STAFF001`, `STAFF002`, or `STAFF003` / `staff123`

## 📁 Project Structure

```
├── app.py                 # Main Flask application
├── database.py           # Database configuration and initialization
├── requirements.txt      # Python dependencies
├── setup_demo_data.py   # Demo data setup script
├── test_app.py          # Unit tests
├── templates/           # HTML templates
├── static/             # CSS, JS, and uploaded files
└── vishnorex.db        # SQLite database file
```

## 🔧 Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key (auto-generated if not set)

### File Upload Settings

- **Allowed file types**: PNG, JPG, JPEG, GIF
- **Maximum file size**: 16MB
- **Upload directories**: 
  - Staff photos: `static/uploads/`
  - School logos: `static/school_logos/`

## 🧪 Testing

Run the test suite:
```bash
python test_app.py
```

## 🔒 Security Features

- **CSRF Protection**: All forms protected against CSRF attacks
- **Password Hashing**: Secure password storage using Werkzeug
- **File Upload Validation**: Restricted file types and size limits
- **SQL Injection Prevention**: Parameterized queries throughout
- **Session Management**: Secure session handling

## 🔌 ZK Biometric Device Integration

### Features
- **🌐 Cloud Connectivity**: Remote access to biometric devices via internet
- **🔌 Ethernet Support**: Direct local network connection (legacy mode)
- **🔄 Real-time Sync**: Automatic attendance synchronization
- **🔒 Secure Communication**: Encrypted data transmission with authentication
- **📱 Multi-device Management**: Centralized control of multiple devices
- **🔧 Dual Database**: SQLite (main) + MySQL (backup) support
- **👥 User Mapping**: Automatic mapping between device users and staff
- **🌐 Web Interface**: Easy-to-use device management interface
- **⏰ Multiple Punch Types**: Support for Check In/Out, Overtime In/Out
- **📊 REST API**: RESTful APIs for third-party integrations
- **🔄 WebSocket Support**: Real-time communication
- **📴 Offline Support**: Queue messages when connection is lost

### Supported Devices
- ZK Fingerprint devices
- ZK Face recognition devices
- ZK Multi-biometric devices
- Any ZK device with TCP/IP communication
- **NEW**: Cloud-connected devices via internet

### Connection Modes

#### 1. Cloud Mode (NEW) 🌐
- **Remote Access**: Connect to devices over the internet
- **Secure**: Encrypted communication with authentication
- **Scalable**: Support for multiple locations
- **Real-time**: WebSocket-based real-time updates

#### 2. Ethernet Mode (Legacy) 🔌
- **Local Network**: Direct IP connection to devices
- **Low Latency**: Direct communication
- **Reliable**: No internet dependency
- **Traditional**: Original connection method

#### 3. Hybrid Mode (Recommended) 🔄
- **Best of Both**: Automatic failover between cloud and ethernet
- **Flexible**: Choose connection method per device
- **Resilient**: Continues working if one method fails

### Quick Setup

#### Option 1: Cloud Setup (Recommended)
```bash
# Install all dependencies
pip install -r requirements.txt

# Configure cloud connectivity
python network_config.py
# Choose option 2 (Cloud) or 3 (Both)

# Start application
python app.py
```

### Cloud Configuration

#### Environment Variables
Create a `.env` file for cloud configuration:
```env
CLOUD_API_BASE_URL=https://api.zkcloud.example.com
CLOUD_WEBSOCKET_URL=wss://ws.zkcloud.example.com
CLOUD_API_KEY=your_api_key_here
CLOUD_SECRET_KEY=your_secret_key_here
CLOUD_ORG_ID=your_organization_id
CLOUD_USE_SSL=true
CLOUD_AUTO_SYNC=true
CLOUD_SYNC_INTERVAL=30
```

#### Device Configuration
Configure devices in `cloud_config.json`:
```json
{
  "devices": [
    {
      "device_id": "ZK_001",
      "device_name": "Main Biometric Device",
      "local_ip": "192.168.1.201",
      "local_port": 4370,
      "cloud_enabled": true,
      "sync_interval": 30
    }
  ]
}
```

### API Endpoints

#### Cloud API
- `GET /api/cloud/status` - Get cloud connector status
- `GET /api/cloud/devices` - List all devices
- `POST /api/cloud/devices/{id}/sync` - Trigger device sync
- `GET /api/cloud/devices/{id}/users` - Get device users
- `GET /api/cloud/devices/{id}/attendance` - Get attendance records
- `POST /api/cloud/devices/{id}/command` - Send device command

#### Authentication
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "X-Organization-ID: YOUR_ORG_ID" \
     https://api.zkcloud.example.com/api/cloud/status
```

### Network Configuration

#### Ethernet Mode
- **Device IP**: 192.168.1.201
- **Subnet Mask**: 255.255.255.0
- **Gateway**: 192.168.1.1
- **Port**: 4370

#### Cloud Mode
- **Internet Connection**: Required
- **Firewall**: Allow HTTPS (443) and WSS (443)
- **Bandwidth**: Minimal (< 1 MB/hour per device)
- **Latency**: < 500ms recommended

### Migration from Ethernet to Cloud

See [CLOUD_MIGRATION_GUIDE.md](CLOUD_MIGRATION_GUIDE.md) for detailed migration instructions.

#### Quick Migration Steps:
1. **Backup**: `cp vishnorex.db backup.db`
2. **Install**: `pip install -r requirements.txt`
3. **Configure**: `python network_config.py`
4. **Test**: Verify cloud connectivity in admin dashboard

#### Option 2: Ethernet Only (Legacy)
```bash
# Install basic dependencies
pip install pyzk pymysql

# Configure network (run as admin)
python network_config.py
# Choose option 1 (Ethernet)

# Test integration
python test_zk_integration.py

# Run demo
python demo_zk_sync.py
```

## 📊 Database Schema

The system uses SQLite with the following main tables:
- `schools` - Institution information
- `company_admins` - System administrators
- `admins` - School administrators  
- `staff` - Staff members
- `attendance` - Daily attendance records
- `leave_applications` - Leave requests and approvals

## 🚀 Deployment

For production deployment:

1. Set a strong `SECRET_KEY` environment variable
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure a reverse proxy (e.g., Nginx)
4. Consider using PostgreSQL instead of SQLite
5. Set up proper backup procedures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.
