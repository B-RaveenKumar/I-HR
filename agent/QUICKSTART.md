# Quick Start Guide - Vishnorex Biometric Agent

## 5-Minute Setup

### Step 1: Install Dependencies (1 minute)

Open Command Prompt:
```cmd
cd "d:\Vishnorex-srk-Final\SM-DL-AWMS-SAC\SRK other version\Staff Management\agent"
pip install PyQt5 requests
```

### Step 2: Generate API Key (1 minute)

1. Open Vishnorex in browser
2. Login as admin
3. Go to **Biometric Devices** → **Agents** tab
4. Click **"Generate API Key"**
5. Copy the key (you won't see it again!)

### Step 3: Configure Agent (2 minutes)

1. Run the agent:
   ```cmd
   python biometric_agent.py
   ```

2. Click **"Configuration"**

3. Enter:
   - **Server URL**: `http://your-server-ip:5000`
   - **API Key**: Paste the key from Step 2
   - **Agent Name**: `Agent-1`

4. Click **"Add Device"**:
   - IP: `192.168.1.201` (your ZK device IP)
   - Port: `4370`
   - Name: `Main Device`

5. Click **"Test Connection"** to verify

6. Click **"Save"**

### Step 4: Start Agent (1 minute)

1. Click **"Start Agent"** button
2. Watch the activity log for:
   ```
   Agent registered successfully
   Heartbeat sent
   Polling Main Device...
   Found X records from Main Device
   Synced X records from Main Device
   ```

3. **Minimize to system tray** (agent keeps running)

### Done! 🎉

Your agent is now:
- ✅ Polling your ZK device every 60 seconds
- ✅ Syncing attendance to your Vishnorex server
- ✅ Running in the background (system tray)

---

## Next Steps

### Make it Auto-Start with Windows

1. Download NSSM: https://nssm.cc/download
2. Copy `nssm.exe` to `agent` folder
3. Right-click Command Prompt → Run as Administrator
4. Run:
   ```cmd
   cd agent
   python install_service.py
   ```

### Monitor Activity

- **Double-click system tray icon** to show window
- **Check activity log** for sync status
- **Logs saved to**: `agent\biometric_agent.log`

### Add More Devices

1. Click **"Configuration"**
2. Click **"Add Device"**
3. Repeat for each device
4. Click **"Save"**

---

## Troubleshooting

**"Failed to register agent"**  
→ Check server URL and API key

**"Cannot connect to device"**  
→ Verify device IP with: `ping 192.168.1.201`

**"No new records"**  
→ Normal if no one used the device recently

---

## Full Documentation

See `README.md` for complete documentation.
