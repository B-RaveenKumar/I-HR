"""
Universal ADMS Parser Module
Protocol-agnostic parser for ZK biometric device attendance data.

Supports multiple data formats:
- Text/Tab-separated (Legacy devices: K40, F18, etc.)
- JSON (Modern devices: uFace, SpeedFace, etc.)
- XML (Specific older models)

This module implements intelligent format detection and normalization.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

# Configure logging
logger = logging.getLogger(__name__)


class UniversalADMSParser:
    """
    Universal parser for ADMS attendance data.
    Auto-detects format and normalizes to standard output.
    """
    
    # Punch code mappings
    PUNCH_CODE_MAP = {
        0: 'check-in',
        1: 'check-out',
        2: 'break-out',
        3: 'break-in',
        4: 'overtime-in',
        5: 'overtime-out'
    }
    
    # Verification method mappings
    VERIFY_METHOD_MAP = {
        0: 'password',
        1: 'fingerprint',
        2: 'face',
        3: 'palm',
        4: 'card',
        5: 'iris',
        15: 'face',  # Some devices use 15 for face
    }
    
    def __init__(self):
        """Initialize the parser"""
        self.last_detected_format = None
    
    def detect_format(self, raw_data: str, content_type: Optional[str] = None) -> str:
        """
        Detect the data format of incoming payload.
        
        Args:
            raw_data: Raw request body as string
            content_type: HTTP Content-Type header (optional)
        
        Returns:
            Format type: 'json', 'xml', 'text', or 'unknown'
        """
        if not raw_data or not raw_data.strip():
            return 'empty'
        
        data = raw_data.strip()
        
        # Check Content-Type header first (most reliable)
        if content_type:
            content_type_lower = content_type.lower()
            if 'json' in content_type_lower:
                return 'json'
            elif 'xml' in content_type_lower:
                return 'xml'
            elif 'text' in content_type_lower or 'plain' in content_type_lower:
                return 'text'
        
        # Format detection by content inspection
        # JSON detection
        if data.startswith('{') or data.startswith('['):
            try:
                json.loads(data)
                return 'json'
            except:
                pass
        
        # XML detection
        if data.startswith('<?xml') or data.startswith('<'):
            try:
                ET.fromstring(data)
                return 'xml'
            except:
                pass
        
        # Text/Tab-separated detection (most common legacy format)
        # Look for patterns like: ATTLOG, USER, OPLOG, or tab-separated values
        if '\t' in data or 'ATTLOG' in data or 'USER' in data or 'OPLOG' in data:
            return 'text'
        
        # Check for common text format patterns
        # Pattern: number timestamp number number
        text_pattern = r'^\d+\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\d+\s+\d+'
        if re.match(text_pattern, data.split('\n')[0]):
            return 'text'
        
        logger.warning(f"Unknown format detected. First 100 chars: {data[:100]}")
        return 'unknown'
    
    def parse(self, raw_data: str, content_type: Optional[str] = None) -> Dict:
        """
        Parse attendance data from any format.
        
        Args:
            raw_data: Raw request body
            content_type: HTTP Content-Type header
        
        Returns:
            Dict with:
            {
                'success': bool,
                'format': str,
                'records': List[Dict],
                'error': str (if failed)
            }
        """
        try:
            # Detect format
            data_format = self.detect_format(raw_data, content_type)
            self.last_detected_format = data_format
            
            logger.info(f"Detected format: {data_format}")
            
            if data_format == 'empty':
                return {
                    'success': False,
                    'format': 'empty',
                    'records': [],
                    'error': 'Empty payload'
                }
            
            # Parse based on detected format
            if data_format == 'json':
                return self._parse_json(raw_data)
            elif data_format == 'xml':
                return self._parse_xml(raw_data)
            elif data_format == 'text':
                return self._parse_text(raw_data)
            else:
                # Unknown format - log for debugging
                return {
                    'success': False,
                    'format': 'unknown',
                    'records': [],
                    'error': 'Unknown data format',
                    'raw_sample': raw_data[:500]  # First 500 chars for debugging
                }
        
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return {
                'success': False,
                'format': 'error',
                'records': [],
                'error': str(e)
            }
    
    def _parse_json(self, raw_data: str) -> Dict:
        """
        Parse JSON format attendance data.
        
        Expected formats:
        1. Array of logs: [{"user": "101", "time": "2025-10-30 09:00:00", ...}]
        2. Object with data array: {"data": [...], "serial": "..."}
        """
        try:
            data = json.loads(raw_data)
            records = []
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Direct array of records
                logs = data
            elif isinstance(data, dict):
                # Object with 'data', 'records', 'logs', or 'attendance' key
                logs = (data.get('data') or 
                       data.get('records') or 
                       data.get('logs') or 
                       data.get('attendance') or 
                       [data])  # Single record
            else:
                return {
                    'success': False,
                    'format': 'json',
                    'records': [],
                    'error': 'Unexpected JSON structure'
                }
            
            # Normalize each log
            for log in logs:
                normalized = self._normalize_record(log, 'json')
                if normalized:
                    records.append(normalized)
            
            return {
                'success': True,
                'format': 'json',
                'records': records
            }
        
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'format': 'json',
                'records': [],
                'error': f'JSON parse error: {e}'
            }
    
    def _parse_xml(self, raw_data: str) -> Dict:
        """
        Parse XML format attendance data.
        
        Expected format:
        <AttendanceLogs>
            <Log user="101" time="2025-10-30 09:00:00" status="0" verify="1"/>
        </AttendanceLogs>
        """
        try:
            root = ET.fromstring(raw_data)
            records = []
            
            # Find log entries (try multiple common tag names)
            log_tags = ['Log', 'Record', 'Attendance', 'Entry']
            
            for tag_name in log_tags:
                logs = root.findall(f'.//{tag_name}')
                if logs:
                    break
            else:
                # No logs found with common names, try all children
                logs = list(root)
            
            # Normalize each log
            for log_elem in logs:
                # Convert XML element to dict
                log_dict = log_elem.attrib
                normalized = self._normalize_record(log_dict, 'xml')
                if normalized:
                    records.append(normalized)
            
            return {
                'success': True,
                'format': 'xml',
                'records': records
            }
        
        except ET.ParseError as e:
            return {
                'success': False,
                'format': 'xml',
                'records': [],
                'error': f'XML parse error: {e}'
            }
    
    def _parse_text(self, raw_data: str) -> Dict:
        """
        Parse text/tab-separated format attendance data.
        
        Expected formats:
        1. ATTLOG format: ATTLOG\t101\t2025-10-30 09:00:00\t0\t1
        2. Raw tab-separated: 101\t2025-10-30 09:00:00\t0\t1\t0
        3. Space-separated: 101 2025-10-30 09:00:00 0 1
        """
        try:
            lines = raw_data.strip().split('\n')
            records = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip command responses and status lines
                if line.startswith('OK') or line.startswith('ERROR'):
                    continue
                
                # Parse ATTLOG format
                if line.startswith('ATTLOG'):
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        log_dict = {
                            'user_id': parts[1],
                            'timestamp': parts[2],
                            'status': parts[3] if len(parts) > 3 else '0',
                            'verify_method': parts[4] if len(parts) > 4 else '1'
                        }
                        normalized = self._normalize_record(log_dict, 'text')
                        if normalized:
                            records.append(normalized)
                
                # Parse raw tab-separated or space-separated
                elif '\t' in line or re.match(r'^\d+[\s\t]+\d{4}-\d{2}-\d{2}', line):
                    # Try tab-separated first
                    parts = line.split('\t') if '\t' in line else line.split()
                    
                    if len(parts) >= 2:
                        log_dict = {
                            'user_id': parts[0],
                            'timestamp': parts[1],
                            'status': parts[2] if len(parts) > 2 else '0',
                            'verify_method': parts[3] if len(parts) > 3 else '1',
                            'temperature': parts[4] if len(parts) > 4 else None,  # Palm scanners may include temperature
                            'mask_status': parts[5] if len(parts) > 5 else None   # Face scanners may include mask detection
                        }
                        normalized = self._normalize_record(log_dict, 'text')
                        if normalized:
                            records.append(normalized)
            
            return {
                'success': True,
                'format': 'text',
                'records': records
            }
        
        except Exception as e:
            return {
                'success': False,
                'format': 'text',
                'records': [],
                'error': f'Text parse error: {e}'
            }
    
    def _normalize_record(self, raw_record: Dict, source_format: str) -> Optional[Dict]:
        """
        Normalize a record from any format to standard output.
        
        Args:
            raw_record: Raw log data (dict with various key names)
            source_format: Original format ('json', 'xml', 'text')
        
        Returns:
            Standardized dict or None if invalid
        """
        try:
            # Extract user ID (many possible field names)
            user_id = (raw_record.get('user_id') or 
                      raw_record.get('user') or 
                      raw_record.get('pin') or 
                      raw_record.get('userid') or 
                      raw_record.get('emp_id') or
                      raw_record.get('cardno') or
                      raw_record.get('staff_id'))
            
            if not user_id:
                logger.warning(f"No user_id found in record: {raw_record}")
                return None
            
            # Extract timestamp (many possible field names and formats)
            timestamp_str = (raw_record.get('timestamp') or 
                           raw_record.get('time') or 
                           raw_record.get('verify_time') or 
                           raw_record.get('punch_time') or
                           raw_record.get('datetime') or
                           raw_record.get('att_time'))
            
            if not timestamp_str:
                logger.warning(f"No timestamp found in record: {raw_record}")
                return None
            
            # Parse timestamp to datetime object
            timestamp = self._parse_timestamp(timestamp_str)
            if not timestamp:
                return None
            
            # Extract status/punch code
            status = raw_record.get('status') or raw_record.get('punch_code') or '0'
            punch_code = int(status) if isinstance(status, (int, str)) and str(status).isdigit() else 0
            
            # Extract verification method
            verify_method = raw_record.get('verify_method') or raw_record.get('verify') or raw_record.get('method') or '1'
            verify_code = int(verify_method) if isinstance(verify_method, (int, str)) and str(verify_method).isdigit() else 1
            
            # Map to readable names
            verification_type = self.PUNCH_CODE_MAP.get(punch_code, 'check-in')
            biometric_method = self.VERIFY_METHOD_MAP.get(verify_code, 'fingerprint')
            
            # Build normalized record
            normalized = {
                'user_id': str(user_id),
                'timestamp': timestamp,
                'timestamp_str': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'punch_code': punch_code,
                'verification_type': verification_type,
                'verify_method': verify_code,
                'biometric_method': biometric_method,
                'source_format': source_format
            }
            
            # Include extra fields if present (for palm scanners with temperature, etc.)
            if 'temperature' in raw_record and raw_record['temperature']:
                normalized['temperature'] = raw_record['temperature']
            
            if 'mask_status' in raw_record and raw_record['mask_status']:
                normalized['mask_status'] = raw_record['mask_status']
            
            return normalized
        
        except Exception as e:
            logger.error(f"Error normalizing record: {e}, raw: {raw_record}")
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp from various formats.
        
        Supported formats:
        - 2025-10-30 09:00:00
        - 2025-10-30T09:00:00
        - 2025/10/30 09:00:00
        - 30/10/2025 09:00:00
        - Unix timestamp (integer)
        """
        if not timestamp_str:
            return None
        
        timestamp_str = str(timestamp_str).strip()
        
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%dT%H:%M',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # Try Unix timestamp (integer seconds)
        try:
            unix_ts = int(timestamp_str)
            if unix_ts > 1000000000 and unix_ts < 9999999999:  # Reasonable range
                return datetime.fromtimestamp(unix_ts)
        except (ValueError, OSError):
            pass
        
        logger.warning(f"Could not parse timestamp: {timestamp_str}")
        return None
    
    def get_last_format(self) -> Optional[str]:
        """Get the last detected format"""
        return self.last_detected_format


# Convenience function for quick parsing
def parse_attendance_data(raw_data: str, content_type: Optional[str] = None) -> Dict:
    """
    Quick function to parse attendance data.
    
    Args:
        raw_data: Raw request body
        content_type: HTTP Content-Type header
    
    Returns:
        Parsed result dict
    """
    parser = UniversalADMSParser()
    return parser.parse(raw_data, content_type)
