import os
import django
import sys

# Set up django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def inspect():
    output_file = r"D:\N-RFQ\db_inspection_results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        original_stdout = sys.stdout
        sys.stdout = f
        try:
            with connection.cursor() as cursor:
                # Get all table names
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                print("=== ALL TABLES IN SYSTEM ===")
                for table in tables:
                    print(f"- {table}")
                    
                print("\n=== DETAILED SCHEMA FOR BOP RELATED TABLES ===")
                bop_tables = [t for t in tables if 'bop' in t.lower() or 'customerinfo' in t.lower() or 'opportunity' in t.lower()]
                for table in bop_tables:
                    print(f"\nTable: {table}")
                    # Columns
                    cursor.execute(f"""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = %s
                        ORDER BY ordinal_position;
                    """, [table])
                    columns = cursor.fetchall()
                    print("  Columns:")
                    for col in columns:
                        print(f"    - {col[0]} ({col[1]}), Nullable: {col[2]}, Default: {col[3]}")
                        
                    # Primary Key / Foreign Key / Constraints
                    cursor.execute(f"""
                        SELECT
                            tc.constraint_name, 
                            tc.constraint_type,
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM 
                            information_schema.table_constraints AS tc 
                            JOIN information_schema.key_column_usage AS kcu
                              ON tc.constraint_name = kcu.constraint_name
                              AND tc.table_schema = kcu.table_schema
                            LEFT JOIN information_schema.constraint_column_usage AS ccu
                              ON ccu.constraint_name = tc.constraint_name
                              AND ccu.table_schema = ccu.table_schema
                        WHERE tc.table_schema='public' AND tc.table_name=%s;
                    """, [table])
                    constraints = cursor.fetchall()
                    print("  Constraints & Relationships:")
                    for con in constraints:
                        print(f"    - {con[0]} ({con[1]}) on column: {con[2]} -> references: {con[3]}.{con[4] if con[4] else ''}")
        finally:
            sys.stdout = original_stdout

if __name__ == '__main__':
    inspect()
    print("Done")
