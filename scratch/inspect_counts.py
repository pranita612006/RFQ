import os
import sys

sys.path.insert(0, r"d:\N-RFQ")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import connection

customer_id = "CUST-005"
item_creation_id = "3052024"

with connection.cursor() as cur:
    # 1. Count in tbl_OfferSheetPartDetails
    try:
        cur.execute("""
            SELECT COUNT(*) FROM tbl_OfferSheetPartDetails 
            WHERE LOWER("Customer_ID") = LOWER(%s) AND LOWER("ItemCreation_Id") = LOWER(%s) AND UPPER("Categorisation") = 'LOCAL BOC'
        """, [customer_id, item_creation_id])
        print(f"tbl_OfferSheetPartDetails count: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"tbl_OfferSheetPartDetails query error: {e}")

    # 2. Count in tbl_bomcreation_partselection
    try:
        cur.execute("""
            SELECT COUNT(*) 
            FROM tbl_bomcreation_partselection ps
            JOIN tbl_bomcreation bc ON ps."BOMCreation_ID" = bc."BOMCreation_Id"
            WHERE LOWER(bc."Customer_ID") = LOWER(%s) AND LOWER(bc."ItemCreation_Id") = LOWER(%s) AND UPPER(ps."Categorisation") = 'LOCAL BOC'
        """, [customer_id, item_creation_id])
        print(f"tbl_bomcreation_partselection count (without pdm join): {cur.fetchone()[0]}")
    except Exception as e:
        print(f"tbl_bomcreation_partselection query error: {e}")

    # 3. Count in ztbl_offersheet_boc
    try:
        cur.execute("""
            SELECT COUNT(*) FROM ztbl_offersheet_boc 
            WHERE LOWER(customer_id) = LOWER(%s) AND LOWER(CAST(itemcreation_id AS text)) = LOWER(%s) AND UPPER(boc_type) = 'LOCAL'
        """, [customer_id, item_creation_id])
        print(f"ztbl_offersheet_boc count: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"ztbl_offersheet_boc query error: {e}")
