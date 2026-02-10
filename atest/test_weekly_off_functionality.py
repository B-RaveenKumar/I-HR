#!/usr/bin/env python3
"""
Comprehensive test for Weekly Off Configuration functionality
Tests the integration between Holiday Management system and staff calendars
"""

import requests
import json
import datetime
from datetime import timedelta

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_ADMIN_EMAIL = "admin@test.com"
TEST_ADMIN_PASSWORD = "admin123"

class WeeklyOffTester:
    def __init__(self):
        self.session = requests.Session()
        self.csrf_token = None
        
    def login_admin(self):
        """Login as admin to get session and CSRF token"""
        print("🔐 Logging in as admin...")
        
        # Get login page to extract CSRF token
        login_page = self.session.get(f"{BASE_URL}/login")
        if login_page.status_code != 200:
            raise Exception(f"Failed to access login page: {login_page.status_code}")
        
        # Extract CSRF token from login page
        import re
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
        if not csrf_match:
            raise Exception("CSRF token not found in login page")
        
        csrf_token = csrf_match.group(1)
        
        # Login with credentials
        login_data = {
            'email': TEST_ADMIN_EMAIL,
            'password': TEST_ADMIN_PASSWORD,
            'csrf_token': csrf_token
        }
        
        response = self.session.post(f"{BASE_URL}/login", data=login_data)
        if response.status_code != 200 or 'dashboard' not in response.url:
            raise Exception(f"Login failed: {response.status_code}")
        
        print("✅ Admin login successful")
        
        # Get CSRF token for API calls
        dashboard_page = self.session.get(f"{BASE_URL}/admin/dashboard")
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', dashboard_page.text)
        if csrf_match:
            self.csrf_token = csrf_match.group(1)
            print(f"✅ CSRF token obtained: {self.csrf_token[:10]}...")
        
    def test_get_weekly_off_config(self):
        """Test getting current weekly off configuration"""
        print("\n📅 Testing GET weekly off configuration...")
        
        response = self.session.get(f"{BASE_URL}/api/weekly_off_config")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                weekly_off_days = data.get('weekly_off_days', [])
                print(f"✅ Current weekly off days: {weekly_off_days}")
                return weekly_off_days
            else:
                print(f"❌ API returned error: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ Failed to get weekly off config: {response.status_code}")
        
        return []
    
    def test_save_weekly_off_config(self, sunday_off=True, additional_days=None):
        """Test saving weekly off configuration"""
        print(f"\n💾 Testing SAVE weekly off configuration...")
        print(f"Sunday Off: {sunday_off}, Additional Days: {additional_days or []}")
        
        if not self.csrf_token:
            print("❌ No CSRF token available")
            return False
        
        # Prepare form data
        form_data = {
            'csrf_token': self.csrf_token,
            'sunday_off_enabled': 'true' if sunday_off else 'false'
        }
        
        # Add additional off days
        if additional_days:
            for day in additional_days:
                form_data['additional_off_days'] = day
        
        response = self.session.post(f"{BASE_URL}/api/weekly_off_config", data=form_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Weekly off configuration saved: {data.get('message')}")
                return True
            else:
                print(f"❌ Save failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ Failed to save weekly off config: {response.status_code}")
        
        return False
    
    def test_weekly_off_calendar_integration(self):
        """Test that weekly off days appear in calendar"""
        print("\n📊 Testing weekly off calendar integration...")
        
        # Get current date range (this week)
        today = datetime.date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Test staff holidays API (which should include weekly off logic)
        response = self.session.get(
            f"{BASE_URL}/api/staff/holidays",
            params={
                'start_date': start_of_week.strftime('%Y-%m-%d'),
                'end_date': end_of_week.strftime('%Y-%m-%d'),
                'staff_id': 1  # Assuming staff ID 1 exists
            }
        )
        
        print(f"Staff holidays API Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                holidays = data.get('holidays', [])
                print(f"✅ Found {len(holidays)} holidays/events for this week")
                
                # Check for weekly off days
                weekly_off_events = [h for h in holidays if 'weekly' in h.get('holiday_name', '').lower()]
                print(f"📅 Weekly off events found: {len(weekly_off_events)}")
                
                for event in weekly_off_events:
                    print(f"  - {event.get('holiday_name')} on {event.get('start_date')}")
                
                return len(weekly_off_events) > 0
            else:
                print(f"❌ Staff holidays API error: {data.get('message')}")
        else:
            print(f"❌ Staff holidays API failed: {response.status_code}")
        
        return False
    
    def run_comprehensive_test(self):
        """Run all weekly off functionality tests"""
        print("🚀 Starting Weekly Off Configuration Comprehensive Test")
        print("=" * 60)
        
        try:
            # Step 1: Login
            self.login_admin()
            
            # Step 2: Get current configuration
            current_config = self.test_get_weekly_off_config()
            
            # Step 3: Test saving Sunday only
            print("\n" + "="*40)
            print("TEST 1: Sunday Only Configuration")
            print("="*40)
            success1 = self.test_save_weekly_off_config(sunday_off=True, additional_days=[])
            
            # Verify the save
            if success1:
                new_config = self.test_get_weekly_off_config()
                expected = ['sunday']
                if new_config == expected:
                    print("✅ Sunday-only configuration verified")
                else:
                    print(f"❌ Configuration mismatch. Expected: {expected}, Got: {new_config}")
            
            # Step 4: Test saving Sunday + Saturday
            print("\n" + "="*40)
            print("TEST 2: Sunday + Saturday Configuration")
            print("="*40)
            success2 = self.test_save_weekly_off_config(sunday_off=True, additional_days=['saturday'])
            
            # Verify the save
            if success2:
                new_config = self.test_get_weekly_off_config()
                expected = ['sunday', 'saturday']
                # Sort both lists for comparison
                if sorted(new_config) == sorted(expected):
                    print("✅ Sunday + Saturday configuration verified")
                else:
                    print(f"❌ Configuration mismatch. Expected: {sorted(expected)}, Got: {sorted(new_config)}")
            
            # Step 5: Test calendar integration
            print("\n" + "="*40)
            print("TEST 3: Calendar Integration")
            print("="*40)
            calendar_success = self.test_weekly_off_calendar_integration()
            
            # Summary
            print("\n" + "="*60)
            print("📊 TEST SUMMARY")
            print("="*60)
            print(f"✅ Admin Login: SUCCESS")
            print(f"{'✅' if current_config is not None else '❌'} Get Configuration: {'SUCCESS' if current_config is not None else 'FAILED'}")
            print(f"{'✅' if success1 else '❌'} Save Sunday Only: {'SUCCESS' if success1 else 'FAILED'}")
            print(f"{'✅' if success2 else '❌'} Save Sunday + Saturday: {'SUCCESS' if success2 else 'FAILED'}")
            print(f"{'✅' if calendar_success else '❌'} Calendar Integration: {'SUCCESS' if calendar_success else 'FAILED'}")
            
            overall_success = all([success1, success2, calendar_success])
            print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    tester = WeeklyOffTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)
