"""
Test the availability API directly to see what data is being returned
"""

import requests
import json

def test_availability_api():
    # Test the availability endpoint
    url = "http://127.0.0.1:5500/api/hierarchical-timetable/assignments/availability"
    
    print("\n" + "="*80)
    print("TESTING AVAILABILITY API")
    print("="*80)
    print(f"\nRequesting: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                staff_list = data.get('staff', [])
                print(f"\nTotal staff returned: {len(staff_list)}")
                
                # Find Manjukumaran C
                for staff in staff_list:
                    if 'Manjukumaran' in staff.get('name', ''):
                        print("\n" + "="*80)
                        print(f"FOUND: {staff['name']} (ID: {staff['id']})")
                        print("="*80)
                        
                        availability = staff.get('availability', {})
                        
                        # Check Monday (day 1)
                        monday = availability.get('1', {})
                        assigned = monday.get('assigned', [])
                        free = monday.get('free', [])
                        
                        print(f"\nMonday assignments:")
                        print(f"  Assigned periods: {assigned} (Count: {len(assigned)})")
                        print(f"  Free periods: {free} (Count: {len(free)})")
                        
                        # Show all days
                        print(f"\nAll days availability:")
                        day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
                                   4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
                        for day_num in range(1, 7):
                            day_data = availability.get(str(day_num), {})
                            if day_data:
                                day_name = day_names.get(day_num, f'Day {day_num}')
                                assigned_day = day_data.get('assigned', [])
                                free_day = day_data.get('free', [])
                                if assigned_day:
                                    print(f"  {day_name}: Assigned {assigned_day}, Free {free_day}")
                        
                        break
                else:
                    print("\n⚠ Manjukumaran C not found in staff list")
                    print("\nAll staff found:")
                    for staff in staff_list[:10]:  # Show first 10
                        print(f"  - {staff.get('name')} (ID: {staff.get('id')})")
            else:
                print(f"\n✗ API returned error: {data.get('message')}")
        else:
            print(f"\n✗ HTTP Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to Flask server")
        print("  Make sure Flask is running on http://127.0.0.1:5500")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_availability_api()
