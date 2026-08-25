import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.BOC.models import BocCreation, BocItemCard

print("Item nos in BocItemCard for first customer:")
item = BocItemCard.objects.first()
if item:
    print(f"Customer: {item.customerid}, Item No: {item.no}")
    print("Trying to find in BocCreation:")
    boc = BocCreation.objects.filter(itemcreation_id=item.no, customer_id=item.customerid).first()
    print(f"Found BOC: {boc}")
else:
    print("No item cards")

print("\nFirst 5 BocCreation records:")
for b in BocCreation.objects.all()[:5]:
    print(f"boc_creation_id: {b.boc_creation_id}, itemcreation_id: {b.itemcreation_id}, customer_id: {b.customer_id}, drg_revno: {b.drg_revno}")
