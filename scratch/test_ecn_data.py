import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    try:
        cursor.execute('SELECT "No" FROM tbl_itemcard_ecn LIMIT 1')
        print("Quoted \"No\" worked:", cursor.fetchone())
    except Exception as e:
        print("Quoted \"No\" failed:", e)

    try:
        cursor.execute('SELECT no FROM tbl_itemcard_ecn LIMIT 1')
        print("Unquoted no worked:", cursor.fetchone())
    except Exception as e:
        print("Unquoted no failed:", e)