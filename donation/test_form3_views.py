#!/usr/bin/env python
import requests
import sys

def test_form3_views():
    base_url = "http://localhost:8000"
    
    print("=== Testing Form 3 Admin Views ===\n")
    
    # Test 1: Login as form3_admin
    print("1. Testing login...")
    session = requests.Session()
    
    # Get login page
    login_response = session.get(f"{base_url}/login/")
    if login_response.status_code != 200:
        print(f"❌ Login page not accessible: {login_response.status_code}")
        return False
    
    # Login
    login_data = {
        'username': 'form3_admin',
        'password': 'form3admin123'
    }
    login_response = session.post(f"{base_url}/login/", data=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    print("✅ Login successful")
    
    # Test 2: Access Form 3 dashboard
    print("\n2. Testing Form 3 dashboard...")
    dashboard_response = session.get(f"{base_url}/form3-admin/dashboard/")
    if dashboard_response.status_code != 200:
        print(f"❌ Dashboard not accessible: {dashboard_response.status_code}")
        return False
    
    # Check if the response contains the expected data
    content = dashboard_response.text
    if "91" in content or "Total Form 3 students" in content:
        print("✅ Dashboard accessible and shows student data")
    else:
        print("⚠️ Dashboard accessible but may not show correct data")
        print(f"Response preview: {content[:500]}...")
    
    # Test 3: Access Form 3 students page
    print("\n3. Testing Form 3 students page...")
    students_response = session.get(f"{base_url}/form3-admin/students/")
    if students_response.status_code != 200:
        print(f"❌ Students page not accessible: {students_response.status_code}")
        return False
    
    # Check if the response contains student data
    students_content = students_response.text
    if "91" in students_content or "students found" in students_content:
        print("✅ Students page accessible and shows student data")
    else:
        print("⚠️ Students page accessible but may not show correct data")
        print(f"Response preview: {students_content[:500]}...")
    
    print("\n=== Test Complete ===")
    return True

if __name__ == "__main__":
    try:
        test_form3_views()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
