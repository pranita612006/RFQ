import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import models
from django.db.models import FilteredRelation, Q, F, FloatField, Value, ExpressionWrapper
from django.db.models.functions import Coalesce

class TestBomCreation(models.Model):
    bomcreation_id = models.IntegerField(primary_key=True, db_column='BOMCreation_ID')
    table_id = models.IntegerField(db_column='table_id', null=True, blank=True)
    class Meta:
        app_label = 'CostingBCCal'
        db_table = 'tbl_BomCreation'
        managed = False

class TestOfferSheetPartDetails(models.Model):
    part_number = models.CharField(max_length=100, db_column='Part_Number', null=True, blank=True)
    description = models.TextField(db_column='Description', null=True, blank=True)
    unit_of_measure_code = models.CharField(max_length=20, db_column='Unit_of_Measure_Code', null=True, blank=True)
    quantity = models.FloatField(db_column='Quantity', default=0.0)
    internal_cost = models.FloatField(db_column='Internal_Cost', default=0.0)
    settle_price = models.FloatField(db_column='Settle Price', null=True, blank=True)
    categorisation = models.CharField(max_length=50, db_column='Categorisation', null=True, blank=True)
    customer_id = models.IntegerField(db_column='Customer_ID')
    itemcreation_id = models.IntegerField(db_column='ItemCreation_Id')
    bomcreation = models.ForeignKey(TestBomCreation, on_delete=models.DO_NOTHING, db_column='BOMCreation_ID', null=True, blank=True)
    table_id = models.IntegerField(db_column='Table_id', null=True, blank=True)
    class Meta:
        app_label = 'CostingBCCal'
        db_table = 'tbl_OfferSheetPartDetails'
        managed = False

qs = TestOfferSheetPartDetails.objects.annotate(
    bom=FilteredRelation('bomcreation', condition=Q(bomcreation__table_id=F('table_id'))),
    bom_tbl=F('bom__table_id'),
    safe_settle_price=Coalesce('settle_price', Value(0.0, output_field=FloatField())),
    calculated_cost=ExpressionWrapper(
        F('quantity') * Coalesce('settle_price', Value(0.0, output_field=FloatField())),
        output_field=FloatField()
    )
).filter(
    categorisation='LOCAL BOC',
    customer_id=1,
    itemcreation_id=1
).distinct()

print("Generated SQL with bom_tbl:")
print(str(qs.query))
