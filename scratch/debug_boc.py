"""
Debug script: run with   python scratch/debug_boc.py
Checks what data exists for the given customer+item in the BOC-related tables.
"""
import os, sys, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection

CUSTOMER_ID      = "CUST-005"
ITEM_CREATION_ID = "3052024"

print("=" * 70)
print(f"Debugging BOC for customer={CUSTOMER_ID!r}  item={ITEM_CREATION_ID!r}")
print("=" * 70)

# ── 1. tbl_bomcreation ────────────────────────────────────────────────
print("\n[1] tbl_bomcreation rows:")
with connection.cursor() as cur:
    cur.execute("""
        SELECT "BOMCreation_Id", "Customer_ID", "ItemCreation_Id", "Remark", "Table_Id"
        FROM tbl_bomcreation
        WHERE LOWER("Customer_ID") = LOWER(%s)
          AND LOWER("ItemCreation_Id") = LOWER(%s)
        LIMIT 20
    """, [CUSTOMER_ID, ITEM_CREATION_ID])
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    if rows:
        print(f"  {cols}")
        for r in rows:
            print(f"  {r}")
    else:
        print("  *** NO ROWS FOUND ***")
        # Try without filter to see what's there
        cur.execute("SELECT DISTINCT \"Customer_ID\", \"ItemCreation_Id\" FROM tbl_bomcreation LIMIT 10")
        sample = cur.fetchall()
        print("  Sample Customer_ID / ItemCreation_Id values in tbl_bomcreation:")
        for s in sample:
            print(f"    {s}")

# ── 2. tbl_bomcreation_partselection (categorisation values) ──────────
print("\n[2] tbl_bomcreation_partselection – distinct Categorisation values:")
with connection.cursor() as cur:
    cur.execute("""
        SELECT DISTINCT ps."Categorisation", COUNT(*) as cnt
        FROM tbl_bomcreation_partselection ps
        INNER JOIN tbl_bomcreation bc
            ON ps."BOMCreation_ID" = bc."BOMCreation_Id"
        WHERE LOWER(bc."Customer_ID") = LOWER(%s)
          AND LOWER(bc."ItemCreation_Id") = LOWER(%s)
        GROUP BY ps."Categorisation"
    """, [CUSTOMER_ID, ITEM_CREATION_ID])
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  Categorisation={r[0]!r}  count={r[1]}")
    else:
        print("  *** NO ROWS FOUND in partselection for this customer+item ***")
        # Show sample BOMCreation_IDs
        cur.execute('SELECT DISTINCT "BOMCreation_ID" FROM tbl_bomcreation_partselection LIMIT 10')
        sample = cur.fetchall()
        print("  Sample BOMCreation_ID values in tbl_bomcreation_partselection:")
        for s in sample:
            print(f"    {s}")

# ── 3. Check if zQry_OfferSheet_PartDetails view exists ───────────────
print("\n[3] Does zQry_OfferSheet_PartDetails view exist?")
with connection.cursor() as cur:
    cur.execute("""
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE LOWER(table_name) = LOWER('zQry_OfferSheet_PartDetails')
    """)
    r = cur.fetchone()
    print(f"  {'EXISTS: ' + str(r) if r else 'NOT FOUND'}")

# ── 4. Direct BOC service call ────────────────────────────────────────
print("\n[4] Direct service call: fetch_boc_part_details('LOCAL BOC'):")
try:
    from apps.CostingBCCal.services import fetch_boc_part_details
    rows = fetch_boc_part_details(CUSTOMER_ID, ITEM_CREATION_ID, "LOCAL BOC")
    print(f"  Returned {len(rows)} rows")
    for r in rows[:3]:
        print(f"    {r}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n[5] Direct service call: fetch_boc_part_details('IMPORTED BOC'):")
try:
    rows = fetch_boc_part_details(CUSTOMER_ID, ITEM_CREATION_ID, "IMPORTED BOC")
    print(f"  Returned {len(rows)} rows")
except Exception as e:
    print(f"  ERROR: {e}")

# ── 6. tbl_bom_partdetails_master sample ─────────────────────────────
print("\n[6] tbl_bom_partdetails_master sample (first 5 rows):")
with connection.cursor() as cur:
    cur.execute('SELECT "Part No", "Categorisation", "Cost_Price", "Settle Price" FROM tbl_bom_partdetails_master LIMIT 5')
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  PartNo={r[0]!r}  Cat={r[1]!r}  Cost={r[2]}  Settle={r[3]}")
    else:
        print("  *** EMPTY TABLE ***")

print("\nDone.")
