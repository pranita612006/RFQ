from datetime import date, datetime
import logging
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)

LOCKED_STATUSES = ["sent for approval", "send_approval", "pending_approval", "approved"]

def is_record_locked(instance):
    """
    Utility function to check whether a record is in a read-only / locked state.
    """
    if not instance:
        return False
    status = (getattr(instance, 'action_status', '') or getattr(instance, 'status', '') or '').strip().lower()
    return status in LOCKED_STATUSES

def process_send_approval(instance, user=None, transaction_model=None, transaction_fk_kwargs=None):
    """
    Dedicated service function to process "SendApproval" workflow.
    Validates state, prerequisites, child transactions, ECN history snapshots, and updates status.
    
    :param instance: The header record instance (e.g., BOMHeader, BOCHeader, BlanketSalesOrder).
    :param user: The Django User object performing the request.
    :param transaction_model: Optional child model class to verify parts/line items exist.
    :param transaction_fk_kwargs: Dictionary of kwargs to filter child model (e.g., {'bom_creation_id': instance.bom_creation_id}).
    :return: Updated instance after status change and audit stamping.
    """
    current_status = (getattr(instance, 'action_status', '') or getattr(instance, 'status', '') or '').strip()
    current_status_lower = current_status.lower()
    
    # 1. State Validation
    if current_status_lower == "approved":
        raise ValidationError("Action Blocked: Approved records cannot be sent for approval.")
        
    if current_status_lower in ["sent for approval", "send_approval", "pending_approval"]:
        raise ValidationError("Action Blocked: Record is already sent for approval.")
        
    # 2. Prerequisite Field Validation
    if hasattr(instance, 'item_creation_id') and not getattr(instance, 'item_creation_id', None):
        raise ValidationError("Action Blocked: Item Creation ID is required before sending for approval.")

    if hasattr(instance, 'customer_id') and not getattr(instance, 'customer_id', None):
        raise ValidationError("Action Blocked: Customer ID is required before sending for approval.")
        
    # 3. Child Object Existence Check
    if transaction_model and transaction_fk_kwargs:
        child_count = transaction_model.objects.filter(**transaction_fk_kwargs).count()
        if child_count == 0:
            raise ValidationError("Action Blocked: Cannot send for approval without any associated parts, items, or child transactions.")
            
    # 4. ECN Integration Check
    # Check if an ECN workflow applies (e.g., ECN_TYPE >= 1 or ECN_ID present)
    ecn_id = getattr(instance, 'ecn_id', None) or getattr(instance, 'last_ecn_no', None)
    ecn_type = getattr(instance, 'ecn_type', None)
    
    # Attempt lookup from linked ItemCardECN if available
    if not ecn_id and hasattr(instance, 'item_creation_id') and getattr(instance, 'item_creation_id', None):
        from .models import ItemCardECN
        item_ecn = ItemCardECN.objects.filter(no=instance.item_creation_id).first()
        if item_ecn:
            ecn_id = item_ecn.ecn_id
            ecn_type = item_ecn.ecn_type

    if ecn_id or (ecn_type is not None and str(ecn_type) not in ['', '0']):
        logger.info(f"[SendApproval] Validated ECN revision snapshot for record {getattr(instance, 'bom_creation_id', instance.pk)} (ECN ID: {ecn_id}, ECN Type: {ecn_type}).")
        # Ensure snapshot timestamp/user linking for ECN revision history
        if hasattr(instance, 'ecn_linked'):
            setattr(instance, 'ecn_linked', True)

    # 5. Status Transition & Audit Stamping
    if hasattr(instance, 'action_status'):
        instance.action_status = "Sent for approval"
    elif hasattr(instance, 'status'):
        instance.status = "Sent for approval"
        
    # Timestamp stamping
    now_date = date.today()
    if hasattr(instance, 'last_date_modified'):
        instance.last_date_modified = now_date
    if hasattr(instance, 'sent_for_approval_at'):
        instance.sent_for_approval_at = timezone.now()
        
    # User audit metadata stamping
    username = user.username if (user and hasattr(user, 'username')) else str(user or 'System')
    if hasattr(instance, 'sent_by'):
        setattr(instance, 'sent_by', username)
    if hasattr(instance, 'requested_by'):
        setattr(instance, 'requested_by', username)
    if hasattr(instance, 'last_modified_by'):
        setattr(instance, 'last_modified_by', username)
        
    logger.info(f"[SendApproval] Entity {instance.__class__.__name__} (PK: {instance.pk}) status set to 'Sent for approval' by user '{username}'.")
    
    instance.save()
    return instance

def check_bom_locked(bom_creation_id):
    """
    Checks if a BOM is locked (Sent for Approval, Approved).
    Raises ValidationError if it is locked.
    """
    if not bom_creation_id:
        return
        
    from .models import BOMHeader
    header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
    if not header:
        return
        
    if is_record_locked(header):
        raise ValidationError(f"Action Blocked: BOM Record '{bom_creation_id}' is locked (Status: {header.action_status}).")


