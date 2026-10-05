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
        AND table_name ILIKE '%conversion%'
    """)
    print("Tables:", [r[0] for r in cursor.fetchall()])

    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema='public' 
        AND table_name ILIKE '%conversion%'
    """)
    print("Views:", [r[0] for r in cursor.fetchall()])

    cursor.execute("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE column_name ILIKE '%subcategory%'
    """)
    print("Subcategory columns:", [f"{r[0]}.{r[1]}" for r in cursor.fetchall()])
