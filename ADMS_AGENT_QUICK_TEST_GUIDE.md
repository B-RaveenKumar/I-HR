# Quick Test Guide - ADMS & Agent Sync

## Prerequisites

1. **Server Running:** Flask app must be running on port 5000 (or your configured port)
2. **Database Ready:** All tables exist and are properly configured
3. **Devices Registered:** 
   - ADMS devices registered with serial numbers
   - Agent_LAN devices registered with device IDs
4. **Agent Created:** Agent registered with API key (for Agent endpoints)

---

## Test 1: ADMS Push (No Authentication)

### Setup
```sql
-- Register ADMS device first
INSERT INTO biometric_devices (device_name, serial_number, connection_type, school_id, is_active)
VALUES ('Test ADMS Device', 'ZKTEST001', 'ADMS', 1, 1);

-- Register test staff
INSERT INTO staff (staff_id, full_name, school_id)
VALUES ('TEST001', 'Test User', 1);
```

### Test Request
```bash
curl -X POST http://localhost:5000/api/cloud/adms/push \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "ZKTEST001",
    "device_time": "2025-12-03 10:00:00",
    "records": [
      {
        "user_id": "TEST001",
        "timestamp": "2025-12-03 09:00:00",
        "punch_code": 0,
        "verify_method": 1
      }
    ]
  }'
```

### Expected Response
```json
{
  "success": true,
  "device_id": 1,
  "device_name": "Test ADMS Device",
  "school_id": 1,
  "records_received": 1,
  "processed": 1,
  "rejected": 0,
  "ignored": 0,
  "duplicates": 0,
  "details": [...],
  "message": "Successfully processed 1 attendance record(s), skipped 0 duplicates"
}
```

### Test Duplicate Prevention
```bash
# Send same request again
curl -X POST http://localhost:5000/api/cloud/adms/push \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "ZKTEST001",
    "device_time": "2025-12-03 10:00:00",
    "records": [
      {
        "user_id": "TEST001",
        "timestamp": "2025-12-03 09:00:00",
        "punch_code": 0,
        "verify_method": 1
      }
    ]
  }'
```

### Expected Response (Duplicate)
```json
{
  "success": true,
  "records_received": 1,
  "processed": 0,
  "rejected": 0,
  "ignored": 0,
  "duplicates": 1,
  "message": "Successfully processed 0 attendance record(s), skipped 1 duplicates"
}
```

---

## Test 2: Agent Push Logs (With Authentication)

### Setup
```sql
-- Create agent (if not exists)
INSERT INTO biometric_agents (agent_name, api_key, school_id, is_active)
VALUES ('Test Agent', 'test_api_key_12345', 1, 1);

-- Register Agent_LAN device
INSERT INTO biometric_devices (device_name, connection_type, school_id, is_active)
VALUES ('Test Agent Device', 'Agent_LAN', 1, 1);

-- Get the device_id from above insert
-- SELECT id FROM biometric_devices WHERE device_name = 'Test Agent Device';
```

### Test Request
```bash
curl -X POST http://localhost:5000/api/cloud/agent/push_logs \
  -H "Authorization: Bearer test_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 2,
    "records": [
      {
        "user_id": "TEST001",
        "timestamp": "2025-12-03T10:00:00",
        "punch_code": 0,
        "verify_method": 1
      }
    ]
  }'
```

### Expected Response
```json
{
  "success": true,
  "agent_id": 1,
  "agent_name": "Test Agent",
  "device_id": 2,
  "device_name": "Test Agent Device",
  "school_id": 1,
  "records_received": 1,
  "processed": 1,
  "rejected": 0,
  "ignored": 0,
  "duplicates": 0,
  "message": "Successfully processed 1 attendance record(s), skipped 0 duplicates"
}
```

---

## Test 3: Agent Heartbeat

### Test Request
```bash
curl -X POST http://localhost:5000/api/cloud/agent/heartbeat \
  -H "Authorization: Bearer test_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "Test Agent",
    "status": "active",
    "devices": []
  }'
```

### Expected Response
```json
{
  "success": true,
  "agent_id": 1,
  "agent_name": "Test Agent",
  "message": "Heartbeat received",
  "timestamp": "2025-12-03T10:30:45"
}
```

---

## Test 4: Agent Info

### Test Request
```bash
curl -X GET http://localhost:5000/api/cloud/agent/info \
  -H "Authorization: Bearer test_api_key_12345"
```

### Expected Response
```json
{
  "success": true,
  "agent_id": 1,
  "agent_name": "Test Agent",
  "school_id": 1,
  "status": "active",
  "last_seen": "2025-12-03 10:30:45",
  "created_at": "2025-12-03 08:00:00"
}
```

---

## Test 5: Error Cases

### Test 5.1: ADMS - Unknown Serial Number
```bash
curl -X POST http://localhost:5000/api/cloud/adms/push \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "UNKNOWN_SERIAL",
    "records": []
  }'
```

**Expected:** 404 - Device not registered

### Test 5.2: Agent - Invalid API Key
```bash
curl -X POST http://localhost:5000/api/cloud/agent/push_logs \
  -H "Authorization: Bearer invalid_key" \
  -H "Content-Type: application/json" \
  -d '{"device_id": 1, "records": []}'
```

**Expected:** 401 - Invalid API key

### Test 5.3: Agent - Institution Mismatch
```sql
-- Create device in different institution
INSERT INTO biometric_devices (device_name, connection_type, school_id, is_active)
VALUES ('Other School Device', 'Agent_LAN', 2, 1);
```

```bash
curl -X POST http://localhost:5000/api/cloud/agent/push_logs \
  -H "Authorization: Bearer test_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 3,
    "records": [{"user_id": "TEST001", "timestamp": "2025-12-03T10:00:00", "punch_code": 0}]
  }'
```

**Expected:** 403 - Institution mismatch

### Test 5.4: Staff Not in Institution
```bash
curl -X POST http://localhost:5000/api/cloud/adms/push \
  -H "Content-Type: application/json" \
  -d '{
    "serial_number": "ZKTEST001",
    "records": [
      {
        "user_id": "NONEXISTENT",
        "timestamp": "2025-12-03 10:00:00",
        "punch_code": 0,
        "verify_method": 1
      }
    ]
  }'
```

**Expected:** 200 with rejected count = 1, reason = 'institution_mismatch'

---

## Verify Database Changes

### Check Biometric Verifications
```sql
SELECT bv.id, s.staff_id, s.full_name, bv.verification_type, 
       bv.verification_time, bv.biometric_method, bv.verification_status
FROM biometric_verifications bv
JOIN staff s ON bv.staff_id = s.id
WHERE bv.verification_time >= date('now')
ORDER BY bv.verification_time DESC;
```

### Check Attendance Records
```sql
SELECT a.id, s.staff_id, s.full_name, a.date, a.time_in, a.time_out, 
       a.status, a.late_duration_minutes
FROM attendance a
JOIN staff s ON a.staff_id = s.id
WHERE a.date >= date('now')
ORDER BY a.date DESC, a.time_in DESC;
```

### Check Device Sync Status
```sql
SELECT device_name, connection_type, last_sync, sync_status
FROM biometric_devices
WHERE connection_type IN ('ADMS', 'Agent_LAN')
ORDER BY last_sync DESC;
```

### Check Agent Activity
```sql
SELECT agent_name, status, last_seen, is_active
FROM biometric_agents
ORDER BY last_seen DESC;
```

---

## Check Logs

### Flask Console
Watch for these patterns:

```
INFO:cloud_api:ADMS Push received from device ZKTEST001: 1 record(s)
INFO:zk_biometric:✓ Firewall passed: Staff 'Test User' (ID: TEST001, DB_ID: 1) validated for institution 1
INFO:zk_biometric:✓ Punch processed successfully: Test User (check-in) at 09:00:00 on device Test ADMS Device
INFO:cloud_api:ADMS Push processed for device Test ADMS Device: 1 processed, 0 rejected, 0 ignored, 0 duplicates
```

```
INFO:cloud_api:Agent push received from Test Agent (Agent ID: 1): Device 2, 1 record(s)
INFO:cloud_api:Agent push processed from Test Agent: Device Test Agent Device: 1 processed, 0 rejected, 0 ignored, 0 duplicates
```

### Database Logs
```sql
-- Check for duplicate prevention logs
SELECT * FROM biometric_verifications
WHERE staff_id IN (SELECT id FROM staff WHERE staff_id = 'TEST001')
AND verification_time = '2025-12-03 09:00:00';
-- Should return only ONE record even if pushed multiple times
```

---

## Performance Testing

### Test Batch Processing
```bash
# Create 100 records in one push
curl -X POST http://localhost:5000/api/cloud/adms/push \
  -H "Content-Type: application/json" \
  -d @large_payload.json
```

**large_payload.json:**
```json
{
  "serial_number": "ZKTEST001",
  "device_time": "2025-12-03 10:00:00",
  "records": [
    {"user_id": "TEST001", "timestamp": "2025-12-03 09:00:00", "punch_code": 0, "verify_method": 1},
    {"user_id": "TEST001", "timestamp": "2025-12-03 17:00:00", "punch_code": 1, "verify_method": 1},
    ...
  ]
}
```

**Expected:** All records processed in <2 seconds

---

## Common Issues & Solutions

### Issue: "Device not found"
**Solution:** Check device is registered with correct serial number (ADMS) or device ID (Agent)

### Issue: "Invalid API key"
**Solution:** Verify API key in Authorization header matches biometric_agents.api_key

### Issue: "Institution mismatch"
**Solution:** Ensure device and staff belong to same institution (school_id)

### Issue: All records marked as duplicates
**Solution:** Check biometric_verifications table - records may have been processed already

### Issue: Records rejected with "institution_mismatch"
**Solution:** Verify staff exists in the same institution as the device

---

## Cleanup Test Data

```sql
-- Remove test records
DELETE FROM biometric_verifications WHERE staff_id IN (SELECT id FROM staff WHERE staff_id = 'TEST001');
DELETE FROM attendance WHERE staff_id IN (SELECT id FROM staff WHERE staff_id = 'TEST001');
DELETE FROM staff WHERE staff_id = 'TEST001';
DELETE FROM biometric_devices WHERE serial_number = 'ZKTEST001' OR device_name LIKE 'Test%';
DELETE FROM biometric_agents WHERE agent_name = 'Test Agent';
```

---

## Production Checklist

- [ ] Test ADMS push with real device serial number
- [ ] Test Agent push with real agent API key
- [ ] Verify duplicate prevention works
- [ ] Check institution firewall blocks cross-institution access
- [ ] Monitor Flask logs for errors
- [ ] Verify attendance records are created correctly
- [ ] Check device sync status updates
- [ ] Test with multiple simultaneous devices
- [ ] Verify performance with large batches (100+ records)
- [ ] Set up monitoring/alerting for failed pushes

---

**Testing Complete!** ✅

All endpoints now use the same unified processing logic with duplicate prevention, institution firewall, and detailed reporting.
