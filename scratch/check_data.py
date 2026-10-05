import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.CostingBCCal.services import fetch_boc_part_details
from apps.CostingBCCal.models import OfferSheetPartDetails
from django.db import connection

print("Checking OfferSheetPartDetails:")
try:
    print("OfferSheetPartDetails count:", OfferSheetPartDetails.objects.count())
    print("OfferSheetPartDetails rows for CUST-005:", list(OfferSheetPartDetails.objects.filter(customer_id="CUST-005")))
except Exception as e:
    print("OfferSheetPartDetails error:", e)

print("\nChecking fetch_boc_part_details for CUST-005 / 3052024:")
try:
    res_local = fetch_boc_part_details("CUST-005", "3052024", "LOCAL BOC")
    print(f"fetch_boc_part_details LOCAL BOC count: {len(res_local)}")
    for r in res_local[:5]:
        print(" ", r)
except Exception as e:
    print("fetch_boc_part_details error:", e)

print("\nChecking tables in DB directly:")
with connection.cursor() as cur:
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name ILIKE '%offersheetpartdetails%'")
    print("tables matching offersheetpartdetails:", cur.fetchall())
    cur.execute("SELECT count(*) FROM tbl_bomcreation_partselection WHERE LOWER(customer_id) = 'cust-005'")
    print("tbl_bomcreation_partselection rows for cust-005:", cur.fetchall())
