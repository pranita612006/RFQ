import os
import sys

sys.path.insert(0, r"d:\N-RFQ")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.CostingBCCal.models import OfferSheetPartDetails, OfferSheetBOC
from apps.CostingBCCal.services import fetch_boc_part_details

customer_id = "CUST-005"
item_creation_id = 3052024

print("=== 1. fetch_boc_part_details (service function) ===")
service_rows = fetch_boc_part_details(customer_id, str(item_creation_id), "LOCAL BOC")
print(f"Total service rows: {len(service_rows)}")
for r in service_rows:
    print(f"  PN: {r.get('part_number')!r} | Qty: {r.get('quantity')} | IR: {r.get('internal_cost')} | SP: {r.get('settle_price')}")

print("\n=== 2. OfferSheetPartDetails ORM query ===")
orm_qs = OfferSheetPartDetails.objects.filter(
    categorisation__iexact="LOCAL BOC",
    customer_id=customer_id,
    itemcreation_id=item_creation_id,
)
print(f"Total ORM rows: {orm_qs.count()}")
for item in orm_qs:
    print(f"  ID: {item.id} | PN: {item.part_number!r} | Qty: {item.quantity} | IR: {item.internal_cost} | SP: {item.settle_price}")

print("\n=== 3. OfferSheetBOC ORM query ===")
boc_qs = OfferSheetBOC.objects.filter(
    customer_id=customer_id,
    itemcreation_id=item_creation_id,
    boc_type="Local",
)
print(f"Total OfferSheetBOC rows: {boc_qs.count()}")
for item in boc_qs:
    print(f"  ID: {item.id} | PN: {item.part_number!r} | Qty: {item.quantity} | IR: {item.internal_cost} | SP: {item.settle_price}")
