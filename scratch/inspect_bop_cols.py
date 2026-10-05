import sys
import os

sys.path.insert(0, r'd:\N-RFQ')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    for tbl in ['tbl_bopcreation', 'tbl_bop_tab', 'tbl_bopcreation_ecn', 'tbl_bop_tab_ecn']:
        try:
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{tbl}' ORDER BY ordinal_position")
            cols = cursor.fetchall()
            print(f"--- Columns of {tbl} ---")
            for c in cols:
                print(f"  {c[0]} ({c[1]})")
        except Exception as e:
            print(f"Error inspecting {tbl}: {e}")

    try:
        cursor.execute("SELECT DISTINCT action_status FROM tbl_bopcreation")
        print("\nDistinct action_status in tbl_bopcreation:", cursor.fetchall())
    except Exception as e:
        print("\nError action_status tbl_bopcreation:", e)

    try:
        cursor.execute("SELECT DISTINCT remark FROM tbl_bopcreation")
        print("\nDistinct remark in tbl_bopcreation:", cursor.fetchall())
    except Exception as e:
        print("\nError remark tbl_bopcreation:", e)
