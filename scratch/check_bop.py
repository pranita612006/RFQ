import sys
import os

sys.path.insert(0, r'd:\N-RFQ')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        AND table_name ILIKE '%bop%'
    """)
    print("BOP Tables:", [r[0] for r in cursor.fetchall()])

    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema='public' 
        AND table_name ILIKE '%bop%'
    """)
    print("BOP Views:", [r[0] for r in cursor.fetchall()])

    for tbl in ['tbl_bopcreation', 'tbl_bop_tab', 'tbl_bop_cellallienment', 'tbl_bop_tolling', 'qry_bopsendforapproval']:
        try:
            cursor.execute(f'SELECT count(*) FROM "{tbl}"')
            print(f"Count for {tbl}:", cursor.fetchone()[0])
        except Exception as e:
            print(f"Count for {tbl} error:", e)
            connection.rollback()
