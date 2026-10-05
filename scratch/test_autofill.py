import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from apps.BlanketSales.views import get_item_customer_details, get_blanketso_details, get_bso_lines
import json

rf = RequestFactory()

# Test get_item_customer_details for item '1234567890'
req = rf.get('/BlanketSales/api/get_item_customer_details/?item_no=1234567890')
req.session = {'active_customer_id': 'CUST-001', 'active_customer_name': 'Albonair GMBH'}
req.has_active_customer = True
res = get_item_customer_details(req)
data = json.loads(res.content)
print("item '1234567890' line_defaults:")
print(" ", data.get('line_defaults'))

# Test selecting BSO_202110311 when item_no in query is 1234567890
req = rf.get('/BlanketSales/api/get_blanketso_details/?bso_creation_id=BSO_202110311&item_no=1234567890')
req.session = {'active_customer_id': 'CUST-001', 'active_customer_name': 'Albonair GMBH'}
req.has_active_customer = True
res = get_blanketso_details(req)
bso_det = json.loads(res.content)
print("\nBSO_202110311 with mismatched item_no=1234567890:")
print("  table_ids:", bso_det.get('table_ids'))
print("  item_creation_id:", bso_det.get('item_creation_id'))

# Test get_bso_lines with mismatched item_no
req = rf.get('/BlanketSales/api/get_bso_lines/?bso_creation_id=BSO_202110311&table_id=1&item_no=1234567890')
req.session = {'active_customer_id': 'CUST-001', 'active_customer_name': 'Albonair GMBH'}
req.has_active_customer = True
res = get_bso_lines(req)
lines_res = json.loads(res.content)
print("\nget_bso_lines with mismatched item_no=1234567890:")
print("  records found:", len(lines_res.get('records', [])))
for r in lines_res.get('records', []):
    print(" ", r['id_field'], r['line_no_field'], r['description'], r['table_id'])
