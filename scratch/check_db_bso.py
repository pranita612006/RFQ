import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def get_all_items(customer_id):
    variants = [customer_id, customer_id.zfill(8), customer_id.lstrip('0')]
    variants = list(dict.fromkeys(variants))
    items_dict = {}

    with connection.cursor() as c:
        # 1. tbl_itemcard
        c.execute("SELECT no, description FROM tbl_itemcard WHERE customerid = ANY(%s)", [variants])
        for no, desc in c.fetchall():
            if no:
                items_dict[no] = desc or ''

        # 2. tbl_boc_creation
        c.execute("SELECT itemcreation_id, part_name FROM tbl_boc_creation WHERE customer_id = ANY(%s)", [variants])
        for no, desc in c.fetchall():
            if no and no not in items_dict:
                items_dict[no] = desc or ''

        # 3. tbl_opportunitymaster
        c.execute("SELECT item_no, part_name FROM tbl_opportunitymaster WHERE customerid = ANY(%s)", [variants])
        for no, desc in c.fetchall():
            if no and no not in items_dict:
                items_dict[no] = desc or ''

        # 4. tbl_blanketso
        c.execute("SELECT itemcreation_id FROM tbl_blanketso WHERE customer_id = ANY(%s)", [variants])
        for (no,) in c.fetchall():
            if no and no not in items_dict:
                items_dict[no] = ''

        # 5. tbl_bso_saleslines
        c.execute("SELECT itemcreation_id, description FROM tbl_bso_saleslines WHERE customer_id = ANY(%s)", [variants])
        for no, desc in c.fetchall():
            if no and no not in items_dict:
                items_dict[no] = desc or ''

    return [{'no': k, 'description': v} for k, v in sorted(items_dict.items())]

print("CUST-001 items:", get_all_items('CUST-001'))
print("CUST-005 items:", get_all_items('CUST-005'))
