import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cur:
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND (table_name ILIKE '%offersheet%' OR table_name ILIKE '%bom%')")
    print("Tables:", cur.fetchall())

    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name ILIKE 'tbl_offersheetpartdetails'")
    print("OfferSheetPartDetails columns:", cur.fetchall())

    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name ILIKE 'tbl_bomcreation'")
    print("tbl_bomcreation columns:", cur.fetchall())
