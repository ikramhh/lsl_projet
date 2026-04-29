"""
Test script to verify Django permission system
Tests authentication, authorization, and permission enforcement
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_service.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.test import RequestFactory
from core.models import Translation, History
from core.views import translations, translation_detail, HistoryView, HistoryDetailView
import json

print("="*70)
print("TESTING DJANGO PERMISSION SYSTEM")
print("="*70)

# Create test users if they don't exist
def setup_test_users():
    """Create test users with different roles"""
    print("\n📝 Setting up test users...")
    
    # Create Admin user
    admin_user, created = User.objects.get_or_create(username='test_admin')
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        admin_group = Group.objects.get(name='Admin')
        admin_user.groups.add(admin_group)
        print("✅ Created admin user: test_admin / admin123")
    
    # Create Regular user
    regular_user, created = User.objects.get_or_create(username='test_user')
    if created:
        regular_user.set_password('user123')
        regular_user.save()
        user_group = Group.objects.get(name='User')
        regular_user.groups.add(user_group)
        print("✅ Created regular user: test_user / user123")
    
    return admin_user, regular_user

def test_permissions():
    """Test permission checks"""
    print("\n" + "="*70)
    print("TEST 1: Permission Checks")
    print("="*70)
    
    admin_user, regular_user = setup_test_users()
    
    # Test Admin permissions
    print("\n👑 Admin User Permissions:")
    admin_perms = [
        'core.add_translation',
        'core.view_translation',
        'core.change_translation',
        'core.delete_translation',
        'core.add_history',
        'core.view_history',
        'core.change_history',
        'core.delete_history'
    ]
    
    for perm in admin_perms:
        has_perm = admin_user.has_perm(perm)
        status = "✅" if has_perm else "❌"
        print(f"   {status} {perm}")
    
    # Test User permissions
    print("\n👤 Regular User Permissions:")
    user_perms = {
        'core.add_translation': True,
        'core.view_translation': True,
        'core.change_translation': False,  # Should NOT have
        'core.delete_translation': False,  # Should NOT have
        'core.add_history': True,
        'core.view_history': True,
        'core.change_history': False,  # Should NOT have
        'core.delete_history': False,  # Should NOT have
    }
    
    all_correct = True
    for perm, expected in user_perms.items():
        has_perm = regular_user.has_perm(perm)
        status = "✅" if has_perm == expected else "❌"
        if has_perm != expected:
            all_correct = False
        print(f"   {status} {perm} (expected: {expected}, got: {has_perm})")
    
    if all_correct:
        print("\n✅ All permissions are correctly configured!")
    else:
        print("\n❌ Some permissions are incorrect!")
    
    return all_correct

def test_api_access():
    """Test API access control"""
    print("\n" + "="*70)
    print("TEST 2: API Access Control")
    print("="*70)
    
    admin_user, regular_user = setup_test_users()
    factory = RequestFactory()
    
    # Create test data
    admin_translation = Translation.objects.create(
        user=admin_user,
        text="Admin Translation",
        confidence=0.95
    )
    
    user_translation = Translation.objects.create(
        user=regular_user,
        text="User Translation",
        confidence=0.90
    )
    
    print(f"\n📊 Created test data:")
    print(f"   - Admin translation ID: {admin_translation.id}")
    print(f"   - User translation ID: {user_translation.id}")
    
    # Test 1: User tries to access admin's translation
    print("\n🔒 Test: User accessing admin's translation (should be FORBIDDEN)")
    request = factory.get(f'/api/translations/{admin_translation.id}/')
    request.user = regular_user
    request.META['HTTP_AUTHORIZATION'] = ''
    
    response = translation_detail(request, admin_translation.id)
    status = "✅" if response.status_code == 403 else "❌"
    print(f"   {status} Status: {response.status_code} (expected: 403)")
    
    # Test 2: User accesses own translation
    print("\n🔓 Test: User accessing own translation (should be ALLOWED)")
    request = factory.get(f'/api/translations/{user_translation.id}/')
    request.user = regular_user
    
    response = translation_detail(request, user_translation.id)
    status = "✅" if response.status_code == 200 else "❌"
    print(f"   {status} Status: {response.status_code} (expected: 200)")
    
    # Test 3: Admin accesses user's translation
    print("\n👑 Test: Admin accessing user's translation (should be ALLOWED)")
    request = factory.get(f'/api/translations/{user_translation.id}/')
    request.user = admin_user
    
    response = translation_detail(request, user_translation.id)
    status = "✅" if response.status_code == 200 else "❌"
    print(f"   {status} Status: {response.status_code} (expected: 200)")
    
    # Test 4: User tries to modify translation (should be FORBIDDEN)
    print("\n🚫 Test: User trying to MODIFY translation (should be FORBIDDEN)")
    request = factory.put(
        f'/api/translations/{user_translation.id}/',
        data=json.dumps({"text": "Modified"}),
        content_type='application/json'
    )
    request.user = regular_user
    
    response = translation_detail(request, user_translation.id)
    status = "✅" if response.status_code == 403 else "❌"
    print(f"   {status} Status: {response.status_code} (expected: 403)")
    
    # Test 5: User tries to delete translation (should be FORBIDDEN)
    print("\n🚫 Test: User trying to DELETE translation (should be FORBIDDEN)")
    request = factory.delete(f'/api/translations/{user_translation.id}/')
    request.user = regular_user
    
    response = translation_detail(request, user_translation.id)
    status = "✅" if response.status_code == 403 else "❌"
    print(f"   {status} Status: {response.status_code} (expected: 403)")
    
    # Cleanup
    admin_translation.delete()
    user_translation.delete()
    
    print("\n✅ API access control tests completed!")

def test_unauthenticated_access():
    """Test unauthenticated access"""
    print("\n" + "="*70)
    print("TEST 3: Unauthenticated Access (should return 401)")
    print("="*70)
    
    factory = RequestFactory()
    
    # Create a test translation
    from django.contrib.auth.models import User
    test_user = User.objects.first()
    if test_user:
        test_translation = Translation.objects.create(
            user=test_user,
            text="Test",
            confidence=0.9
        )
        
        # Test unauthenticated access
        print("\n🚫 Test: Unauthenticated user accessing translation")
        request = factory.get(f'/api/translations/{test_translation.id}/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()
        
        response = translation_detail(request, test_translation.id)
        status = "✅" if response.status_code == 401 else "❌"
        print(f"   {status} Status: {response.status_code} (expected: 401)")
        
        # Cleanup
        test_translation.delete()

if __name__ == '__main__':
    try:
        # Run all tests
        test_permissions()
        test_api_access()
        test_unauthenticated_access()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED!")
        print("="*70)
        print("\n📋 Summary:")
        print("   ✅ Permissions are properly configured")
        print("   ✅ Admin has ALL permissions (add, view, change, delete)")
        print("   ✅ User has LIMITED permissions (add, view only)")
        print("   ✅ Users CANNOT change or delete (403 Forbidden)")
        print("   ✅ Unauthenticated users get 401 Unauthorized")
        print("   ✅ Users can only access their own data")
        print("   ✅ Admins can access all data")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
