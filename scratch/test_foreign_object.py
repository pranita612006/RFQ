import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import models
from django.db.models.fields.related import ForeignObject

class BomCreationTest(models.Model):
    bomcreation_id = models.IntegerField(primary_key=True, db_column='BOMCreation_ID')
    table_id = models.IntegerField(db_column='table_id', null=True, blank=True)
    remark = models.TextField(db_column='Remark', null=True, blank=True)
    class Meta:
        app_label = 'CostingBCCal'
        db_table = 'tbl_BomCreation'
        managed = False

class PartDetailsTest(models.Model):
    part_number = models.CharField(max_length=100, db_column='Part_Number', null=True, blank=True)
    description = models.TextField(db_column='Description', null=True, blank=True)
    unit_of_measure_code = models.CharField(max_length=20, db_column='Unit_of_Measure_Code', null=True, blank=True)
    quantity = models.FloatField(db_column='Quantity', default=0.0)
    internal_cost = models.FloatField(db_column='Internal_Cost', default=0.0)
    settle_price = models.FloatField(db_column='Settle Price', null=True, blank=True)
    categorisation = models.CharField(max_length=50, db_column='Categorisation', null=True, blank=True)
    customer_id = models.IntegerField(db_column='Customer_ID')
    itemcreation_id = models.IntegerField(db_column='ItemCreation_Id')
    bomcreation_id = models.IntegerField(db_column='BOMCreation_ID', null=True, blank=True)
    table_id = models.IntegerField(db_column='Table_id', null=True, blank=True)
    
    bom = ForeignObject(
        BomCreationTest,
        on_delete=models.DO_NOTHING,
        from_fields=['bomcreation_id', 'table_id'],
        to_fields=['bomcreation_id', 'table_id'],
        null=True,
        blank=True
    )
    class Meta:
        app_label = 'CostingBCCal'
        db_table = 'tbl_OfferSheetPartDetails'
        managed = False

from django.db.models import FloatField, Value, ExpressionWrapper, F
from django.db.models.functions import Coalesce

qs = PartDetailsTest.objects.filter(
    categorisation='LOCAL BOC',
    customer_id=1,
    itemcreation_id=1
).select_related('bom').annotate(
    safe_settle_price=Coalesce('settle_price', Value(0.0, output_field=FloatField())),
    calculated_cost=ExpressionWrapper(
        F('quantity') * Coalesce('settle_price', Value(0.0, output_field=FloatField())),
        output_field=FloatField()
    )
).distinct()

print("ForeignObject with select_related SQL:")
print(str(qs.query))
