import os, sys
sys.path.insert(0, r'd:\N-RFQ')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()

from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sys.tables WHERE name LIKE '%bop%' OR name LIKE '%imported%' OR name LIKE '%BOC%' ORDER BY name")
    print("=== Tables matching bop/imported/BOC ===")
    for r in cursor.fetchall():
        print(r[0])

    # Also check for a BOC imported details table
    cursor.execute("SELECT name FROM sys.tables WHERE name LIKE '%boc%' ORDER BY name")
    print("\n=== Tables matching boc ===")
    for r in cursor.fetchall():
        print(r[0])

    # Check columns of tbl_bop_master if it exists
    try:
        cursor.execute("SELECT TOP 0 * FROM tbl_bop_master")
        cols = [col[0] for col in cursor.description]
        print(f"\n=== tbl_bop_master columns ===\n{cols}")
    except:
        print("\ntbl_bop_master does NOT exist")

    # Check for BOPMaster-like table
    cursor.execute("SELECT name FROM sys.tables WHERE name LIKE '%master%' AND name LIKE '%bop%' ORDER BY name")
    print("\n=== Tables matching master+bop ===")
    for r in cursor.fetchall():
        print(r[0])
