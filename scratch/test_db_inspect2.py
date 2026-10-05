import os
import sys
sys.path.insert(0, r"d:\N-RFQ")
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as cur:
    # Check sample customer and item in tbl_bomcreation_partselection
    cur.execute("""
        SELECT "Customer_ID", "ItemCreation_Id", "Part_Number", "Categorisation", "Quantity"
        FROM tbl_bomcreation_partselection
        WHERE UPPER("Categorisation") LIKE '%LOCAL%'
        LIMIT 5;
    """)
    print("Partselection sample:")
    for r in cur.fetchall():
        print(r)

    # Check ztbl_offersheet_boc
    cur.execute("""
        SELECT COUNT(*) FROM ztbl_offersheet_boc;
    """)
    print("ztbl_offersheet_boc count:", cur.fetchone()[0])

    # Check tbl_bom_partdetails_master
    cur.execute("""
        SELECT "Part No", "Cost_Price", "Rate", "Settle Price"
        FROM tbl_bom_partdetails_master
        WHERE "Part No" IN (
            SELECT "Part_Number" FROM tbl_bomcreation_partselection WHERE UPPER("Categorisation") LIKE '%LOCAL%' LIMIT 5
        );
    """)
    print("Master sample for local parts:")
    for r in cur.fetchall():
        print(r)
