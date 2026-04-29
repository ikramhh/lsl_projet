"""
Django management command to setup user groups and roles
Usage: python manage.py setup_groups
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Setup user groups (Admin, User) with appropriate permissions'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🔧 Setting up user groups and permissions...'))
        
        # Create Admin group
        admin_group, created = Group.objects.get_or_create(name='Admin')
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created "Admin" group'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  "Admin" group already exists'))
        
        # Create User group
        user_group, created = Group.objects.get_or_create(name='User')
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created "User" group'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  "User" group already exists'))
        
        # Assign permissions to Admin group (all permissions)
        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(self.style.SUCCESS(f'✅ Assigned {admin_permissions.count()} permissions to Admin group'))
        
        # Assign basic permissions to User group (view and change their own data)
        user_permissions = Permission.objects.filter(
            codename__in=[
                'view_translation',
                'add_translation',
                'change_translation',
                'view_history',
                'add_history',
                'change_history',
            ]
        )
        user_group.permissions.set(user_permissions)
        self.stdout.write(self.style.SUCCESS(f'✅ Assigned {user_permissions.count()} permissions to User group'))
        
        # Assign first superuser to Admin group
        superusers = User.objects.filter(is_superuser=True)
        if superusers.exists():
            for superuser in superusers:
                superuser.groups.add(admin_group)
                self.stdout.write(self.style.SUCCESS(f'✅ Added superuser "{superuser.username}" to Admin group'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 GROUP SETUP SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'👑 Admin group: {admin_group.user_set.count()} users')
        self.stdout.write(f'👤 User group: {user_group.user_set.count()} users')
        self.stdout.write('='*60)
        self.stdout.write('\n💡 To add users to groups:')
        self.stdout.write('   python manage.py shell')
        self.stdout.write('   >>> from django.contrib.auth.models import User, Group')
        self.stdout.write('   >>> user = User.objects.get(username="your_username")')
        self.stdout.write('   >>> admin_group = Group.objects.get(name="Admin")')
        self.stdout.write('   >>> user.groups.add(admin_group)')
        self.stdout.write('='*60 + '\n')
