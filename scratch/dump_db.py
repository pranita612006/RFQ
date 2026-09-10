import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.CostingBCCal.models import DTAssignmentYearData
from django.db import connection

out = []
with connection.cursor() as cur:
    cur.execute("SELECT itemcreation_id, category, year, cost FROM tbl_dtassigmentyeardata ORDER BY itemcreation_id, category, year")
    cols = [d[0] for d in cur.description]
    for r in cur.fetchall():
        d = dict(zip(cols, r))
        d['cost'] = float(d['cost']) if d['cost'] is not None else None
        out.append(d)

with open('scratch/db_dump.json', 'w') as f:
    json.dump(out, f, indent=2)
print("Dumped", len(out), "rows")
