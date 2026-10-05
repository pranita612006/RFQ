import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.urls import resolve, reverse
from django.test import RequestFactory
from apps.CostingBCCal.views import get_boc_tab_data, save_local_boc_data
import json

print("Testing URL reverse and resolve...")
url_get = reverse("get_boc_tab_data")
url_save = reverse("save_local_boc_data")
print("get_boc_tab_data URL:", url_get)
print("save_local_boc_data URL:", url_save)

rf = RequestFactory()

# 1. Test get_boc_tab_data with missing params
req1 = rf.get("/CostingBCCal/boc/tab-data/")
resp1 = get_boc_tab_data(req1)
print("Missing params status:", resp1.status_code, resp1.content.decode('utf-8'))
assert resp1.status_code == 400

# 2. Test get_boc_tab_data with sample params
req2 = rf.get("/CostingBCCal/boc/tab-data/?customer_id=999999&item_creation_id=888888")
resp2 = get_boc_tab_data(req2)
print("Sample params status:", resp2.status_code, resp2.content.decode('utf-8'))
assert resp2.status_code == 200
data2 = json.loads(resp2.content.decode('utf-8'))
assert data2["status"] == "success"
assert "local_boc" in data2

# 3. Test save_local_boc_data validation with missing params
req3 = rf.post("/CostingBCCal/boc/save-local-boc-data/", data=json.dumps({}), content_type="application/json")
resp3 = save_local_boc_data(req3)
print("Save missing params status:", resp3.status_code, resp3.content.decode('utf-8'))
assert resp3.status_code == 400

print("All URL and view tests passed!")
