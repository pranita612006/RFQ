import os
import django

# Set up django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Get columns for tbl_bomcreation_ecn
    cursor.execute("PRAGMA table_info(tbl_bomcreation_ecn)")
    print("tbl_bomcreation_ecn columns:")
    for row in cursor.fetchall():
        print(row)
        
    print("\n---")
    
    # Get columns for tbl_bomcreation_partselection_ecn
    cursor.execute("PRAGMA table_info(tbl_bomcreation_partselection_ecn)")
    print("tbl_bomcreation_partselection_ecn columns:")
    for row in cursor.fetchall():
        print(row)
        
    print("\n---")
    
    # Query first few rows from tbl_bomcreation_ecn
    cursor.execute("SELECT * FROM tbl_bomcreation_ecn LIMIT 5")
    print("tbl_bomcreation_ecn rows:")
    for row in cursor.fetchall():
        print(row)
