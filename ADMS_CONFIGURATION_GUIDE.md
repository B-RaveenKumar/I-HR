# ZK Device ADMS Configuration Guide

This guide explains how to configure ZK biometric devices to push attendance data directly to your web server using ADMS (Attendance Data Management System) protocol.

---

## Overview

**ADMS Mode** allows ZK devices to automatically push attendance records to your server via HTTP POST requests, eliminating the need for manual sync or Local Agent software.

**Benefits:**
- ✅ Real-time attendance updates
- ✅ No polling required
- ✅ Works over internet (with port forwarding)
- ✅ Automatic retry on connection failure
- ✅ Device-initiated (no server polling)

---

## Prerequisites

### 1. Network Requirements

Your server must be accessible from the device. Options:

**Option A: Same LAN**
- Device and server on same network
- Server IP: `192.168.x.x`
- No port forwarding needed

**Option B: Internet Access**
- Device has internet access
- Server has public IP or domain
- Port forwarding configured on router

### 2. Server Requirements

- Flask server running on accessible IP
- Port open (default: 5000 or your configured port)
- ADMS endpoint active: `/iclock/cdata.aspx`

### 3. Device Requirements

- ZK device with ADMS/Cloud Push support
- Admin access to device web interface or standalone software
- Firmware version supporting HTTP Push (most modern ZK devices)

---

## Step 1: Get Server Details

Before configuring the device, you need:

### 1.1 Get Your Server IP

**If on LAN:**
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```
Example: `192.168.1.50`

**If on Internet:**
- Use your public IP or domain name
- Find public IP: Visit `https://whatismyipaddress.com/`
- Example: `203.0.113.45`

### 1.2 Get Your Server Port

Default Flask port: `5000`

Check your `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # <-- This is your port
```

### 1.3 Test Server Endpoint

Open browser and visit:
```
http://YOUR_IP:YOUR_PORT/api/cloud/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-02T10:30:45",
  "service": "ZK Biometric Cloud API"
}
```

If you see this, your server is ready!

---

## Step 2: Find Device Serial Number

The serial number is crucial for identifying the device in your system.

### Method 1: Device Admin Panel

1. Access device admin panel (usually via browser or standalone software)
2. Navigate to **Device Information** or **System Info**
3. Look for **Serial Number** or **Device SN**
4. Example: `ZKDEV123456` or `DGD9190012345`

### Method 2: Device Display

Some devices show serial on the main screen:
- Press **Menu** → **Device Info** → **Serial Number**

### Method 3: Physical Label

Check the back or bottom of the device for a sticker with the serial number.

**⚠️ IMPORTANT:** Save this serial number - you'll need it for both device configuration AND web registration.

---

## Step 3: Register Device in Web System

**BEFORE configuring the device**, register it in your web system:

1. Log in as admin
2. Navigate to **Device Management** (when UI is implemented)
3. Click **Add Device**
4. Fill in the form:
   - **Device Name:** `Main Gate ADMS` (your choice)
   - **Institution:** Select your institution
   - **Connection Type:** Select `ADMS`
   - **Serial Number:** `ZKDEV123456` (from Step 2)

5. **IMPORTANT:** Note the **Server Configuration** displayed:
   ```
   -------------------------------------------------------
   !  IMPORTANT: Configure Device Network Settings       !
   -------------------------------------------------------
   |  Server Address: 203.0.113.45                        |
   |  Server Port:    5000                                |
   |  Endpoint Path:  /iclock/cdata.aspx                 |
   -------------------------------------------------------
   ```

6. Click **Save Device**

---

## Step 4: Configure ZK Device (Web Interface Method)

### 4.1 Access Device Web Interface

1. Find device IP address:
   - Check device display: **Menu** → **Network** → **IP Address**
   - Or use ZKAccess software to scan network

2. Open browser and navigate to:
   ```
   http://DEVICE_IP
   ```
   Example: `http://192.168.1.201`

3. Log in with admin credentials:
   - Default username: `admin`
   - Default password: `admin` (or your custom password)

### 4.2 Configure ADMS Push

1. Navigate to: **Options** → **Cloud** or **Advanced** → **ADMS**

2. Configure the following:

   | Setting | Value |
   |---------|-------|
   | **Enable ADMS** | ✅ Checked/Enabled |
   | **Server Address** | `203.0.113.45` (your server IP) |
   | **Server Port** | `5000` (your server port) |
   | **Protocol** | HTTP |
   | **Push Interval** | `60` seconds (recommended) |
   | **Endpoint URL** | `/iclock/cdata.aspx` |
   | **Connection Timeout** | `30` seconds |
   | **Retry Count** | `3` |

3. **Advanced Settings (if available):**
   - **Push on Event:** Enable (immediate push on attendance)
   - **Push on Interval:** Enable (periodic sync)
   - **Include User Data:** Disable (we only need attendance logs)

4. Click **Save** or **Apply**

### 4.3 Test Connection

Most devices have a **Test Connection** button. Click it to verify:

**Expected Result:**
```
Connection Test: SUCCESS
Server Response: 200 OK
```

**If Failed:**
- Check server IP and port
- Verify firewall allows incoming connections
- Check if server is running
- Try pinging server from device (if device supports it)

---

## Step 5: Configure ZK Device (ZKAccess Software Method)

If your device doesn't have a web interface, use ZKAccess/ZKTime standalone software.

### 5.1 Install ZKAccess Software

1. Download from ZKTeco official website
2. Install on Windows PC
3. Launch application

### 5.2 Add Device to Software

1. Click **Device** → **Add Device**
2. Enter device IP and admin password
3. Click **Connect**

### 5.3 Configure ADMS

1. Select device in device list
2. Right-click → **Device Parameters** or **Cloud Settings**
3. Navigate to **ADMS** or **Cloud Push** tab
4. Configure settings (same as web interface above)
5. Click **Upload Settings to Device**
6. Wait for confirmation

---

## Step 6: Verify Configuration

### 6.1 Check Device Status

1. On device display: **Menu** → **System** → **Cloud Status**
2. Expected: **Connected** or **Online**

### 6.2 Generate Test Attendance

1. Register a test user on device (or use existing)
2. Perform fingerprint verification
3. Check device display for success message

### 6.3 Check Server Logs

**Method 1: Flask Console**

Watch Flask console for incoming requests:
```
INFO:cloud_api:ADMS Push received from device ZKDEV123456: 1 record(s)
INFO:zk_biometric:✓ Punch processed successfully: John Doe (check-in) at 10:30:45 on device Main Gate ADMS
```

**Method 2: Database Query**

Check biometric_verifications table:
```sql
SELECT * FROM biometric_verifications 
WHERE device_ip LIKE 'Device:%' 
ORDER BY verification_time DESC 
LIMIT 5;
```

**Method 3: API Call**

```bash
curl http://localhost:5000/api/cloud/adms/devices -H "Authorization: Bearer YOUR_API_KEY"
```

Look for your device with recent `last_sync` timestamp.

---

## Troubleshooting

### Issue 1: Device Shows "Connection Failed"

**Possible Causes:**
1. Server not accessible from device network
2. Firewall blocking port
3. Incorrect IP/port configuration

**Solutions:**

**Check 1: Ping Test**
```bash
# From device (if supported) or from a PC on same network as device
ping YOUR_SERVER_IP
```

**Check 2: Port Test**
```bash
# From PC on same network as device
telnet YOUR_SERVER_IP YOUR_PORT
```

**Check 3: Firewall**
```bash
# Windows - Allow port
netsh advfirewall firewall add rule name="Flask ADMS" dir=in action=allow protocol=TCP localport=5000

# Linux - Allow port
sudo ufw allow 5000/tcp
```

### Issue 2: Device Connects but No Data Received

**Possible Causes:**
1. Endpoint URL incorrect
2. Serial number mismatch
3. Device not registered in web system

**Solutions:**

**Check 1: Verify Endpoint**
Device endpoint should be EXACTLY: `/iclock/cdata.aspx`

**Check 2: Check Serial Number**
```sql
SELECT serial_number, device_name FROM biometric_devices WHERE connection_type = 'ADMS';
```
Compare with device serial number.

**Check 3: Enable Debug Logging**

Edit `cloud_api.py`:
```python
logger.setLevel(logging.DEBUG)  # Add at top of file
```

Restart server and watch for detailed logs.

### Issue 3: "Device with serial number not registered"

**Cause:** Device not added to web system or serial mismatch

**Solution:**
1. Check device serial in database:
   ```sql
   SELECT * FROM biometric_devices WHERE serial_number = 'ZKDEV123456';
   ```
2. If not found, add device via Device Management UI
3. If found but different serial, update device configuration

### Issue 4: Firewall Rejection (Staff Not Found)

**Cause:** Staff belongs to different institution than device

**Solution:**
```sql
-- Check device institution
SELECT device_name, school_id FROM biometric_devices WHERE serial_number = 'ZKDEV123456';

-- Check staff institution
SELECT staff_id, full_name, school_id FROM staff WHERE staff_id = '101';
```

Verify both have same `school_id`. If not, reassign device or staff to correct institution.

### Issue 5: Duplicate Push / Delayed Push

**Cause:** Push interval too short or network delays

**Solution:**
- Increase push interval to 60-120 seconds
- Enable "Push on Event" instead of interval-based
- Check network latency

---

## Router Configuration (For Internet Access)

If device and server are on different networks, configure port forwarding on server's router.

### Port Forwarding Setup

**Router Admin Panel:**
1. Log into router (usually `192.168.1.1` or `192.168.0.1`)
2. Navigate to **Port Forwarding** or **Virtual Server**
3. Add new rule:
   - **External Port:** `5000` (or your choice)
   - **Internal IP:** Your server's LAN IP (e.g., `192.168.1.50`)
   - **Internal Port:** `5000`
   - **Protocol:** `TCP`
4. Save and apply

**Update Device Configuration:**
- **Server Address:** Your public IP (not LAN IP)
- **Server Port:** External port from router rule

---

## Security Considerations

### 1. Use HTTPS (Recommended)

For production, use HTTPS instead of HTTP:

**Requirements:**
- SSL certificate (Let's Encrypt free option)
- Reverse proxy (Nginx/Apache)
- Configure device with `https://` URL

### 2. Restrict Access

**Firewall Rule:**
```bash
# Allow only from device IP
sudo ufw allow from DEVICE_IP to any port 5000
```

### 3. Monitor for Abuse

Check for unusual activity:
```sql
SELECT serial_number, COUNT(*) as push_count, MAX(verification_time) as last_push
FROM biometric_verifications
WHERE device_ip LIKE 'Device:%'
GROUP BY serial_number
HAVING push_count > 1000;  -- Alert if > 1000 pushes per day
```

---

## Device Configuration Checklist

**Before Starting:**
- [ ] Server is running and accessible
- [ ] Health check endpoint returns success
- [ ] Device serial number recorded
- [ ] Device registered in web system

**Device Configuration:**
- [ ] ADMS enabled
- [ ] Server IP/domain configured
- [ ] Server port configured (5000)
- [ ] Endpoint path: `/iclock/cdata.aspx`
- [ ] Push interval: 60 seconds
- [ ] Connection test: SUCCESS

**Verification:**
- [ ] Test attendance performed
- [ ] Server logs show "ADMS Push received"
- [ ] Database shows new attendance record
- [ ] Device status: Connected

---

## Advanced: Multiple Devices

To configure multiple ADMS devices:

1. **Register each device** in web system with unique serial number
2. **Configure each device** with same server IP/port (they all push to same endpoint)
3. **Institution segregation** is automatic (based on serial number lookup)

**Example:**
```
Device A (Serial: ZK001) → Institution 1
Device B (Serial: ZK002) → Institution 2
Device C (Serial: ZK003) → Institution 1

All push to: http://server:5000/iclock/cdata.aspx

Server automatically routes:
  - ZK001 punches → Institution 1 staff only
  - ZK002 punches → Institution 2 staff only
  - ZK003 punches → Institution 1 staff only
```

---

## ADMS vs Direct LAN vs Local Agent

| Feature | ADMS | Direct LAN | Local Agent |
|---------|------|------------|-------------|
| **Sync Method** | Device pushes | Server polls | Agent polls & pushes |
| **Real-time** | ✅ Yes | ❌ No (manual) | ⚠️ Near real-time |
| **Internet Required** | ✅ Yes (or LAN) | ❌ No | ❌ No |
| **Port Forwarding** | ✅ Required (if internet) | ❌ Not needed | ❌ Not needed |
| **Setup Complexity** | ⭐⭐ Medium | ⭐ Easy | ⭐⭐⭐ Complex |
| **Best For** | Remote branches | Single office | Isolated networks |

---

## Sample Device Configuration File

If your device supports configuration export, the settings should look like:

```ini
[ADMS]
Enable=1
ServerAddress=203.0.113.45
ServerPort=5000
Protocol=HTTP
EndpointURL=/iclock/cdata.aspx
PushInterval=60
ConnectionTimeout=30
RetryCount=3
PushOnEvent=1
PushOnInterval=1
```

---

## Support & Resources

**ZKTeco Documentation:**
- Official: https://www.zkteco.com/en/
- User Manual: Check device box or manufacturer website

**Server Endpoint:**
- Health Check: `http://YOUR_SERVER:5000/api/cloud/health`
- ADMS Push: `http://YOUR_SERVER:5000/iclock/cdata.aspx` (GET/POST)
- Device List: `http://YOUR_SERVER:5000/api/cloud/adms/devices` (requires API key)

**Need Help?**
- Check server logs: Flask console
- Check database: `biometric_verifications` table
- Enable debug logging in `cloud_api.py`

---

**Last Updated:** December 2, 2025  
**Tested Devices:** ZKTeco K40, iClock 360, F18, F22  
**Protocol Version:** ADMS 1.0/2.0
