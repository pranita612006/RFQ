import os
import sys

sys.path.insert(0, r"d:\N-RFQ")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from apps.CostingBCCal.services import fetch_local_boc_part_details
from apps.customer_creation.models import CustomerInfo
from apps.item_creation.models import ItemCard

print("Testing fetch_local_boc_part_details...")
cust_id = CustomerInfo.objects.values_list("customer_id", flat=True).first() or "C001"
item_id = ItemCard.objects.values_list("no", flat=True).first() or "I001"

print(f"Sample Customer ID: {cust_id}, Item Creation ID: {item_id}")

records = fetch_local_boc_part_details(cust_id, item_id)
print(f"Resulting LOCAL BOC records count: {len(records)}")
for r in records[:5]:
    print(r)
