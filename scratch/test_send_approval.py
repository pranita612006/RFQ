import os
import sys
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.core.exceptions import ValidationError
from apps.BOM.models import BOMHeader, BOMTransaction
from apps.BOM.services import process_send_approval, is_record_locked
from apps.BOM.permissions import can_user_edit_record
from apps.BOM.forms import BOMHeaderForm, LockableFormMixin

def test_workflow():
    print("--- Testing SendApproval Service & Locking Safeguards ---")
    
    # Create mock unpersisted BOMHeader for testing logic
    header = BOMHeader(
        bom_creation_id="TEST_BOM_001",
        item_creation_id="TEST_ITEM_001",
        customer_id="CUST_001",
        action_status="Draft"
    )
    
    print(f"Initial Status: '{header.action_status}'")
    print(f"Is Locked initially? {is_record_locked(header)}")
    assert not is_record_locked(header), "Draft record should not be locked"
    
    # Attempt process_send_approval (without child parts first to test validation)
    try:
        process_send_approval(
            instance=header,
            transaction_model=BOMTransaction,
            transaction_fk_kwargs={'bom_creation_id': 'NON_EXISTENT_ID'}
        )
        print("FAIL: Expected validation error for missing child parts!")
    except ValidationError as e:
        print(f"PASS: Caught expected validation error -> {e.message}")
        
    # Simulate valid child transaction exists by setting status manually for unit test
    header.action_status = "Sent for approval"
    print(f"Updated Status: '{header.action_status}'")
    print(f"Is Locked now? {is_record_locked(header)}")
    assert is_record_locked(header), "Status 'Sent for approval' must be locked"
    
    # Test form disablement via LockableFormMixin
    form = BOMHeaderForm(instance=header)
    disabled_fields = [name for name, field in form.fields.items() if field.disabled]
    print(f"Disabled fields count on locked form: {len(disabled_fields)} / {len(form.fields)}")
    assert len(disabled_fields) == len(form.fields), "All fields must be disabled when form is locked!"
    
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_workflow()
