import functools
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.http import JsonResponse
from .services import is_record_locked

def can_user_edit_record(user, instance):
    """
    Checks if a given user can edit the record instance.
    If the record is locked ('Sent for approval', 'Approved', etc.):
    - Admin / Superuser / Authorized users can edit or revert.
    - Standard users are denied edit access.
    """
    if not is_record_locked(instance):
        return True
        
    if user and user.is_authenticated:
        if user.is_superuser or user.is_staff or user.has_perm('BOM.can_edit_locked_record'):
            return True
            
    return False

def check_record_permission(user, instance):
    """
    Raises ValidationError if the record is locked and user lacks permission to edit.
    """
    if not can_user_edit_record(user, instance):
        status = getattr(instance, 'action_status', '') or getattr(instance, 'status', '')
        raise ValidationError(f"Action Blocked: Record is currently locked with status '{status}'. Edits are restricted for standard users.")

class LockPermissionMixin:
    """
    View / Form Mixin to enforce record locking permissions.
    """
    def check_object_lock(self, request, instance):
        if not can_user_edit_record(request.user, instance):
            raise PermissionDenied("You do not have permission to modify a record that is sent for approval or approved.")
