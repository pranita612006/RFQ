import os
import sys
import json
import traceback

sys.path.insert(0, r"d:\N-RFQ")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import RequestFactory
from apps.CostingBCCal.views import save_local_boc_data

factory = RequestFactory()
payload = {
    "customer_id": "CUST-005",
    "item_creation_id": 3052024,
    "rows": [
        {
            "id": 1,
            "part_number": "12X9 PA12 HIPHL",
            "description": "BLACK TUBE",
            "uom_code": "MTR",
            "quantity": 1.56,
            "internal_rate": 23.89,
            "settle_price": 22.33
        }
    ]
}

req = factory.post(
    '/CostingBCCal/save-local-boc/',
    data=json.dumps(payload),
    content_type='application/json'
)

try:
    resp = save_local_boc_data(req)
    print("STATUS CODE:", resp.status_code)
    print("CONTENT:", resp.content.decode('utf-8'))
except Exception as e:
    print("EXCEPTION CAUGHT:")
    traceback.print_exc()
