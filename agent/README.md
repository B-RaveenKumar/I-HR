# Vishnorex Biometric Agent - Local Device Bridge

## Overview

The **Vishnorex Biometric Agent** is a Windows desktop application that enables the **Agent_LAN** connection mode for the Unified Biometric Ecosystem. It runs as a system tray application (and optionally as a Windows service) to:

- 🔄 Poll ZK biometric devices on your local network
- 📤 Push attendance logs to your Vishnorex server automatically
- 💓 Send heartbeat signals to maintain connection status
- 🖥️ Provide a user-friendly GUI for configuration and monitoring
- 🚀 Auto-start with Windows for unattended operation

---

## Features

### Core Functionality
- ✅ **Multi-Device Support**: Monitor multiple ZK devices simultaneously
- ✅ **Automatic Polling**: Configurable polling intervals (default: 60 seconds)
- ✅ **Secure Authentication**: API key-based authentication with server
- ✅ **Real-time Monitoring**: Live activity log in system tray application
- ✅ **Offline Resilience**: Continues operation even if server is temporarily unavailable
- ✅ **Incremental Sync**: Only syncs new records since last successful sync

### User Interface
- 🎨 **System Tray Integration**: Runs minimized in system tray
- ⚙️ **Configuration Dialog**: Easy setup for server URL, API key, and devices
- 📊 **Activity Log**: View real-time sync status and errors
- 🧪 **Connection Testing**: Test device connectivity before adding

### Service Features
- 🔧 **Windows Service Mode**: Run as background service with auto-start
- 📝 **Logging**: Comprehensive logging to `biometric_agent.log`
- 🔒 **Security**: API keys stored locally (not in source control)

---

## Installation

### Prerequisites

1. **Python 3.8+** installed on Windows
2. **PyQt5** for GUI
3. **requests** library for HTTP communication
4. **NSSM** (optional, for Windows service installation)

### Step 1: Install Python Dependencies

Open Command Prompt in the `agent` directory:

```cmd
cd "d:\Vishnorex-srk-Final\SM-DL-AWMS-SAC\SRK other version\Staff Management\agent"
pip install -r requirements.txt
```

This installs:
- `PyQt5` - GUI framework
- `requests` - HTTP client

### Step 2: Configure the Agent

1. **Run the agent** for the first time:
   ```cmd
   python biometric_agent.py
   ```

2. **Click "Configuration"** button

3. **Enter Server Settings:**
   - **Server URL**: Your Vishnorex server URL (e.g., `http://192.168.1.100:5000`)
   - **API Key**: Generate from Vishnorex web UI (Device Management page)
   - **Agent Name**: Give your agent a unique name (e.g., `Office-Agent-1`)

4. **Add Devices:**
   - Click "Add Device"
   - Enter device IP (e.g., `192.168.1.201`)
   - Enter device port (default: `4370`)
   - Give device a name (e.g., `Main Entrance`)
   - Click "Test Connection" to verify

5. **Set Intervals:**
   - **Poll Interval**: How often to check devices for new records (default: 60 seconds)
   - **Heartbeat Interval**: How often to send status to server (default: 60 seconds)

6. **Click "Save"**

### Step 3: Start the Agent

Click the **"Start Agent"** button in the main window. You should see:
- Status changes to "Running" (green)
- Activity log shows "Agent registered successfully"
- Periodic heartbeat and polling messages

---

## Windows Service Installation (Optional)

Running as a Windows service ensures the agent starts automatically with Windows.

### Download NSSM

1. Download NSSM from: https://nssm.cc/download
2. Extract `nssm.exe` (64-bit version)
3. Copy `nssm.exe` to the `agent` folder

### Install as Service

1. **Right-click** Command Prompt → **Run as Administrator**

2. Navigate to agent directory:
   ```cmd
   cd "d:\Vishnorex-srk-Final\SM-DL-AWMS-SAC\SRK other version\Staff Management\agent"
   ```

3. Run installer:
   ```cmd
   python install_service.py
   ```

4. Follow prompts to install and start the service

### Service Management

**Start Service:**
```cmd
nssm start VishnorexBiometricAgent
```

**Stop Service:**
```cmd
nssm stop VishnorexBiometricAgent
```

**Check Status:**
```cmd
nssm status VishnorexBiometricAgent
```

**Uninstall Service:**
```cmd
python install_service.py uninstall
```

Or use Windows Services (`services.msc`) to manage the service.

---

## Usage

### Running as Desktop Application

1. Double-click `biometric_agent.py` or run:
   ```cmd
   python biometric_agent.py
   ```

2. The application opens and minimizes to system tray

3. **Double-click tray icon** to show main window

4. **Right-click tray icon** for quick menu:
   - Show Window
   - Exit

### Configuration Changes

1. Stop the agent (click "Stop Agent")
2. Click "Configuration"
3. Make changes
4. Click "Save"
5. Restart the agent

### Monitoring Activity

The **Activity Log** shows:
- 🟢 **Green**: Successful operations (sync, registration)
- 🟡 **Orange**: Warnings (connection issues, no new records)
- 🔴 **Red**: Errors (authentication failures, device errors)
- ⚫ **Black**: Informational messages

Example log entries:
```
[14:30:15] Agent started
[14:30:16] Agent registered successfully
[14:30:17] Heartbeat sent
[14:31:15] Polling Main Entrance...
[14:31:16] Found 3 records from Main Entrance
[14:31:17] Synced 3 records from Main Entrance
```

---

## Troubleshooting

### Agent Won't Start

**Problem**: "Failed to register agent - check API key"

**Solution**:
1. Verify API key is correct (copy from Vishnorex web UI)
2. Check server URL is accessible (try opening in browser)
3. Ensure server is running and `/api/agent/register` endpoint exists

---

### Cannot Connect to Device

**Problem**: "Cannot connect to Main Entrance"

**Solution**:
1. Verify device IP is correct
2. Check device is powered on and connected to network
3. Ping device: `ping 192.168.1.201`
4. Try port 4370 (default) or 32150 (some models)
5. Check firewall isn't blocking connections

---

### No Records Being Synced

**Problem**: Log shows "No new records" repeatedly

**Possible Causes**:
1. ✅ **Normal**: No one has used the device since last sync
2. ❌ **Device clock wrong**: Check device time matches server time
3. ❌ **Last sync time incorrect**: Delete `config.json` and reconfigure

---

### Service Won't Start

**Problem**: Service starts then immediately stops

**Solution**:
1. Check logs: `agent\service_error.log`
2. Verify Python path in service configuration
3. Run manually first to ensure configuration is valid
4. Check NSSM installation is correct

---

## API Key Generation

To generate an API key for the agent:

1. Log in to Vishnorex web UI as admin
2. Go to **Biometric Devices** page
3. Click **"Agents"** tab
4. Click **"Generate API Key"** button
5. Copy the generated key (it won't be shown again!)
6. Paste into agent configuration

**Security Note**: Treat API keys like passwords. Each agent should have its own unique key.

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│  Vishnorex Biometric Agent (Windows Desktop)       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐      ┌──────────────┐            │
│  │  Main UI    │──────│  Config      │            │
│  │  (PyQt5)    │      │  Manager     │            │
│  └─────────────┘      └──────────────┘            │
│         │                                          │
│         │                                          │
│  ┌─────▼──────────────────────────────┐           │
│  │  Agent Worker (Background Thread)  │           │
│  ├────────────────────────────────────┤           │
│  │  • Device Polling Loop             │           │
│  │  • Heartbeat Loop                  │           │
│  │  • Server Communication            │           │
│  └────────────────────────────────────┘           │
│         │              │                           │
│         │              │                           │
└─────────┼──────────────┼───────────────────────────┘
          │              │
          ▼              ▼
   ┌──────────────┐  ┌─────────────────┐
   │  ZK Device   │  │  Vishnorex      │
   │  (Local LAN) │  │  Server (API)   │
   └──────────────┘  └─────────────────┘
```

### Data Flow

1. **Registration**: Agent registers with server using API key
2. **Polling**: Agent connects to each ZK device, retrieves new records
3. **Processing**: Records formatted and prepared for API
4. **Pushing**: Records sent to server via `/api/agent/push_logs`
5. **Heartbeat**: Status sent to server via `/api/agent/heartbeat`
6. **Tracking**: Last sync time stored to avoid duplicate processing

---

## Configuration File

Location: `agent\config.json`

```json
{
    "server_url": "http://192.168.1.100:5000",
    "api_key": "your-api-key-here",
    "agent_name": "Office-Agent-1",
    "devices": [
        {
            "ip": "192.168.1.201",
            "port": 4370,
            "name": "Main Entrance"
        },
        {
            "ip": "192.168.1.202",
            "port": 4370,
            "name": "Back Door"
        }
    ],
    "poll_interval": 60,
    "heartbeat_interval": 60,
    "last_sync": {
        "192.168.1.201": "2025-12-02T14:30:00.000000",
        "192.168.1.202": "2025-12-02T14:30:00.000000"
    }
}
```

**Fields:**
- `server_url`: Vishnorex server base URL
- `api_key`: Authentication key (keep secret!)
- `agent_name`: Unique identifier for this agent
- `devices`: Array of ZK devices to monitor
- `poll_interval`: Seconds between device polls
- `heartbeat_interval`: Seconds between heartbeats
- `last_sync`: Last successful sync timestamp per device (auto-managed)

---

## Logs

### Application Log
**Location**: `agent\biometric_agent.log`

Contains detailed logs of all agent operations:
- Device connections
- Record retrieval
- Server communication
- Errors and warnings

### Service Logs (if installed as service)
**Location**: 
- `agent\service_output.log` - stdout
- `agent\service_error.log` - stderr

---

## Security Best Practices

1. ✅ **Protect API Keys**: Never commit `config.json` to source control
2. ✅ **Use HTTPS**: Configure server with SSL for production
3. ✅ **Firewall Rules**: Only allow agent to access required ports
4. ✅ **Regular Updates**: Keep agent software up to date
5. ✅ **Unique Keys**: Each agent should have its own API key
6. ✅ **Key Rotation**: Regenerate API keys periodically

---

## Performance Tuning

### Polling Interval
- **Default**: 60 seconds
- **High Traffic**: 30 seconds (more frequent sync)
- **Low Traffic**: 120-300 seconds (reduce server load)

### Heartbeat Interval
- **Default**: 60 seconds
- **Stable Network**: 120 seconds
- **Unreliable Network**: 30 seconds (faster detection of disconnects)

### Multiple Devices
- Agent polls devices **sequentially** (one at a time)
- Each device poll takes ~2-5 seconds
- With 10 devices, one complete cycle takes ~20-50 seconds
- Adjust poll interval accordingly

---

## Uninstallation

### Desktop Application
Simply delete the `agent` folder. No registry entries or system files.

### Windows Service
1. **Stop and remove service**:
   ```cmd
   python install_service.py uninstall
   ```

2. **Delete agent folder** (optional)

---

## FAQ

**Q: Can I run multiple agents on the same network?**  
A: Yes! Each agent should have:
- Unique agent name
- Its own API key
- Non-overlapping device assignments (avoid polling same device from multiple agents)

**Q: What happens if the server is offline?**  
A: The agent continues polling devices and logs errors. When server comes back online, the next sync will include all missed records (devices retain logs).

**Q: Can I monitor the same device from multiple institutions?**  
A: No. Each device belongs to one institution. The server enforces this via API key authentication.

**Q: How do I update the agent?**  
A: 
1. Stop agent/service
2. Replace `biometric_agent.py` with new version
3. Run `pip install -r requirements.txt` (if dependencies changed)
4. Restart agent/service

**Q: Does this work on Linux/Mac?**  
A: The agent uses PyQt5 which is cross-platform, but service installation is Windows-specific. For Linux, use systemd instead of NSSM.

---

## Support

For issues or questions:
1. Check logs: `agent\biometric_agent.log`
2. Verify configuration: `agent\config.json`
3. Test manually: Run `python biometric_agent.py` in console
4. Check server API endpoints are operational

---

## Version History

**v1.0.0** (2025-12-02)
- Initial release
- Multi-device support
- System tray application
- Windows service support
- Configuration GUI
- Real-time activity log
- API key authentication
- Incremental sync with last_sync tracking

---

## License

Part of the Vishnorex Staff Management System.  
All rights reserved.
