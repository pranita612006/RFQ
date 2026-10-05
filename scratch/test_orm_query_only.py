import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db.models import F, FloatField, Value, ExpressionWrapper
from django.db.models.functions import Coalesce
from apps.CostingBCCal.models import OfferSheetPartDetails

qs = (
    OfferSheetPartDetails.objects.filter(
        categorisation="LOCAL BOC",
        customer_id=10,
        itemcreation_id=20,
    )
    .select_related("bom")
    .annotate(
        safe_settle_price=Coalesce("settle_price", Value(0.0, output_field=FloatField())),
        calculated_cost=ExpressionWrapper(
            F("quantity") * Coalesce("settle_price", Value(0.0, output_field=FloatField())),
            output_field=FloatField(),
        ),
    )
    .distinct()
)

print("Annotated query with Coalesce and calculated_cost:")
print(str(qs.query))
