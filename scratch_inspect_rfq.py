import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute(
    "SELECT column_name, data_type FROM information_schema.columns "
    "WHERE table_name='tbl_rfq_details' ORDER BY ordinal_position"
)
print("tbl_rfq_details columns:", cursor.fetchall())

cursor.execute(
    "SELECT column_name, data_type FROM information_schema.columns "
    "WHERE table_name='tbl_bomcreation' ORDER BY ordinal_position"
)
print("tbl_bomcreation columns:", cursor.fetchall())

cursor.execute(
    "SELECT column_name, data_type FROM information_schema.columns "
    "WHERE table_name='tbl_offersheetrmconversion' ORDER BY ordinal_position"
)
print("tbl_offersheetrmconversion columns:", cursor.fetchall())

# Sample data from tbl_rfq_details
cursor.execute("SELECT * FROM tbl_rfq_details LIMIT 3")
cols = [d[0] for d in cursor.description]
rows = cursor.fetchall()
print("rfq_details sample:", [dict(zip(cols, r)) for r in rows])
