"""services.py — Business-logic layer for BOC (Bill of Components) processing.

This module is intentionally import-free of Django views/request objects so
that its functions can be unit-tested without an HTTP context.

Public API
----------
validate_boc_prerequisites(customer_id, item_creation_id)
    Raises ValidationError if upstream gates have not been passed.

generate_or_sync_boc(customer_id, item_creation_id, user, source_items, rm_flag)
    Full sync: validate -> delete stale rows -> bulk-create new rows.

export_boc_to_excel(customer_id, item_creation_id) -> BytesIO
    Builds an openpyxl workbook from OfferSheetRMConversion and returns the
    byte stream ready to be served as an HTTP attachment.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    BomCreation,
    BopCreation,
    OfferSheetRMConversion,
    RFQDetails,
)

logger = logging.getLogger(__name__)

User = get_user_model()

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_TWO_PLACES = Decimal("0.01")


def _round2(value: Any) -> Decimal:
    """Return *value* rounded to 2 decimal places as a Decimal."""
    try:
        return Decimal(str(value)).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


# ---------------------------------------------------------------------------
# 1. Prerequisite validation
# ---------------------------------------------------------------------------

def validate_boc_prerequisites(
    customer_id: str,
    item_creation_id: str,
) -> None:
    """Verify all upstream gates before allowing a BOC sync.

    Checks (in order):
    1. BOM must exist with remark='Approved' for the given customer and item.
    2. BOP must exist with action_status='Approved' for the given customer and item.
    3. RFQ must NOT be completed (is_completed must not equal 'Yes').

    Parameters
    ----------
    customer_id:
        The customer identifier string.
    item_creation_id:
        The item creation identifier string.

    Raises
    ------
    ValidationError
        On the first failed gate, with a human-readable message.
    """
    # Gate 1: BOM Approved
    bom_approved = BomCreation.objects.filter(
        customer_id=customer_id,
        item_creation_id=item_creation_id,
        remark="Approved",
    ).exists()

    if not bom_approved:
        raise ValidationError(
            f"BOM is not approved for Customer '{customer_id}', "
            f"Item '{item_creation_id}'. "
            "Please ensure BOM remark is set to 'Approved' before syncing BOC."
        )

    # Gate 2: BOP Approved
    bop_approved = BopCreation.objects.filter(
        customer_id=customer_id,
        itemcreation_id=item_creation_id,
        action_status="Approved",
    ).exists()

    if not bop_approved:
        raise ValidationError(
            f"BOP is not approved for Customer '{customer_id}', "
            f"Item '{item_creation_id}'. "
            "Please ensure BOP action_status is set to 'Approved' before syncing BOC."
        )

    # Gate 3: RFQ not yet completed
    rfq_completed = RFQDetails.objects.filter(
        customer_id=customer_id,
        itemcreation_id=item_creation_id,
        is_completed="Yes",
    ).exists()

    if rfq_completed:
        raise ValidationError(
            f"RFQ is already completed for Customer '{customer_id}', "
            f"Item '{item_creation_id}'. "
            "BOC sync is not allowed after RFQ completion."
        )


# ---------------------------------------------------------------------------
# 2. Generate / sync BOC rows
# ---------------------------------------------------------------------------

def generate_or_sync_boc(
    customer_id: str,
    item_creation_id: str,
    user: Any,
    source_items: list[dict[str, Any]],
    rm_flag: str,
) -> int:
    """Validate prerequisites then atomically replace OfferSheetRMConversion rows.

    The delete and bulk-insert are wrapped in a single transaction.atomic block
    so they are never partially visible to concurrent readers.

    Parameters
    ----------
    customer_id:
        Customer identifier.
    item_creation_id:
        Item creation identifier.
    user:
        The currently authenticated Django user (stored on each created row).
    source_items:
        A list of dicts representing the BOM/RM lines to persist.
        Required keys per item:
            part_number       (str, optional)
            raw_material_desc (str)
            tube_size         (str, optional)
            unit              (str)
            internal_cost     (numeric, optional)
            rate_per_unit     (numeric)
            qnty              (numeric)
        total_cost is calculated here as round(qnty * rate_per_unit, 2).
    rm_flag:
        Identifies the RM category/flag (e.g. 'RM', 'Tube').

    Returns
    -------
    int
        The number of records inserted.

    Raises
    ------
    ValidationError
        If upstream prerequisites are not satisfied.
    """
    # Validate before touching any data
    validate_boc_prerequisites(customer_id, item_creation_id)

    today = date.today()
    authenticated_user = user if (user and getattr(user, "is_authenticated", False)) else None

    # Pre-build ORM objects outside the transaction to minimise lock time
    new_records: list[OfferSheetRMConversion] = []
    for item in source_items:
        qnty         = _round2(item.get("qnty", 0))
        rate_per_unit = _round2(item.get("rate_per_unit", 0))
        total_cost   = _round2(qnty * rate_per_unit)

        internal_cost_raw = item.get("internal_cost")
        internal_cost = _round2(internal_cost_raw) if internal_cost_raw is not None else None

        new_records.append(
            OfferSheetRMConversion(
                part_number=item.get("part_number") or None,
                raw_material_desc=item.get("raw_material_desc", ""),
                tube_size=item.get("tube_size") or None,
                unit=item.get("unit", ""),
                internal_cost=internal_cost,
                rate_per_unit=rate_per_unit,
                qnty=qnty,
                total_cost=total_cost,
                rm_flag=rm_flag,
                customer_id=customer_id,
                item_creation_id=item_creation_id,
                process_date=today,
            )
        )

    with transaction.atomic():
        deleted_count, _ = OfferSheetRMConversion.objects.filter(
            customer_id=customer_id,
            item_creation_id=item_creation_id,
            rm_flag=rm_flag,
        ).delete()

        logger.info(
            "[BOC] Deleted %d stale OfferSheetRMConversion rows "
            "(customer=%r, item=%r, rm_flag=%r)",
            deleted_count,
            customer_id,
            item_creation_id,
            rm_flag,
        )

        OfferSheetRMConversion.objects.bulk_create(new_records, batch_size=500)
        inserted = len(new_records)

        logger.info(
            "[BOC] Inserted %d OfferSheetRMConversion rows "
            "(customer=%r, item=%r, rm_flag=%r)",
            inserted,
            customer_id,
            item_creation_id,
            rm_flag,
        )

    return inserted


# ---------------------------------------------------------------------------
# 3. Excel export
# ---------------------------------------------------------------------------

# Ordered list of (model_field_name, display_header_label)
_EXPORT_COLUMN_MAP: list[tuple[str, str]] = [
    ("part_number",       "Part Number"),
    ("raw_material_desc", "Raw Material Description"),
    ("tube_size",         "Tube Size"),
    ("unit",              "Unit"),
    ("internal_cost",     "Internal Cost"),
    ("rate_per_unit",     "Rate Per Unit"),
    ("qnty",              "Quantity"),
    ("total_cost",        "Total Cost"),
    ("rm_flag",           "RM Flag"),
    ("customer_id",       "Customer ID"),
    ("item_creation_id",  "Item Creation ID"),
    ("process_date",      "Process Date"),
]

def export_boc_to_excel(
    customer_id: str,
    item_creation_id: str,
) -> BytesIO:
    """Build an openpyxl workbook from OfferSheetRMConversion and return it as BytesIO.

    The workbook has a single sheet 'BOC Data' with:
    - A styled header row (navy background, white bold text).
    - All matching rows for the given customer and item.
    - Auto-sized columns (capped at 50 chars wide).
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    header_fill = PatternFill("solid", fgColor="2E3A59")
    header_font = Font(bold=True, color="FFFFFF", size=10)
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    data_font = Font(size=9)
    data_align = Alignment(horizontal="left", vertical="center")
    thin = Side(style="thin")
    thin_border = Border(left=thin, right=thin, top=thin, bottom=thin)

    fields  = [field for field, _ in _EXPORT_COLUMN_MAP]
    headers = [label for _, label in _EXPORT_COLUMN_MAP]

    qs = (
        OfferSheetRMConversion.objects
        .filter(customer_id=customer_id, item_creation_id=item_creation_id)
        .order_by("id")
        .values(*fields)
    )

    # Build workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOC Data"

    # Header row
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill      = header_fill
        cell.font      = header_font
        cell.alignment = header_align
        cell.border    = thin_border

    ws.row_dimensions[1].height = 22

    # Data rows
    for row_idx, record in enumerate(qs, start=2):
        for col_idx, field in enumerate(fields, start=1):
            raw   = record.get(field)
            value = str(raw) if raw is not None else ""
            cell  = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font      = data_font
            cell.alignment = data_align
            cell.border    = thin_border


    # Auto-size columns
    for col_idx in range(1, len(headers) + 1):
        col_letter = get_column_letter(col_idx)
        max_width  = len(headers[col_idx - 1])
        for row_idx in range(2, ws.max_row + 1):
            cell_val = ws.cell(row=row_idx, column=col_idx).value or ""
            max_width = max(max_width, len(str(cell_val)))
        ws.column_dimensions[col_letter].width = min(max_width + 4, 50)

    # Stream to BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 4. Access Query Implementation for IMPORTED BOC
# ---------------------------------------------------------------------------

def fetch_boc_part_details(customer_id: str, item_creation_id: str, categorisation: str = "LOCAL BOC") -> list[dict[str, Any]]:
    """Fetch BOC part details matching the MS Access query logic.

    Reproduces Access query:
    SELECT DISTINCT 
        t1.Part_Number,
        t1.Description,
        t1.Unit_of_Measure_Code,
        t1.Quantity,
        t1.Internal_Cost,
        Nz(t1.[Settle Price],0) AS [Settle Price],
        (t1.Quantity*Nz(t1.[Settle Price],0)) AS Cost,
        t1.Categorisation,
        t1.Customer_ID,
        t1.ItemCreation_Id,
        t1.BOMCreation_ID
    FROM zQry_OfferSheet_PartDetails AS t1
    LEFT JOIN tbl_BomCreation AS t2
        ON (t1.BOMCreation_ID = t2.BOMCreation_ID)
        AND (t1.Table_id = t2.table_id)
    WHERE
        t1.Categorisation = categorisation
        AND t1.Customer_ID = customer_id
        AND t1.ItemCreation_Id = item_creation_id;
    """
    if not customer_id or not item_creation_id:
        return []

    records: list[dict[str, Any]] = []
    seen = set()

    cat_target = (categorisation or "LOCAL BOC").strip().upper()

    # Strategy 1a: Try querying zQry_OfferSheet_PartDetails with LEFT JOIN tbl_BomCreation
    sql_strategy_1a = """
        SELECT DISTINCT
            t1."Part_Number",
            t1."Description",
            t1."Unit_of_Measure_Code",
            t1."Quantity",
            t1."Internal_Cost",
            COALESCE(t1."Settle Price", 0) AS settle_price,
            (COALESCE(t1."Quantity", 0) * COALESCE(t1."Settle Price", 0)) AS cost,
            t1."Categorisation",
            t1."Customer_ID",
            t1."ItemCreation_Id",
            t1."BOMCreation_ID"
        FROM "zQry_OfferSheet_PartDetails" AS t1
        LEFT JOIN "tbl_BomCreation" AS t2
            ON (t1."BOMCreation_ID" = t2."BOMCreation_ID" OR t1."BOMCreation_ID" = t2."BOMCreation_Id")
            AND (t1."Table_id" = t2."table_id" OR t1."Table_id" = t2."Table_Id")
        WHERE
            UPPER(t1."Categorisation") = UPPER(%s)
            AND LOWER(t1."Customer_ID") = LOWER(%s)
            AND LOWER(t1."ItemCreation_Id") = LOWER(%s);
    """

    # Strategy 1b: Try tbl_OfferSheetPartDetails with LEFT JOIN tbl_BomCreation
    sql_strategy_1b = """
        SELECT DISTINCT
            t1."Part_Number",
            t1."Description",
            t1."Unit_of_Measure_Code",
            t1."Quantity",
            t1."Internal_Cost",
            COALESCE(t1."Settle Price", 0) AS settle_price,
            (COALESCE(t1."Quantity", 0) * COALESCE(t1."Settle Price", 0)) AS cost,
            t1."Categorisation",
            t1."Customer_ID",
            t1."ItemCreation_Id",
            t1."BOMCreation_ID"
        FROM "tbl_OfferSheetPartDetails" AS t1
        LEFT JOIN "tbl_BomCreation" AS t2
            ON (t1."BOMCreation_ID" = t2."BOMCreation_Id" OR t1."BOMCreation_ID" = t2."BOMCreation_ID")
            AND (t1."Table_id" = t2."Table_Id" OR t1."Table_id" = t2."table_id")
        WHERE
            UPPER(t1."Categorisation") = UPPER(%s)
            AND LOWER(t1."Customer_ID") = LOWER(%s)
            AND LOWER(t1."ItemCreation_Id") = LOWER(%s);
    """

    # Strategy 2: Join tbl_bomcreation_partselection and tbl_bomcreation + tbl_bom_partdetails_master
    sql_strategy_2 = """
        SELECT DISTINCT
            ps."Part_Number" AS part_number,
            COALESCE(ps."Description", '') AS description,
            COALESCE(ps."Unit_of_Measure_Code", '') AS uom_code,
            COALESCE(ps."Quantity", 0) AS quantity,
            COALESCE(pdm."Cost_Price", 0.0) AS internal_cost,
            COALESCE(pdm."Settle_Price", 0.0) AS settle_price,
            (COALESCE(ps."Quantity", 0) * COALESCE(pdm."Settle_Price", 0.0)) AS cost,
            ps."Categorisation" AS categorisation,
            COALESCE(bc."Customer_ID", ps."Customer_ID") AS customer_id,
            COALESCE(bc."ItemCreation_Id", ps."ItemCreation_Id") AS item_creation_id,
            COALESCE(bc."BOMCreation_Id", ps."BOMCreation_ID") AS bom_creation_id
        FROM "tbl_bomcreation_partselection" AS ps
        LEFT JOIN "tbl_bomcreation" AS bc
            ON ps."BOMCreation_ID" = bc."BOMCreation_Id"
        LEFT JOIN "tbl_bom_partdetails_master" AS pdm
            ON LOWER(ps."Part_Number") = LOWER(pdm."Part_No")
        WHERE
            UPPER(ps."Categorisation") = UPPER(%s)
            AND (LOWER(bc."Customer_ID") = LOWER(%s) OR LOWER(ps."Customer_ID") = LOWER(%s))
            AND (LOWER(bc."ItemCreation_Id") = LOWER(%s) OR LOWER(ps."ItemCreation_Id") = LOWER(%s));
    """

    # Strategy 3: Standard unquoted lowercase Postgres tables
    sql_strategy_3 = """
        SELECT DISTINCT
            ps.part_number,
            COALESCE(ps.description, '') AS description,
            COALESCE(ps.unit_of_measure_code, '') AS uom_code,
            COALESCE(ps.quantity, 0) AS quantity,
            COALESCE(pdm.cost_price, 0.0) AS internal_cost,
            COALESCE(pdm.settle_price, 0.0) AS settle_price,
            (COALESCE(ps.quantity, 0) * COALESCE(pdm.settle_price, 0.0)) AS cost,
            ps.categorisation,
            COALESCE(bc.customer_id, ps.customer_id) AS customer_id,
            COALESCE(bc.itemcreation_id, ps.itemcreation_id) AS item_creation_id,
            COALESCE(bc.bomcreation_id, ps.bomcreation_id) AS bom_creation_id
        FROM tbl_bomcreation_partselection AS ps
        LEFT JOIN tbl_bomcreation AS bc
            ON ps.bomcreation_id = bc.bomcreation_id
        LEFT JOIN tbl_bom_partdetails_master AS pdm
            ON LOWER(ps.part_number) = LOWER(pdm.part_no)
        WHERE
            UPPER(ps.categorisation) = UPPER(%s)
            AND (LOWER(bc.customer_id) = LOWER(%s) OR LOWER(ps.customer_id) = LOWER(%s))
            AND (LOWER(bc.itemcreation_id) = LOWER(%s) OR LOWER(ps.itemcreation_id) = LOWER(%s));
    """

    from django.db import connection
    from django.db.models import Q

    # Determine possible customer IDs (e.g. 'CUST-005' and '5')
    cust_ids = [customer_id.strip()]
    if '-' in customer_id:
        num_part = customer_id.split('-')[-1].lstrip('0')
        if num_part and num_part not in cust_ids:
            cust_ids.append(num_part)
    elif customer_id.strip().isdigit():
        padded = f"CUST-{int(customer_id.strip()):03d}"
        if padded not in cust_ids:
            cust_ids.append(padded)

    item_ids = [item_creation_id.strip()]
    if item_creation_id.strip().lstrip('0') and item_creation_id.strip().lstrip('0') not in item_ids:
        item_ids.append(item_creation_id.strip().lstrip('0'))

    # Categories to attempt
    cats_to_try = [cat_target]
    if "RAW" in cat_target:
        for c in ["RAW MATERIAL", "Raw Material", "RM"]:
            if c not in cats_to_try:
                cats_to_try.append(c)

    for c_try in cats_to_try:
        for c_id in cust_ids:
            for i_id in item_ids:
                for sql_query in [sql_strategy_1a, sql_strategy_1b, sql_strategy_2, sql_strategy_3]:
                    try:
                        with connection.cursor() as cursor:
                            num_params = sql_query.count("%s")
                            if num_params == 5:
                                params = [c_try, c_id, c_id, i_id, i_id]
                            else:
                                params = [c_try, c_id, i_id]
                            cursor.execute(sql_query, params)
                            rows = cursor.fetchall()
                            if rows:
                                for r in rows:
                                    p_num = str(r[0] or "").strip()
                                    desc = str(r[1] or "").strip()
                                    uom = str(r[2] or "").strip()
                                    qty = float(r[3] or 0)
                                    icost = float(r[4] or 0)
                                    sprice = float(r[5] or 0)
                                    cost = float(r[6] or (qty * sprice))
                                    cat = str(r[7] or c_try).strip()
                                    row_cid = str(r[8] or c_id).strip()
                                    row_iid = str(r[9] or i_id).strip()
                                    b_id = str(r[10] or "").strip()

                                    key = (p_num, desc, uom, qty, icost, sprice, cost, cat, row_cid, row_iid, b_id)
                                    if key not in seen:
                                        seen.add(key)
                                        records.append({
                                            "Part_Number": p_num,
                                            "part_number": p_num,
                                            "Description": desc,
                                            "description": desc,
                                            "Unit_of_Measure_Code": uom,
                                            "uom_code": uom,
                                            "Quantity": qty,
                                            "quantity": qty,
                                            "Internal_Cost": icost,
                                            "internal_rate": icost,
                                            "internal_cost": icost,
                                            "Settle Price": sprice,
                                            "settle_price": sprice,
                                            "Cost": cost,
                                            "cost": cost,
                                            "Categorisation": cat,
                                            "categorisation": cat,
                                            "Customer_ID": row_cid,
                                            "customer_id": row_cid,
                                            "ItemCreation_Id": row_iid,
                                            "item_creation_id": row_iid,
                                            "BOMCreation_ID": b_id,
                                            "bom_creation_id": b_id,
                                        })
                                if records:
                                    return records
                    except Exception as e:
                        logger.debug(f"[{c_try}] SQL query strategy failed: {e}")
                        continue

    # Strategy 4: Fallback to model-level ORM lookups if raw SQL returns no rows
    try:
        from apps.CostingBCCal.models import OfferSheetPartDetails
        cust_q = Q(customer_id__in=cust_ids)
        item_q = Q(itemcreation_id__in=item_ids)

        cat_q = Q(categorisation__iexact=cat_target)
        if "RAW" in cat_target:
            cat_q |= Q(categorisation__icontains="raw") | Q(categorisation__iexact="RM")

        osp_qs = OfferSheetPartDetails.objects.filter(
            cust_q,
            item_q,
        ).filter(cat_q)

        if osp_qs.exists():
            for item in osp_qs:
                p_num = (item.part_number or "").strip()
                desc = (item.description or "").strip()
                uom = (item.unit_of_measure_code or "").strip()
                qty = float(item.quantity or 0)
                icost = float(item.internal_cost or 0)
                sprice = float(item.settle_price or 0)
                cost = round(qty * sprice, 4)
                cat = (item.categorisation or cat_target).strip()
                b_id = str(item.bomcreation_id or "").strip()
                key = (p_num, desc, uom, qty, icost, sprice, cost, cat, customer_id, item_creation_id, b_id)
                if key not in seen:
                    seen.add(key)
                    records.append({
                        "Part_Number": p_num, "part_number": p_num,
                        "Description": desc, "description": desc,
                        "Unit_of_Measure_Code": uom, "uom_code": uom,
                        "Quantity": qty, "quantity": qty,
                        "Internal_Cost": icost, "internal_rate": icost, "internal_cost": icost,
                        "Settle Price": sprice, "settle_price": sprice,
                        "Cost": cost, "cost": cost,
                        "Categorisation": cat, "categorisation": cat,
                        "Customer_ID": customer_id, "customer_id": customer_id,
                        "ItemCreation_Id": item_creation_id, "item_creation_id": item_creation_id,
                        "BOMCreation_ID": b_id, "bom_creation_id": b_id,
                    })
            if records:
                return records
    except Exception as e:
        logger.debug(f"OfferSheetPartDetails ORM lookup failed: {e}")

    # Strategy 5: Query BOM models (BOMHeader, BOMTransaction, BOMPartDetailsMaster)
    try:
        from apps.BOM.models import BOMTransaction, BOMHeader, BOMPartDetailsMaster

        cust_q = Q(customer_id__in=cust_ids)
        item_q = Q(item_creation_id__in=item_ids)

        bom_headers = list(BOMHeader.objects.filter(
            cust_q,
            item_q,
        ).values_list("bom_creation_id", flat=True))

        if bom_headers:
            cat_q = Q(categorisation__iexact=cat_target)
            if "RAW" in cat_target:
                cat_q |= Q(categorisation__icontains="raw") | Q(categorisation__iexact="RM")

            transactions = BOMTransaction.objects.filter(
                bom_creation_id__in=bom_headers,
            ).filter(cat_q)
            part_nos = [t.part_number for t in transactions if t.part_number]
            master_map = {}
            if part_nos:
                for master in BOMPartDetailsMaster.objects.filter(part_no__in=part_nos):
                    master_map[master.part_no.strip().lower()] = master
                    master_map[master.part_no.strip().lower()] = master

            for tx in transactions:
                p_num = (tx.part_number or "").strip()
                master = master_map.get(p_num.lower())
                desc = (tx.description or (master.part_description if master else "") or "").strip()
                uom = (tx.uom_code or (master.base_unit_of_measure if master else "") or "").strip()
                qty = float(tx.quantity or 0)
                icost = float(master.cost_price if (master and master.cost_price is not None) else 0)
                sprice = float(master.settle_price if (master and master.settle_price is not None) else 0)
                cost = round(qty * sprice, 4)
                cat = cat_target
                b_id = str(tx.bom_creation_id or "").strip()

                key = (p_num, desc, uom, qty, icost, sprice, cost, cat, customer_id, item_creation_id, b_id)
                if key not in seen:
                    seen.add(key)
                    records.append({
                        "Part_Number": p_num,
                        "part_number": p_num,
                        "Description": desc,
                        "description": desc,
                        "Unit_of_Measure_Code": uom,
                        "uom_code": uom,
                        "Quantity": qty,
                        "quantity": qty,
                        "Internal_Cost": icost,
                        "internal_rate": icost,
                        "internal_cost": icost,
                        "Settle Price": sprice,
                        "settle_price": sprice,
                        "Cost": cost,
                        "cost": cost,
                        "Categorisation": cat,
                        "categorisation": cat,
                        "Customer_ID": customer_id,
                        "customer_id": customer_id,
                        "ItemCreation_Id": item_creation_id,
                        "item_creation_id": item_creation_id,
                        "BOMCreation_ID": b_id,
                        "bom_creation_id": b_id,
                    })
    except Exception as e:
        logger.error(f"[{cat_target}] Fallback model lookup failed: {e}")

    return records


def fetch_imported_boc_part_details(customer_id: str, item_creation_id: str) -> list[dict[str, Any]]:
    """Fetch IMPORTED BOC part details matching the MS Access query logic."""
    return fetch_boc_part_details(customer_id, item_creation_id, categorisation="IMPORTED BOC")


def fetch_local_boc_part_details(customer_id: str, item_creation_id: str) -> list[dict[str, Any]]:
    """Fetch LOCAL BOC part details matching the MS Access query logic."""
    return fetch_boc_part_details(customer_id, item_creation_id, categorisation="LOCAL BOC")


