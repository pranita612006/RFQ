import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.BOM.models import BOMPartDetailsMaster, BOMProdItemPartGrpMaster
from django.db import connection

print("=== Checking tbl_bom_partdetails_master ===")
try:
    count = BOMPartDetailsMaster.objects.count()
    print(f"Total rows: {count}")
    if count > 0:
        sample = list(BOMPartDetailsMaster.objects.values('part_no', 'part_description', 'base_unit_of_measure', 'categorisation', 'part_status')[:3])
        print(f"Sample rows: {sample}")
    else:
        print("Table is EMPTY - this is why no options show!")
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== Checking BOMProdItemPartGrpMaster ===")
try:
    count2 = BOMProdItemPartGrpMaster.objects.count()
    print(f"Total rows: {count2}")
    if count2 > 0:
        sample2 = list(BOMProdItemPartGrpMaster.objects.values('grp_part_no', 'grp_part_description')[:3])
        print(f"Sample rows: {sample2}")
    else:
        print("Table is EMPTY")
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== Raw SQL check on actual table name ===")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM tbl_bom_partdetails_master")
        print(f"Raw count: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Raw SQL ERROR: {e}")
