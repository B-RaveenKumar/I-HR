# Universal ADMS Receiver - Quick Start Guide

## 🚀 Installation & Setup (5 Minutes)

### Step 1: Run Database Migration
```bash
cd "d:\HRMS\Staff Management (2)-22222\Staff Management"
python migrate_universal_adms.py
```

**Expected Output:**
```
✓ Backup created: backups/vishnorex_pre_universal_adms_YYYYMMDD_HHMMSS.db
✓ Connected to database
✓ Successfully completed 3 migration step(s)
```

### Step 2: Test the Parser
```bash
python test_universal_parser.py
```

**Expected Output:**
```
🎉 ALL TESTS PASSED! 🎉

✅ The Universal ADMS Parser is working correctly!
✅ Ready to handle:
   • Legacy fingerprint devices (K40, F18)
   • Modern face recognition (uFace, SpeedFace)
   • Palm scanners with temperature
   • All data formats (Text, JSON, XML)
```

### Step 3: Restart Your Flask Application
```bash
# Stop current server (Ctrl+C)
python app.py
```

**Verify Startup:**
```
 * Running on http://0.0.0.0:5000
 * Universal ADMS Receiver enabled
```

---

## 📱 Device Setup

### For Legacy Devices (K40, F18, etc.)

**On Device Settings:**
1. Go to **Communication** → **ADMS**
2. Enable **ADMS Push**
3. Set **Server URL**: `http://your-server-ip:5000/iclock/cdata.aspx`
4. Set **Push Interval**: `30 seconds`
5. Save and restart device

**In Your System:**
1. Go to **Device Management**
2. Click **"Add New Device"**
3. Fill in:
   - Device Name: `Main Entrance Fingerprint`
   - Connection Type: `ADMS`
   - Serial Number: `[Get from device: Device Info → SN]`
   - School/Institution: Select your institution
4. Save

### For Modern Devices (uFace, SpeedFace, etc.)

**On Device Settings:**
1. Go to **Network** → **Cloud** or **ADMS**
2. Enable **Push**
3. Set **Push URL**: `http://your-server-ip:5000/iclock/cdata.aspx`
4. Set **Push Mode**: `Real-time`
5. Save

**In Your System:**
- Same as legacy devices above

---

## ✅ Quick Test

### Test 1: Check Device Handshake

**Step 1:** Wait for device to connect (or restart device)

**Step 2:** Check logs:
```sql
SELECT serial_number, device_model, firmware_ver, last_handshake 
FROM biometric_devices 
WHERE serial_number = 'YOUR_DEVICE_SN';
```

**Expected:** `last_handshake` should be recent (within last 5 minutes)

### Test 2: Test Attendance Punch

**Step 1:** Have someone punch in/out on the device

**Step 2:** Check attendance:
```sql
SELECT * FROM biometric_verifications 
ORDER BY verification_time DESC 
LIMIT 5;
```

**Expected:** New record with recent timestamp

### Test 3: Check Protocol Detection

```sql
SELECT serial_number, detected_format, parsed_successfully, created_at 
FROM protocol_detection_log 
ORDER BY created_at DESC 
LIMIT 10;
```

**Expected:** 
- `detected_format` = `json`, `text`, or `xml`
- `parsed_successfully` = `1`

---

## 🔍 Troubleshooting

### Issue: Device not showing in logs

**Quick Fix:**
```sql
-- Check unknown devices
SELECT * FROM unknown_device_log 
ORDER BY last_seen DESC 
LIMIT 5;
```

**If device is there:** Register it in Device Management using the serial number shown

### Issue: Attendance not recording

**Quick Fix:**
```sql
-- Check if staff exists
SELECT staff_id, full_name FROM staff WHERE staff_id = 'USER_ID_FROM_DEVICE';
```

**If not found:** Ensure staff `staff_id` matches the User ID configured in the biometric device

### Issue: Parse errors

**Quick Fix:**
```sql
-- Check parse errors
SELECT serial_number, detected_format, error_message, 
       SUBSTR(raw_body, 1, 200) as sample 
FROM protocol_detection_log 
WHERE parsed_successfully = 0 
ORDER BY created_at DESC 
LIMIT 5;
```

**Review** `raw_body` to see what format the device is sending

---

## 📊 Verify Everything is Working

### Health Check SQL Queries

```sql
-- 1. Active devices with metadata
SELECT device_name, serial_number, device_model, protocol_type, last_sync 
FROM biometric_devices 
WHERE is_active = 1;

-- 2. Recent attendance (last 24 hours)
SELECT COUNT(*) as total_punches 
FROM biometric_verifications 
WHERE verification_time > datetime('now', '-1 day');

-- 3. Protocol detection summary
SELECT detected_format, COUNT(*) as count, 
       SUM(parsed_successfully) as successful 
FROM protocol_detection_log 
GROUP BY detected_format;

-- 4. Unknown devices attempting to connect
SELECT COUNT(*) as unknown_devices 
FROM unknown_device_log;
```

---

## 🎯 Success Criteria

✅ **Migration completed** without errors  
✅ **Test suite passed** all tests  
✅ **Device registered** and showing in Device Management  
✅ **Handshake successful** (last_handshake populated)  
✅ **Protocol detected** correctly (Text/JSON/XML)  
✅ **Attendance recording** when staff punch in/out  

---

## 📞 Need Help?

### Check Logs
```bash
# Flask application logs
tail -f app.log

# Or if using console
# Look for messages like:
# "Universal ADMS request from SN: ..."
# "Detected format: ..."
# "Processed X record(s) from device..."
```

### Enable Debug Mode
In [app.py](app.py), add at the top:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Review Documentation
- [UNIVERSAL_ADMS_RECEIVER.md](UNIVERSAL_ADMS_RECEIVER.md) - Full documentation
- [ICLOCK_PROTOCOL_GUIDE.txt](ICLOCK_PROTOCOL_GUIDE.txt) - Protocol reference

---

## 🎓 Next Steps

After successful setup:

1. **Test with multiple devices** - Verify all device types work
2. **Monitor protocol_detection_log** - Ensure all formats parse correctly
3. **Train staff** - Show them how attendance appears in real-time
4. **Set up notifications** - Configure alerts for failed punches
5. **Regular backups** - Schedule database backups

---

**Ready?** Run the migration and start testing! 🚀

```bash
python migrate_universal_adms.py
python test_universal_parser.py
python app.py
```
