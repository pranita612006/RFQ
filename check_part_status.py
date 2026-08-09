import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.BOM.models import BOMPartDetailsMaster

print("=== Total rows ===")
print(BOMPartDetailsMaster.objects.count())

print("\n=== Distinct Part_Status values ===")
statuses = BOMPartDetailsMaster.objects.values_list('part_status', flat=True).distinct()
for s in statuses:
    print(repr(s))
