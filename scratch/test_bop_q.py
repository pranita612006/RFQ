import sys
import os

sys.path.insert(0, r'd:\N-RFQ')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.db import connection

def run(label, sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        rows = cursor.fetchall()
    print(f"\n=== {label} ({len(rows)} rows) ===")
    for r in rows[:5]:
        print(r)

run("BOP Customers (all)", """
    SELECT DISTINCT customer_id
    FROM tbl_bopcreation
    WHERE customer_id IS NOT NULL
    ORDER BY customer_id
""")

run("BOP Customers (sent for approval)", """
    SELECT DISTINCT customer_id
    FROM tbl_bopcreation
    WHERE LOWER(TRIM(COALESCE(action_status, remark, ''))) = 'sent for approval'
      AND customer_id IS NOT NULL
    ORDER BY customer_id
""")

with connection.cursor() as c:
    c.execute("SELECT DISTINCT customer_id FROM tbl_bopcreation WHERE customer_id IS NOT NULL LIMIT 1")
    row = c.fetchone()

if row:
    cust = row[0]
    run(f"BOP Items for {cust}", """
        SELECT DISTINCT itemcreation_id::text AS item_id
        FROM tbl_bopcreation
        WHERE customer_id = %s AND itemcreation_id IS NOT NULL
        ORDER BY item_id
    """, [cust])

    run(f"BOP IDs for {cust}", """
        SELECT DISTINCT bopcreation_id
        FROM tbl_bopcreation
        WHERE customer_id = %s
        ORDER BY bopcreation_id
    """, [cust])

    run(f"BOP Lines for {cust}", """
        SELECT c.customer_id, c.itemcreation_id::text, c.bopcreation_id,
               COALESCE(c.action_status, c.remark, '') AS action_status,
               COALESCE(t.seq_no, 0), COALESCE(t.total_cost, 0)
        FROM tbl_bopcreation c
        LEFT JOIN tbl_bop_tab t ON t.bopcreationid = c.bopcreation_id
        WHERE c.customer_id = %s
        LIMIT 5
    """, [cust])
else:
    print("No customers in tbl_bopcreation")

print("\nDone.")
