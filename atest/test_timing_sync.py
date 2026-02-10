#!/usr/bin/env python3
"""
Test script to verify institution timing synchronization
"""

import requests
import json
import time

def test_timing_sync():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing Institution Timing Synchronization")
    print("=" * 50)
    
    # Test 1: Get current timings
    print("\n1. Getting current institution timings...")
    try:
        response = requests.get(f"{base_url}/api/get_institution_timings")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"   ✅ Current check-in: {data['checkin_time']}")
                print(f"   ✅ Current check-out: {data['checkout_time']}")
            else:
                print(f"   ❌ API returned error: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 2: Test sync verification
    print("\n2. Testing timing synchronization status...")
    try:
        response = requests.get(f"{base_url}/api/test_timing_sync")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                sync_check = data['sync_check']
                print(f"   📊 Institution Check-in: {sync_check['institution_checkin']}")
                print(f"   📊 Institution Check-out: {sync_check['institution_checkout']}")
                print(f"   📊 Shift Manager Check-in: {sync_check['shift_manager_checkin']}")
                print(f"   📊 Shift Manager Check-out: {sync_check['shift_manager_checkout']}")
                print(f"   📊 Attendance Test: {sync_check['attendance_status_test']}")
                
                if sync_check['systems_synced']:
                    print("   ✅ All systems are synchronized!")
                else:
                    print("   ⚠️ Systems may not be fully synchronized")
            else:
                print(f"   ❌ Sync test failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test Complete")
    print("\nTo test timing updates:")
    print("1. Open the Work Time Assignment page in your browser")
    print("2. Log in as admin")
    print("3. Update the timings and save")
    print("4. Run this script again to see the synchronization")

if __name__ == "__main__":
    test_timing_sync()
