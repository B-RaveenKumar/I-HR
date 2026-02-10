"""
Vishnorex Biometric Agent - Local Device Bridge
Windows desktop application for Agent_LAN connection mode
Polls ZK devices on local network and pushes attendance to server
"""

import sys
import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QDialog, 
                              QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                              QPushButton, QTextEdit, QGroupBox, QFormLayout,
                              QMessageBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QIcon, QPixmap, QColor

# Add parent directory to path to import zk_biometric
sys.path.insert(0, str(Path(__file__).parent.parent))
from zk_biometric import ZKBiometricDevice

# Configure logging
log_file = os.path.join(os.path.dirname(__file__), 'biometric_agent.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages agent configuration (API key, server URL, devices)"""
    
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
    
    @staticmethod
    def load_config():
        """Load configuration from file"""
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        return {
            'server_url': 'http://localhost:5000',
            'api_key': '',
            'school_id': 1,  # Institution ID
            'devices': [],  # [{'ip': '192.168.1.201', 'port': 4370, 'name': 'Main Device'}]
            'poll_interval': 60,  # seconds
            'heartbeat_interval': 60,  # seconds
            'agent_name': 'Agent-1',
            'last_sync': {}  # {device_ip: timestamp}
        }
    
    @staticmethod
    def save_config(config):
        """Save configuration to file"""
        try:
            os.makedirs('agent', exist_ok=True)
            with open(ConfigManager.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Configuration saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False


class AgentWorker(QObject):
    """Background worker for device polling and server communication"""
    
    status_update = pyqtSignal(str, str)  # (message, level: info/warning/error/success)
    log_message = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = False
        self.registered = False
        
    def start(self):
        """Start the worker threads"""
        self.running = True
        
        # Check if agent already has an API key
        if self.config.get('api_key'):
            # Verify existing API key
            if self.verify_agent():
                self.registered = True
                self.status_update.emit("Agent connected successfully", "success")
            else:
                self.status_update.emit("Invalid API key - please reconfigure", "error")
                self.running = False
                return
        else:
            # No API key - need to register via web interface first
            self.status_update.emit("No API key found - please create agent via web interface first", "error")
            self.running = False
            return
        
        # Start polling thread
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def stop(self):
        """Stop the worker threads"""
        self.running = False
        self.status_update.emit("Agent stopped", "warning")
    
    def verify_agent(self):
        """Verify agent API key with server"""
        try:
            url = f"{self.config['server_url']}/api/agent/info"
            headers = {
                'Authorization': f"Bearer {self.config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"Agent verified: {result.get('agent_name')} (ID: {result.get('agent_id')})")
                    return True
            
            logger.error(f"Agent verification failed: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False
    
    def register_agent(self):
        """Register agent with server (only use this from web interface, not on startup)"""
        try:
            url = f"{self.config['server_url']}/api/agent/register"
            headers = {'Content-Type': 'application/json'}
            data = {
                'school_id': self.config.get('school_id', 1),
                'agent_name': self.config['agent_name'],
                'admin_token': self.config.get('api_key', ''),  # Optional token for security
                'version': '1.0.0',
                'os': 'Windows',
                'devices': self.config.get('devices', [])
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success'):
                    # Save the returned API key
                    if 'api_key' in result:
                        self.config['api_key'] = result['api_key']
                        ConfigManager.save_config(self.config)
                    logger.info(f"Agent registered successfully: {result.get('message', '')}")
                    return True
                else:
                    logger.error(f"Registration failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                logger.error(f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def _heartbeat_loop(self):
        """Send heartbeat to server periodically"""
        while self.running:
            try:
                url = f"{self.config['server_url']}/api/agent/heartbeat"
                headers = {
                    'Authorization': f"Bearer {self.config['api_key']}",
                    'Content-Type': 'application/json'
                }
                data = {
                    'agent_name': self.config['agent_name'],
                    'status': 'active',
                    'devices': self.config['devices']
                }
                
                response = requests.post(url, json=data, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat sent")
                else:
                    self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                self.status_update.emit(f"Heartbeat failed: {str(e)}", "warning")
            
            # Sleep in small intervals to allow quick stop
            for _ in range(self.config['heartbeat_interval']):
                if not self.running:
                    break
                time.sleep(1)
    
    def _poll_loop(self):
        """Poll devices for attendance records periodically"""
        while self.running:
            for device in self.config['devices']:
                if not self.running:
                    break
                    
                try:
                    self.poll_device(device)
                except Exception as e:
                    logger.error(f"Error polling device {device['ip']}: {e}")
                    self.status_update.emit(f"Error polling {device['name']}: {str(e)}", "error")
            
            # Sleep in small intervals to allow quick stop
            for _ in range(self.config['poll_interval']):
                if not self.running:
                    break
                time.sleep(1)
    
    def poll_device(self, device):
        """Poll a single device for new attendance records"""
        device_ip = device['ip']
        device_port = device.get('port', 4370)
        device_name = device.get('name', device_ip)
        
        # Get last sync time for this device
        last_sync_str = self.config['last_sync'].get(device_ip)
        if last_sync_str:
            last_sync = datetime.fromisoformat(last_sync_str)
        else:
            # First sync - get records from last 24 hours
            last_sync = datetime.now() - timedelta(hours=24)
        
        logger.info(f"Polling device {device_name} ({device_ip}) since {last_sync}")
        self.log_message.emit(f"[{datetime.now().strftime('%H:%M:%S')}] Polling {device_name}...")
        
        try:
            # Connect to device
            zk_device = ZKBiometricDevice(device_ip, port=device_port, timeout=10)
            if not zk_device.connect():
                logger.warning(f"Cannot connect to device {device_ip}")
                self.status_update.emit(f"Cannot connect to {device_name}", "warning")
                return
            
            # Get new attendance records
            records = zk_device.get_new_attendance_records(last_sync)
            zk_device.disconnect()
            
            logger.info(f"Retrieved {len(records)} records from {device_name} (after {last_sync})")
            
            if records:
                logger.info(f"Found {len(records)} new records from {device_name}")
                self.log_message.emit(f"Found {len(records)} new records from {device_name}")
                
                # Push records to server
                if self.push_attendance_logs(device, records):
                    # Update last sync time to now
                    new_sync_time = datetime.now().isoformat()
                    self.config['last_sync'][device_ip] = new_sync_time
                    ConfigManager.save_config(self.config)
                    logger.info(f"Updated last_sync for {device_ip} to {new_sync_time}")
                    self.status_update.emit(f"✓ Synced {len(records)} records from {device_name}", "success")
                else:
                    self.status_update.emit(f"✗ Failed to push records from {device_name}", "error")
            else:
                self.log_message.emit(f"No new records from {device_name}")
                
        except Exception as e:
            logger.error(f"Error polling device {device_ip}: {e}")
            raise
    
    def push_attendance_logs(self, device, records):
        """Push attendance logs to server"""
        try:
            url = f"{self.config['server_url']}/api/agent/push_logs"
            headers = {
                'Authorization': f"Bearer {self.config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            # Check if device has device_id (from database)
            device_id = device.get('device_id')
            if not device_id:
                logger.error(f"Device {device.get('name', device['ip'])} has no device_id. Please configure it in the web interface first.")
                return False
            
            # Format records for API
            formatted_records = []
            for record in records:
                formatted_records.append({
                    'user_id': record.get('user_id'),
                    'timestamp': record.get('timestamp').isoformat() if isinstance(record.get('timestamp'), datetime) else record.get('timestamp'),
                    'punch_code': record.get('punch', 0),
                    'verify_method': record.get('status', 1)  # 1=fingerprint, 2=face, 3=password, 4=card
                })
            
            data = {
                'device_id': device_id,
                'records': formatted_records
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Pushed {len(records)} records: {result.get('processed', 0)} processed")
                return True
            else:
                logger.error(f"Failed to push logs: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error pushing logs: {e}")
            return False
    
    def test_connection(self, device_ip, device_port):
        """Test connection to a device"""
        try:
            zk_device = ZKBiometricDevice(device_ip, port=device_port, timeout=10)
            if zk_device.connect():
                users = zk_device.get_users()
                zk_device.disconnect()
                return True, f"Connected! Found {len(users)} users"
            else:
                return False, "Failed to connect"
        except Exception as e:
            return False, str(e)


class ConfigDialog(QDialog):
    """Configuration dialog for agent settings"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Agent Configuration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Server settings
        server_group = QGroupBox("Server Settings")
        server_layout = QFormLayout()
        
        self.server_url_edit = QLineEdit(self.config.get('server_url', ''))
        self.api_key_edit = QLineEdit(self.config.get('api_key', ''))
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.agent_name_edit = QLineEdit(self.config.get('agent_name', ''))
        self.school_id_edit = QLineEdit(str(self.config.get('school_id', '1')))
        
        server_layout.addRow("Server URL:", self.server_url_edit)
        server_layout.addRow("API Key:", self.api_key_edit)
        server_layout.addRow("Agent Name:", self.agent_name_edit)
        server_layout.addRow("Institution ID:", self.school_id_edit)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Device settings
        device_group = QGroupBox("Devices")
        device_layout = QVBoxLayout()
        
        self.device_list = QListWidget()
        for device in self.config.get('devices', []):
            device_id = device.get('device_id', 'NOT SET')
            item_text = f"[ID:{device_id}] {device['name']} - {device['ip']}:{device.get('port', 4370)}"
            self.device_list.addItem(item_text)
        
        device_layout.addWidget(self.device_list)
        
        # Device buttons
        device_btn_layout = QHBoxLayout()
        add_device_btn = QPushButton("Add Device")
        add_device_btn.clicked.connect(self.add_device)
        remove_device_btn = QPushButton("Remove Device")
        remove_device_btn.clicked.connect(self.remove_device)
        test_device_btn = QPushButton("Test Connection")
        test_device_btn.clicked.connect(self.test_device)
        
        device_btn_layout.addWidget(add_device_btn)
        device_btn_layout.addWidget(remove_device_btn)
        device_btn_layout.addWidget(test_device_btn)
        device_layout.addLayout(device_btn_layout)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Intervals
        interval_group = QGroupBox("Polling Intervals")
        interval_layout = QFormLayout()
        
        self.poll_interval_edit = QLineEdit(str(self.config.get('poll_interval', 60)))
        self.heartbeat_interval_edit = QLineEdit(str(self.config.get('heartbeat_interval', 60)))
        
        interval_layout.addRow("Poll Interval (seconds):", self.poll_interval_edit)
        interval_layout.addRow("Heartbeat Interval (seconds):", self.heartbeat_interval_edit)
        
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def add_device(self):
        """Add a new device"""
        from PyQt5.QtWidgets import QInputDialog
        
        # Show instruction message
        QMessageBox.information(self, "Add Device", 
            "IMPORTANT: Before adding a device here:\n\n"
            "1. Go to the web interface (Biometric Device Management)\n"
            "2. Add the device with connection type 'Agent_LAN'\n"
            "3. Assign it to this agent\n"
            "4. Note down the Device ID from the web interface\n\n"
            "Then enter the details below:")
        
        device_id, ok0 = QInputDialog.getInt(self, "Add Device", 
            "Device ID (from web interface):", 1, 1, 999999)
        if not ok0:
            return
        
        ip, ok1 = QInputDialog.getText(self, "Add Device", "Device IP Address:")
        if not ok1 or not ip:
            return
        
        port, ok2 = QInputDialog.getInt(self, "Add Device", "Device Port:", 4370, 1, 65535)
        if not ok2:
            return
        
        name, ok3 = QInputDialog.getText(self, "Add Device", "Device Name:", text=f"Device-{ip}")
        if not ok3 or not name:
            return
        
        device = {'device_id': device_id, 'ip': ip, 'port': port, 'name': name}
        self.config['devices'].append(device)
        
        item_text = f"[ID:{device_id}] {name} - {ip}:{port}"
        self.device_list.addItem(item_text)
    
    def remove_device(self):
        """Remove selected device"""
        current_row = self.device_list.currentRow()
        if current_row >= 0:
            self.config['devices'].pop(current_row)
            self.device_list.takeItem(current_row)
    
    def test_device(self):
        """Test connection to selected device"""
        current_row = self.device_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Test Device", "Please select a device to test")
            return
        
        device = self.config['devices'][current_row]
        
        QMessageBox.information(self, "Testing", f"Testing connection to {device['name']}...\nThis may take a few seconds.")
        
        # Import here to access worker
        worker = AgentWorker(self.config)
        success, message = worker.test_connection(device['ip'], device.get('port', 4370))
        
        if success:
            QMessageBox.information(self, "Connection Test", f"✓ {message}")
        else:
            QMessageBox.warning(self, "Connection Test", f"✗ {message}")
    
    def save_config(self):
        """Save configuration"""
        try:
            self.config['server_url'] = self.server_url_edit.text().strip()
            self.config['api_key'] = self.api_key_edit.text().strip()
            self.config['agent_name'] = self.agent_name_edit.text().strip()
            self.config['school_id'] = int(self.school_id_edit.text().strip())
            self.config['poll_interval'] = int(self.poll_interval_edit.text())
            self.config['heartbeat_interval'] = int(self.heartbeat_interval_edit.text())
            
            if not self.config['server_url']:
                QMessageBox.warning(self, "Validation", "Server URL is required")
                return
            
            if not self.config['api_key']:
                QMessageBox.warning(self, "Validation", "API Key is required")
                return
            
            if not self.config['agent_name']:
                QMessageBox.warning(self, "Validation", "Agent Name is required")
                return
            
            if not self.config.get('school_id'):
                QMessageBox.warning(self, "Validation", "Institution ID is required")
                return
            
            if ConfigManager.save_config(self.config):
                QMessageBox.information(self, "Success", "Configuration saved successfully")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to save configuration")
                
        except ValueError:
            QMessageBox.warning(self, "Validation", "Invalid interval values")


class MainWindow(QDialog):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.config = ConfigManager.load_config()
        self.worker = None
        self.setWindowTitle("Vishnorex Biometric Agent")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Status section
        status_group = QGroupBox("Agent Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Agent")
        self.start_btn.clicked.connect(self.start_agent)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        
        self.stop_btn = QPushButton("Stop Agent")
        self.stop_btn.clicked.connect(self.stop_agent)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px; font-weight: bold;")
        
        config_btn = QPushButton("Configuration")
        config_btn.clicked.connect(self.open_config)
        config_btn.setStyleSheet("padding: 8px;")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(config_btn)
        layout.addLayout(control_layout)
        
        # Log section
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # QTextEdit doesn't have setMaximumBlockCount, we'll manage log size manually
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
        # Add initial log message
        self.add_log("Agent initialized. Click 'Start Agent' to begin.", "info")
    
    def start_agent(self):
        """Start the agent worker"""
        if not self.config.get('api_key'):
            QMessageBox.warning(self, "Configuration Required", 
                              "Please configure the agent (API Key) before starting.")
            self.open_config()
            return
        
        if not self.config.get('devices'):
            QMessageBox.warning(self, "No Devices", 
                              "Please add at least one device in configuration.")
            self.open_config()
            return
        
        self.worker = AgentWorker(self.config)
        self.worker.status_update.connect(self.update_status)
        self.worker.log_message.connect(lambda msg: self.add_log(msg, "info"))
        self.worker.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        self.add_log("Agent started", "success")
    
    def stop_agent(self):
        """Stop the agent worker"""
        if self.worker:
            self.worker.stop()
            self.worker = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        self.add_log("Agent stopped", "warning")
    
    def open_config(self):
        """Open configuration dialog"""
        was_running = False
        if self.worker and self.worker.running:
            was_running = True
            self.stop_agent()
        
        dialog = ConfigDialog(self.config, self)
        if dialog.exec_():
            self.config = ConfigManager.load_config()
            self.add_log("Configuration updated", "success")
            
            if was_running:
                reply = QMessageBox.question(self, "Restart Agent", 
                                            "Configuration changed. Restart agent?",
                                            QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.start_agent()
    
    def update_status(self, message, level):
        """Update status display"""
        self.add_log(message, level)
    
    def add_log(self, message, level="info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Color coding
        colors = {
            'info': 'black',
            'success': 'green',
            'warning': 'orange',
            'error': 'red'
        }
        color = colors.get(level, 'black')
        
        html = f'<span style="color: {color};">[{timestamp}] {message}</span><br>'
        self.log_text.append(html.strip())
        
        # Limit log size (keep last 500 lines approximately)
        text = self.log_text.toPlainText()
        lines = text.split('\n')
        if len(lines) > 500:
            # Keep only last 400 lines
            self.log_text.setPlainText('\n'.join(lines[-400:]))
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class SystemTrayApp(QApplication):
    """System tray application"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        self.main_window = MainWindow()
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to load icon, use default if not found
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Use default icon
            from PyQt5.QtWidgets import QStyle
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show Window")
        show_action.triggered.connect(self.show_main_window)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Exit")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
        self.tray_icon.setToolTip("Vishnorex Biometric Agent")
        
        # Show main window on first run
        self.main_window.show()
    
    def show_main_window(self):
        """Show main window"""
        self.main_window.show()
        self.main_window.activateWindow()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
    
    def quit_app(self):
        """Quit application"""
        # Stop worker if running
        if self.main_window.worker and self.main_window.worker.running:
            self.main_window.worker.stop()
            time.sleep(1)  # Give time for threads to stop
        
        self.tray_icon.hide()
        self.quit()


def main():
    """Main entry point"""
    app = SystemTrayApp(sys.argv)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
