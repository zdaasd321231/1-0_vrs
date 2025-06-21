import requests
import unittest
import time
import json
import sys
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://3d99d134-9e1a-456a-a667-5f664942b8da.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class VNCAPITester:
    def __init__(self, base_url=API_URL):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_sessions = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.text else {}
                except json.JSONDecodeError:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_hello_world(self):
        """Test the root endpoint"""
        success, response = self.run_test(
            "Hello World API",
            "GET",
            "",
            200
        )
        if success:
            print(f"Response: {response}")
        return success

    def test_create_vnc_session(self, display_id=1, geometry="1024x768"):
        """Create a VNC session"""
        success, response = self.run_test(
            f"Create VNC Session (Display:{display_id}, Geometry:{geometry})",
            "POST",
            "vnc/sessions",
            200,
            data={"display_id": display_id, "geometry": geometry}
        )
        if success and 'id' in response:
            self.created_sessions.append(response['id'])
            print(f"Created VNC session with ID: {response['id']}")
            print(f"Session details: Display ID: {response['display_id']}, Port: {response['port']}, WebSocket Port: {response['websocket_port']}")
            return response['id']
        return None

    def test_get_vnc_sessions(self):
        """Get all VNC sessions"""
        success, response = self.run_test(
            "Get All VNC Sessions",
            "GET",
            "vnc/sessions",
            200
        )
        if success:
            print(f"Found {len(response)} VNC sessions")
            for session in response:
                print(f"Session ID: {session['id']}, Display: {session['display_id']}, Status: {session['status']}")
        return success

    def test_get_vnc_session(self, session_id):
        """Get a specific VNC session"""
        success, response = self.run_test(
            f"Get VNC Session (ID: {session_id})",
            "GET",
            f"vnc/sessions/{session_id}",
            200
        )
        if success:
            print(f"Session details: {response}")
        return success

    def test_get_vnc_connection_info(self, session_id):
        """Get VNC connection info"""
        success, response = self.run_test(
            f"Get VNC Connection Info (ID: {session_id})",
            "GET",
            f"vnc/connect/{session_id}",
            200
        )
        if success:
            print(f"VNC URL: {response.get('vnc_url')}")
            print(f"WebSocket URL: {response.get('websocket_url')}")
            print(f"noVNC URL: {response.get('novnc_url')}")
            print(f"Password: {response.get('password')}")
        return success

    def test_delete_vnc_session(self, session_id):
        """Delete a VNC session"""
        success, response = self.run_test(
            f"Delete VNC Session (ID: {session_id})",
            "DELETE",
            f"vnc/sessions/{session_id}",
            200
        )
        if success:
            print(f"Session deleted: {response.get('message', '')}")
            if session_id in self.created_sessions:
                self.created_sessions.remove(session_id)
        return success

    def cleanup(self):
        """Clean up any created sessions"""
        print("\n🧹 Cleaning up test sessions...")
        for session_id in self.created_sessions[:]:
            self.test_delete_vnc_session(session_id)

def main():
    tester = VNCAPITester()
    
    # Test Hello World API
    tester.test_hello_world()
    
    # Test getting VNC sessions (initial state)
    tester.test_get_vnc_sessions()
    
    # Test creating VNC sessions with different configurations
    session_id1 = tester.test_create_vnc_session(display_id=1, geometry="1024x768")
    session_id2 = tester.test_create_vnc_session(display_id=2, geometry="1280x720")
    
    # Test getting all sessions after creation
    tester.test_get_vnc_sessions()
    
    # Test getting specific session details
    if session_id1:
        tester.test_get_vnc_session(session_id1)
    
    # Test getting connection info
    if session_id1:
        tester.test_get_vnc_connection_info(session_id1)
    
    # Test deleting a session
    if session_id2:
        tester.test_delete_vnc_session(session_id2)
    
    # Test getting sessions after deletion
    tester.test_get_vnc_sessions()
    
    # Clean up any remaining sessions
    tester.cleanup()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())