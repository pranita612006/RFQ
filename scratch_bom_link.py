import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection
from apps.BOM.models import BOMHeader

def variants(item_id):
    v = [str(item_id).strip()]
    if v[0].isdigit():
        v.append(v[0].zfill(8))
        v.append(str(int(v[0])))
    return list(dict.fromkeys(x for x in v if x))

def resolve(item_id, bop_id="", customer_id="CUST-005"):
    vs = variants(item_id)
    print(f"\nResolve item={item_id} bop={bop_id} customer={customer_id} variants={vs}")
    with connection.cursor() as c:
        if bop_id:
            c.execute(
                "SELECT bomcreation_id, itemcreation_id FROM tbl_rfq_details "
                "WHERE bopcreation_id = %s AND customer_id = %s LIMIT 1",
                [bop_id, customer_id],
            )
            row = c.fetchone()
            print("  rfq by bop:", row)
        c.execute(
            "SELECT bomcreation_id, itemcreation_id FROM tbl_rfq_details "
            "WHERE customer_id = %s AND itemcreation_id = ANY(%s) LIMIT 1",
            [customer_id, vs],
        )
        print("  rfq by item:", c.fetchone())
    bom = BOMHeader.objects.filter(item_creation_id__in=vs, customer_id=customer_id).first()
    if not bom:
        bom = BOMHeader.objects.filter(item_creation_id__in=vs).first()
    print("  bomcreation:", bom.bom_creation_id if bom else None, bom.item_creation_id if bom else None)

resolve("10112008", "Bop_202210011", "CUST-005")
resolve("3052024", "Bop_202405221", "CUST-005")
resolve("03052024", "", "CUST-005")
