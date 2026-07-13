import os
import django

# Set up django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.BOP.models import BOPCreation
from apps.item_creation.models import ItemCard
from apps.opportunities.models import OpportunityMaster

print("=== Item Cards ===")
for item in ItemCard.objects.all()[:10]:
    print(f"Item: {item.no}, Customer: {item.customer_id}, Cell: {item.cell}, CellType: {item.cell_type}")

print("\n=== Opportunity Master ===")
for opp in OpportunityMaster.objects.all()[:10]:
    print(f"ItemNo: {opp.item_no}, CustomerName: {getattr(opp, 'customer_name_db', '')}, Project: {getattr(opp, 'project_name_db', '')}")

print("\n=== BOP Creation ===")
for bop in BOPCreation.objects.all()[:10]:
    print(f"BOP ID: {bop.bopcreation_id}, Table ID: {bop.id}, ItemCreationID: {bop.itemcreation_id}, Cell: {bop.cell}")
