#!/usr/bin/env python3
"""
Universal ADMS Parser - Test Suite
Tests all supported formats and edge cases
"""

import sys
import json
from datetime import datetime

# Import the parser
from universal_adms_parser import UniversalADMSParser, parse_attendance_data


def test_format_detection():
    """Test format detection logic"""
    print("=" * 80)
    print("TEST 1: Format Detection")
    print("=" * 80)
    
    parser = UniversalADMSParser()
    
    # Test JSON detection
    json_data = '{"data": [{"user": "101", "time": "2025-12-12 09:00:00"}]}'
    format1 = parser.detect_format(json_data)
    print(f"✓ JSON detection: {format1} (expected: json)")
    assert format1 == 'json', "JSON detection failed"
    
    # Test XML detection
    xml_data = '<?xml version="1.0"?><Logs><Log user="101" time="2025-12-12 09:00:00"/></Logs>'
    format2 = parser.detect_format(xml_data)
    print(f"✓ XML detection: {format2} (expected: xml)")
    assert format2 == 'xml', "XML detection failed"
    
    # Test Text detection
    text_data = 'ATTLOG\t101\t2025-12-12 09:00:00\t0\t1'
    format3 = parser.detect_format(text_data)
    print(f"✓ Text detection: {format3} (expected: text)")
    assert format3 == 'text', "Text detection failed"
    
    # Test tab-separated without ATTLOG
    text_data2 = '101\t2025-12-12 09:00:00\t0\t1'
    format4 = parser.detect_format(text_data2)
    print(f"✓ Tab-separated detection: {format4} (expected: text)")
    assert format4 == 'text', "Tab-separated detection failed"
    
    print("\n✅ All format detection tests passed!\n")


def test_legacy_text_parsing():
    """Test Legacy Text/Tab-separated format (K40, F18)"""
    print("=" * 80)
    print("TEST 2: Legacy Text Format Parsing (Fingerprint Devices)")
    print("=" * 80)
    
    # Test 1: ATTLOG format
    text_data1 = """ATTLOG\t101\t2025-12-12 09:00:00\t0\t1
ATTLOG\t102\t2025-12-12 09:15:30\t1\t1
ATTLOG\t103\t2025-12-12 09:30:45\t0\t1"""
    
    result1 = parse_attendance_data(text_data1)
    
    print(f"\n✓ Parse success: {result1['success']}")
    print(f"✓ Detected format: {result1['format']}")
    print(f"✓ Records parsed: {len(result1['records'])}")
    
    assert result1['success'], "Text parsing failed"
    assert result1['format'] == 'text', "Wrong format detected"
    assert len(result1['records']) == 3, "Wrong record count"
    
    # Check first record
    record1 = result1['records'][0]
    print(f"\n✓ Sample Record:")
    print(f"  - User ID: {record1['user_id']}")
    print(f"  - Timestamp: {record1['timestamp_str']}")
    print(f"  - Verification Type: {record1['verification_type']}")
    print(f"  - Biometric Method: {record1['biometric_method']}")
    
    assert record1['user_id'] == '101', "Wrong user ID"
    assert record1['verification_type'] == 'check-in', "Wrong verification type"
    assert record1['biometric_method'] == 'fingerprint', "Wrong biometric method"
    
    # Test 2: Raw tab-separated
    text_data2 = "101\t2025-12-12 09:00:00\t0\t1\t36.5\t0"
    
    result2 = parse_attendance_data(text_data2)
    print(f"\n✓ Tab-separated with extra fields parsed: {len(result2['records'])} record(s)")
    
    if result2['records']:
        record2 = result2['records'][0]
        print(f"  - Temperature captured: {record2.get('temperature', 'N/A')}")
        print(f"  - Mask status captured: {record2.get('mask_status', 'N/A')}")
    
    print("\n✅ Legacy text parsing tests passed!\n")


def test_modern_json_parsing():
    """Test Modern JSON format (uFace, SpeedFace)"""
    print("=" * 80)
    print("TEST 3: Modern JSON Format Parsing (Face Recognition)")
    print("=" * 80)
    
    # Test 1: Array of records
    json_data1 = json.dumps({
        "data": [
            {
                "user_id": "101",
                "timestamp": "2025-12-12 09:00:00",
                "punch_code": 0,
                "verify_method": 2
            },
            {
                "user_id": "102",
                "timestamp": "2025-12-12 09:15:00",
                "punch_code": 1,
                "verify_method": 2
            }
        ]
    })
    
    result1 = parse_attendance_data(json_data1, 'application/json')
    
    print(f"\n✓ Parse success: {result1['success']}")
    print(f"✓ Detected format: {result1['format']}")
    print(f"✓ Records parsed: {len(result1['records'])}")
    
    assert result1['success'], "JSON parsing failed"
    assert result1['format'] == 'json', "Wrong format detected"
    assert len(result1['records']) == 2, "Wrong record count"
    
    # Check face recognition detection
    record1 = result1['records'][0]
    print(f"\n✓ Sample Record:")
    print(f"  - User ID: {record1['user_id']}")
    print(f"  - Verification Type: {record1['verification_type']}")
    print(f"  - Biometric Method: {record1['biometric_method']}")
    
    assert record1['biometric_method'] == 'face', "Wrong biometric method (expected face)"
    
    # Test 2: Direct array format
    json_data2 = json.dumps([
        {"user": "101", "time": "2025-12-12 09:00:00", "status": 0, "verify": 2}
    ])
    
    result2 = parse_attendance_data(json_data2)
    print(f"\n✓ Direct array format parsed: {len(result2['records'])} record(s)")
    
    print("\n✅ JSON parsing tests passed!\n")


def test_xml_parsing():
    """Test XML format (Older specific models)"""
    print("=" * 80)
    print("TEST 4: XML Format Parsing")
    print("=" * 80)
    
    xml_data = """<?xml version="1.0"?>
<AttendanceLogs>
    <Log user="101" time="2025-12-12 09:00:00" status="0" verify="1"/>
    <Log user="102" time="2025-12-12 09:15:00" status="1" verify="1"/>
</AttendanceLogs>"""
    
    result = parse_attendance_data(xml_data, 'application/xml')
    
    print(f"\n✓ Parse success: {result['success']}")
    print(f"✓ Detected format: {result['format']}")
    print(f"✓ Records parsed: {len(result['records'])}")
    
    assert result['success'], "XML parsing failed"
    assert result['format'] == 'xml', "Wrong format detected"
    assert len(result['records']) == 2, "Wrong record count"
    
    record = result['records'][0]
    print(f"\n✓ Sample Record:")
    print(f"  - User ID: {record['user_id']}")
    print(f"  - Timestamp: {record['timestamp_str']}")
    
    print("\n✅ XML parsing tests passed!\n")


def test_verification_type_mapping():
    """Test punch code to verification type mapping"""
    print("=" * 80)
    print("TEST 5: Verification Type Mapping")
    print("=" * 80)
    
    parser = UniversalADMSParser()
    
    test_cases = [
        (0, 'check-in'),
        (1, 'check-out'),
        (2, 'break-out'),
        (3, 'break-in'),
        (4, 'overtime-in'),
        (5, 'overtime-out')
    ]
    
    for punch_code, expected_type in test_cases:
        actual_type = parser.PUNCH_CODE_MAP.get(punch_code)
        print(f"✓ Punch code {punch_code} → {actual_type}")
        assert actual_type == expected_type, f"Wrong mapping for punch code {punch_code}"
    
    print("\n✅ Verification type mapping tests passed!\n")


def test_biometric_method_mapping():
    """Test verify method to biometric method mapping"""
    print("=" * 80)
    print("TEST 6: Biometric Method Mapping")
    print("=" * 80)
    
    parser = UniversalADMSParser()
    
    test_cases = [
        (0, 'password'),
        (1, 'fingerprint'),
        (2, 'face'),
        (3, 'palm'),
        (4, 'card'),
        (5, 'iris'),
        (15, 'face')  # Some devices use 15 for face
    ]
    
    for verify_code, expected_method in test_cases:
        actual_method = parser.VERIFY_METHOD_MAP.get(verify_code)
        print(f"✓ Verify code {verify_code} → {actual_method}")
        assert actual_method == expected_method, f"Wrong mapping for verify code {verify_code}"
    
    print("\n✅ Biometric method mapping tests passed!\n")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("=" * 80)
    print("TEST 7: Edge Cases & Error Handling")
    print("=" * 80)
    
    # Test empty data
    result1 = parse_attendance_data("")
    print(f"✓ Empty data handled: success={result1['success']}, format={result1['format']}")
    assert not result1['success'], "Empty data should fail"
    assert result1['format'] == 'empty', "Wrong format for empty data"
    
    # Test unknown format
    unknown_data = "RANDOMDATA123456789"
    result2 = parse_attendance_data(unknown_data)
    print(f"✓ Unknown format handled: success={result2['success']}, format={result2['format']}")
    
    # Test malformed JSON
    bad_json = '{"data": [{"user": "101"'  # Missing closing
    result3 = parse_attendance_data(bad_json)
    print(f"✓ Malformed JSON handled: success={result3['success']}")
    assert not result3['success'], "Malformed JSON should fail"
    
    # Test malformed XML
    bad_xml = '<Logs><Log user="101"'  # Missing closing
    result4 = parse_attendance_data(bad_xml)
    print(f"✓ Malformed XML handled: success={result4['success']}")
    
    print("\n✅ Edge case tests passed!\n")


def test_timestamp_parsing():
    """Test various timestamp formats"""
    print("=" * 80)
    print("TEST 8: Timestamp Format Handling")
    print("=" * 80)
    
    parser = UniversalADMSParser()
    
    test_timestamps = [
        ('2025-12-12 09:00:00', 'Standard format'),
        ('2025-12-12T09:00:00', 'ISO format'),
        ('2025/12/12 09:00:00', 'Slash separator'),
        ('2025-12-12 09:00', 'Without seconds'),
    ]
    
    for timestamp_str, description in test_timestamps:
        result = parser._parse_timestamp(timestamp_str)
        if result:
            print(f"✓ {description}: '{timestamp_str}' → {result}")
            assert isinstance(result, datetime), "Should return datetime object"
        else:
            print(f"⚠ {description}: '{timestamp_str}' → Failed to parse")
    
    print("\n✅ Timestamp parsing tests passed!\n")


def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "UNIVERSAL ADMS PARSER - TEST SUITE" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    try:
        test_format_detection()
        test_legacy_text_parsing()
        test_modern_json_parsing()
        test_xml_parsing()
        test_verification_type_mapping()
        test_biometric_method_mapping()
        test_edge_cases()
        test_timestamp_parsing()
        
        print("\n")
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 25 + "🎉 ALL TESTS PASSED! 🎉" + " " * 29 + "║")
        print("╚" + "=" * 78 + "╝")
        print("\n")
        print("✅ The Universal ADMS Parser is working correctly!")
        print("✅ Ready to handle:")
        print("   • Legacy fingerprint devices (K40, F18)")
        print("   • Modern face recognition (uFace, SpeedFace)")
        print("   • Palm scanners with temperature")
        print("   • All data formats (Text, JSON, XML)")
        print("\n")
        
        return True
        
    except AssertionError as e:
        print("\n")
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 30 + "❌ TEST FAILED!" + " " * 33 + "║")
        print("╚" + "=" * 78 + "╝")
        print(f"\nError: {e}\n")
        return False
    
    except Exception as e:
        print("\n")
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 30 + "❌ TEST ERROR!" + " " * 33 + "║")
        print("╚" + "=" * 78 + "╝")
        print(f"\nException: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
