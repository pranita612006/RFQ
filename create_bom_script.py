import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.BOM.models import BOMHeader
from datetime import date
from django.db.models import Max

item_id = 'TEST-BOM-ITEM'
customer_id = 'CUST001'
today = date.today()

max_row = BOMHeader.objects.filter(item_creation_id=item_id, customer_id=customer_id).aggregate(max_row=Max('bom_row_id'))['max_row']
int_bom_row_id = int(max_row or 0) + 1
bom_creation_id = f"BOM{today.strftime('%Y%m%d')}{int_bom_row_id}"

max_table = BOMHeader.objects.filter(item_creation_id=item_id).aggregate(max_table=Max('table_id'))['max_table']
table_id = str(int(max_table or 0) + 1)

bom_record = BOMHeader.objects.create(
    item_creation_id=item_id,
    customer_id=customer_id,
    bom_row_id=int_bom_row_id,
    bom_creation_id=bom_creation_id,
    table_id=table_id,
    action_status='Created',
    create_date=today,
    description='Created by AI',
    uom_code='EA',
    last_date_modified=today
)
print(f"Successfully created BOM record: {bom_creation_id}")
