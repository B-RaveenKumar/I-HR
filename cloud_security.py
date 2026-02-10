#!/usr/bin/env python3
"""
Cloud Security Module
Handles authentication, encryption, and security for cloud communications
"""

import hashlib
import hmac
import time
import jwt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudSecurity:
    """Handles cloud security operations"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self._fernet = None
        self.token_expiry_hours = 24
    
    def generate_api_key(self, length: int = 32) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(length)
    
    def generate_device_token(self, device_id: str, organization_id: str, 
                            expires_in_hours: int = None) -> str:
        """Generate JWT token for device authentication"""
        if expires_in_hours is None:
            expires_in_hours = self.token_expiry_hours
        
        payload = {
            'device_id': device_id,
            'organization_id': organization_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'type': 'device_token'
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        logger.info(f"Generated device token for {device_id}")
        return token
    
    def verify_device_token(self, token: str) -> Optional[Dict]:
        """Verify and decode device JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != 'device_token':
                logger.warning("Invalid token type")
                return None
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
                logger.warning("Token expired")
                return None
            
            logger.info(f"Token verified for device {payload['device_id']}")
            return payload
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def generate_api_signature(self, method: str, url: str, body: str = "", 
                             timestamp: str = None) -> Tuple[str, str]:
        """Generate HMAC signature for API requests"""
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        # Create string to sign
        string_to_sign = f"{method}\n{url}\n{body}\n{timestamp}"
        
        # Generate signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature, timestamp
    
    def verify_api_signature(self, method: str, url: str, body: str, 
                           signature: str, timestamp: str, 
                           max_age_seconds: int = 300) -> bool:
        """Verify HMAC signature for API requests"""
        try:
            # Check timestamp age
            request_time = int(timestamp)
            current_time = int(time.time())
            
            if abs(current_time - request_time) > max_age_seconds:
                logger.warning("Request timestamp too old")
                return False
            
            # Generate expected signature
            expected_signature, _ = self.generate_api_signature(
                method, url, body, timestamp
            )
            
            # Compare signatures
            if hmac.compare_digest(signature, expected_signature):
                logger.info("API signature verified")
                return True
            else:
                logger.warning("API signature verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    def get_encryption_key(self, password: str, salt: bytes = None) -> Fernet:
        """Get encryption key from password"""
        if salt is None:
            salt = b'zkbiometric_salt_2024'  # Use consistent salt for same password
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def encrypt_data(self, data: str, password: str = None) -> str:
        """Encrypt sensitive data"""
        if password:
            fernet = self.get_encryption_key(password)
        else:
            if not self._fernet:
                self._fernet = self.get_encryption_key(self.secret_key)
            fernet = self._fernet
        
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str, password: str = None) -> str:
        """Decrypt sensitive data"""
        try:
            if password:
                fernet = self.get_encryption_key(password)
            else:
                if not self._fernet:
                    self._fernet = self.get_encryption_key(self.secret_key)
                fernet = self._fernet
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        password_hash = base64.urlsafe_b64encode(kdf.derive(password.encode())).decode()
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            expected_hash, _ = self.hash_password(password, salt)
            return hmac.compare_digest(password_hash, expected_hash)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def generate_session_token(self, user_id: str, user_type: str, 
                             expires_in_hours: int = 8) -> str:
        """Generate session token for web users"""
        payload = {
            'user_id': user_id,
            'user_type': user_type,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'type': 'session_token'
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        logger.info(f"Generated session token for user {user_id}")
        return token
    
    def verify_session_token(self, token: str) -> Optional[Dict]:
        """Verify and decode session JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != 'session_token':
                logger.warning("Invalid session token type")
                return None
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
                logger.warning("Session token expired")
                return None
            
            logger.info(f"Session token verified for user {payload['user_id']}")
            return payload
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Session token verification failed: {e}")
            return None
    
    def create_secure_headers(self, api_key: str, organization_id: str, 
                            method: str = 'GET', url: str = '', 
                            body: str = '') -> Dict[str, str]:
        """Create secure headers for API requests"""
        signature, timestamp = self.generate_api_signature(method, url, body)
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'X-Organization-ID': organization_id,
            'X-Timestamp': timestamp,
            'X-Signature': signature,
            'Content-Type': 'application/json',
            'User-Agent': 'ZK-Biometric-Cloud/1.0'
        }
        
        return headers
    
    def validate_request_headers(self, headers: Dict[str, str], method: str, 
                               url: str, body: str = '') -> Tuple[bool, str]:
        """Validate incoming request headers"""
        try:
            # Check required headers
            required_headers = ['Authorization', 'X-Organization-ID', 'X-Timestamp', 'X-Signature']
            for header in required_headers:
                if header not in headers:
                    return False, f"Missing required header: {header}"
            
            # Extract values
            auth_header = headers['Authorization']
            if not auth_header.startswith('Bearer '):
                return False, "Invalid Authorization header format"
            
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            organization_id = headers['X-Organization-ID']
            timestamp = headers['X-Timestamp']
            signature = headers['X-Signature']
            
            # Verify signature
            if not self.verify_api_signature(method, url, body, signature, timestamp):
                return False, "Invalid signature"
            
            return True, "Valid request"
            
        except Exception as e:
            logger.error(f"Header validation error: {e}")
            return False, f"Validation error: {str(e)}"
    
    def sanitize_input(self, input_data: str, max_length: int = 1000) -> str:
        """Sanitize input data to prevent injection attacks"""
        if not isinstance(input_data, str):
            input_data = str(input_data)
        
        # Limit length
        if len(input_data) > max_length:
            input_data = input_data[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r']
        for char in dangerous_chars:
            input_data = input_data.replace(char, '')
        
        return input_data.strip()
    
    def rate_limit_key(self, identifier: str, action: str) -> str:
        """Generate rate limiting key"""
        return f"rate_limit:{identifier}:{action}"
    
    def is_rate_limited(self, identifier: str, action: str, 
                       max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Check if request should be rate limited (simplified version)"""
        # This is a simplified implementation
        # In production, you would use Redis or similar for distributed rate limiting
        key = self.rate_limit_key(identifier, action)
        
        # For now, just log the rate limit check
        logger.info(f"Rate limit check for {key}: {max_requests} requests per {window_seconds} seconds")
        
        # Always allow for this implementation
        return False

# Global security instance
cloud_security = CloudSecurity()

def get_cloud_security() -> CloudSecurity:
    """Get the global cloud security instance"""
    return cloud_security

def generate_api_key() -> str:
    """Generate a new API key"""
    return cloud_security.generate_api_key()

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data"""
    return cloud_security.encrypt_data(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    return cloud_security.decrypt_data(encrypted_data)
