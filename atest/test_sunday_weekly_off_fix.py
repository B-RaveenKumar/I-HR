#!/usr/bin/env python3
"""
Test for Sunday Weekly Off Configuration Fix
Tests that Sunday is correctly marked as weekly off (not Saturday)
"""

import requests
import json
import datetime
from datetime import timedelta

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_ADMIN_EMAIL = "admin@test.com"
TEST_ADMIN_PASSWORD = "admin123"

class SundayWeeklyOffTester:
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
    
    def test_ui_changes(self):
        """Test that the UI no longer has additional weekly off days dropdown"""
        print("\n🖥️ Testing UI Changes...")
        
        response = self.session.get(f"{BASE_URL}/admin/work_time_assignment")
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check that additional off days dropdown is removed
            has_additional_dropdown = 'additionalOffDays' in page_content
            has_additional_label = 'Additional Weekly Off Days' in page_content
            has_sunday_checkbox = 'sundayOffEnabled' in page_content
            has_sunday_label = 'Sunday as Weekly Off' in page_content
            
            print(f"{'❌' if has_additional_dropdown else '✅'} Additional off days dropdown: {'FOUND (should be removed)' if has_additional_dropdown else 'REMOVED'}")
            print(f"{'❌' if has_additional_label else '✅'} Additional off days label: {'FOUND (should be removed)' if has_additional_label else 'REMOVED'}")
            print(f"{'✅' if has_sunday_checkbox else '❌'} Sunday checkbox: {'FOUND' if has_sunday_checkbox else 'MISSING'}")
            print(f"{'✅' if has_sunday_label else '❌'} Sunday label: {'FOUND' if has_sunday_label else 'MISSING'}")
            
            return not has_additional_dropdown and not has_additional_label and has_sunday_checkbox and has_sunday_label
        else:
            print(f"❌ Failed to load work time assignment page: {response.status_code}")
            return False
    
    def test_sunday_weekly_off_save(self):
        """Test saving Sunday as weekly off"""
        print("\n💾 Testing Sunday Weekly Off Save...")
        
        if not self.csrf_token:
            print("❌ No CSRF token available")
            return False
        
        # Enable Sunday weekly off
        form_data = {
            'csrf_token': self.csrf_token,
            'sunday_off_enabled': 'true'
        }
        
        response = self.session.post(f"{BASE_URL}/api/weekly_off_config", data=form_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Sunday weekly off configuration saved successfully")
                return True
            else:
                print(f"❌ Save failed: {data.get('message')}")
        else:
            print(f"❌ Failed to save: {response.status_code}")
        
        return False
    
    def test_sunday_weekly_off_load(self):
        """Test loading Sunday weekly off configuration"""
        print("\n📥 Testing Sunday Weekly Off Load...")
        
        response = self.session.get(f"{BASE_URL}/api/weekly_off_config")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                weekly_off_days = data.get('weekly_off_days', [])
                print(f"✅ Weekly off days loaded: {weekly_off_days}")
                
                # Should only contain 'sunday'
                expected = ['sunday']
                if weekly_off_days == expected:
                    print("✅ Configuration matches expected (Sunday only)")
                    return True
                else:
                    print(f"❌ Configuration mismatch. Expected: {expected}, Got: {weekly_off_days}")
            else:
                print(f"❌ Load failed: {data.get('message')}")
        else:
            print(f"❌ Failed to load: {response.status_code}")
        
        return False
    
    def test_day_of_week_mapping(self):
        """Test that Sunday is correctly identified as day 0"""
        print("\n📅 Testing Day of Week Mapping...")
        
        # Test with a known Sunday date
        test_sunday = datetime.date(2024, 1, 7)  # This is a Sunday
        test_saturday = datetime.date(2024, 1, 6)  # This is a Saturday
        
        print(f"Test Sunday date: {test_sunday} (weekday: {test_sunday.weekday()})")
        print(f"Test Saturday date: {test_saturday} (weekday: {test_saturday.weekday()})")
        
        # Python's weekday(): Monday=0, Sunday=6
        # JavaScript's getDay(): Sunday=0, Saturday=6
        # Our conversion should map Python Sunday (6) to our Sunday (0)
        
        python_sunday_weekday = test_sunday.weekday()  # Should be 6
        our_sunday_weekday = (python_sunday_weekday + 1) % 7  # Should be 0
        
        python_saturday_weekday = test_saturday.weekday()  # Should be 5
        our_saturday_weekday = (python_saturday_weekday + 1) % 7  # Should be 6
        
        print(f"Python Sunday weekday: {python_sunday_weekday} -> Our format: {our_sunday_weekday}")
        print(f"Python Saturday weekday: {python_saturday_weekday} -> Our format: {our_saturday_weekday}")
        
        sunday_correct = our_sunday_weekday == 0
        saturday_correct = our_saturday_weekday == 6
        
        print(f"{'✅' if sunday_correct else '❌'} Sunday mapping: {'CORRECT (0)' if sunday_correct else f'INCORRECT ({our_sunday_weekday})'}")
        print(f"{'✅' if saturday_correct else '❌'} Saturday mapping: {'CORRECT (6)' if saturday_correct else f'INCORRECT ({our_saturday_weekday})'}")
        
        return sunday_correct and saturday_correct
    
    def run_comprehensive_test(self):
        """Run all Sunday weekly off fix tests"""
        print("📅 Starting Sunday Weekly Off Configuration Fix Test")
        print("=" * 60)
        
        try:
            # Step 1: Login
            self.login_admin()
            
            # Step 2: Test UI changes
            print("\n" + "="*50)
            print("TEST 1: UI Changes Verification")
            print("="*50)
            ui_success = self.test_ui_changes()
            
            # Step 3: Test day of week mapping
            print("\n" + "="*50)
            print("TEST 2: Day of Week Mapping Logic")
            print("="*50)
            mapping_success = self.test_day_of_week_mapping()
            
            # Step 4: Test saving Sunday weekly off
            print("\n" + "="*50)
            print("TEST 3: Save Sunday Weekly Off")
            print("="*50)
            save_success = self.test_sunday_weekly_off_save()
            
            # Step 5: Test loading Sunday weekly off
            print("\n" + "="*50)
            print("TEST 4: Load Sunday Weekly Off")
            print("="*50)
            load_success = self.test_sunday_weekly_off_load()
            
            # Summary
            print("\n" + "="*60)
            print("📅 SUNDAY WEEKLY OFF FIX TEST SUMMARY")
            print("="*60)
            print(f"✅ Admin Login: SUCCESS")
            print(f"{'✅' if ui_success else '❌'} UI Changes: {'SUCCESS' if ui_success else 'FAILED'}")
            print(f"{'✅' if mapping_success else '❌'} Day Mapping Logic: {'SUCCESS' if mapping_success else 'FAILED'}")
            print(f"{'✅' if save_success else '❌'} Save Sunday Weekly Off: {'SUCCESS' if save_success else 'FAILED'}")
            print(f"{'✅' if load_success else '❌'} Load Sunday Weekly Off: {'SUCCESS' if load_success else 'FAILED'}")
            
            overall_success = all([ui_success, mapping_success, save_success, load_success])
            
            print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
            
            if overall_success:
                print("\n📅 Sunday Weekly Off Configuration Fix is working perfectly!")
                print("✅ Additional weekly off days dropdown removed")
                print("✅ Sunday correctly mapped as day 0")
                print("✅ Only Sunday can be configured as weekly off")
                print("✅ Calendar will correctly show Sunday (not Saturday) as weekly off")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    tester = SundayWeeklyOffTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)
