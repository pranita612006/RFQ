import os
import sys

sys.path.insert(0, r'd:\N-RFQ')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Mock openpyxl if missing in venv
try:
    import openpyxl
except ImportError:
    from unittest.mock import MagicMock
    sys.modules['openpyxl'] = MagicMock()
    sys.modules['openpyxl.styles'] = MagicMock()
    sys.modules['openpyxl.utils'] = MagicMock()

import django
from django.conf import settings

# Override DB to SQLite for instant local unit test
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': r'd:\N-RFQ\db.sqlite3',
    }
}

django.setup()

from apps.CostingBCCal.services import fetch_imported_boc_part_details
from apps.CostingBCCal.views import get_boc_tab_data
from django.test import RequestFactory

def test_query():
    print("Testing fetch_imported_boc_part_details...")
    # Test empty params
    res = fetch_imported_boc_part_details("", "")
    print(f"Empty params test: {len(res)} records")
    assert res == [], "Expected empty list for empty parameters"

    # Test sample customer and item_creation_id
    res_sample = fetch_imported_boc_part_details("CUST001", "ITEM001")
    print(f"Sample test CUST001 / ITEM001: {len(res_sample)} records")

    # Test get_boc_tab_data request
    rf = RequestFactory()
    req = rf.get("/CostingBCCal/boc/tab-data/?customer_id=CUST001&item_creation_id=ITEM001", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    req.session = {}
    resp = get_boc_tab_data(req)
    print(f"get_boc_tab_data status code: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    print("get_boc_tab_data response content snippet:", resp.content[:300].decode('utf-8'))

if __name__ == '__main__':
    test_query()
    print("\nSUCCESS: All query logic tests passed successfully!")
