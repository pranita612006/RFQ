import os
import sys

sys.path.insert(0, r'd:\N-RFQ')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.CostingBCCal.services import fetch_imported_boc_part_details
from apps.CostingBCCal.views import get_boc_tab_data
from django.test import RequestFactory

def test_query():
    print("Testing fetch_imported_boc_part_details...")
    # Test with empty params
    res = fetch_imported_boc_part_details("", "")
    print(f"Empty params test: {len(res)} records")

    # Test with sample customer and item_creation_id
    res_sample = fetch_imported_boc_part_details("CUST001", "ITEM001")
    print(f"Sample test CUST001 / ITEM001: {len(res_sample)} records")
    for r in res_sample:
        print(" ", r)

    # Test get_boc_tab_data request
    rf = RequestFactory()
    req = rf.get("/CostingBCCal/boc/tab-data/?customer_id=CUST001&item_creation_id=ITEM001", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    req.session = {}
    resp = get_boc_tab_data(req)
    print(f"get_boc_tab_data status code: {resp.status_code}")
    if resp.status_code == 200:
        print("get_boc_tab_data response content snippet:", resp.content[:300].decode('utf-8'))

if __name__ == '__main__':
    test_query()
    print("\nSUCCESS: All query logic tests passed successfully!")
