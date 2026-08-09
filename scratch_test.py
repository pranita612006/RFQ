import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.BOM.models import BOMPartDetailsMaster
try:
    print('COUNT:', BOMPartDetailsMaster.objects.count())
    parts = list(BOMPartDetailsMaster.objects.values("part_no", "part_description", "base_unit_of_measure", "categorisation", "part_status")[:5])
    print('PARTS:', parts)
except Exception as e:
    print('ERROR:', e)
