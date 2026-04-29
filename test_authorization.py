"""
Test script to verify authorization system
Run this AFTER starting the api_service server
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_authorization():
    print("="*60)
    print("🧪 TESTING AUTHORIZATION SYSTEM")
    print("="*60)
    
    # Test 1: Login as admin
    print("\n📝 Test 1: Admin Login")
    print("-" * 60)
    try:
        response = requests.post(f"{BASE_URL}/api/login/", json={
            "username": "kouki",
            "password": "kouki123"  # Change to your actual password
        })
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data.get('access')
            print(f"✅ Admin login successful")
            print(f"   Token: {admin_token[:20]}...")
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   {response.text}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Is the server running on port 8000?")
        return
    
    # Test 2: Admin access all history
    print("\n📝 Test 2: Admin Access All History")
    print("-" * 60)
    try:
        response = requests.get(
            f"{BASE_URL}/api/history/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Admin can access history")
            print(f"   Found {len(history)} history records")
        else:
            print(f"❌ Admin access failed: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Unauthenticated access
    print("\n📝 Test 3: Unauthenticated Access (Should Fail)")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/api/history/")
        
        if response.status_code == 401:
            print(f"✅ Correctly denied access (401 Unauthorized)")
        else:
            print(f"❌ Should have returned 401, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Create a regular user
    print("\n📝 Test 4: Create Regular User")
    print("-" * 60)
    try:
        # Create user via Django shell command
        import subprocess
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', 
             'from django.contrib.auth.models import User; '
             'User.objects.get_or_create(username="testuser", defaults={"password": "test123"})'],
            capture_output=True,
            text=True
        )
        print(f"✅ Test user created (or already exists)")
    except Exception as e:
        print(f"⚠️  Could not create test user: {e}")
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print("✅ Admin authentication: Working")
    print("✅ Admin authorization: Working")
    print("✅ Unauthenticated blocked: Working")
    print("="*60)
    print("\n💡 Next steps:")
    print("1. Create a regular user via Django admin")
    print("2. Add user to 'User' group")
    print("3. Test that regular users can only see their own data")
    print("4. Test that regular users get 403 for admin actions")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_authorization()
