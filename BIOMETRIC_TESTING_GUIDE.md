# Unified Biometric System - Quick Test Guide

This guide provides step-by-step instructions for testing the newly implemented Unified Biometric Ecosystem.

---

## Prerequisites

✅ Database migration completed successfully  
✅ Flask server running (`python app.py`)  
✅ At least one institution (school) in database

---

## Test 1: Verify Database Tables

**Objective:** Confirm new tables were created correctly

**Steps:**

1. Open SQLite database:
   ```bash
   sqlite3 vishnorex.db
   ```

2. Check tables exist:
   ```sql
   .tables
   ```
   **Expected:** You should see `biometric_agents` and `biometric_devices` in the list

3. Check device table structure:
   ```sql
   PRAGMA table_info(biometric_devices);
   ```
   **Expected:** 12 columns including `school_id`, `connection_type`, `agent_id`, etc.

4. Check agent table structure:
   ```sql
   PRAGMA table_info(biometric_agents);
   ```
   **Expected:** 7 columns including `school_id`, `api_key`, `last_heartbeat`, etc.

5. Verify legacy device was migrated:
   ```sql
   SELECT id, device_name, school_id, connection_type, ip_address 
   FROM biometric_devices;
   ```
   **Expected:** One row with device_name="Legacy Main Device", ip_address="192.168.1.201"

---

## Test 2: Register a Local Agent

**Objective:** Test agent registration and API key generation

**Method 1: Using curl**

```bash
curl -X POST http://localhost:5000/api/agent/register ^
  -H "Content-Type: application/json" ^
  -d "{\"school_id\": 4, \"agent_name\": \"Test Agent\"}"
```

**Method 2: Using Python**

```python
import requests

response = requests.post('http://localhost:5000/api/agent/register', json={
    'school_id': 4,
    'agent_name': 'Test Agent'
})

print(response.json())
```

**Expected Response:**
```json
{
  "success": true,
  "agent_id": 1,
  "api_key": "abcdef1234567890abcdef1234567890abcdef1234567890",
  "message": "Agent 'Test Agent' created successfully"
}
```

**Save the `api_key` for next tests!**

---

## Test 3: Agent Heartbeat

**Objective:** Test agent authentication and keep-alive

**Replace `YOUR_API_KEY` with the key from Test 2:**

```bash
curl -X POST http://localhost:5000/api/agent/heartbeat ^
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Expected Response:**
```json
{
  "success": true,
  "agent_id": 1,
  "school_id": 4,
  "timestamp": "2025-12-02T10:30:45.123456",
  "commands": []
}
```

**Verify in Database:**
```sql
SELECT agent_name, last_heartbeat FROM biometric_agents WHERE id = 1;
```
The `last_heartbeat` should be updated to current time.

---

## Test 4: Add Device via Direct LAN

**Objective:** Test device creation

**Using Python:**

```python
from database import get_db, create_biometric_device

# Simulate adding a device
result = create_biometric_device(
    school_id=4,
    device_name="Front Gate",
    connection_type="Direct_LAN",
    ip_address="192.168.1.100",
    port=4370
)

print(result)
```

**Expected Output:**
```python
{
  'success': True,
  'message': "Device 'Front Gate' created successfully",
  'device_id': 2
}
```

**Verify in Database:**
```sql
SELECT id, device_name, school_id, connection_type, ip_address 
FROM biometric_devices 
WHERE id = 2;
```

---

## Test 5: Add ADMS Device

**Objective:** Test ADMS device registration

**Using Python:**

```python
from database import create_biometric_device

result = create_biometric_device(
    school_id=4,
    device_name="Admin Block ADMS",
    connection_type="ADMS",
    serial_number="ZKDEV123456",
    port=4370
)

print(result)
```

**Expected Output:**
```python
{
  'success': True,
  'message': "Device 'Admin Block ADMS' created successfully",
  'device_id': 3
}
```

---

## Test 6: Add Agent-Connected Device

**Objective:** Test agent-linked device creation

**Using Python:**

```python
from database import create_biometric_device

result = create_biometric_device(
    school_id=4,
    device_name="Back Gate (Agent)",
    connection_type="Agent_LAN",
    ip_address="192.168.10.50",
    port=4370,
    agent_id=1  # From Test 2
)

print(result)
```

---

## Test 7: Test Institution Firewall (Rejection Scenario)

**Objective:** Verify cross-institution punch is BLOCKED

**Setup:**
1. Create a test staff in Institution 4 with staff_id="TEST001"
2. Create a device assigned to Institution 5

**Test Code:**

```python
from zk_biometric import UnifiedAttendanceProcessor
from datetime import datetime

processor = UnifiedAttendanceProcessor()

# Attempt to punch staff from Institution 4 on a device in Institution 5
result = processor.process_attendance_punch(
    device_id=999,  # Hypothetical device in Institution 5
    user_id="TEST001",  # Staff exists in Institution 4 only
    timestamp=datetime.now(),
    punch_code=0
)

print(result)
```

**Expected Result:**
```python
{
  'success': False,
  'message': 'Staff ID TEST001 not found in institution (school_id: 5)',
  'reason': 'institution_mismatch',
  'action': 'rejected',
  'staff_id': None
}
```

**Verify Rejection Logged:**
```sql
SELECT * FROM biometric_verifications 
WHERE verification_status = 'failed' 
ORDER BY verification_time DESC 
LIMIT 1;
```

---

## Test 8: Test Institution Firewall (Success Scenario)

**Objective:** Verify correct institution punch is ALLOWED

**Test Code:**

```python
from zk_biometric import UnifiedAttendanceProcessor
from datetime import datetime

processor = UnifiedAttendanceProcessor()

# Punch staff from Institution 4 on a device in Institution 4
result = processor.process_attendance_punch(
    device_id=1,  # Legacy device in Institution 4
    user_id="TEST001",  # Staff exists in Institution 4
    timestamp=datetime.now(),
    punch_code=0
)

print(result)
```

**Expected Result:**
```python
{
  'success': True,
  'message': 'Check-in processed: Test Staff at 10:30:45 (Status: present)',
  'action': 'check-in',
  'staff_id': 123,
  'reason': ''
}
```

**Verify in Attendance Table:**
```sql
SELECT * FROM attendance 
WHERE staff_id = (SELECT id FROM staff WHERE staff_id = 'TEST001') 
AND date = DATE('now');
```

---

## Test 9: ADMS Push Endpoint

**Objective:** Test ADMS webhook receiver

**Setup:**
Ensure device with serial "ZKDEV123456" exists (from Test 5)

**Test Request:**

```bash
curl -X POST http://localhost:5000/api/cloud/adms/push ^
  -H "Content-Type: application/json" ^
  -d "{\"serial_number\": \"ZKDEV123456\", \"records\": [{\"user_id\": \"TEST001\", \"timestamp\": \"2025-12-02 10:30:45\", \"punch_code\": 0, \"verify_method\": 1}]}"
```

**Expected Response:**
```json
{
  "success": true,
  "device_id": 3,
  "device_name": "Admin Block ADMS",
  "school_id": 4,
  "records_received": 1,
  "processed": 1,
  "rejected": 0,
  "ignored": 0,
  "message": "Successfully processed 1 attendance record(s)"
}
```

---

## Test 10: Agent Push Logs Endpoint

**Objective:** Test agent attendance upload

**Prerequisites:**
- Agent API key from Test 2
- Device assigned to agent from Test 6

**Test Request:**

```bash
curl -X POST http://localhost:5000/api/agent/push_logs ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_API_KEY" ^
  -d "{\"device_id\": 4, \"records\": [{\"user_id\": \"TEST001\", \"timestamp\": \"2025-12-02T10:30:45\", \"punch_code\": 0, \"verify_method\": 1}]}"
```

**Expected Response:**
```json
{
  "success": true,
  "device_id": 4,
  "device_name": "Back Gate (Agent)",
  "agent_id": 1,
  "records_received": 1,
  "processed": 1,
  "rejected": 0,
  "ignored": 0,
  "message": "Successfully processed 1 attendance record(s)"
}
```

---

## Test 11: Batch Processing

**Objective:** Test multiple punches in one request

**Test Code:**

```python
from zk_biometric import UnifiedAttendanceProcessor
from datetime import datetime

processor = UnifiedAttendanceProcessor()

punches = [
    {'user_id': 'TEST001', 'timestamp': datetime.now(), 'punch_code': 0, 'verification_method': 'fingerprint'},
    {'user_id': 'TEST002', 'timestamp': datetime.now(), 'punch_code': 0, 'verification_method': 'fingerprint'},
    {'user_id': 'NONEXISTENT', 'timestamp': datetime.now(), 'punch_code': 0, 'verification_method': 'fingerprint'},
]

result = processor.process_batch_punches(device_id=1, punches=punches)

print(f"Processed: {result['processed']}")
print(f"Rejected: {result['rejected']}")
print(f"Ignored: {result['ignored']}")
print(f"\nDetails: {result['details']}")
```

**Expected:** 2 processed, 1 rejected

---

## Test 12: Device Sync Status Update

**Objective:** Test sync timestamp tracking

**Test Code:**

```python
from database import update_device_sync_status
from datetime import datetime

success = update_device_sync_status(
    device_id=1, 
    last_sync=datetime.now(), 
    sync_status='success'
)

print(f"Update successful: {success}")
```

**Verify in Database:**
```sql
SELECT device_name, last_sync, sync_status 
FROM biometric_devices 
WHERE id = 1;
```

---

## Test 13: Get Devices for Institution

**Objective:** Test device retrieval helper

**Test Code:**

```python
from database import get_device_for_institution

# Get all devices for institution 4
devices = get_device_for_institution(school_id=4)

print(f"Found {len(devices)} device(s):")
for device in devices:
    print(f"  - {device['device_name']} ({device['connection_type']})")
```

---

## Test 14: Get Primary Device (Backward Compatibility)

**Objective:** Test backward compatibility helper

**Test Code:**

```python
from database import get_primary_device_for_institution

device = get_primary_device_for_institution(school_id=4)

if device:
    print(f"Primary device: {device['device_name']}")
    print(f"IP: {device['ip_address']}")
    print(f"Connection: {device['connection_type']}")
else:
    print("No active device found")
```

---

## Test 15: Agent API Key Verification

**Objective:** Test agent authentication

**Test Code:**

```python
from database import verify_agent_api_key

agent_info = verify_agent_api_key("YOUR_API_KEY_HERE")

if agent_info:
    print(f"Agent authenticated: {agent_info['agent_name']}")
    print(f"School: {agent_info['school_name']}")
    print(f"Active: {agent_info['is_active']}")
else:
    print("Invalid API key")
```

---

## Troubleshooting

### Issue: "Staff ID not found in institution"

**Cause:** Staff doesn't exist or belongs to different institution

**Solution:**
```sql
-- Check staff institution
SELECT staff_id, full_name, school_id FROM staff WHERE staff_id = 'TEST001';

-- Check device institution
SELECT device_name, school_id FROM biometric_devices WHERE id = 1;
```

### Issue: "Device not found"

**Cause:** Device ID doesn't exist or is inactive

**Solution:**
```sql
-- List all active devices
SELECT id, device_name, school_id, is_active FROM biometric_devices;
```

### Issue: "Invalid API key"

**Cause:** API key incorrect or agent deactivated

**Solution:**
```sql
-- Check agent status
SELECT agent_name, api_key, is_active FROM biometric_agents WHERE id = 1;
```

---

## Success Criteria

✅ All database tables created  
✅ Legacy device migrated  
✅ Agent registration successful  
✅ Agent heartbeat updates timestamp  
✅ Institution firewall blocks cross-institution punches  
✅ Institution firewall allows same-institution punches  
✅ ADMS endpoint receives and processes punches  
✅ Agent endpoint receives and processes punches  
✅ Batch processing works correctly  
✅ Device sync status updates  
✅ Helper functions return correct data

---

## Next: UI Testing (Phase 2)

Once Device Management UI is implemented, test:
- Device list display
- Add device form (all 3 connection types)
- Edit device
- Delete device
- Agent registration wizard
- Agent list display
- ADMS server configuration display

---

**Last Updated:** December 2, 2025  
**Test Coverage:** Backend API (Phase 1)  
**Estimated Test Time:** 30-45 minutes
