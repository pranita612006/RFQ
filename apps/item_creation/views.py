import datetime
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from urllib.parse import urlencode

from .forms import SendItemEmailForm
from .models import (
    ApplyTemplate, ItemCard, UnitOfMeasure, ItemCategory,
    ProductGroup, Cell, CellType, HSNCode, CustomerInfo, RFQDetails,
)
from config.decorators import require_active_customer

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_fy_quarter(date=None):
    """Return (monthyear, fy, quarter) strings matching Access VBA logic."""
    if date is None:
        date = datetime.date.today()
    month = date.month
    year = date.year
    monthyear = f"{month:02d}/{year}"
    if month > 3:  # April–December
        fy = f"{year}-{str(year + 1)[-2:]}"
        if 4 <= month <= 6:
            quarter = "Q1"
        elif 7 <= month <= 9:
            quarter = "Q2"
        else:
            quarter = "Q3"
    else:  # January–March
        fy = f"{year - 1}-{str(year)[-2:]}"
        quarter = "Q4"
    return monthyear, fy, quarter


def _is_rfq_completed(customer_id, item_no):
    """Return True if tbl_rfq_details has is_completed=True for customer+item."""
    return RFQDetails.objects.filter(
        customer_id=customer_id,
        itemcreation_id=item_no,
        is_completed=True,
    ).exists()


def _get_ecn_count(customer_id, item_no):
    """Return count of ECN records for customer+item from tbl_itemcard_ecn."""
    with connection.cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) FROM tbl_itemcard_ecn WHERE customerid=%s AND "No"=%s',
            [customer_id, item_no],
        )
        return cur.fetchone()[0]


def _insert_itemcard_ecn(ecn_id, ecn_type, customer_id, customer_name, item_no,
                          fields, monthyear, fy, quarter):
    """Raw INSERT into tbl_itemcard_ecn. All field columns are text."""
    now_str = datetime.date.today().strftime("%Y-%m-%d")
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tbl_itemcard_ecn (
                ecn_id, ecn_type, customerid, customername, "No",
                template_name, description, base_unit_of_measure, shelf_no,
                cell, cell_type, item_category_code, product_group_code,
                status, last_date_modified, fixture_no, no_of_meft, no_of_parts,
                customer_name, revision_no, customer_vendor_code, hsn_sac_code,
                costing_method, inventory_posting_group, price_profit_calculation,
                gen_prod_posting_group, replenishment_system, qc_applicable,
                manufacturing_policy, assembly_policy, reordering_policy,
                include_inventory, gst_credit, flushing_method, template_applied,
                rounding_precision, gst_group_code, monthyear, fy, quarter
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """,
            [
                ecn_id, ecn_type, customer_id, customer_name, item_no,
                fields.get('template_name'), fields.get('description'), fields.get('base_unit_of_measure'), fields.get('shelf_no'),
                fields.get('cell'), fields.get('cell_type'), fields.get('item_category_code'), fields.get('product_group_code'),
                fields.get('status'), now_str, fields.get('fixture_no'), fields.get('no_of_meft'), fields.get('no_of_parts'),
                fields.get('customer_name'), fields.get('revision_no'), fields.get('customer_vendor_code'), fields.get('hsn_sac_code'),
                fields.get('costing_method'), fields.get('inventory_posting_group'), fields.get('price_profit_calculation'),
                fields.get('gen_prod_posting_group'), fields.get('replenishment_system'), fields.get('qc_applicable'),
                fields.get('manufacturing_policy'), fields.get('assembly_policy'), fields.get('reordering_policy'),
                fields.get('include_inventory'), fields.get('gst_credit'), fields.get('flushing_method'), fields.get('template_applied'),
                fields.get('rounding_precision'), fields.get('gst_group_code'), monthyear, fy, quarter,
            ],
        )


def _register_rfq_details(customer_id, customer_name, item_no, username="SYSTEM"):
    """
    Initial RFQ / Item Registration:
    When an RFQ is created in Item Creation, insert or update the initial row in
    tbl_rfq_details with customer_id, customername, itemcreation_id, is_completed = False,
    action_date, and updated_by.
    """
    now_dt = datetime.datetime.now()
    user_str = username or "SYSTEM"
    try:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id FROM tbl_rfq_details WHERE customer_id = %s AND itemcreation_id = %s LIMIT 1",
                [customer_id, item_no]
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE tbl_rfq_details
                    SET customername = %s,
                        action_date = %s,
                        updated_by = %s
                    WHERE id = %s
                    """,
                    [customer_name, now_dt, user_str, row[0]]
                )
            else:
                try:
                    cur.execute(
                        """
                        INSERT INTO tbl_rfq_details (
                            customer_id, customername, itemcreation_id,
                            is_completed, action_date, updated_by
                        ) VALUES (%s, %s, %s, FALSE, %s, %s)
                        """,
                        [customer_id, customer_name, item_no, now_dt, user_str]
                    )
                except Exception as insert_err:
                    logger.warning("Default INSERT into tbl_rfq_details failed (%s), attempting with explicit ID", insert_err)
                    cur.execute("SELECT COALESCE(MAX(CASE WHEN id ~ '^[0-9]+$' THEN id::bigint ELSE 0 END), 0) + 1 FROM tbl_rfq_details")
                    next_id = cur.fetchone()[0]
                    cur.execute(
                        """
                        INSERT INTO tbl_rfq_details (
                            id, customer_id, customername, itemcreation_id,
                            is_completed, action_date, updated_by
                        ) VALUES (%s, %s, %s, %s, FALSE, %s, %s)
                        """,
                        [next_id, customer_id, customer_name, item_no, now_dt, user_str]
                    )
    except Exception as e:
        logger.exception("Failed to register RFQ details for item_no=%s: %s", item_no, e)


# ─────────────────────────────────────────────────────────────────────────────
# Item Creation – Main Form
# ─────────────────────────────────────────────────────────────────────────────

@require_active_customer
def item_creation_form(request):
    """Render the Item Creation form with all dropdown data."""
    selected_customer_id = request.active_customer['id']
    selected_name = request.active_customer['name']

    template_names = ApplyTemplate.objects.values_list("template_name", flat=True).distinct()
    uoms = UnitOfMeasure.objects.all()
    item_categories = ItemCategory.objects.all()
    product_groups = ProductGroup.objects.all()
    cells = Cell.objects.all()
    cell_types = CellType.objects.all()
    hsn_codes = HSNCode.objects.all()

    items = list(ItemCard.objects.filter(customer_id=selected_customer_id).values_list("no", flat=True))

    # Customer vendor code + short name from tbl_customerinfo
    cust_vendor_code = ""
    cust_short_name = ""
    try:
        ci = CustomerInfo.objects.filter(customer_id=selected_customer_id).first()
        if ci:
            cust_vendor_code = ci.primary_contact_no or ""
            cust_short_name = ci.shortname or ""
    except Exception:
        pass

    return render(request, "item_creation/item_creation_form.html", {
        "template_name": template_names,
        "s_item": items,
        "uoms": uoms,
        "item_categories": item_categories,
        "cells": cells,
        "cell_types": cell_types,
        "hsn_codes": hsn_codes,
        "product_groups": product_groups,
        "selected_customer_id": selected_customer_id,
        "selected_name": selected_name,
        "cust_vendor_code": cust_vendor_code,
        "cust_short_name": cust_short_name,
    })


# ─────────────────────────────────────────────────────────────────────────────
# AJAX – Lookup APIs
# ─────────────────────────────────────────────────────────────────────────────

def get_template_data(request):
    """Return template field defaults for a given template name."""
    template_name = request.GET.get("template_name", "")
    try:
        t = ApplyTemplate.objects.get(template_name=template_name)
        return JsonResponse({
            "costing_method": t.costing_method or "",
            "inventory_posting_group": t.inventory_posting_group or "",
            "price_profit_calculation": t.price_profit_calculation or "",
            "gen_prod_posting_group": t.gen_prod_posting_group or "",
            "replenishment_system": t.replenishment_system or "",
            "qc_applicable": t.qc_applicable or "",
            "manufacturing_policy": t.manufacturing_policy or "",
            "assembly_policy": t.assembly_policy or "",
            "reordering_policy": t.reordering_policy or "",
            "include_inventory": t.include_inventory or "",
            "gst_credit": t.gst_credit or "",
            "flushing_method": t.flushing_method or "",
            "template_applied": t.template_applied or "",
            "rounding_precision": t.rounding_precision or "",
            "gst_group_code": t.gst_group_code or "",
        })
    except ApplyTemplate.DoesNotExist:
        return JsonResponse({"error": "Template not found"}, status=404)
    except Exception as e:
        logger.exception("get_template_data error: %s", template_name)
        return JsonResponse({"error": str(e)}, status=500)


def get_item_details(request):
    """Return full item details + ECN count + RFQ lock status for a given item number."""
    item_no = request.GET.get("item_no", "").strip()
    cust_id = request.GET.get("customer_id", "").strip()

    if not item_no:
        return JsonResponse({"error": "Missing item_no"}, status=400)

    item = ItemCard.objects.filter(no=item_no, customer_id=cust_id).first()
    if not item:
        return JsonResponse({"error": "Item not found"}, status=404)

    # Last ECN
    ecn_count = _get_ecn_count(cust_id, item_no)
    last_ecn = f"ECN:{ecn_count - 1}" if ecn_count > 0 else ""

    # RFQ lock check
    is_locked = _is_rfq_completed(cust_id, item_no)

    return JsonResponse({
        "no": item.no or "",
        "description": item.description or "",
        "template_name": item.template_name or "",
        "base_unit_of_measure": item.base_unit_of_measure or "",
        "shelf_no": item.shelf_no or "",
        "cell": item.cell or "",
        "cell_type": item.cell_type or "",
        "item_category_code": item.item_category_code or "",
        "product_group_code": item.product_group_code or "",
        "status": item.status or "",
        "last_date_modified": item.last_date_modified or "",
        "fixture_no": item.fixture_no or "",
        "no_of_meft": item.no_of_meft or "",
        "no_of_parts": item.no_of_parts or "",
        "customer_name": item.customer_name or "",
        "revision_no": item.revision_no or "",
        "customer_vendor_code": item.customer_vendor_code or "",
        "hsn_sac_code": item.hsn_sac_code or "",
        "costing_method": item.costing_method or "",
        "inventory_posting_group": item.inventory_posting_group or "",
        "price_profit_calculation": item.price_profit_calculation or "",
        "gen_prod_posting_group": item.gen_prod_posting_group or "",
        "replenishment_system": item.replenishment_system or "",
        "qc_applicable": item.qc_applicable or "",
        "manufacturing_policy": item.manufacturing_policy or "",
        "assembly_policy": item.assembly_policy or "",
        "reordering_policy": item.reordering_policy or "",
        "include_inventory": item.include_inventory or "",
        "gst_credit": item.gst_credit or "",
        "flushing_method": item.flushing_method or "",
        "template_applied": item.template_applied or "",
        "rounding_precision": item.rounding_precision or "",
        "gst_group_code": item.gst_group_code or "",
        "last_ecn": last_ecn,
        "is_locked": is_locked,
    })


def get_hsn_gst(request):
    """Return GST Group Code for a given HSN/SAC Code. Also handles FG+ABT auto-fill."""
    hsn = request.GET.get("hsn", "").strip()
    template = request.GET.get("template_name", "").strip()
    category_code = request.GET.get("item_category_code", "").strip()

    # FG template auto-fill override (Access logic)
    auto_hsn = ""
    if template.upper() == "FG":
        if category_code.upper() == "ABT":
            auto_hsn = "87083000"
        elif category_code:
            auto_hsn = "87089900"

    # If auto_hsn determined, use that to look up GST
    lookup_code = auto_hsn if auto_hsn else hsn
    gst_group_code = ""
    try:
        h = HSNCode.objects.filter(code=lookup_code).first()
        if h:
            gst_group_code = h.gst_group_code or ""
    except Exception:
        pass

    return JsonResponse({
        "auto_hsn": auto_hsn,
        "gst_group_code": gst_group_code,
    })


# ─────────────────────────────────────────────────────────────────────────────
# CRUD – Add / Update / Delete
# ─────────────────────────────────────────────────────────────────────────────

@require_active_customer
@require_POST
def add_item(request):
    """Add new item to tbl_itemcard + create ECN:0 ORIGINAL row in tbl_itemcard_ecn."""
    customer_id = request.active_customer['id']
    customer_name = request.active_customer['name']
    p = request.POST

    item_no = p.get("no", "").strip()
    template_name = p.get("templatename", "").strip()
    item_category_code = p.get("item_category_code", "").strip()
    product_group_code = p.get("product_group_code", "").strip()
    base_unit_of_measure = p.get("base_unit_of_measure", "").strip()
    hsn_sac_code = p.get("hsn", "").strip()

    # ── Validations ─────────────────────────────────────────────────────────
    errors = []
    if not item_no:
        errors.append("Item Number is required.")
    if not template_name:
        errors.append("Template Name is required.")
    if not item_category_code:
        errors.append("Item Category Code is required.")
    if not product_group_code:
        errors.append("Product Group Code is required.")
    if not base_unit_of_measure:
        errors.append("Base Unit of Measure is required.")
    if not hsn_sac_code:
        errors.append("HSN/SAC Code is required.")

    # Numeric fields
    no_of_meft = p.get("noofmeet", "").strip()
    no_of_parts = p.get("noofparts", "").strip()
    if no_of_meft and not no_of_meft.isdigit():
        errors.append("No Of MEFT must be numeric.")
    if no_of_parts and not no_of_parts.isdigit():
        errors.append("No Of Parts must be numeric.")

    if errors:
        return JsonResponse({"success": False, "errors": errors}, status=400)

    # Duplicate check
    if ItemCard.objects.filter(no=item_no).exists():
        return JsonResponse({"success": False, "errors": [
            f"Item number '{item_no}' already exists. Cannot create duplicate."
        ]}, status=400)

    monthyear, fy, quarter = _compute_fy_quarter()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fields = {
        'template_name': template_name,
        'description': p.get("description", ""),
        'base_unit_of_measure': base_unit_of_measure,
        'shelf_no': p.get("shelf_no", ""),
        'cell': p.get("cell", ""),
        'cell_type': p.get("cell_type", ""),
        'item_category_code': item_category_code,
        'product_group_code': product_group_code,
        'status': p.get("status", ""),
        'fixture_no': p.get("fixture", ""),
        'no_of_meft': no_of_meft,
        'no_of_parts': no_of_parts,
        'customer_name': p.get("custname_short", ""),
        'revision_no': p.get("revision", ""),
        'customer_vendor_code': p.get("custVenderCode", ""),
        'hsn_sac_code': hsn_sac_code,
        'costing_method': p.get("costingmethod", ""),
        'inventory_posting_group': p.get("inventory", ""),
        'price_profit_calculation': p.get("priceprofit", ""),
        'gen_prod_posting_group': p.get("genpro", ""),
        'replenishment_system': p.get("replenishment", ""),
        'qc_applicable': p.get("qc", ""),
        'manufacturing_policy': p.get("manu", ""),
        'assembly_policy': p.get("assembly", ""),
        'reordering_policy': p.get("reordering", ""),
        'include_inventory': p.get("inventoryinclude", ""),
        'gst_credit': p.get("gst", ""),
        'flushing_method': p.get("flushing", ""),
        'template_applied': p.get("template_applied", ""),
        'rounding_precision': p.get("rounding", ""),
        'gst_group_code': p.get("gstgroup", ""),
    }

    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tbl_itemcard (
                    no, customerid, customername, template_name, description,
                    base_unit_of_measure, shelf_no, cell, cell_type,
                    item_category_code, product_group_code, status,
                    last_date_modified, fixture_no, no_of_meft, no_of_parts,
                    customer_name, revision_no, customer_vendor_code, hsn_sac_code,
                    costing_method, inventory_posting_group, price_profit_calculation,
                    gen_prod_posting_group, replenishment_system, qc_applicable,
                    manufacturing_policy, assembly_policy, reordering_policy,
                    include_inventory, gst_credit, flushing_method, template_applied,
                    rounding_precision, gst_group_code, monthyear, fy, quarter
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                [
                    item_no, customer_id, customer_name, fields['template_name'], fields['description'],
                    fields['base_unit_of_measure'], fields['shelf_no'], fields['cell'], fields['cell_type'],
                    fields['item_category_code'], fields['product_group_code'], fields['status'],
                    now_str, fields['fixture_no'], fields['no_of_meft'], fields['no_of_parts'],
                    fields['customer_name'], fields['revision_no'], fields['customer_vendor_code'], fields['hsn_sac_code'],
                    fields['costing_method'], fields['inventory_posting_group'], fields['price_profit_calculation'],
                    fields['gen_prod_posting_group'], fields['replenishment_system'], fields['qc_applicable'],
                    fields['manufacturing_policy'], fields['assembly_policy'], fields['reordering_policy'],
                    fields['include_inventory'], fields['gst_credit'], fields['flushing_method'], fields['template_applied'],
                    fields['rounding_precision'], fields['gst_group_code'], monthyear, fy, quarter,
                ],
            )

        # Create initial ECN:0 ORIGINAL record
        _insert_itemcard_ecn("ECN:0", "ORIGINAL", customer_id, customer_name, item_no,
                              fields, monthyear, fy, quarter)

        # Initial RFQ / Item Registration in tbl_rfq_details
        user_name = request.user.username if (request.user and request.user.is_authenticated) else "SYSTEM"
        _register_rfq_details(customer_id, customer_name, item_no, user_name)

        return JsonResponse({"success": True, "message": "Record saved!", "item_no": item_no})

    except Exception as e:
        logger.exception("add_item error for item_no=%s", item_no)
        return JsonResponse({"success": False, "errors": [str(e)]}, status=500)


@require_active_customer
@require_POST
def update_item(request):
    """Update existing item in tbl_itemcard and sync tbl_itemcard_ecn ECN:0 ORIGINAL row."""
    customer_id = request.active_customer['id']
    p = request.POST
    item_no = p.get("no", "").strip()

    if not item_no:
        return JsonResponse({"success": False, "errors": ["Item number is required."]}, status=400)

    # Numeric fields
    no_of_meft = p.get("noofmeet", "").strip()
    no_of_parts = p.get("noofparts", "").strip()
    if no_of_meft and not no_of_meft.isdigit():
        return JsonResponse({"success": False, "errors": ["No Of MEFT must be numeric."]}, status=400)
    if no_of_parts and not no_of_parts.isdigit():
        return JsonResponse({"success": False, "errors": ["No Of Parts must be numeric."]}, status=400)

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE tbl_itemcard SET
                    template_name=%s, description=%s, base_unit_of_measure=%s, shelf_no=%s,
                    cell=%s, cell_type=%s, item_category_code=%s, product_group_code=%s,
                    status=%s, last_date_modified=%s, fixture_no=%s, no_of_meft=%s, no_of_parts=%s,
                    customer_name=%s, revision_no=%s, customer_vendor_code=%s, hsn_sac_code=%s,
                    costing_method=%s, inventory_posting_group=%s, price_profit_calculation=%s,
                    gen_prod_posting_group=%s, replenishment_system=%s, qc_applicable=%s,
                    manufacturing_policy=%s, assembly_policy=%s, reordering_policy=%s,
                    include_inventory=%s, gst_credit=%s, flushing_method=%s, template_applied=%s,
                    rounding_precision=%s, gst_group_code=%s, is_download=NULL
                WHERE no=%s AND customerid=%s
                """,
                [
                    p.get("templatename"), p.get("description"), p.get("base_unit_of_measure"), p.get("shelf_no"),
                    p.get("cell"), p.get("cell_type"), p.get("item_category_code"), p.get("product_group_code"),
                    p.get("status"), now_str, p.get("fixture"), no_of_meft, no_of_parts,
                    p.get("custname_short"), p.get("revision"), p.get("custVenderCode"), p.get("hsn"),
                    p.get("costingmethod"), p.get("inventory"), p.get("priceprofit"),
                    p.get("genpro"), p.get("replenishment"), p.get("qc"),
                    p.get("manu"), p.get("assembly"), p.get("reordering"),
                    p.get("inventoryinclude"), p.get("gst"), p.get("flushing"), p.get("template_applied"),
                    p.get("rounding"), p.get("gstgroup"),
                    item_no, customer_id,
                ],
            )
            # Sync ECN:0 ORIGINAL row
            cur.execute(
                """
                UPDATE tbl_itemcard_ecn SET
                    template_name=%s, description=%s, base_unit_of_measure=%s, shelf_no=%s,
                    cell=%s, cell_type=%s, item_category_code=%s, product_group_code=%s,
                    status=%s, last_date_modified=%s, fixture_no=%s, no_of_meft=%s, no_of_parts=%s,
                    customer_name=%s, revision_no=%s, customer_vendor_code=%s, hsn_sac_code=%s,
                    costing_method=%s, inventory_posting_group=%s, price_profit_calculation=%s,
                    gen_prod_posting_group=%s, replenishment_system=%s, qc_applicable=%s,
                    manufacturing_policy=%s, assembly_policy=%s, reordering_policy=%s,
                    include_inventory=%s, gst_credit=%s, flushing_method=%s, template_applied=%s,
                    rounding_precision=%s, gst_group_code=%s
                WHERE "No"=%s AND customerid=%s AND ecn_id='ECN:0'
                """,
                [
                    p.get("templatename"), p.get("description"), p.get("base_unit_of_measure"), p.get("shelf_no"),
                    p.get("cell"), p.get("cell_type"), p.get("item_category_code"), p.get("product_group_code"),
                    p.get("status"), now_str, p.get("fixture"), no_of_meft, no_of_parts,
                    p.get("custname_short"), p.get("revision"), p.get("custVenderCode"), p.get("hsn"),
                    p.get("costingmethod"), p.get("inventory"), p.get("priceprofit"),
                    p.get("genpro"), p.get("replenishment"), p.get("qc"),
                    p.get("manu"), p.get("assembly"), p.get("reordering"),
                    p.get("inventoryinclude"), p.get("gst"), p.get("flushing"), p.get("template_applied"),
                    p.get("rounding"), p.get("gstgroup"),
                    item_no, customer_id,
                ],
            )

        # Sync customer name / audit in tbl_rfq_details
        user_name = request.user.username if (request.user and request.user.is_authenticated) else "SYSTEM"
        customer_name = request.active_customer.get('name', '')
        _register_rfq_details(customer_id, customer_name, item_no, user_name)

        return JsonResponse({"success": True, "message": "Record updated successfully!"})

    except Exception as e:
        logger.exception("update_item error for item_no=%s", item_no)
        return JsonResponse({"success": False, "errors": [str(e)]}, status=500)


@require_active_customer
@require_POST
def delete_item(request):
    """Delete item from tbl_itemcard (not tbl_itemcard_ecn — ECN history is preserved)."""
    customer_id = request.active_customer['id']
    item_no = request.POST.get("no", "").strip()

    if not item_no:
        return JsonResponse({"success": False, "errors": ["Item number is required."]}, status=400)

    try:
        with connection.cursor() as cur:
            cur.execute(
                "DELETE FROM tbl_itemcard WHERE no=%s AND customerid=%s",
                [item_no, customer_id],
            )
        return JsonResponse({"success": True, "message": "Record deleted successfully!"})
    except Exception as e:
        logger.exception("delete_item error for item_no=%s", item_no)
        return JsonResponse({"success": False, "errors": [str(e)]}, status=500)


def get_item_list(request):
    """Return JSON list of items for the active customer (for grid + dropdown refresh)."""
    customer_id = request.GET.get("customer_id", "")
    items = list(
        ItemCard.objects.filter(customer_id=customer_id)
        .values("no", "description", "template_name", "status", "hsn_sac_code", "last_date_modified")
    )
    return JsonResponse({"items": items})


# ─────────────────────────────────────────────────────────────────────────────
# ECN Request Form
# ─────────────────────────────────────────────────────────────────────────────

@require_active_customer
def ecn_request_page(request):
    """Render ECN Request form."""
    customer_id = request.active_customer['id']
    customer_name = request.active_customer['name']

    items = list(ItemCard.objects.filter(customer_id=customer_id).values_list("no", flat=True))
    template_names = ApplyTemplate.objects.values_list("template_name", flat=True).distinct()
    uoms = UnitOfMeasure.objects.all()
    item_categories = ItemCategory.objects.all()
    product_groups = ProductGroup.objects.all()
    cells = Cell.objects.all()
    cell_types = CellType.objects.all()
    hsn_codes = HSNCode.objects.all()

    return render(request, "item_creation/frm_itemcreation_ecn.html", {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "s_items": items,
        "template_names": template_names,
        "uoms": uoms,
        "item_categories": item_categories,
        "product_groups": product_groups,
        "cells": cells,
        "cell_types": cell_types,
        "hsn_codes": hsn_codes,
    })


def get_ecn_item_details(request):
    """Return latest ECN/item data for ECN form population + revision history."""
    item_no = request.GET.get("item_no", "").strip()
    customer_id = request.GET.get("customer_id", "").strip()

    if not item_no:
        return JsonResponse({"error": "Missing item_no"}, status=400)

    ecn_count = _get_ecn_count(customer_id, item_no)

    # Load from latest ECN or from tbl_itemcard if no ECNs yet
    if ecn_count == 0:
        item = ItemCard.objects.filter(no=item_no, customer_id=customer_id).first()
        if not item:
            return JsonResponse({"error": "Item not found"}, status=404)
        data = {
            "ecn_id": "ECN:0",
            "ecn_type": "REPLICATE",
            "customer_id": item.customer_id or "",
            "customer_name_org": item.customer_name_org or "",
            "template_name": item.template_name or "",
            "description": item.description or "",
            "base_unit_of_measure": item.base_unit_of_measure or "",
            "shelf_no": item.shelf_no or "",
            "cell": item.cell or "",
            "cell_type": item.cell_type or "",
            "item_category_code": item.item_category_code or "",
            "product_group_code": item.product_group_code or "",
            "status": item.status or "",
            "last_date_modified": item.last_date_modified or "",
            "fixture_no": item.fixture_no or "",
            "no_of_meft": item.no_of_meft or "",
            "no_of_parts": item.no_of_parts or "",
            "customer_name": item.customer_name or "",
            "revision_no": item.revision_no or "",
            "customer_vendor_code": item.customer_vendor_code or "",
            "hsn_sac_code": item.hsn_sac_code or "",
            "costing_method": item.costing_method or "",
            "inventory_posting_group": item.inventory_posting_group or "",
            "price_profit_calculation": item.price_profit_calculation or "",
            "gen_prod_posting_group": item.gen_prod_posting_group or "",
            "replenishment_system": item.replenishment_system or "",
            "qc_applicable": item.qc_applicable or "",
            "manufacturing_policy": item.manufacturing_policy or "",
            "assembly_policy": item.assembly_policy or "",
            "reordering_policy": item.reordering_policy or "",
            "include_inventory": item.include_inventory or "",
            "gst_credit": item.gst_credit or "",
            "flushing_method": item.flushing_method or "",
            "template_applied": item.template_applied or "",
            "rounding_precision": item.rounding_precision or "",
            "gst_group_code": item.gst_group_code or "",
            "ecn_count": 0,
        }
    else:
        # Latest ECN (highest numbered)
        last_ecn_id = f"ECN:{ecn_count - 1}"
        with connection.cursor() as cur:
            cur.execute(
                """SELECT ecn_id, ecn_type, customerid, customername,
                          template_name, description, base_unit_of_measure, shelf_no,
                          cell, cell_type, item_category_code, product_group_code,
                          status, last_date_modified, fixture_no, no_of_meft, no_of_parts,
                          customer_name, revision_no, customer_vendor_code, hsn_sac_code,
                          costing_method, inventory_posting_group, price_profit_calculation,
                          gen_prod_posting_group, replenishment_system, qc_applicable,
                          manufacturing_policy, assembly_policy, reordering_policy,
                          include_inventory, gst_credit, flushing_method, template_applied,
                          rounding_precision, gst_group_code
                   FROM tbl_itemcard_ecn
                   WHERE "No"=%s AND customerid=%s AND ecn_id=%s
                   LIMIT 1""",
                [item_no, customer_id, last_ecn_id],
            )
            row = cur.fetchone()
            if not row:
                return JsonResponse({"error": "ECN record not found"}, status=404)
            cols = [c[0] for c in cur.description]
            d = dict(zip(cols, row))

        data = {
            "ecn_id": d.get("ecn_id", ""),
            "ecn_type": "REPLICATE",
            "customer_id": d.get("customerid", ""),
            "customer_name_org": d.get("customername", ""),
            "template_name": d.get("template_name", "") or "",
            "description": d.get("description", "") or "",
            "base_unit_of_measure": d.get("base_unit_of_measure", "") or "",
            "shelf_no": d.get("shelf_no", "") or "",
            "cell": d.get("cell", "") or "",
            "cell_type": d.get("cell_type", "") or "",
            "item_category_code": d.get("item_category_code", "") or "",
            "product_group_code": d.get("product_group_code", "") or "",
            "status": d.get("status", "") or "",
            "last_date_modified": d.get("last_date_modified", "") or "",
            "fixture_no": d.get("fixture_no", "") or "",
            "no_of_meft": d.get("no_of_meft", "") or "",
            "no_of_parts": d.get("no_of_parts", "") or "",
            "customer_name": d.get("customer_name", "") or "",
            "revision_no": d.get("revision_no", "") or "",
            "customer_vendor_code": d.get("customer_vendor_code", "") or "",
            "hsn_sac_code": d.get("hsn_sac_code", "") or "",
            "costing_method": d.get("costing_method", "") or "",
            "inventory_posting_group": d.get("inventory_posting_group", "") or "",
            "price_profit_calculation": d.get("price_profit_calculation", "") or "",
            "gen_prod_posting_group": d.get("gen_prod_posting_group", "") or "",
            "replenishment_system": d.get("replenishment_system", "") or "",
            "qc_applicable": d.get("qc_applicable", "") or "",
            "manufacturing_policy": d.get("manufacturing_policy", "") or "",
            "assembly_policy": d.get("assembly_policy", "") or "",
            "reordering_policy": d.get("reordering_policy", "") or "",
            "include_inventory": d.get("include_inventory", "") or "",
            "gst_credit": d.get("gst_credit", "") or "",
            "flushing_method": d.get("flushing_method", "") or "",
            "template_applied": d.get("template_applied", "") or "",
            "rounding_precision": d.get("rounding_precision", "") or "",
            "gst_group_code": d.get("gst_group_code", "") or "",
            "ecn_count": ecn_count,
        }

    # ECN history rows for the table
    history = []
    with connection.cursor() as cur:
        cur.execute(
            """SELECT ecn_id, ecn_type, "No", description, template_name,
                      revision_no, status, last_date_modified
               FROM tbl_itemcard_ecn
               WHERE "No"=%s AND customerid=%s
               ORDER BY ecn_id""",
            [item_no, customer_id],
        )
        cols = [c[0] for c in cur.description]
        for row in cur.fetchall():
            history.append(dict(zip(cols, row)))

    data["history"] = history
    return JsonResponse(data)


@require_active_customer
@require_POST
def create_ecn(request):
    """Create a new ECN REPLICATE revision and update the master tbl_itemcard."""
    customer_id = request.active_customer['id']
    customer_name = request.active_customer['name']
    p = request.POST

    item_no = p.get("ecn_item_no", "").strip()
    if not item_no:
        return JsonResponse({"success": False, "errors": ["Item number is required."]}, status=400)

    # Numeric fields validation
    no_of_meft = p.get("ecn_noofmeet", "").strip()
    no_of_parts = p.get("ecn_noofparts", "").strip()
    if no_of_meft and not no_of_meft.isdigit():
        return JsonResponse({"success": False, "errors": ["No Of MEFT must be numeric."]}, status=400)
    if no_of_parts and not no_of_parts.isdigit():
        return JsonResponse({"success": False, "errors": ["No Of Parts must be numeric."]}, status=400)

    ecn_count = _get_ecn_count(customer_id, item_no)
    new_ecn_id = f"ECN:{ecn_count}"
    monthyear, fy, quarter = _compute_fy_quarter()

    fields = {
        'template_name': p.get("ecn_templatename", ""),
        'description': p.get("ecn_description", ""),
        'base_unit_of_measure': p.get("ecn_base_unit_of_measure", ""),
        'shelf_no': p.get("ecn_shelf_no", ""),
        'cell': p.get("ecn_cell", ""),
        'cell_type': p.get("ecn_cell_type", ""),
        'item_category_code': p.get("ecn_item_category_code", ""),
        'product_group_code': p.get("ecn_product_group_code", ""),
        'status': p.get("ecn_status", ""),
        'fixture_no': p.get("ecn_fixture", ""),
        'no_of_meft': no_of_meft,
        'no_of_parts': no_of_parts,
        'customer_name': p.get("ecn_custname_short", ""),
        'revision_no': p.get("ecn_revision", ""),
        'customer_vendor_code': p.get("ecn_custVenderCode", ""),
        'hsn_sac_code': p.get("ecn_hsn", ""),
        'costing_method': p.get("ecn_costingmethod", ""),
        'inventory_posting_group': p.get("ecn_inventory", ""),
        'price_profit_calculation': p.get("ecn_priceprofit", ""),
        'gen_prod_posting_group': p.get("ecn_genpro", ""),
        'replenishment_system': p.get("ecn_replenishment", ""),
        'qc_applicable': p.get("ecn_qc", ""),
        'manufacturing_policy': p.get("ecn_manu", ""),
        'assembly_policy': p.get("ecn_assembly", ""),
        'reordering_policy': p.get("ecn_reordering", ""),
        'include_inventory': p.get("ecn_inventoryinclude", ""),
        'gst_credit': p.get("ecn_gst", ""),
        'flushing_method': p.get("ecn_flushing", ""),
        'template_applied': p.get("ecn_template_applied", ""),
        'rounding_precision': p.get("ecn_rounding", ""),
        'gst_group_code': p.get("ecn_gstgroup", ""),
    }

    try:
        # Insert new ECN revision row
        _insert_itemcard_ecn(new_ecn_id, "REPLICATE", customer_id, customer_name,
                              item_no, fields, monthyear, fy, quarter)

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update master tbl_itemcard with latest changes
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE tbl_itemcard SET
                    template_name=%s, description=%s, base_unit_of_measure=%s, shelf_no=%s,
                    cell=%s, cell_type=%s, item_category_code=%s, product_group_code=%s,
                    status=%s, last_date_modified=%s, fixture_no=%s, no_of_meft=%s, no_of_parts=%s,
                    customer_name=%s, revision_no=%s, customer_vendor_code=%s, hsn_sac_code=%s,
                    costing_method=%s, inventory_posting_group=%s, price_profit_calculation=%s,
                    gen_prod_posting_group=%s, replenishment_system=%s, qc_applicable=%s,
                    manufacturing_policy=%s, assembly_policy=%s, reordering_policy=%s,
                    include_inventory=%s, gst_credit=%s, flushing_method=%s, template_applied=%s,
                    rounding_precision=%s, gst_group_code=%s, is_download=NULL
                WHERE no=%s AND customerid=%s
                """,
                [
                    fields['template_name'], fields['description'], fields['base_unit_of_measure'], fields['shelf_no'],
                    fields['cell'], fields['cell_type'], fields['item_category_code'], fields['product_group_code'],
                    fields['status'], now_str, fields['fixture_no'], fields['no_of_meft'], fields['no_of_parts'],
                    fields['customer_name'], fields['revision_no'], fields['customer_vendor_code'], fields['hsn_sac_code'],
                    fields['costing_method'], fields['inventory_posting_group'], fields['price_profit_calculation'],
                    fields['gen_prod_posting_group'], fields['replenishment_system'], fields['qc_applicable'],
                    fields['manufacturing_policy'], fields['assembly_policy'], fields['reordering_policy'],
                    fields['include_inventory'], fields['gst_credit'], fields['flushing_method'], fields['template_applied'],
                    fields['rounding_precision'], fields['gst_group_code'],
                    item_no, customer_id,
                ],
            )

        return JsonResponse({
            "success": True,
            "message": f"ECN updated successfully! New ECN: {new_ecn_id}",
            "new_ecn_id": new_ecn_id,
        })

    except Exception as e:
        logger.exception("create_ecn error for item_no=%s", item_no)
        return JsonResponse({"success": False, "errors": [str(e)]}, status=500)


@require_active_customer
@require_POST
def delete_ecn(request):
    """Delete all ECN records for item (from tbl_itemcard_ecn only)."""
    customer_id = request.active_customer['id']
    item_no = request.POST.get("ecn_item_no", "").strip()

    if not item_no:
        return JsonResponse({"success": False, "errors": ["Item number is required."]}, status=400)

    try:
        with connection.cursor() as cur:
            cur.execute(
                'DELETE FROM tbl_itemcard_ecn WHERE "No"=%s AND customerid=%s',
                [item_no, customer_id],
            )
        return JsonResponse({"success": True, "message": "ECN records deleted successfully!"})
    except Exception as e:
        logger.exception("delete_ecn error for item_no=%s", item_no)
        return JsonResponse({"success": False, "errors": [str(e)]}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# Send Email
# ─────────────────────────────────────────────────────────────────────────────

def send_item_email(request):
    if request.method != "POST":
        return redirect("item_creation")

    form = SendItemEmailForm(request.POST)
    customer_id = request.POST.get("customer_id", "")
    customer_name = request.POST.get("customer_name", "")

    redirect_url = "{}?{}".format(
        reverse("item_creation"),
        urlencode({"customer_id": customer_id, "name": customer_name}),
    )

    if not form.is_valid():
        messages.error(request, "Please enter a valid recipient email address.")
        return redirect(redirect_url)

    recipient_email = form.cleaned_data["recipient_email"]
    item_no = request.POST.get("no", "")

    html_body = (
        f"Hi<br><br>"
        f"New RFQ received and Item created with ID: {item_no}<br><br>"
        f"All the documents are saved in folder<br><br>"
        f"Please start preparing your respective details to timely close this RFQ.<br><br><br>"
        f"Regards,<br>Voss Team"
    )

    email = EmailMultiAlternatives(
        subject=f"Item Creation: {item_no}",
        body="Please view this email in an HTML-supported client.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.attach_alternative(html_body, "text/html")

    try:
        email.send()
        messages.success(request, f"Item details sent successfully to {recipient_email}.")
    except Exception as exc:
        messages.error(request, f"Email could not be sent: {exc}")

    return redirect(redirect_url)
