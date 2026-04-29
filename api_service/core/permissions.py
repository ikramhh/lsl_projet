"""
Custom permissions for role-based access control using Django's built-in permission system
"""
from rest_framework import permissions
from django.contrib.auth.models import Group


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    Admin users are members of the 'Admin' group.
    """
    message = "Admin privileges required."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is in Admin group
        return request.user.groups.filter(name='Admin').exists()


class HasModelPermission(permissions.BasePermission):
    """
    Custom permission that checks Django's built-in model permissions.
    Uses auth_permission table for proper permission checking.
    """
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins have full access to everything
        if request.user.groups.filter(name='Admin').exists():
            return True
        
        # Check specific permissions based on request method
        model = getattr(view, 'model_class', None)
        if not model:
            # If no model class specified, allow (will be checked at object level)
            return True
        
        # Map HTTP methods to Django permission codenames
        permission_map = {
            'GET': 'view',
            'POST': 'add',
            'PUT': 'change',
            'PATCH': 'change',
            'DELETE': 'delete'
        }
        
        action = permission_map.get(request.method)
        if not action:
            return False
        
        # Check if user has the specific permission
        perm_codename = f'{action}_{model._meta.model_name}'
        return request.user.has_perm(f'core.{perm_codename}')
    
    def has_object_permission(self, request, view, obj):
        # Admins can access everything
        if request.user.groups.filter(name='Admin').exists():
            return True
        
        # For GET requests, check view permission + ownership
        if request.method == 'GET':
            if not request.user.has_perm('core.view_translation') and \
               not request.user.has_perm('core.view_history'):
                return False
            # Users can only view their own objects
            if hasattr(obj, 'user'):
                return obj.user == request.user
        
        # For POST (create), ownership is set automatically
        if request.method == 'POST':
            return True
        
        # For PUT/PATCH/DELETE, check change/delete permission + ownership
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # Regular users should NOT have change/delete permissions
            # This is enforced by the permission system
            if hasattr(obj, 'user'):
                return obj.user == request.user
        
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins.
    Enhanced with Django's built-in permission checks.
    - Admins can access all objects
    - Regular users can only access their own objects
    - Users WITHOUT change/delete permissions cannot modify/delete
    """
    message = "You can only access your own data."
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins have full access
        if request.user.groups.filter(name='Admin').exists():
            return True
        
        # For destructive operations, check if user has permission
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # Get the model from the view's queryset
            model = view.queryset.model if hasattr(view, 'queryset') else None
            if model:
                action = 'change' if request.method in ['PUT', 'PATCH'] else 'delete'
                perm_codename = f'{action}_{model._meta.model_name}'
                
                # If user doesn't have the permission, deny immediately
                if not request.user.has_perm(f'core.{perm_codename}'):
                    return False
        
        # Regular users can access list/create
        return True
    
    def has_object_permission(self, request, view, obj):
        # Admins can access everything
        if request.user.groups.filter(name='Admin').exists():
            return True
        
        # Check ownership based on model
        # For History and Translation models
        if hasattr(obj, 'user'):
            # For GET requests, check if user owns the object
            if request.method == 'GET':
                return obj.user == request.user
            
            # For PUT/PATCH/DELETE, users should not have these permissions
            # But double-check ownership anyway
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                # This should never be reached if has_permission works correctly
                # But as an extra safety measure:
                return False
        
        # Fallback: deny access
        return False


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object.
    Enhanced with Django's built-in permission checks.
    """
    message = "You can only access your own data."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For destructive operations, check permissions
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            model = view.queryset.model if hasattr(view, 'queryset') else None
            if model:
                action = 'change' if request.method in ['PUT', 'PATCH'] else 'delete'
                perm_codename = f'{action}_{model._meta.model_name}'
                
                if not request.user.has_perm(f'core.{perm_codename}'):
                    return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Check ownership
        if hasattr(obj, 'user'):
            # For GET - allow if owner
            if request.method == 'GET':
                return obj.user == request.user
            
            # For PUT/PATCH/DELETE - deny (users don't have these permissions)
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                return False
        
        return False
