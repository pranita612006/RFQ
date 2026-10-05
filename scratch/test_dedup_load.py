import os
import sys

sys.path.insert(0, r"d:\N-RFQ")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.CostingBCCal.models import OfferSheetBOC

customer_id_str = "CUST-005"
item_id_int = 3052024

saved_qs = OfferSheetBOC.objects.filter(
    customer_id=customer_id_str,
    itemcreation_id=item_id_int,
    boc_type="Local",
).order_by("id")

print(f"Raw count in ztbl_offersheet_boc: {saved_qs.count()}")

local_boc = []
seen_parts = set()
for item in saved_qs:
    p_num = (item.part_number or "").strip()
    desc  = (item.description or "").strip()
    uom   = (item.unit_of_measure_code or "").strip()
    qty   = float(item.quantity or 0.0)

    key = (p_num.lower(), desc.lower(), uom.lower(), qty)
    if key in seen_parts:
        continue
    seen_parts.add(key)

    settle = float(item.settle_price or 0.0)
    cost = float(item.cost or round(qty * settle, 4))
    local_boc.append({
        "id":             item.id,
        "part_number":    p_num,
        "description":    desc,
        "uom_code":       uom,
        "quantity":       qty,
        "internal_rate":  float(item.internal_cost or 0.0),
        "settle_price":   settle,
        "cost":           cost,
    })

print(f"Deduplicated count: {len(local_boc)}")
for r in local_boc:
    print(f"  PN: {r['part_number']!r} | Desc: {r['description']!r} | Qty: {r['quantity']} | IR: {r['internal_rate']} | SP: {r['settle_price']}")
