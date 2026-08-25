import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.BOC.models import BocCreationEcn, BocCreation

print("=== tbl_boc_creation_ecn rows ===")
rows = list(BocCreationEcn.objects.all()[:10])
if not rows:
    print("  (no rows found)")
for r in rows:
    print(f"  boc_creation_id={r.boc_creation_id!r}  table_id={r.table_id!r}  ecn_id={r.ecn_id!r}")

print()
print("=== tbl_boc_creation sample ===")
for r in BocCreation.objects.all().values('boc_creation_id', 'table_id')[:10]:
    print(f"  boc_creation_id={r['boc_creation_id']!r}  table_id={r['table_id']!r}")
