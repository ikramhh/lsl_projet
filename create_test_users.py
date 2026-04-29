"""
Script to create test users and setup authorization
Run this from auth_service directory
"""

import os
import sys
import django

# Setup Django - add auth_service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'auth_service'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from django.contrib.auth.models import User, Group

def create_test_users():
    print("="*60)
    print("👥 CREATING TEST USERS")
    print("="*60)
    
    # Get or create User group
    user_group, created = Group.objects.get_or_create(name='User')
    if created:
        print("✅ Created 'User' group")
    else:
        print("✅ 'User' group already exists")
    
    # Get Admin group
    admin_group, created = Group.objects.get_or_create(name='Admin')
    if created:
        print("✅ Created 'Admin' group")
    else:
        print("✅ 'Admin' group already exists")
    
    # Create test users
    test_users = [
        {
            'username': 'testuser1',
            'password': 'test123',
            'email': 'testuser1@example.com',
            'first_name': 'Test',
            'last_name': 'User1'
        },
        {
            'username': 'testuser2',
            'password': 'test123',
            'email': 'testuser2@example.com',
            'first_name': 'Test',
            'last_name': 'User2'
        },
        {
            'username': 'demouser',
            'password': 'demo123',
            'email': 'demo@example.com',
            'first_name': 'Demo',
            'last_name': 'User'
        }
    ]
    
    print("\n📝 Creating users...")
    for user_data in test_users:
        username = user_data['username']
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"⚠️  User '{username}' already exists, skipping...")
            user = User.objects.get(username=username)
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                password=user_data['password'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            print(f"✅ Created user: {username}")
        
        # Add to User group
        user.groups.add(user_group)
        print(f"   └─ Added to 'User' group")
    
    # Make sure superuser is in Admin group
    superusers = User.objects.filter(is_superuser=True)
    for superuser in superusers:
        superuser.groups.add(admin_group)
        print(f"\n👑 Added superuser '{superuser.username}' to 'Admin' group")
    
    # Summary
    print("\n" + "="*60)
    print("📊 USER SUMMARY")
    print("="*60)
    
    print(f"\n👑 Admin Group ({admin_group.user_set.count()} users):")
    for user in admin_group.user_set.all():
        print(f"   - {user.username} (superuser: {user.is_superuser})")
    
    print(f"\n👤 User Group ({user_group.user_set.count()} users):")
    for user in user_group.user_set.all():
        print(f"   - {user.username}")
    
    print("\n" + "="*60)
    print("🔐 LOGIN CREDENTIALS")
    print("="*60)
    print("\n👑 Admin:")
    print("   Username: kouki (or your superuser)")
    print("   Password: <your_superuser_password>")
    
    print("\n👤 Regular Users:")
    for user_data in test_users:
        print(f"   Username: {user_data['username']}")
        print(f"   Password: {user_data['password']}")
        print()
    
    print("="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\n💡 Next: Test the authorization with test_authorization.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    create_test_users()
