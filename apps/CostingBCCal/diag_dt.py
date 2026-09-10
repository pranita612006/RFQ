"""
Diagnostic script: trace why DTAssignmentYearData costs don't autofill.
Run: python manage.py shell < apps/CostingBCCal/diag_dt.py
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

print("=" * 72)
print("1. RAW SQL: What's actually in tbl_dtassigmentyeardata?")
print("=" * 72)
with connection.cursor() as cur:
    try:
        cur.execute("SELECT COUNT(*) FROM tbl_dtassigmentyeardata")
        total = cur.fetchone()[0]
        print(f"   Total rows: {total}")
    except Exception as e:
        print(f"   ERROR counting rows: {e}")
        total = 0

    if total > 0:
        cur.execute("""
            SELECT itemcreation_id, category, year, cost
            FROM tbl_dtassigmentyeardata
            ORDER BY itemcreation_id, category, year
            LIMIT 20
        """)
        rows = cur.fetchall()
        print(f"   Sample rows (up to 20):")
        for r in rows:
            print(f"     itemcreation_id={r[0]!r}, category={r[1]!r}, year={r[2]!r}, cost={r[3]!r}")

print()
print("=" * 72)
print("2. RAW SQL: What's in tbl_dtcategorylist?")
print("=" * 72)
with connection.cursor() as cur:
    try:
        cur.execute("SELECT * FROM tbl_dtcategorylist ORDER BY category LIMIT 20")
        cols = [d[0] for d in cur.description]
        print(f"   Columns: {cols}")
        rows = cur.fetchall()
        print(f"   Rows ({len(rows)}):")
        for r in rows:
            print(f"     {dict(zip(cols, r))}")
    except Exception as e:
        print(f"   ERROR: {e}")

print()
print("=" * 72)
print("3. ORM: DTCategoryList.objects.all()")
print("=" * 72)
try:
    from apps.CostingBCCal.models import DTCategoryList
    cats = list(DTCategoryList.objects.all())
    print(f"   {len(cats)} categories found")
    for c in cats[:10]:
        print(f"     pk={c.pk!r}, category_name={c.category_name!r}, description={c.description!r}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 72)
print("4. ORM: DTAssignmentYearData — model instance query (uses INNER JOIN)")
print("=" * 72)
try:
    from apps.CostingBCCal.models import DTAssignmentYearData
    # This uses the FK, producing an INNER JOIN with tbl_dtcategorylist
    qs_join = DTAssignmentYearData.objects.all()
    print(f"   Total rows via ORM (INNER JOIN): {qs_join.count()}")
    print(f"   SQL: {qs_join.query}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 72)
print("5. ORM: DTAssignmentYearData.values() query (NO JOIN)")
print("=" * 72)
try:
    qs_values = DTAssignmentYearData.objects.all().values(
        'id', 'item_creation', 'category', 'assignment_year', 'assigned_value'
    )
    print(f"   Total rows via .values() (no JOIN): {qs_values.count()}")
    print(f"   SQL: {qs_values.query}")
    for r in qs_values[:10]:
        print(f"     {r}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 72)
print("6. COMPARISON: Does the FK JOIN drop rows?")
print("=" * 72)
try:
    count_join = DTAssignmentYearData.objects.all().count()
    count_raw = DTAssignmentYearData.objects.all().values('id').count()
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tbl_dtassigmentyeardata")
        count_sql = cur.fetchone()[0]
    print(f"   Raw SQL count:         {count_sql}")
    print(f"   ORM .values() count:   {count_raw}")
    print(f"   ORM instances count:   {count_join}")
    if count_sql != count_join:
        print(f"   ⚠️  MISMATCH: {count_sql - count_join} rows LOST by FK INNER JOIN!")
        # Find which categories in the assignment table don't exist in category table
        with connection.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT a.category 
                FROM tbl_dtassigmentyeardata a
                LEFT JOIN tbl_dtcategorylist c ON a.category = c.category
                WHERE c.category IS NULL
            """)
            orphans = [r[0] for r in cur.fetchall()]
            if orphans:
                print(f"   Orphan categories (in assignment but not in categorylist):")
                for o in orphans:
                    print(f"     {o!r}")
    else:
        print(f"   ✓ Counts match — FK JOIN is not dropping rows")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 72)
print("7. Check: Does .values('category') produce a JOIN or not?")
print("=" * 72)
try:
    qs_test = DTAssignmentYearData.objects.filter(
        item_creation__iexact='test'
    ).values('category', 'assignment_year', 'assigned_value')
    print(f"   SQL for .values('category',...): {qs_test.query}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("DONE")
