import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.item_creation.models import ItemCard
from apps.BOP.models import BOPTabMaster

print("Total items in BOPTabMaster:", BOPTabMaster.objects.count())
for row in BOPTabMaster.objects.all()[:15]:
    print(row.id, row.costcenter_no, row.description)
