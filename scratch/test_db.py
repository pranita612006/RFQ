import os, sys
sys.path.insert(0, r"d:\N-RFQ")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

try:
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
        print("DB SUCCESS:", cur.fetchone())
        
        cur.execute("""
            SELECT DISTINCT rm_flag FROM tbl_offersheetrmconversion LIMIT 10;
        """)
        print("rm_flags in tbl_offersheetrmconversion:", cur.fetchall())

        cur.execute("""
            SELECT COUNT(*) FROM tbl_bom_partdetails_master WHERE categorisation ILIKE '%Raw Material%';
        """)
        print("Count Raw Material in tbl_bom_partdetails_master:", cur.fetchone())

        cur.execute("""
            SELECT "Part Description", "Part No", "Customer", "Base Unit of Measure", "Settle Price", "Categorisation"
            FROM tbl_bom_partdetails_master 
            WHERE categorisation ILIKE '%Raw Material%'
            LIMIT 3;
        """)
        print("Sample tbl_bom_partdetails_master:", cur.fetchall())
except Exception as e:
    print("DB ERROR:", e)
