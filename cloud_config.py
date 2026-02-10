#!/usr/bin/env python3
"""
Cloud Configuration Management
Handles configuration for cloud-based ZK biometric device connectivity
"""

import os
import json
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CloudEndpoint:
    """Cloud endpoint configuration"""
    name: str
    url: str
    api_key: str
    timeout: int = 30
    retry_attempts: int = 3
    enabled: bool = True

@dataclass
class DeviceConfig:
    """Device configuration for cloud connectivity"""
    device_id: str
    device_name: str
    device_type: str = "ZK_BIOMETRIC"
    local_ip: str = "192.168.1.201"
    local_port: int = 4370
    cloud_enabled: bool = True
    sync_interval: int = 30  # seconds
    last_sync: Optional[str] = None

@dataclass
class CloudConfig:
    """Main cloud configuration"""
    # Cloud service settings
    cloud_provider: str = "custom"  # custom, aws, azure, gcp
    api_base_url: str = "http://182.66.109.42:32150"
    websocket_url: str = "ws://182.66.109.42:32150"
    mqtt_broker: str = "182.66.109.42"
    mqtt_port: int = 32150
    
    # Authentication
    api_key: str = ""
    secret_key: str = ""
    organization_id: str = ""
    
    # Connection settings
    connection_timeout: int = 30
    retry_attempts: int = 3
    heartbeat_interval: int = 60
    
    # Security
    use_ssl: bool = True
    verify_ssl: bool = True
    encryption_enabled: bool = True
    
    # Sync settings
    auto_sync: bool = True
    sync_interval: int = 30
    batch_size: int = 100
    
    # Backup settings
    local_backup: bool = True
    backup_retention_days: int = 30

class CloudConfigManager:
    """Manages cloud configuration settings"""
    
    def __init__(self, config_file: str = "cloud_config.json"):
        self.config_file = config_file
        self.config: CloudConfig = CloudConfig()
        self.devices: List[DeviceConfig] = []
        self.endpoints: List[CloudEndpoint] = []
        self._encryption_key = self._get_or_create_encryption_key()
        self.load_config()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_file = ".cloud_key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Make file readable only by owner
            os.chmod(key_file, 0o600)
            return key
    
    def _encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive configuration data"""
        if not data:
            return data
        
        fernet = Fernet(self._encryption_key)
        return fernet.encrypt(data.encode()).decode()
    
    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive configuration data"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            fernet = Fernet(self._encryption_key)
            return fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return ""
    
    def load_config(self):
        """Load configuration from file and environment variables"""
        # Load from environment variables first
        self._load_from_env()
        
        # Load from config file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load main config
                if 'config' in data:
                    config_data = data['config']
                    # Decrypt sensitive fields
                    if 'api_key' in config_data:
                        config_data['api_key'] = self._decrypt_sensitive_data(config_data['api_key'])
                    if 'secret_key' in config_data:
                        config_data['secret_key'] = self._decrypt_sensitive_data(config_data['secret_key'])
                    
                    self.config = CloudConfig(**config_data)
                
                # Load devices
                if 'devices' in data:
                    self.devices = [DeviceConfig(**device) for device in data['devices']]
                
                # Load endpoints
                if 'endpoints' in data:
                    endpoints_data = data['endpoints']
                    for endpoint_data in endpoints_data:
                        # Decrypt API key
                        if 'api_key' in endpoint_data:
                            endpoint_data['api_key'] = self._decrypt_sensitive_data(endpoint_data['api_key'])
                        self.endpoints.append(CloudEndpoint(**endpoint_data))
                
                logger.info(f"Configuration loaded from {self.config_file}")
                
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'CLOUD_API_BASE_URL': 'api_base_url',
            'CLOUD_WEBSOCKET_URL': 'websocket_url',
            'CLOUD_MQTT_BROKER': 'mqtt_broker',
            'CLOUD_MQTT_PORT': 'mqtt_port',
            'CLOUD_API_KEY': 'api_key',
            'CLOUD_SECRET_KEY': 'secret_key',
            'CLOUD_ORG_ID': 'organization_id',
            'CLOUD_USE_SSL': 'use_ssl',
            'CLOUD_VERIFY_SSL': 'verify_ssl',
            'CLOUD_AUTO_SYNC': 'auto_sync',
            'CLOUD_SYNC_INTERVAL': 'sync_interval'
        }
        
        for env_var, config_attr in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Convert boolean strings
                if config_attr in ['use_ssl', 'verify_ssl', 'auto_sync']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                # Convert integer strings
                elif config_attr in ['mqtt_port', 'sync_interval']:
                    value = int(value)
                
                setattr(self.config, config_attr, value)
    
    def _create_default_config(self):
        """Create default configuration"""
        # Add default device if none exists
        if not self.devices:
            default_device = DeviceConfig(
                device_id="181",
                device_name="ZK Biometric Device 181",
                local_ip="182.66.109.42",
                local_port=32150
            )
            self.devices.append(default_device)
        
        # Add default endpoint if none exists
        if not self.endpoints:
            default_endpoint = CloudEndpoint(
                name="primary",
                url=self.config.api_base_url,
                api_key=self.config.api_key
            )
            self.endpoints.append(default_endpoint)
        
        logger.info("Default configuration created")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Prepare data for saving
            config_data = asdict(self.config)
            
            # Encrypt sensitive fields
            config_data['api_key'] = self._encrypt_sensitive_data(config_data['api_key'])
            config_data['secret_key'] = self._encrypt_sensitive_data(config_data['secret_key'])
            
            # Prepare endpoints data
            endpoints_data = []
            for endpoint in self.endpoints:
                endpoint_data = asdict(endpoint)
                endpoint_data['api_key'] = self._encrypt_sensitive_data(endpoint_data['api_key'])
                endpoints_data.append(endpoint_data)
            
            data = {
                'config': config_data,
                'devices': [asdict(device) for device in self.devices],
                'endpoints': endpoints_data
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def add_device(self, device: DeviceConfig):
        """Add a new device configuration"""
        # Check if device already exists
        for existing_device in self.devices:
            if existing_device.device_id == device.device_id:
                logger.warning(f"Device {device.device_id} already exists")
                return False
        
        self.devices.append(device)
        self.save_config()
        logger.info(f"Added device: {device.device_id}")
        return True
    
    def remove_device(self, device_id: str):
        """Remove a device configuration"""
        self.devices = [d for d in self.devices if d.device_id != device_id]
        self.save_config()
        logger.info(f"Removed device: {device_id}")
    
    def get_device(self, device_id: str) -> Optional[DeviceConfig]:
        """Get device configuration by ID"""
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None
    
    def add_endpoint(self, endpoint: CloudEndpoint):
        """Add a new cloud endpoint"""
        # Check if endpoint already exists
        for existing_endpoint in self.endpoints:
            if existing_endpoint.name == endpoint.name:
                logger.warning(f"Endpoint {endpoint.name} already exists")
                return False
        
        self.endpoints.append(endpoint)
        self.save_config()
        logger.info(f"Added endpoint: {endpoint.name}")
        return True
    
    def get_primary_endpoint(self) -> Optional[CloudEndpoint]:
        """Get the primary cloud endpoint"""
        for endpoint in self.endpoints:
            if endpoint.enabled and endpoint.name == "primary":
                return endpoint
        
        # Return first enabled endpoint if no primary
        for endpoint in self.endpoints:
            if endpoint.enabled:
                return endpoint
        
        return None
    
    def validate_config(self) -> Dict[str, List[str]]:
        """Validate configuration and return any errors"""
        errors = {
            'config': [],
            'devices': [],
            'endpoints': []
        }
        
        # Validate main config
        if not self.config.api_base_url:
            errors['config'].append("API base URL is required")
        
        if not self.config.api_key:
            errors['config'].append("API key is required")
        
        if not self.config.organization_id:
            errors['config'].append("Organization ID is required")
        
        # Validate devices
        if not self.devices:
            errors['devices'].append("At least one device must be configured")
        
        device_ids = set()
        for device in self.devices:
            if device.device_id in device_ids:
                errors['devices'].append(f"Duplicate device ID: {device.device_id}")
            device_ids.add(device.device_id)
        
        # Validate endpoints
        if not self.endpoints:
            errors['endpoints'].append("At least one endpoint must be configured")
        
        endpoint_names = set()
        for endpoint in self.endpoints:
            if endpoint.name in endpoint_names:
                errors['endpoints'].append(f"Duplicate endpoint name: {endpoint.name}")
            endpoint_names.add(endpoint.name)
        
        return errors

# Global configuration manager instance
config_manager = CloudConfigManager()

def get_cloud_config() -> CloudConfig:
    """Get the current cloud configuration"""
    return config_manager.config

def get_device_config(device_id: str) -> Optional[DeviceConfig]:
    """Get device configuration by ID"""
    return config_manager.get_device(device_id)

def get_all_devices() -> List[DeviceConfig]:
    """Get all device configurations"""
    return config_manager.devices

def get_primary_endpoint() -> Optional[CloudEndpoint]:
    """Get the primary cloud endpoint"""
    return config_manager.get_primary_endpoint()
