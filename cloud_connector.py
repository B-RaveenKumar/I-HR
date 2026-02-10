#!/usr/bin/env python3
"""
Cloud Connector Service
Acts as a bridge between ZK biometric devices and cloud platform
"""

import os
import asyncio
import json
import logging
import threading
import time
import websocket
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import asdict
import schedule

# Check if cloud is disabled
CLOUD_DISABLED = os.environ.get('DISABLE_CLOUD', '0') == '1'

if not CLOUD_DISABLED:
    from zk_biometric import ZKBiometricDevice
    from cloud_config import get_cloud_config, get_device_config, get_all_devices, get_primary_endpoint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudConnector:
    """Main cloud connector service"""

    def __init__(self):
        # Check if cloud is disabled
        if CLOUD_DISABLED:
            logger.info("Cloud connector disabled via DISABLE_CLOUD environment variable")
            self.running = False
            self.disabled = True
            return

        self.disabled = False
        self.config = get_cloud_config()
        self.endpoint = get_primary_endpoint()
        self.devices = get_all_devices()
        self.running = False
        self.websocket = None
        self.last_heartbeat = None
        self.sync_thread = None
        self.websocket_thread = None

        # Event handlers
        self.on_attendance_record = None
        self.on_device_status_change = None
        self.on_cloud_message = None

        # Device connections cache
        self.device_connections = {}

        # Message queue for offline support
        self.message_queue = []
        self.max_queue_size = 1000
    
    def start(self):
        """Start the cloud connector service"""
        if hasattr(self, 'disabled') and self.disabled:
            logger.info("Cloud connector is disabled - skipping start")
            return True

        if self.running:
            logger.warning("Cloud connector is already running")
            return

        logger.info("Starting cloud connector service...")
        self.running = True

        # Validate configuration
        if not self._validate_config():
            logger.error("Invalid configuration. Cannot start cloud connector.")
            return False

        # Start background threads
        self._start_sync_thread()
        self._start_websocket_thread()
        self._schedule_tasks()

        logger.info("Cloud connector service started successfully")
        return True
    
    def stop(self):
        """Stop the cloud connector service"""
        logger.info("Stopping cloud connector service...")
        self.running = False
        
        # Close websocket connection
        if self.websocket:
            self.websocket.close()
        
        # Wait for threads to finish
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        
        if self.websocket_thread and self.websocket_thread.is_alive():
            self.websocket_thread.join(timeout=5)
        
        # Close device connections
        for device_id, zk_device in self.device_connections.items():
            try:
                zk_device.disconnect()
            except:
                pass
        
        self.device_connections.clear()
        logger.info("Cloud connector service stopped")
    
    def _validate_config(self) -> bool:
        """Validate configuration before starting"""
        if not self.endpoint:
            logger.error("No cloud endpoint configured")
            return False
        
        if not self.endpoint.api_key:
            logger.error("No API key configured")
            return False
        
        if not self.devices:
            logger.error("No devices configured")
            return False
        
        return True
    
    def _start_sync_thread(self):
        """Start the synchronization thread"""
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info("Sync thread started")
    
    def _start_websocket_thread(self):
        """Start the WebSocket connection thread"""
        self.websocket_thread = threading.Thread(target=self._websocket_loop, daemon=True)
        self.websocket_thread.start()
        logger.info("WebSocket thread started")
    
    def _schedule_tasks(self):
        """Schedule periodic tasks"""
        # Schedule heartbeat
        schedule.every(self.config.heartbeat_interval).seconds.do(self._send_heartbeat)
        
        # Schedule device sync
        schedule.every(self.config.sync_interval).seconds.do(self._sync_all_devices)
        
        # Schedule queue processing
        schedule.every(10).seconds.do(self._process_message_queue)
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Task scheduler started")
    
    def _run_scheduler(self):
        """Run the task scheduler"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def _sync_loop(self):
        """Main synchronization loop"""
        while self.running:
            try:
                self._sync_all_devices()
                time.sleep(self.config.sync_interval)
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _websocket_loop(self):
        """WebSocket connection loop with reconnection"""
        while self.running:
            try:
                self._connect_websocket()
                time.sleep(5)  # Wait before reconnecting
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _connect_websocket(self):
        """Connect to cloud WebSocket"""
        if not self.config.websocket_url:
            logger.warning("WebSocket URL not configured")
            return
        
        try:
            # Prepare headers with authentication
            headers = {
                'Authorization': f'Bearer {self.endpoint.api_key}',
                'X-Organization-ID': self.config.organization_id
            }
            
            # Create WebSocket connection
            self.websocket = websocket.WebSocketApp(
                self.config.websocket_url,
                header=headers,
                on_open=self._on_websocket_open,
                on_message=self._on_websocket_message,
                on_error=self._on_websocket_error,
                on_close=self._on_websocket_close
            )
            
            # Run WebSocket (this blocks until connection closes)
            self.websocket.run_forever()
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
    
    def _on_websocket_open(self, ws):
        """WebSocket connection opened"""
        logger.info("WebSocket connection established")
        
        # Send initial device registration
        self._register_devices()
        
        # Send heartbeat
        self._send_heartbeat()
    
    def _on_websocket_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            logger.info(f"Received WebSocket message: {message_type}")
            
            if message_type == 'device_command':
                self._handle_device_command(data)
            elif message_type == 'sync_request':
                self._handle_sync_request(data)
            elif message_type == 'heartbeat_response':
                self.last_heartbeat = datetime.now()
            
            # Call custom message handler if set
            if self.on_cloud_message:
                self.on_cloud_message(data)
                
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _on_websocket_error(self, ws, error):
        """WebSocket error occurred"""
        logger.error(f"WebSocket error: {error}")
    
    def _on_websocket_close(self, ws, close_status_code, close_msg):
        """WebSocket connection closed"""
        logger.warning(f"WebSocket connection closed: {close_status_code} - {close_msg}")
    
    def _register_devices(self):
        """Register all devices with cloud platform"""
        for device in self.devices:
            if device.cloud_enabled:
                self._send_websocket_message({
                    'type': 'device_register',
                    'device_id': device.device_id,
                    'device_name': device.device_name,
                    'device_type': device.device_type,
                    'local_ip': device.local_ip,
                    'local_port': device.local_port,
                    'timestamp': datetime.now().isoformat()
                })
    
    def _send_websocket_message(self, message: Dict):
        """Send message via WebSocket"""
        if self.websocket and self.websocket.sock and self.websocket.sock.connected:
            try:
                self.websocket.send(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
        
        # Add to queue if WebSocket not available
        self._queue_message(message)
        return False
    
    def _queue_message(self, message: Dict):
        """Queue message for later delivery"""
        if len(self.message_queue) >= self.max_queue_size:
            # Remove oldest message
            self.message_queue.pop(0)
        
        message['queued_at'] = datetime.now().isoformat()
        self.message_queue.append(message)
        logger.debug(f"Message queued: {message.get('type')}")
    
    def _process_message_queue(self):
        """Process queued messages"""
        if not self.message_queue:
            return
        
        # Try to send queued messages
        messages_to_remove = []
        for i, message in enumerate(self.message_queue):
            if self._send_websocket_message(message):
                messages_to_remove.append(i)
            else:
                break  # Stop if we can't send
        
        # Remove successfully sent messages
        for i in reversed(messages_to_remove):
            self.message_queue.pop(i)
        
        if messages_to_remove:
            logger.info(f"Processed {len(messages_to_remove)} queued messages")
    
    def _send_heartbeat(self):
        """Send heartbeat to cloud platform"""
        heartbeat_data = {
            'type': 'heartbeat',
            'timestamp': datetime.now().isoformat(),
            'device_count': len([d for d in self.devices if d.cloud_enabled]),
            'queue_size': len(self.message_queue)
        }
        
        self._send_websocket_message(heartbeat_data)
    
    def _sync_all_devices(self):
        """Sync attendance data from all devices"""
        for device in self.devices:
            if device.cloud_enabled:
                try:
                    self._sync_device(device)
                except Exception as e:
                    logger.error(f"Error syncing device {device.device_id}: {e}")
    
    def _sync_device(self, device_config):
        """Sync attendance data from a specific device"""
        device_id = device_config.device_id
        
        # Get or create device connection
        zk_device = self._get_device_connection(device_config)
        if not zk_device:
            return
        
        try:
            # Get new attendance records since last sync
            since_time = None
            if device_config.last_sync:
                since_time = datetime.fromisoformat(device_config.last_sync)
            
            records = zk_device.get_new_attendance_records(since_time)
            
            if records:
                logger.info(f"Found {len(records)} new records from device {device_id}")
                
                # Send records to cloud
                for record in records:
                    self._send_attendance_record(device_id, record)
                
                # Update last sync time
                device_config.last_sync = datetime.now().isoformat()
                
                # Call custom handler if set
                if self.on_attendance_record:
                    for record in records:
                        self.on_attendance_record(device_id, record)
        
        except Exception as e:
            logger.error(f"Error syncing device {device_id}: {e}")
    
    def _get_device_connection(self, device_config) -> Optional[ZKBiometricDevice]:
        """Get or create device connection"""
        device_id = device_config.device_id
        
        # Check if connection exists and is valid
        if device_id in self.device_connections:
            zk_device = self.device_connections[device_id]
            # Test connection
            try:
                if zk_device.connection:
                    return zk_device
            except:
                pass
        
        # Create new connection
        try:
            zk_device = ZKBiometricDevice(
                device_ip=device_config.local_ip,
                port=device_config.local_port,
                timeout=self.config.connection_timeout
            )
            
            if zk_device.connect():
                self.device_connections[device_id] = zk_device
                logger.info(f"Connected to device {device_id} at {device_config.local_ip}")
                return zk_device
            else:
                logger.error(f"Failed to connect to device {device_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error connecting to device {device_id}: {e}")
            return None
    
    def _send_attendance_record(self, device_id: str, record: Dict):
        """Send attendance record to cloud platform"""
        cloud_record = {
            'type': 'attendance_record',
            'device_id': device_id,
            'user_id': record['user_id'],
            'timestamp': record['timestamp'].isoformat(),
            'verification_type': record['verification_type'],
            'punch_code': record['punch'],
            'status': record['status'],
            'verify_method': record.get('verify', 0),
            'uploaded_at': datetime.now().isoformat()
        }
        
        self._send_websocket_message(cloud_record)
    
    def _handle_device_command(self, data: Dict):
        """Handle device command from cloud"""
        device_id = data.get('device_id')
        command = data.get('command')
        
        logger.info(f"Received device command: {command} for device {device_id}")
        
        device_config = get_device_config(device_id)
        if not device_config:
            logger.error(f"Device {device_id} not found")
            return
        
        zk_device = self._get_device_connection(device_config)
        if not zk_device:
            logger.error(f"Cannot connect to device {device_id}")
            return
        
        try:
            if command == 'get_users':
                users = zk_device.get_users()
                self._send_websocket_message({
                    'type': 'command_response',
                    'device_id': device_id,
                    'command': command,
                    'data': users,
                    'timestamp': datetime.now().isoformat()
                })
            
            elif command == 'sync_attendance':
                self._sync_device(device_config)
            
            elif command == 'clear_attendance':
                success = zk_device.clear_attendance()
                self._send_websocket_message({
                    'type': 'command_response',
                    'device_id': device_id,
                    'command': command,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Error executing command {command} on device {device_id}: {e}")
    
    def _handle_sync_request(self, data: Dict):
        """Handle sync request from cloud"""
        device_id = data.get('device_id')
        
        if device_id:
            # Sync specific device
            device_config = get_device_config(device_id)
            if device_config:
                self._sync_device(device_config)
        else:
            # Sync all devices
            self._sync_all_devices()
    
    def send_cloud_api_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
        """Send HTTP API request to cloud platform"""
        if not self.endpoint:
            logger.error("No cloud endpoint configured")
            return None
        
        url = f"{self.endpoint.url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.endpoint.api_key}',
            'Content-Type': 'application/json',
            'X-Organization-ID': self.config.organization_id
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=self.endpoint.timeout,
                verify=self.config.verify_ssl
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_device_status(self, device_id: str) -> Dict:
        """Get device status"""
        device_config = get_device_config(device_id)
        if not device_config:
            return {'status': 'not_configured'}
        
        zk_device = self._get_device_connection(device_config)
        if not zk_device:
            return {'status': 'disconnected'}
        
        try:
            users = zk_device.get_users()
            return {
                'status': 'connected',
                'user_count': len(users),
                'last_sync': device_config.last_sync,
                'device_ip': device_config.local_ip
            }
        except:
            return {'status': 'error'}

# Global cloud connector instance
cloud_connector = CloudConnector()

def start_cloud_connector():
    """Start the cloud connector service"""
    return cloud_connector.start()

def stop_cloud_connector():
    """Stop the cloud connector service"""
    cloud_connector.stop()

def get_cloud_connector() -> CloudConnector:
    """Get the cloud connector instance"""
    return cloud_connector
