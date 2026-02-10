#!/usr/bin/env python3
"""
Cloud API Endpoints
REST API endpoints for cloud-based ZK biometric device communication
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Blueprint, request, jsonify, current_app
from functools import wraps

from cloud_config import get_cloud_config, get_device_config, get_all_devices
from cloud_connector import get_cloud_connector
from database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for cloud API
cloud_api = Blueprint('cloud_api', __name__, url_prefix='/api/cloud')

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Remove 'Bearer ' prefix if present
        if api_key.startswith('Bearer '):
            api_key = api_key[7:]
        
        # Validate API key
        config = get_cloud_config()
        if api_key != config.api_key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_organization(f):
    """Decorator to require organization ID"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        org_id = request.headers.get('X-Organization-ID')
        if not org_id:
            return jsonify({'error': 'Organization ID required'}), 400
        
        # Validate organization ID
        config = get_cloud_config()
        if org_id != config.organization_id:
            return jsonify({'error': 'Invalid organization ID'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@cloud_api.route('/status', methods=['GET'])
@require_api_key
def get_cloud_status():
    """Get cloud connector status"""
    try:
        connector = get_cloud_connector()
        config = get_cloud_config()
        devices = get_all_devices()
        
        # Get device statuses
        device_statuses = []
        for device in devices:
            if device.cloud_enabled:
                status = connector.get_device_status(device.device_id)
                device_statuses.append({
                    'device_id': device.device_id,
                    'device_name': device.device_name,
                    'local_ip': device.local_ip,
                    'status': status['status'],
                    'last_sync': device.last_sync,
                    'user_count': status.get('user_count', 0)
                })
        
        return jsonify({
            'success': True,
            'cloud_connector_running': connector.running,
            'websocket_connected': connector.websocket is not None and 
                                 connector.websocket.sock and 
                                 connector.websocket.sock.connected,
            'last_heartbeat': connector.last_heartbeat.isoformat() if connector.last_heartbeat else None,
            'message_queue_size': len(connector.message_queue),
            'device_count': len(device_statuses),
            'devices': device_statuses,
            'config': {
                'api_base_url': config.api_base_url,
                'websocket_url': config.websocket_url,
                'auto_sync': config.auto_sync,
                'sync_interval': config.sync_interval
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting cloud status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices', methods=['GET'])
@require_api_key
@require_organization
def get_devices():
    """Get all configured devices"""
    try:
        devices = get_all_devices()
        connector = get_cloud_connector()
        
        device_list = []
        for device in devices:
            status = connector.get_device_status(device.device_id)
            device_list.append({
                'device_id': device.device_id,
                'device_name': device.device_name,
                'device_type': device.device_type,
                'local_ip': device.local_ip,
                'local_port': device.local_port,
                'cloud_enabled': device.cloud_enabled,
                'sync_interval': device.sync_interval,
                'last_sync': device.last_sync,
                'status': status
            })
        
        return jsonify({
            'success': True,
            'devices': device_list,
            'total_count': len(device_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices/<device_id>/sync', methods=['POST'])
@require_api_key
@require_organization
def sync_device(device_id):
    """Trigger sync for a specific device"""
    try:
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        if not device_config.cloud_enabled:
            return jsonify({'success': False, 'error': 'Device cloud sync disabled'}), 400
        
        connector = get_cloud_connector()
        connector._sync_device(device_config)
        
        return jsonify({
            'success': True,
            'message': f'Sync triggered for device {device_id}',
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error syncing device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices/<device_id>/users', methods=['GET'])
@require_api_key
@require_organization
def get_device_users(device_id):
    """Get users from a specific device"""
    try:
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        connector = get_cloud_connector()
        zk_device = connector._get_device_connection(device_config)
        
        if not zk_device:
            return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
        
        users = zk_device.get_users()
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'users': users,
            'user_count': len(users),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting users from device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices/<device_id>/attendance', methods=['GET'])
@require_api_key
@require_organization
def get_device_attendance(device_id):
    """Get attendance records from a specific device"""
    try:
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        # Get query parameters
        since = request.args.get('since')
        limit = int(request.args.get('limit', 100))
        
        since_time = None
        if since:
            try:
                since_time = datetime.fromisoformat(since)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid since parameter format'}), 400
        
        connector = get_cloud_connector()
        zk_device = connector._get_device_connection(device_config)
        
        if not zk_device:
            return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
        
        # Get attendance records
        if since_time:
            records = zk_device.get_new_attendance_records(since_time)
        else:
            records = zk_device.get_attendance_records()
        
        # Limit results
        if limit and len(records) > limit:
            records = records[:limit]
        
        # Convert datetime objects to ISO format
        formatted_records = []
        for record in records:
            formatted_record = record.copy()
            if 'timestamp' in formatted_record:
                formatted_record['timestamp'] = formatted_record['timestamp'].isoformat()
            formatted_records.append(formatted_record)
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'records': formatted_records,
            'record_count': len(formatted_records),
            'since': since,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting attendance from device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/devices/<device_id>/command', methods=['POST'])
@require_api_key
@require_organization
def send_device_command(device_id):
    """Send command to a specific device"""
    try:
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'success': False, 'error': 'Command required'}), 400
        
        command = data['command']
        connector = get_cloud_connector()
        
        # Handle different commands
        if command == 'clear_attendance':
            zk_device = connector._get_device_connection(device_config)
            if not zk_device:
                return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
            
            success = zk_device.clear_attendance()
            return jsonify({
                'success': success,
                'device_id': device_id,
                'command': command,
                'message': 'Attendance cleared' if success else 'Failed to clear attendance',
                'timestamp': datetime.now().isoformat()
            })
        
        elif command == 'enroll_user':
            user_id = data.get('user_id')
            name = data.get('name')
            
            if not user_id or not name:
                return jsonify({'success': False, 'error': 'user_id and name required'}), 400
            
            zk_device = connector._get_device_connection(device_config)
            if not zk_device:
                return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
            
            result = zk_device.enroll_user(user_id, name)
            return jsonify({
                'success': result['success'],
                'device_id': device_id,
                'command': command,
                'message': result['message'],
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
        
        elif command == 'delete_user':
            user_id = data.get('user_id')
            
            if not user_id:
                return jsonify({'success': False, 'error': 'user_id required'}), 400
            
            zk_device = connector._get_device_connection(device_config)
            if not zk_device:
                return jsonify({'success': False, 'error': 'Cannot connect to device'}), 503
            
            success = zk_device.delete_user(user_id)
            return jsonify({
                'success': success,
                'device_id': device_id,
                'command': command,
                'message': f'User {user_id} deleted' if success else f'Failed to delete user {user_id}',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
        
        else:
            return jsonify({'success': False, 'error': f'Unknown command: {command}'}), 400
        
    except Exception as e:
        logger.error(f"Error sending command to device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/attendance/upload', methods=['POST'])
@require_api_key
@require_organization
def upload_attendance():
    """Upload attendance records to cloud database"""
    try:
        data = request.get_json()
        if not data or 'records' not in data:
            return jsonify({'success': False, 'error': 'Records required'}), 400
        
        records = data['records']
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'success': False, 'error': 'device_id required'}), 400
        
        # Validate device exists
        device_config = get_device_config(device_id)
        if not device_config:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        # Process records
        processed_count = 0
        errors = []
        
        db = get_db()
        
        for record in records:
            try:
                # Validate required fields
                required_fields = ['user_id', 'timestamp', 'verification_type']
                for field in required_fields:
                    if field not in record:
                        errors.append(f"Missing field {field} in record")
                        continue
                
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(record['timestamp'])
                except ValueError:
                    errors.append(f"Invalid timestamp format: {record['timestamp']}")
                    continue
                
                # Check if record already exists
                existing = db.execute('''
                    SELECT id FROM cloud_attendance_log
                    WHERE device_id = ? AND user_id = ? AND timestamp = ?
                ''', (device_id, record['user_id'], timestamp)).fetchone()
                
                if existing:
                    continue  # Skip duplicate
                
                # Insert record
                db.execute('''
                    INSERT INTO cloud_attendance_log
                    (device_id, user_id, timestamp, verification_type, punch_code, status, verify_method, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device_id,
                    record['user_id'],
                    timestamp,
                    record['verification_type'],
                    record.get('punch_code', 0),
                    record.get('status', 0),
                    record.get('verify_method', 0),
                    datetime.now()
                ))
                
                processed_count += 1
                
            except Exception as e:
                errors.append(f"Error processing record: {str(e)}")
        
        db.commit()
        
        return jsonify({
            'success': True,
            'processed_count': processed_count,
            'total_records': len(records),
            'errors': errors,
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error uploading attendance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/config', methods=['GET'])
@require_api_key
def get_cloud_config_api():
    """Get cloud configuration"""
    try:
        config = get_cloud_config()
        
        # Return safe configuration (no sensitive data)
        safe_config = {
            'cloud_provider': config.cloud_provider,
            'api_base_url': config.api_base_url,
            'websocket_url': config.websocket_url,
            'mqtt_broker': config.mqtt_broker,
            'mqtt_port': config.mqtt_port,
            'organization_id': config.organization_id,
            'connection_timeout': config.connection_timeout,
            'retry_attempts': config.retry_attempts,
            'heartbeat_interval': config.heartbeat_interval,
            'use_ssl': config.use_ssl,
            'verify_ssl': config.verify_ssl,
            'encryption_enabled': config.encryption_enabled,
            'auto_sync': config.auto_sync,
            'sync_interval': config.sync_interval,
            'batch_size': config.batch_size,
            'local_backup': config.local_backup,
            'backup_retention_days': config.backup_retention_days
        }
        
        return jsonify({
            'success': True,
            'config': safe_config
        })
        
    except Exception as e:
        logger.error(f"Error getting cloud config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloud_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ZK Biometric Cloud API'
    })


# =============================================================================
# ADMS CLOUD PUSH ENDPOINTS
# =============================================================================

@cloud_api.route('/adms/push', methods=['POST'])
def adms_push_attendance():
    """
    Receive attendance logs pushed from ADMS-configured ZK devices
    
    Expected JSON payload:
    {
        "serial_number": "ZKDEV123456",
        "device_time": "2025-12-02 10:30:45",
        "records": [
            {
                "user_id": "101",
                "timestamp": "2025-12-02 09:15:23",
                "punch_code": 0,
                "verify_method": 1
            }
        ]
    }
    
    Returns:
        JSON response with processing results
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        serial_number = data.get('serial_number')
        records = data.get('records', [])
        
        if not serial_number:
            return jsonify({
                'success': False,
                'error': 'Serial number required'
            }), 400
        
        if not records:
            return jsonify({
                'success': False,
                'error': 'No records provided'
            }), 400
        
        logger.info(f"ADMS Push received from device {serial_number}: {len(records)} record(s)")
        
        # Step 1: Find device by serial number
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, school_id, device_name, is_active
            FROM biometric_devices
            WHERE serial_number = ? AND connection_type = 'ADMS'
        ''', (serial_number,))
        
        device = cursor.fetchone()
        
        if not device:
            logger.warning(f"ADMS Push rejected: Unknown device with serial {serial_number}")
            return jsonify({
                'success': False,
                'error': f'Device with serial number {serial_number} not registered',
                'hint': 'Please register this device in the Device Management interface'
            }), 404
        
        device_id = device[0]
        school_id = device[1]
        device_name = device[2]
        is_active = device[3]
        
        if not is_active:
            return jsonify({
                'success': False,
                'error': f'Device {device_name} is inactive'
            }), 403
        
        # Step 2: Process records using UnifiedAttendanceProcessor (same as agent)
        from zk_biometric import UnifiedAttendanceProcessor
        
        processor = UnifiedAttendanceProcessor()
        processed_count = 0
        rejected_count = 0
        ignored_count = 0
        duplicate_count = 0
        details = []
        
        for record in records:
            try:
                # Parse timestamp
                timestamp_str = record.get('timestamp')
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                user_id = record.get('user_id')
                punch_code = record.get('punch_code', 0)
                verify_method = record.get('verify_method', 1)
                
                # Map verify method: 1=fingerprint, 2=face, 3=password, 4=card
                verify_method_map = {
                    1: 'fingerprint',
                    2: 'face',
                    3: 'password',
                    4: 'card'
                }
                verification_method = verify_method_map.get(verify_method, 'fingerprint')
                
                # DUPLICATE CHECK: Check if this exact log already exists (same as agent)
                cursor.execute('''
                    SELECT id FROM biometric_verifications
                    WHERE staff_id IN (SELECT id FROM staff WHERE staff_id = ? AND school_id = ?)
                    AND verification_time = ?
                    AND verification_type = ?
                ''', (
                    user_id,
                    school_id,
                    timestamp,
                    processor._map_punch_to_verification_type(punch_code)
                ))
                
                existing_log = cursor.fetchone()
                
                if existing_log:
                    # Skip duplicate - already processed
                    duplicate_count += 1
                    logger.debug(f"Skipping duplicate log: Staff {user_id}, Time {timestamp}")
                    details.append({
                        'user_id': user_id,
                        'timestamp': timestamp_str,
                        'action': 'skipped',
                        'reason': 'duplicate_log',
                        'message': 'Log already exists'
                    })
                    continue
                
                # Process the attendance punch
                punch_result = processor.process_attendance_punch(
                    device_id=device_id,
                    user_id=user_id,
                    timestamp=timestamp,
                    punch_code=punch_code,
                    verification_method=verification_method
                )
                
                if punch_result['success']:
                    if punch_result['action'] == 'ignored':
                        ignored_count += 1
                    else:
                        processed_count += 1
                else:
                    rejected_count += 1
                
                details.append({
                    'user_id': user_id,
                    'timestamp': timestamp_str,
                    'action': punch_result.get('action'),
                    'message': punch_result.get('message'),
                    'reason': punch_result.get('reason')
                })
                
            except Exception as e:
                logger.error(f"Error parsing ADMS record: {e}")
                rejected_count += 1
                details.append({
                    'user_id': record.get('user_id', 'unknown'),
                    'timestamp': record.get('timestamp', 'unknown'),
                    'action': 'rejected',
                    'reason': 'parse_error',
                    'message': str(e)
                })
                continue
        
        # Update device sync status
        from database import update_device_sync_status
        update_device_sync_status(device_id, datetime.now(), 'success')
        
        logger.info(
            f"ADMS Push processed for device {device_name}: "
            f"{processed_count} processed, {rejected_count} rejected, "
            f"{ignored_count} ignored, {duplicate_count} duplicates"
        )
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'device_name': device_name,
            'school_id': school_id,
            'records_received': len(records),
            'processed': processed_count,
            'rejected': rejected_count,
            'ignored': ignored_count,
            'duplicates': duplicate_count,
            'details': details,
            'message': f'Successfully processed {processed_count} attendance record(s), skipped {duplicate_count} duplicates'
        })
        
    except Exception as e:
        logger.error(f"Error processing ADMS push: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cloud_api.route('/adms/devices', methods=['GET'])
@require_api_key
def list_adms_devices():
    """List all ADMS-configured devices"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT d.id, d.device_name, d.serial_number, d.is_active, 
                   d.last_sync, d.sync_status, s.name as school_name
            FROM biometric_devices d
            LEFT JOIN schools s ON d.school_id = s.id
            WHERE d.connection_type = 'ADMS'
            ORDER BY s.name, d.device_name
        ''')
        
        devices = []
        for row in cursor.fetchall():
            devices.append({
                'id': row[0],
                'device_name': row[1],
                'serial_number': row[2],
                'is_active': bool(row[3]),
                'last_sync': row[4],
                'sync_status': row[5],
                'school_name': row[6]
            })
        
        return jsonify({
            'success': True,
            'device_count': len(devices),
            'devices': devices
        })
        
    except Exception as e:
        logger.error(f"Error listing ADMS devices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# AGENT LAN ENDPOINTS (Local Agent Bridge)
# =============================================================================

@cloud_api.route('/agent/push_logs', methods=['POST'])
def agent_push_logs():
    """
    Receive attendance logs pushed from Local Agent (Agent_LAN mode)
    
    Expected JSON payload:
    {
        "device_id": 123,
        "records": [
            {
                "user_id": "101",
                "timestamp": "2025-12-02T09:15:23",
                "punch_code": 0,
                "verify_method": 1
            }
        ]
    }
    
    Requires: Bearer token (API key) in Authorization header
    
    Returns:
        JSON response with processing results
    """
    try:
        # Check API key authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Missing or invalid Authorization header'
            }), 401
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Validate agent API key
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, agent_name, school_id, is_active
            FROM biometric_agents
            WHERE api_key = ?
        ''', (api_key,))
        
        agent = cursor.fetchone()
        
        if not agent:
            logger.warning(f"Agent push rejected: Invalid API key")
            return jsonify({
                'success': False,
                'error': 'Invalid API key'
            }), 401
        
        agent_id = agent[0]
        agent_name = agent[1]
        agent_school_id = agent[2]
        is_active = agent[3]
        
        if not is_active:
            return jsonify({
                'success': False,
                'error': f'Agent {agent_name} is inactive'
            }), 403
        
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        device_id = data.get('device_id')
        records = data.get('records', [])
        
        if not device_id:
            return jsonify({
                'success': False,
                'error': 'Device ID required'
            }), 400
        
        if not records:
            return jsonify({
                'success': False,
                'error': 'No records provided'
            }), 400
        
        logger.info(f"Agent push received from {agent_name} (Agent ID: {agent_id}): Device {device_id}, {len(records)} record(s)")
        
        # Validate device belongs to this agent's institution
        cursor.execute('''
            SELECT id, school_id, device_name, is_active
            FROM biometric_devices
            WHERE id = ? AND connection_type = 'Agent_LAN'
        ''', (device_id,))
        
        device = cursor.fetchone()
        
        if not device:
            logger.warning(f"Agent push rejected: Device {device_id} not found or not Agent_LAN type")
            return jsonify({
                'success': False,
                'error': f'Device ID {device_id} not found or not configured for Agent_LAN'
            }), 404
        
        device_db_id = device[0]
        device_school_id = device[1]
        device_name = device[2]
        device_is_active = device[3]
        
        if not device_is_active:
            return jsonify({
                'success': False,
                'error': f'Device {device_name} is inactive'
            }), 403
        
        # INSTITUTION FIREWALL: Verify device belongs to agent's institution
        if device_school_id != agent_school_id:
            logger.error(
                f"🚫 INSTITUTION MISMATCH: Agent {agent_name} (Institution: {agent_school_id}) "
                f"attempted to push logs for device {device_name} (Institution: {device_school_id})"
            )
            return jsonify({
                'success': False,
                'error': 'Institution mismatch: Device does not belong to agent\'s institution'
            }), 403
        
        # Process records using UnifiedAttendanceProcessor (same as ADMS)
        from zk_biometric import UnifiedAttendanceProcessor
        
        processor = UnifiedAttendanceProcessor()
        processed_count = 0
        rejected_count = 0
        ignored_count = 0
        duplicate_count = 0
        details = []
        
        for record in records:
            try:
                # Parse timestamp (ISO format from agent)
                timestamp_str = record.get('timestamp')
                
                # Handle both ISO format and datetime string
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                user_id = record.get('user_id')
                punch_code = record.get('punch_code', 0)
                verify_method = record.get('verify_method', 1)
                
                # Map verify method: 1=fingerprint, 2=face, 3=password, 4=card
                verify_method_map = {
                    1: 'fingerprint',
                    2: 'face',
                    3: 'password',
                    4: 'card'
                }
                verification_method = verify_method_map.get(verify_method, 'fingerprint')
                
                # DUPLICATE CHECK: Check if this exact log already exists (same as ADMS)
                cursor.execute('''
                    SELECT id FROM biometric_verifications
                    WHERE staff_id IN (SELECT id FROM staff WHERE staff_id = ? AND school_id = ?)
                    AND verification_time = ?
                    AND verification_type = ?
                ''', (
                    user_id,
                    device_school_id,
                    timestamp,
                    processor._map_punch_to_verification_type(punch_code)
                ))
                
                existing_log = cursor.fetchone()
                
                if existing_log:
                    # Skip duplicate - already processed
                    duplicate_count += 1
                    logger.debug(f"Skipping duplicate log: Staff {user_id}, Time {timestamp}")
                    details.append({
                        'user_id': user_id,
                        'timestamp': timestamp_str,
                        'action': 'skipped',
                        'reason': 'duplicate_log',
                        'message': 'Log already exists'
                    })
                    continue
                
                # Process the attendance punch
                punch_result = processor.process_attendance_punch(
                    device_id=device_db_id,
                    user_id=user_id,
                    timestamp=timestamp,
                    punch_code=punch_code,
                    verification_method=verification_method
                )
                
                if punch_result['success']:
                    if punch_result['action'] == 'ignored':
                        ignored_count += 1
                    else:
                        processed_count += 1
                else:
                    rejected_count += 1
                
                details.append({
                    'user_id': user_id,
                    'timestamp': timestamp_str,
                    'action': punch_result.get('action'),
                    'message': punch_result.get('message'),
                    'reason': punch_result.get('reason')
                })
                
            except Exception as e:
                logger.error(f"Error parsing agent record: {e}")
                rejected_count += 1
                details.append({
                    'user_id': record.get('user_id', 'unknown'),
                    'timestamp': record.get('timestamp', 'unknown'),
                    'action': 'rejected',
                    'reason': 'parse_error',
                    'message': str(e)
                })
                continue
        
        # Update device sync status
        from database import update_device_sync_status
        update_device_sync_status(device_db_id, datetime.now(), 'success')
        
        # Update agent last seen
        cursor.execute('''
            UPDATE biometric_agents
            SET last_seen = ?, status = 'active'
            WHERE id = ?
        ''', (datetime.now(), agent_id))
        db.commit()
        
        logger.info(
            f"Agent push processed from {agent_name}: Device {device_name}: "
            f"{processed_count} processed, {rejected_count} rejected, "
            f"{ignored_count} ignored, {duplicate_count} duplicates"
        )
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'device_id': device_db_id,
            'device_name': device_name,
            'school_id': device_school_id,
            'records_received': len(records),
            'processed': processed_count,
            'rejected': rejected_count,
            'ignored': ignored_count,
            'duplicates': duplicate_count,
            'message': f'Successfully processed {processed_count} attendance record(s), skipped {duplicate_count} duplicates'
        })
        
    except Exception as e:
        logger.error(f"Error processing agent push: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cloud_api.route('/agent/heartbeat', methods=['POST'])
def agent_heartbeat():
    """
    Agent heartbeat endpoint - updates agent status
    
    Expected JSON payload:
    {
        "agent_name": "Agent-1",
        "status": "active",
        "devices": [...]
    }
    
    Requires: Bearer token (API key) in Authorization header
    """
    try:
        # Check API key authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Missing or invalid Authorization header'
            }), 401
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Validate agent API key
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, agent_name, is_active
            FROM biometric_agents
            WHERE api_key = ?
        ''', (api_key,))
        
        agent = cursor.fetchone()
        
        if not agent:
            return jsonify({
                'success': False,
                'error': 'Invalid API key'
            }), 401
        
        agent_id = agent[0]
        agent_name = agent[1]
        is_active = agent[2]
        
        if not is_active:
            return jsonify({
                'success': False,
                'error': f'Agent {agent_name} is inactive'
            }), 403
        
        # Parse request data
        data = request.get_json()
        status = data.get('status', 'active')
        
        # Update agent heartbeat
        cursor.execute('''
            UPDATE biometric_agents
            SET last_seen = ?, status = ?
            WHERE id = ?
        ''', (datetime.now(), status, agent_id))
        db.commit()
        
        logger.debug(f"Heartbeat received from agent {agent_name}")
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'message': 'Heartbeat received',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing agent heartbeat: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cloud_api.route('/agent/info', methods=['GET'])
def agent_info():
    """
    Get agent information
    
    Requires: Bearer token (API key) in Authorization header
    """
    try:
        # Check API key authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Missing or invalid Authorization header'
            }), 401
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Validate agent API key
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, agent_name, school_id, status, last_seen, created_at
            FROM biometric_agents
            WHERE api_key = ? AND is_active = 1
        ''', (api_key,))
        
        agent = cursor.fetchone()
        
        if not agent:
            return jsonify({
                'success': False,
                'error': 'Invalid API key'
            }), 401
        
        return jsonify({
            'success': True,
            'agent_id': agent[0],
            'agent_name': agent[1],
            'school_id': agent[2],
            'status': agent[3],
            'last_seen': agent[4],
            'created_at': agent[5]
        })
        
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Error handlers
@cloud_api.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@cloud_api.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
