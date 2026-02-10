#!/usr/bin/env python3
"""
Comprehensive test for Color-Coded Holiday Visual Indicators
Tests the visual distinction between different types of holidays
"""

import requests
import json
import datetime
from datetime import timedelta

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_ADMIN_EMAIL = "admin@test.com"
TEST_ADMIN_PASSWORD = "admin123"

class ColorCodedHolidayTester:
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
    
    def create_test_holiday(self, holiday_type, name, description="Test holiday"):
        """Create a test holiday of specified type"""
        print(f"\n🎄 Creating {holiday_type} holiday: {name}")
        
        if not self.csrf_token:
            print("❌ No CSRF token available")
            return None
        
        # Calculate dates (tomorrow to avoid conflicts)
        start_date = (datetime.date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = start_date
        
        form_data = {
            'csrf_token': self.csrf_token,
            'holiday_name': name,
            'start_date': start_date,
            'end_date': end_date,
            'holiday_type': holiday_type,
            'description': description,
            'is_recurring': 'false'
        }
        
        # Add departments for department-specific holidays
        if holiday_type == 'department_specific':
            form_data['departments'] = 'IT'  # Assuming IT department exists
        
        response = self.session.post(f"{BASE_URL}/api/holidays", data=form_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                holiday_id = data.get('holiday_id')
                print(f"✅ {holiday_type} holiday created with ID: {holiday_id}")
                return holiday_id
            else:
                print(f"❌ Failed to create holiday: {data.get('message')}")
        else:
            print(f"❌ Failed to create holiday: {response.status_code}")
        
        return None
    
    def test_holiday_calendar_page(self):
        """Test that holiday calendar page loads with color legend"""
        print("\n📅 Testing Holiday Calendar Page...")
        
        response = self.session.get(f"{BASE_URL}/admin/work_time_assignment")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for color legend elements
            legend_checks = [
                ('calendar-legend', 'Calendar legend container'),
                ('legend-color institution-wide', 'Institution-wide legend color'),
                ('legend-color department-specific', 'Department-specific legend color'),
                ('legend-color common-leave', 'Common leave legend color'),
                ('legend-color weekly-off', 'Weekly off legend color'),
                ('Institution-wide Holidays', 'Institution-wide legend text'),
                ('Department-specific Holidays', 'Department-specific legend text'),
                ('Common Leave Days', 'Common leave legend text'),
                ('Weekly Off Days', 'Weekly off legend text')
            ]
            
            results = []
            for check_item, description in legend_checks:
                found = check_item in page_content
                status = "✅" if found else "❌"
                print(f"{status} {description}: {'FOUND' if found else 'MISSING'}")
                results.append(found)
            
            # Check for CSS color styling
            css_checks = [
                ('linear-gradient(135deg, #28a745', 'Institution-wide green gradient'),
                ('linear-gradient(135deg, #fd7e14', 'Department-specific orange gradient'),
                ('linear-gradient(135deg, #6f42c1', 'Common leave blue/purple gradient'),
                ('linear-gradient(135deg, #6c757d', 'Weekly off gray gradient')
            ]
            
            for check_item, description in css_checks:
                found = check_item in page_content
                status = "✅" if found else "❌"
                print(f"{status} {description}: {'FOUND' if found else 'MISSING'}")
                results.append(found)
            
            return all(results)
        else:
            print(f"❌ Failed to load holiday calendar page: {response.status_code}")
            return False
    
    def test_holiday_management_page(self):
        """Test that holiday management page loads with color legend"""
        print("\n🎄 Testing Holiday Management Page...")
        
        response = self.session.get(f"{BASE_URL}/admin/holiday_management")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for enhanced color styling and legend
            checks = [
                ('calendar-legend', 'Calendar legend container'),
                ('eventDidMount', 'Enhanced tooltip functionality'),
                ('linear-gradient(135deg, #28a745', 'Institution-wide styling'),
                ('linear-gradient(135deg, #fd7e14', 'Department-specific styling'),
                ('linear-gradient(135deg, #6f42c1', 'Common leave styling'),
                ('Institution-wide Holiday (Green)', 'Enhanced tooltip text'),
                ('Department-specific Holiday (Orange)', 'Enhanced tooltip text'),
                ('Common Leave Day (Blue/Purple)', 'Enhanced tooltip text')
            ]
            
            results = []
            for check_item, description in checks:
                found = check_item in page_content
                status = "✅" if found else "❌"
                print(f"{status} {description}: {'FOUND' if found else 'MISSING'}")
                results.append(found)
            
            return all(results)
        else:
            print(f"❌ Failed to load holiday management page: {response.status_code}")
            return False
    
    def test_api_holiday_data(self):
        """Test that API returns holidays with proper type information"""
        print("\n📊 Testing Holiday API Data...")
        
        response = self.session.get(f"{BASE_URL}/api/holidays")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                holidays = data.get('holidays', [])
                print(f"✅ Found {len(holidays)} holidays")
                
                # Check for different holiday types
                types_found = set()
                for holiday in holidays:
                    holiday_type = holiday.get('holiday_type')
                    if holiday_type:
                        types_found.add(holiday_type)
                        print(f"  - {holiday.get('holiday_name', 'Unknown')} ({holiday_type})")
                
                expected_types = {'institution_wide', 'department_specific', 'common_leave'}
                found_expected = types_found.intersection(expected_types)
                
                print(f"✅ Holiday types found: {list(types_found)}")
                print(f"✅ Expected types found: {list(found_expected)}")
                
                return len(found_expected) > 0
            else:
                print(f"❌ API returned error: {data.get('message')}")
        else:
            print(f"❌ Failed to get holidays: {response.status_code}")
        
        return False
    
    def run_comprehensive_test(self):
        """Run all color-coded holiday functionality tests"""
        print("🎨 Starting Color-Coded Holiday Visual Indicators Test")
        print("=" * 65)
        
        try:
            # Step 1: Login
            self.login_admin()
            
            # Step 2: Create test holidays of different types
            print("\n" + "="*50)
            print("TEST 1: Creating Test Holidays")
            print("="*50)
            
            institution_holiday = self.create_test_holiday(
                'institution_wide', 
                'Test Institution Holiday',
                'Green gradient test holiday'
            )
            
            department_holiday = self.create_test_holiday(
                'department_specific',
                'Test Department Holiday', 
                'Orange gradient test holiday'
            )
            
            common_holiday = self.create_test_holiday(
                'common_leave',
                'Test Common Leave',
                'Blue/Purple gradient test holiday'
            )
            
            # Step 3: Test Holiday Calendar Page
            print("\n" + "="*50)
            print("TEST 2: Holiday Calendar Page Color Coding")
            print("="*50)
            calendar_success = self.test_holiday_calendar_page()
            
            # Step 4: Test Holiday Management Page
            print("\n" + "="*50)
            print("TEST 3: Holiday Management Page Color Coding")
            print("="*50)
            management_success = self.test_holiday_management_page()
            
            # Step 5: Test API Data
            print("\n" + "="*50)
            print("TEST 4: Holiday API Data Structure")
            print("="*50)
            api_success = self.test_api_holiday_data()
            
            # Summary
            print("\n" + "="*65)
            print("🎨 COLOR-CODED HOLIDAY TEST SUMMARY")
            print("="*65)
            print(f"✅ Admin Login: SUCCESS")
            print(f"{'✅' if institution_holiday else '❌'} Institution Holiday Creation: {'SUCCESS' if institution_holiday else 'FAILED'}")
            print(f"{'✅' if department_holiday else '❌'} Department Holiday Creation: {'SUCCESS' if department_holiday else 'FAILED'}")
            print(f"{'✅' if common_holiday else '❌'} Common Leave Creation: {'SUCCESS' if common_holiday else 'FAILED'}")
            print(f"{'✅' if calendar_success else '❌'} Calendar Page Color Coding: {'SUCCESS' if calendar_success else 'FAILED'}")
            print(f"{'✅' if management_success else '❌'} Management Page Color Coding: {'SUCCESS' if management_success else 'FAILED'}")
            print(f"{'✅' if api_success else '❌'} API Data Structure: {'SUCCESS' if api_success else 'FAILED'}")
            
            overall_success = all([
                institution_holiday is not None,
                department_holiday is not None, 
                common_holiday is not None,
                calendar_success,
                management_success,
                api_success
            ])
            
            print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
            
            if overall_success:
                print("\n🎨 Color-Coded Holiday Visual Indicators are working perfectly!")
                print("✅ Institution-wide holidays: Green gradient")
                print("✅ Department-specific holidays: Orange gradient") 
                print("✅ Common leave days: Blue/Purple gradient")
                print("✅ Weekly off days: Gray gradient")
                print("✅ Enhanced tooltips with color information")
                print("✅ Comprehensive legend with hover effects")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    tester = ColorCodedHolidayTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)
