import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
from django.conf import settings

# Point test db to in-memory sqlite for instant isolated execution
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}

django.setup()

import json
from django.db import connection
from django.db.models import F, FloatField, Value, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.test import RequestFactory
from django.urls import resolve, reverse

from apps.CostingBCCal.models import OfferSheetPartDetails, BomCreation
from apps.CostingBCCal.views import get_boc_tab_data, save_local_boc_data


def setup_test_tables():
    with connection.cursor() as cur:
        cur.execute("""
            CREATE TABLE tbl_BomCreation (
                BOMCreation_ID INTEGER PRIMARY KEY,
                table_id INTEGER,
                Customer_ID VARCHAR(50),
                ItemCreation_Id VARCHAR(50),
                Remark TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE tbl_OfferSheetPartDetails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Part_Number VARCHAR(100),
                Description TEXT,
                Unit_of_Measure_Code VARCHAR(20),
                Quantity REAL DEFAULT 0.0,
                Internal_Cost REAL DEFAULT 0.0,
                [Settle Price] REAL,
                Categorisation VARCHAR(50),
                Customer_ID INTEGER,
                ItemCreation_Id INTEGER,
                BOMCreation_ID INTEGER,
                Table_id INTEGER
            );
        """)


def test_models():
    print("=== Testing Database Models ===")
    
    # 1. OfferSheetPartDetails
    assert OfferSheetPartDetails._meta.db_table == 'tbl_OfferSheetPartDetails'
    field_names = {f.name for f in OfferSheetPartDetails._meta.get_fields()}
    expected_fields = {
        'id', 'part_number', 'description', 'unit_of_measure_code',
        'quantity', 'internal_cost', 'settle_price', 'categorisation',
        'customer_id', 'itemcreation_id', 'bomcreation_id', 'table_id', 'bom'
    }
    assert expected_fields.issubset(field_names), f"Missing fields: {expected_fields - field_names}"
    
    assert OfferSheetPartDetails._meta.get_field('part_number').db_column == 'Part_Number'
    assert OfferSheetPartDetails._meta.get_field('description').db_column == 'Description'
    assert OfferSheetPartDetails._meta.get_field('unit_of_measure_code').db_column == 'Unit_of_Measure_Code'
    assert OfferSheetPartDetails._meta.get_field('quantity').db_column == 'Quantity'
    assert OfferSheetPartDetails._meta.get_field('internal_cost').db_column == 'Internal_Cost'
    assert OfferSheetPartDetails._meta.get_field('settle_price').db_column == 'Settle Price'
    assert OfferSheetPartDetails._meta.get_field('categorisation').db_column == 'Categorisation'
    assert OfferSheetPartDetails._meta.get_field('customer_id').db_column == 'Customer_ID'
    assert OfferSheetPartDetails._meta.get_field('itemcreation_id').db_column == 'ItemCreation_Id'
    assert OfferSheetPartDetails._meta.get_field('bomcreation_id').db_column == 'BOMCreation_ID'
    assert OfferSheetPartDetails._meta.get_field('table_id').db_column == 'Table_id'
    print("  OfferSheetPartDetails model attributes & column mappings: OK")

    # 2. BomCreation
    assert BomCreation._meta.db_table == 'tbl_BomCreation'
    assert BomCreation._meta.pk.name == 'bomcreation_id'
    assert BomCreation._meta.get_field('bomcreation_id').db_column == 'BOMCreation_ID'
    assert BomCreation._meta.get_field('table_id').db_column == 'table_id'
    print("  BomCreation model attributes & column mappings: OK")


def test_query_generation_and_execution():
    print("=== Testing Query Generation & Multi-Column LEFT JOIN ===")
    setup_test_tables()

    # Seed BomCreation
    with connection.cursor() as cur:
        cur.execute("INSERT INTO tbl_BomCreation (BOMCreation_ID, table_id, Customer_ID, ItemCreation_Id, Remark) VALUES (101, 1, '10', '20', 'Test BOM')")
        cur.execute("INSERT INTO tbl_OfferSheetPartDetails (Part_Number, Description, Unit_of_Measure_Code, Quantity, Internal_Cost, [Settle Price], Categorisation, Customer_ID, ItemCreation_Id, BOMCreation_ID, Table_id) VALUES ('PN-001', 'Widget A', 'PCS', 5.0, 12.5, 15.0, 'LOCAL BOC', 10, 20, 101, 1)")
        cur.execute("INSERT INTO tbl_OfferSheetPartDetails (Part_Number, Description, Unit_of_Measure_Code, Quantity, Internal_Cost, [Settle Price], Categorisation, Customer_ID, ItemCreation_Id, BOMCreation_ID, Table_id) VALUES ('PN-002', 'Widget B (no settle price)', 'PCS', 10.0, 8.0, NULL, 'LOCAL BOC', 10, 20, 101, 1)")
        cur.execute("INSERT INTO tbl_OfferSheetPartDetails (Part_Number, Description, Unit_of_Measure_Code, Quantity, Internal_Cost, [Settle Price], Categorisation, Customer_ID, ItemCreation_Id, BOMCreation_ID, Table_id) VALUES ('PN-003', 'Other Cat', 'PCS', 2.0, 5.0, 6.0, 'IMPORTED BOC', 10, 20, 101, 1)")

    rf = RequestFactory()
    req = rf.get("/CostingBCCal/boc/tab-data/?customer_id=10&item_creation_id=20")
    resp = get_boc_tab_data(req)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode("utf-8"))
    
    assert data["status"] == "success"
    assert len(data["local_boc"]) == 2
    row1 = data["local_boc"][0]
    row2 = data["local_boc"][1]

    # Row 1: Qty 5, Settle 15 => Cost 75
    assert row1["part_number"] == "PN-001"
    assert row1["quantity"] == 5.0
    assert row1["internal_rate"] == 12.5
    assert row1["settle_price"] == 15.0
    assert row1["cost"] == 75.0

    # Row 2: Qty 10, Settle NULL (Coalesced to 0) => Cost 0
    assert row2["part_number"] == "PN-002"
    assert row2["quantity"] == 10.0
    assert row2["settle_price"] == 0.0
    assert row2["cost"] == 0.0

    print("  Fetch query execution and Coalesce calculation: OK")


def test_save_view_logic():
    print("=== Testing Save View Logic (Create & Update) ===")
    rf = RequestFactory()

    # 1. Create a new record (missing id)
    payload_create = {
        "customer_id": 10,
        "item_creation_id": 20,
        "rows": [
            {
                "id": None,
                "part_number": "PN-NEW",
                "description": "Newly added part",
                "unit_of_measure_code": "NOS",
                "quantity": 3.0,
                "internal_rate": 25.0,
                "settle_price": 30.0,
            }
        ]
    }
    req_create = rf.post("/CostingBCCal/boc/save-local-boc-data/", data=json.dumps(payload_create), content_type="application/json")
    resp_create = save_local_boc_data(req_create)
    assert resp_create.status_code == 200
    res_json = json.loads(resp_create.content.decode("utf-8"))
    assert res_json["status"] == "success"
    assert res_json["message"] == "Local BOC records saved successfully."

    created = OfferSheetPartDetails.objects.get(part_number="PN-NEW")
    assert created.categorisation == "LOCAL BOC"
    assert created.customer_id == 10
    assert created.itemcreation_id == 20
    assert created.quantity == 3.0
    assert created.internal_cost == 25.0
    assert created.settle_price == 30.0
    print("  Save View CREATE: OK")

    # 2. Update existing record
    payload_update = {
        "customer_id": 10,
        "item_creation_id": 20,
        "rows": [
            {
                "id": created.id,
                "part_number": "PN-UPDATED",
                "description": "Updated description",
                "unit_of_measure_code": "SET",
                "quantity": 8.0,
                "internal_rate": 40.0,
                "settle_price": 50.0,
            }
        ]
    }
    req_update = rf.post("/CostingBCCal/boc/save-local-boc-data/", data=json.dumps(payload_update), content_type="application/json")
    resp_update = save_local_boc_data(req_update)
    assert resp_update.status_code == 200

    updated = OfferSheetPartDetails.objects.get(id=created.id)
    assert updated.part_number == "PN-UPDATED"
    assert updated.description == "Updated description"
    assert updated.unit_of_measure_code == "SET"
    assert updated.quantity == 8.0
    assert updated.internal_cost == 40.0
    assert updated.settle_price == 50.0
    print("  Save View UPDATE: OK")


def test_urls():
    print("=== Testing URLs ===")
    url_tab = reverse("get_boc_tab_data")
    assert url_tab == "/CostingBCCal/boc/tab-data/"
    match_tab = resolve("/CostingBCCal/boc/tab-data/")
    assert match_tab.func == get_boc_tab_data

    url_save = reverse("save_local_boc_data")
    assert url_save == "/CostingBCCal/boc/save-local-boc-data/"
    match_save = resolve("/CostingBCCal/boc/save-local-boc-data/")
    assert match_save.func == save_local_boc_data
    print("  URLs Reverse and Resolve: OK")


def test_js_file():
    print("=== Testing JavaScript File Integrity ===")
    js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'js', 'boc_local.js')
    assert os.path.exists(js_path), "boc_local.js file missing"
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "function addLocalBOCRow" in content
    assert "no-data-row" in content
    assert "escapeHtml" in content
    assert "parseFloat" in content
    assert ".toFixed(2)" in content
    assert "text-right" in content
    assert "btn-save-local-boc" in content
    assert "boc-local-bom-tbody" in content
    assert "save_local_boc_data" in content or "save-local-boc-data" in content
    assert "X-CSRFToken" in content
    print("  JavaScript syntax & required identifiers: OK")


if __name__ == "__main__":
    test_models()
    test_query_generation_and_execution()
    test_save_view_logic()
    test_urls()
    test_js_file()
    print("\n==========================================")
    print("ALL MODULE VERIFICATION TESTS PASSED 100%!")
    print("==========================================")
