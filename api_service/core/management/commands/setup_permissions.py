"""
Django management command to setup groups and permissions
Usage: python manage.py setup_permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Translation, History


class Command(BaseCommand):
    help = 'Setup groups and permissions for the application'

    def handle(self, *args, **kwargs):
        self.stdout.write('🔧 Setting up groups and permissions...')

        # Get content types for our models
        translation_content_type = ContentType.objects.get_for_model(Translation)
        history_content_type = ContentType.objects.get_for_model(History)

        # ========================================
        # Create Admin Group with ALL permissions
        # ========================================
        admin_group, created = Group.objects.get_or_create(name='Admin')
        
        # Get all permissions for Translation and History models
        permissions = Permission.objects.filter(
            content_type__in=[translation_content_type, history_content_type]
        )
        
        # Add all permissions to Admin group
        admin_group.permissions.set(permissions)
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created Admin group with ALL permissions'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Updated Admin group permissions'))

        # ========================================
        # Create User Group with LIMITED permissions
        # ========================================
        user_group, created = Group.objects.get_or_create(name='User')
        
        # Get only add and view permissions
        add_translation = Permission.objects.get(
            codename='add_translation',
            content_type=translation_content_type
        )
        view_translation = Permission.objects.get(
            codename='view_translation',
            content_type=translation_content_type
        )
        add_history = Permission.objects.get(
            codename='add_history',
            content_type=history_content_type
        )
        view_history = Permission.objects.get(
            codename='view_history',
            content_type=history_content_type
        )
        
        # Set permissions: ONLY add and view (NO change, NO delete)
        user_group.permissions.set([
            add_translation,
            view_translation,
            add_history,
            view_history
        ])
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created User group with ADD and VIEW permissions only'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Updated User group permissions'))

        # ========================================
        # Display permission summary
        # ========================================
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📋 PERMISSION SUMMARY')
        self.stdout.write('='*60)
        
        self.stdout.write(f'\n👑 Admin Group:')
        admin_perms = admin_group.permissions.all()
        for perm in admin_perms:
            self.stdout.write(f'   ✅ {perm.name} ({perm.codename})')
        
        self.stdout.write(f'\n👤 User Group:')
        user_perms = user_group.permissions.all()
        for perm in user_perms:
            self.stdout.write(f'   ✅ {perm.name} ({perm.codename})')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ Permission setup complete!'))
        self.stdout.write('='*60)
