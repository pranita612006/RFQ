import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import sys; sys.path.insert(0, 'd:\\N-RFQ')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = [r[0] for r in cursor.fetchall()]
for t in tables:
    print(t)
