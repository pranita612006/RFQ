import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.CostingBCCal.models import BomCreation, OfferSheetPartDetails
print("BomCreation:", BomCreation)
print("OfferSheetPartDetails:", OfferSheetPartDetails)
print("OfferSheetPartDetails fields:", [f.name for f in OfferSheetPartDetails._meta.get_fields()])
