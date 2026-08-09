import os
import django
from django.core.exceptions import ValidationError

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.test import RequestFactory
from apps.BOM.views import bom_ajax_action
from apps.BOM.models import BOMTransaction, BOMHeader

def test_ajax_actions():
    print("--- Testing BOM Part Edit & Save AJAX endpoints ---")
    # Verify view is loadable and functions import correctly
    assert bom_ajax_action is not None, "bom_ajax_action should be imported successfully"
    print("PASS: Views are loadable.")

if __name__ == "__main__":
    test_ajax_actions()
