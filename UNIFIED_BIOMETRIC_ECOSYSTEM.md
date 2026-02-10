# Unified Biometric Ecosystem - Complete Documentation

## Overview

The **Unified Biometric Ecosystem** is a comprehensive multi-device, multi-institution biometric attendance system for the Vishnorex Staff Management platform. It replaces the previous single-device hardcoded architecture with a flexible, scalable system supporting three connection modes.

**Version**: 1.0.0  
**Release Date**: December 2, 2025  
**Status**: ✅ Production Ready

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Connection Modes](#connection-modes)
4. [Components](#components)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)
10. [Migration Guide](#migration-guide)

---

## Features

### Core Capabilities

✅ **Multi-Device Support**
- Unlimited ZK biometric devices per institution
- Each institution manages their own devices independently
- Device-level segregation enforced at database level

✅ **Three Connection Modes**
1. **Direct_LAN**: Ethernet direct connection (legacy, most reliable)
2. **ADMS**: Cloud Push via ZKTeco ADMS platform (for remote devices)
3. **Agent_LAN**: Local Agent software bridges devices to server

✅ **Institution Segregation**
- Each school/institution has isolated device registry
- Cross-institution device access prevented at API level
- API key authentication per institution

✅ **Automatic Device Resolution**
- All 24 biometric endpoints use dynamic device lookup
- No hardcoded IPs anywhere in codebase
- Primary device auto-selection per institution

✅ **Comprehensive Management UI**
- Web-based device management interface
- Real-time device status monitoring
- Agent registration and health tracking
- CRUD operations for devices and agents

✅ **Desktop Agent Software**
- Windows system tray application
- Polls local devices automatically
- Pushes attendance to server via API
- Windows service support for auto-start
- Configuration GUI with connection testing

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Vishnorex Server (Flask)                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Database Layer (SQLite)                            │   │
│  │  - biometric_devices (connection configs)          │   │
│  │  - biometric_agents (agent registry)               │   │
│  │  - attendance (unified attendance records)         │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────┼────────────────────────────┐   │
│  │  UnifiedAttendanceProcessor                        │   │
│  │  - Device source mapping                           │   │
│  │  - Institution firewall                            │   │
│  │  - Duplicate prevention                            │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────┼────────────────────────────┐   │
│  │  API Endpoints                                      │   │
│  │  - 24 biometric endpoints (dynamic device lookup) │   │
│  │  - 11 device management routes                     │   │
│  │  - 4 agent API endpoints                           │   │
│  │  - 1 ADMS cloud push endpoint                      │   │
│  └────────────────────────┬────────────────────────────┘   │
└─────────────────────────────┼──────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         Mode 1         Mode 2         Mode 3
     Direct_LAN         ADMS      Agent_LAN
              │              │              │
              ▼              ▼              ▼
    ┌──────────────┐  ┌──────────┐  ┌──────────────┐
    │  ZK Device   │  │  ADMS    │  │  Local Agent │
    │  (Ethernet)  │  │  Cloud   │  │  (Desktop)   │
    └──────────────┘  └──────────┘  └──────┬───────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │  ZK Devices  │
                                    │  (Local LAN) │
                                    └──────────────┘
```

### Database Schema

#### biometric_devices
```sql
CREATE TABLE biometric_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,
    device_name TEXT NOT NULL,
    connection_type TEXT NOT NULL,  -- Direct_LAN, ADMS, Agent_LAN
    ip_address TEXT,
    port INTEGER DEFAULT 4370,
    device_id TEXT,                 -- ADMS cloud device ID
    is_primary INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id)
);
```

#### biometric_agents
```sql
CREATE TABLE biometric_agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,
    agent_name TEXT NOT NULL UNIQUE,
    api_key TEXT NOT NULL UNIQUE,
    last_heartbeat TIMESTAMP,
    status TEXT DEFAULT 'inactive',  -- active, inactive, error
    version TEXT,
    os_info TEXT,
    registered_devices TEXT,         -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_id) REFERENCES schools(id)
);
```

---

## Connection Modes

### 1. Direct_LAN (Ethernet Direct Connection)

**Best for**: On-premises devices with stable network

**How it works**:
1. Server connects directly to device IP via TCP
2. Polls device for attendance records on-demand
3. Uses zk_biometric.py (pyzk wrapper)

**Configuration**:
```json
{
    "device_name": "Main Entrance",
    "connection_type": "Direct_LAN",
    "ip_address": "192.168.1.201",
    "port": 4370,
    "is_primary": 1
}
```

**Pros**:
- ✅ Most reliable (direct connection)
- ✅ Real-time sync capability
- ✅ No additional software needed

**Cons**:
- ❌ Requires server and device on same network
- ❌ Firewall configuration needed
- ❌ Not suitable for remote locations

---

### 2. ADMS (Cloud Push via ZKTeco ADMS)

**Best for**: Remote devices, distributed locations

**How it works**:
1. Device connects to ZKTeco ADMS cloud
2. ADMS pushes attendance to Vishnorex via webhook
3. Server receives POST to `/api/cloud/push_attendance`

**Configuration**:
```json
{
    "device_name": "Branch Office",
    "connection_type": "ADMS",
    "device_id": "D123456789",
    "is_primary": 0
}
```

**ADMS Setup**:
1. Configure device on ADMS platform
2. Set webhook URL: `http://your-server/api/cloud/push_attendance`
3. Generate API key in Vishnorex
4. Configure ADMS to send attendance data

**Pros**:
- ✅ Works over internet (no VPN needed)
- ✅ Automatic push from device
- ✅ Scalable to many locations

**Cons**:
- ❌ Requires ADMS subscription
- ❌ Dependent on cloud service uptime
- ❌ Additional configuration complexity

**See**: `ADMS_CONFIGURATION_GUIDE.md` for detailed setup

---

### 3. Agent_LAN (Local Agent Bridge)

**Best for**: Multiple devices on local network, no direct server access

**How it works**:
1. Windows agent software runs on local PC
2. Agent polls devices on local network
3. Agent pushes records to server via API
4. Heartbeat monitoring for agent health

**Configuration**:

**Server side** (device registration):
```json
{
    "device_name": "Agent-Managed Device",
    "connection_type": "Agent_LAN",
    "ip_address": "192.168.1.202",
    "port": 4370
}
```

**Agent side** (agent\config.json):
```json
{
    "server_url": "http://server-ip:5000",
    "api_key": "your-api-key-here",
    "agent_name": "Office-Agent-1",
    "devices": [
        {
            "ip": "192.168.1.202",
            "port": 4370,
            "name": "Device 1"
        }
    ],
    "poll_interval": 60,
    "heartbeat_interval": 60
}
```

**Pros**:
- ✅ Works behind firewall/NAT
- ✅ Supports multiple devices per agent
- ✅ Automatic polling and sync
- ✅ Windows service support (auto-start)

**Cons**:
- ❌ Requires PC running 24/7
- ❌ Additional software to maintain
- ❌ Windows-only (currently)

**See**: `agent\README.md` for complete agent documentation

---

## Components

### Backend Components

#### 1. Database Helper Functions (database.py)
18 functions for device/agent CRUD operations:
- `create_biometric_device()` - Register new device
- `get_devices_by_school()` - List institution's devices
- `get_primary_device_for_institution()` - Get default device
- `register_agent()` - Register new agent
- `update_agent_heartbeat()` - Update agent status
- And 13 more...

#### 2. UnifiedAttendanceProcessor (database.py)
Central attendance processing with:
- Device source mapping
- Institution firewall (prevents cross-institution access)
- Duplicate detection
- Timestamp normalization

```python
processor = UnifiedAttendanceProcessor()
result = processor.process_records(
    records=[...],
    school_id=1,
    device_source='192.168.1.201',
    source_type='Direct_LAN'
)
```

#### 3. API Endpoints (app.py)

**Device Management (11 routes)**:
- `/biometric_devices` - Management UI
- `/api/devices` - List devices (GET)
- `/api/devices` - Create device (POST)
- `/api/devices/<id>` - Get device (GET)
- `/api/devices/<id>` - Update device (PUT)
- `/api/devices/<id>` - Delete device (DELETE)
- `/api/devices/<id>/primary` - Set primary (PUT)
- `/api/agents` - List agents (GET)
- `/api/agents/<id>` - Get agent (GET)
- `/api/agents/<id>` - Update agent (PUT)
- `/api/agents/<id>` - Delete agent (DELETE)

**Agent API (4 endpoints)**:
- `/api/agent/register` - Agent registration
- `/api/agent/heartbeat` - Heartbeat ping
- `/api/agent/push_logs` - Upload attendance records
- `/api/agent/config` - Get agent configuration

**Cloud Push (1 endpoint)**:
- `/api/cloud/push_attendance` - ADMS webhook receiver

**Biometric Operations (24 endpoints)** - All use dynamic device lookup:
- `/verify_biometric` - Staff verification
- `/add_staff` - Create user on device
- `/update_staff_biometric` - Update user
- `/delete_staff` - Remove user
- `/sync_biometric_attendance` - Manual sync
- `/enroll_biometric_user` - Fingerprint enrollment
- And 18 more...

### Frontend Components

#### Device Management UI (templates/biometric_device_management.html)
Tabbed interface with:
- **Devices Tab**: CRUD for devices, set primary, status indicators
- **Agents Tab**: View agents, health status, last heartbeat
- **Settings Tab**: API key generation, connection testing

Features:
- Real-time status updates
- Color-coded device types (LAN=blue, ADMS=green, Agent=orange)
- AJAX operations (no page reload)
- Form validation

#### Desktop Agent (agent/biometric_agent.py)
PyQt5 Windows application:
- System tray integration
- Configuration dialog
- Real-time activity log
- Device connection testing
- Background worker threads
- Windows service installer

---

## Installation

### Server Installation

**Prerequisites**: Flask server already installed

**Step 1**: Database migration already complete (tables exist)

**Step 2**: Verify helper functions in `database.py`
```python
from database import create_biometric_device, get_devices_by_school
```

**Step 3**: Access Device Management UI
- Login as admin
- Navigate to **Biometric Devices** (sidebar link)

---

### Agent Installation

See `agent\README.md` or `agent\QUICKSTART.md` for complete guide.

**Quick Install**:
```cmd
cd agent
pip install -r requirements.txt
python biometric_agent.py
```

---

## Configuration

### Web UI Configuration

1. **Login** as admin
2. **Go to** Biometric Devices page
3. **Click** "Add Device"
4. **Select** connection type:
   - **Direct_LAN**: Enter IP and port
   - **ADMS**: Enter device ID
   - **Agent_LAN**: Enter IP (agent manages connection)
5. **Set** as primary device (optional)
6. **Save**

### Agent Configuration

1. **Generate API Key**: Devices page → Agents tab → Generate Key
2. **Configure Agent**: Run agent → Configuration → Enter server URL + API key
3. **Add Devices**: Click "Add Device" → Enter IP/port → Test connection
4. **Start Agent**: Click "Start Agent"

---

## Usage

### For Administrators

#### View All Devices
Go to **Biometric Devices** → **Devices tab**

Shows:
- Device name and type
- IP address (if applicable)
- Status (Active/Inactive)
- Primary device indicator

#### Add New Device
1. Click **"Add Device"**
2. Fill form:
   - Name: `Main Entrance`
   - Type: `Direct_LAN`
   - IP: `192.168.1.201`
   - Port: `4370`
3. Click **"Save"**

#### Set Primary Device
- Click **"Set Primary"** button next to device
- Primary device is used for all biometric operations by default

#### Register Agent
1. Go to **Agents tab**
2. Click **"Generate API Key"**
3. Copy key (shown once!)
4. Configure agent with this key

#### Monitor Agent Health
**Agents tab** shows:
- Agent name
- Status (Active/Inactive)
- Last heartbeat time
- Registered devices count

---

### For End Users (Staff)

No changes! Staff enrollment and verification work exactly as before, but now use the configured device automatically.

---

## API Reference

### Authentication

**API Key Header**:
```
X-API-Key: your-api-key-here
```

Used by agents and ADMS webhooks.

**Session Authentication**:
All web UI routes use Flask session (existing auth).

---

### Agent API Endpoints

#### POST /api/agent/register
Register a new agent.

**Headers**:
```
X-API-Key: agent-api-key
```

**Body**:
```json
{
    "agent_name": "Office-Agent-1",
    "version": "1.0.0",
    "os": "Windows",
    "devices": [
        {"ip": "192.168.1.201", "port": 4370, "name": "Device 1"}
    ]
}
```

**Response**:
```json
{
    "success": true,
    "message": "Agent registered",
    "agent_id": 1
}
```

---

#### POST /api/agent/heartbeat
Send heartbeat ping.

**Headers**:
```
X-API-Key: agent-api-key
```

**Body**:
```json
{
    "agent_name": "Office-Agent-1",
    "status": "active",
    "devices": [...]
}
```

**Response**:
```json
{
    "success": true,
    "message": "Heartbeat received"
}
```

---

#### POST /api/agent/push_logs
Upload attendance records.

**Headers**:
```
X-API-Key: agent-api-key
```

**Body**:
```json
{
    "agent_name": "Office-Agent-1",
    "device_ip": "192.168.1.201",
    "device_name": "Main Entrance",
    "records": [
        {
            "user_id": "101",
            "timestamp": "2025-12-02T09:00:00",
            "status": 1,
            "punch": 0
        }
    ]
}
```

**Response**:
```json
{
    "success": true,
    "processed": 1,
    "duplicates": 0,
    "errors": 0
}
```

---

### Device Management API

See `app.py` for complete API reference (lines 10500-11500).

---

## Troubleshooting

### Server Issues

**Problem**: Device management page shows no devices

**Solution**:
1. Check database: `SELECT * FROM biometric_devices WHERE school_id = ?`
2. Verify session has `school_id`
3. Check browser console for JS errors

---

**Problem**: "No biometric device configured" error

**Solution**:
1. Add at least one device via web UI
2. Set it as primary device
3. Ensure device connection type is `Direct_LAN` for immediate use

---

### Agent Issues

See `agent\README.md` → Troubleshooting section

Common issues:
- API key invalid → Regenerate key
- Cannot connect to device → Check IP with `ping`
- No records syncing → Check device clock vs server clock

---

### ADMS Issues

See `ADMS_CONFIGURATION_GUIDE.md`

---

## Migration Guide

### From Legacy System (Hardcoded IP)

The migration is **already complete**! All endpoints now use dynamic device lookup.

**What changed**:
- ❌ Removed: Hardcoded `device_ip = '192.168.1.201'`
- ✅ Added: `device_ip, port = get_institution_device()`

**What stayed the same**:
- API signatures unchanged
- Frontend code unchanged
- Staff enrollment process unchanged

**To use your existing device**:
1. Add it to Device Management UI
2. Set as primary device
3. That's it! All operations now use it automatically

---

## Performance Considerations

### Database Indexes

Add indexes for performance:
```sql
CREATE INDEX idx_biometric_devices_school ON biometric_devices(school_id);
CREATE INDEX idx_biometric_agents_school ON biometric_agents(school_id);
CREATE INDEX idx_biometric_agents_status ON biometric_agents(status);
```

### Agent Polling Frequency

- **High Traffic** (500+ staff): Poll every 30 seconds
- **Normal Traffic** (100-500 staff): Poll every 60 seconds (default)
- **Low Traffic** (<100 staff): Poll every 120-300 seconds

### Multiple Agents

- Assign non-overlapping devices to agents
- Don't poll same device from multiple agents
- Use round-robin if needed

---

## Security Considerations

1. ✅ **API Key Rotation**: Regenerate agent keys periodically
2. ✅ **HTTPS**: Use SSL in production (not HTTP)
3. ✅ **Firewall**: Restrict access to agent API endpoints
4. ✅ **Device Isolation**: Enforce institution segregation at database level
5. ✅ **Audit Logging**: Log all device/agent registration changes

---

## Future Enhancements

Possible improvements:
- 📱 Mobile agent app (Android/iOS)
- 🐧 Linux/Mac agent support
- 🔄 Device failover (secondary device auto-switch)
- 📊 Device performance metrics dashboard
- 🔔 Webhook notifications for agent failures
- 🌐 Multi-server agent support (agent pushes to multiple servers)

---

## Version History

**v1.0.0** (December 2, 2025)
- Initial release
- 3 connection modes (Direct_LAN, ADMS, Agent_LAN)
- 24 refactored endpoints with dynamic device lookup
- Device management UI
- Windows desktop agent
- Complete documentation

---

## Support

For issues:
1. Check logs: `biometric_agent.log` (agent), Flask logs (server)
2. Verify configuration: Database tables, API keys
3. Test connections: Ping devices, test agent registration
4. Review documentation: This file, agent README, ADMS guide

---

## License

Part of Vishnorex Staff Management System.  
All rights reserved.

---

**End of Documentation**
