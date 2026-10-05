import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection

for tbl in ['tbl_bomcreation', 'tbl_bomcreation_partselection']:
    with connection.cursor() as cur:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{tbl}' ORDER BY ordinal_position")
        cols = [r[0] for r in cur.fetchall()]
    print(f"\n{tbl}:\n  " + "\n  ".join(cols))
