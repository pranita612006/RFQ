import csv
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction, connection
from django.db.models import Q, F, FloatField, Value, ExpressionWrapper
from django.db.models.functions import Coalesce
from decimal import Decimal, ROUND_HALF_UP
from config.decorators import require_active_customer
from apps.customer_creation.models import CustomerInfo
from apps.item_creation.models import ItemCard
from .models import (
    NormsDetails,
    OfferSheetRMConversion,
    DTAssignmentYearData,
    BomCreation,
    BopCreation,
    BopTab,
    BopTolling,
    OfferSheetPartDetails,
    OfferSheetBOC,
    OfferSheetTransCost,
)



# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

import html

def _safe_float(val, default=None):
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _safe_format_cost(val):
    f = _safe_float(val)
    if f is None:
        return ""
    return f"{f:,.2f}"

def _norm_cat(cat_str):
    if not cat_str:
        return ""
    s = html.unescape(str(cat_str))
    return s.replace("&amp;", "&").strip().lower()



def _norms_to_dict(norm):
    """Serialise a NormsDetails instance to a plain dict."""
    return {
        "Sr_No":               norm.Sr_No,
        "Norms_Code":          norm.Norms_Code          or "",
        "Sheet_Name":          norm.Sheet_Name          or "",
        "Customer_Name":       norm.Customer_Name       or "",
        "Cell_Location":       norm.Cell_Location       or "",
        "Cell_Value":          norm.Cell_Value          or "",
        "Location":            norm.Location            or "",
        "Export_Path":         norm.Export_Path         or "",
        "local_bo_flag":       norm.local_bo_flag,
        "total_local_bo_flag": norm.total_local_bo_flag,
        "packaging_series":    norm.packaging_series,
        "packaging_proto":     norm.packaging_proto,
        "os_template":         norm.os_template         or "",
    }


# ---------------------------------------------------------------------------
# Main form page
# ---------------------------------------------------------------------------

@require_active_customer
def CostingBCCal_form(request):
    """Render the Costing BC Calculations form page with top-dropdown context."""
    selected_customer = (
        request.GET.get("customer_id")
        or request.GET.get("customer")
        or request.session.get("active_customer_id")
        or (request.active_customer.get("id") if hasattr(request, "active_customer") else "")
        or ""
    ).strip()
    selected_item = (
        request.GET.get("item_creation_id")
        or request.GET.get("item_id")
        or ""
    ).strip()
    selected_year = (
        request.GET.get("assignment_year")
        or request.GET.get("year")
        or "2026"
    ).strip()

    # Customer ID dropdown (tbl_customerinfo)
    try:
        customers = list(
            CustomerInfo.objects.order_by("customer_id")
            .values_list("customer_id", flat=True)
            .distinct()
        )
    except Exception:
        customers = []

    # Item Creation ID dropdown (tbl_itemcard)
    try:
        item_qs = ItemCard.objects.all()
        if selected_customer:
            item_qs = item_qs.filter(
                Q(customer_id__iexact=selected_customer)
                | Q(customer_vendor_code__iexact=selected_customer)
            )
        item_ids = list(
            item_qs.order_by("no")
            .values_list("no", flat=True)
            .distinct()
        )
    except Exception:
        item_ids = []

    if not selected_item and item_ids:
        selected_item = item_ids[0]

    context = {
        "customers": customers,
        "item_ids":  item_ids,
        "selected_customer": selected_customer,
        "selected_item": selected_item,
        "selected_year": selected_year,
    }
    return render(request, "CostingBCCal/CostingBCCal_form.html", context)




# ---------------------------------------------------------------------------
# Norms API — List all records
# ---------------------------------------------------------------------------

@require_GET
def norms_list(request):
    """
    GET /CostingBCCal/norms/list/
    Returns all NormsDetails records in ASCENDING order (1, 2, 3...).
    Applies filters only if query parameters are present.
    """
    customer_id = (
        request.GET.get("customer_id", "").strip() or 
        request.GET.get("customer", "").strip()
    )
    item_id = (
        request.GET.get("item_creation_id", "").strip() or 
        request.GET.get("norms_code", "").strip() or 
        request.GET.get("item_id", "").strip()
    )

    # Base Queryset ordered strictly by Sr_No ascending
    qs = NormsDetails.objects.all().order_by("Sr_No")

    # Optional filtering if parameters exist
    if item_id:
        qs = qs.filter(Norms_Code__iexact=item_id)
    if customer_id:
        qs = qs.filter(Customer_Name__iexact=customer_id)

    data = [_norms_to_dict(n) for n in qs]
    return JsonResponse({"records": data}, safe=False)





# ---------------------------------------------------------------------------
# Norms API — Dropdown options
# ---------------------------------------------------------------------------

@require_GET
def norms_dropdowns(request):
    """
    GET /CostingBCCal/norms/dropdowns/
    Returns two lists:
        customer_options  : [{"label": "CName | NCode", "customer_name": ..., "norms_code": ..., "sr_no": ...}, ...]
        norms_code_options: [{"label": "NCode | Sheet",  "norms_code": ...,   "sheet_name": ..., "sr_no": ...}, ...]
    """
    norms = list(NormsDetails.objects.order_by("Customer_Name", "Norms_Code"))

    # Customer Name dropdown — unique per Customer_Name + Norms_Code combination
    seen_customers = set()
    customer_options = []
    for n in norms:
        key = (n.Customer_Name or "", n.Norms_Code or "")
        if key not in seen_customers:
            seen_customers.add(key)
            customer_options.append({
                "label":         f"{n.Customer_Name or ''} | {n.Norms_Code or ''}",
                "customer_name": n.Customer_Name or "",
                "norms_code":    n.Norms_Code    or "",
                "sr_no":         n.Sr_No,
            })

    # Norms Code dropdown — unique per Norms_Code + Sheet_Name combination
    seen_norms = set()
    norms_code_options = []
    for n in norms:
        key = (n.Norms_Code or "", n.Sheet_Name or "")
        if key not in seen_norms:
            seen_norms.add(key)
            norms_code_options.append({
                "label":      f"{n.Norms_Code or ''} | {n.Sheet_Name or ''}",
                "norms_code": n.Norms_Code or "",
                "sheet_name": n.Sheet_Name or "",
                "sr_no":      n.Sr_No,
            })

    return JsonResponse({
        "customer_options":   customer_options,
        "norms_code_options": norms_code_options,
    })


# ---------------------------------------------------------------------------
# Norms API — Update Cell_Location / Cell_Value
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def norms_update(request):
    """
    POST /CostingBCCal/norms/update/
    Body (JSON): { "sr_no": <int>, "cell_location": "...", "cell_value": "..." }
    Updates the matching row and returns the updated record.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid JSON body."}, status=400)

    sr_no         = payload.get("sr_no")
    cell_location = payload.get("cell_location", "")
    cell_value    = payload.get("cell_value", "")

    if not sr_no:
        return JsonResponse({"success": False, "error": "sr_no is required."}, status=400)

    try:
        norm = NormsDetails.objects.get(Sr_No=sr_no)
    except NormsDetails.DoesNotExist:
        return JsonResponse({"success": False, "error": f"Record with Sr_No={sr_no} not found."}, status=404)

    norm.Cell_Location = cell_location
    norm.Cell_Value    = cell_value
    norm.save(update_fields=["Cell_Location", "Cell_Value"])

    return JsonResponse({"success": True, "record": _norms_to_dict(norm)})


# ---------------------------------------------------------------------------
# Norms API — Update Location / Export_Path
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def norms_change_path(request):
    """
    POST /CostingBCCal/norms/change_path/
    Body (JSON): { "sr_no": <int>, "field": "location"|"export_path", "value": "..." }
    Updates either Location or Export_Path for the given record.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid JSON body."}, status=400)

    sr_no = payload.get("sr_no")
    field = payload.get("field", "").lower()
    value = payload.get("value", "")

    if not sr_no:
        return JsonResponse({"success": False, "error": "sr_no is required."}, status=400)
    if field not in ("location", "export_path"):
        return JsonResponse({"success": False, "error": "field must be 'location' or 'export_path'."}, status=400)

    try:
        norm = NormsDetails.objects.get(Sr_No=sr_no)
    except NormsDetails.DoesNotExist:
        return JsonResponse({"success": False, "error": f"Record with Sr_No={sr_no} not found."}, status=404)

    if field == "location":
        norm.Location = value
        norm.save(update_fields=["Location"])
    else:
        norm.Export_Path = value
        norm.save(update_fields=["Export_Path"])

    return JsonResponse({"success": True, "record": _norms_to_dict(norm)})


# ---------------------------------------------------------------------------
# Norms API — CSV Export
# ---------------------------------------------------------------------------

@require_GET
def norms_export(request):
    """
    GET /CostingBCCal/norms/export/
    Optional: ?customer=<name>  — filter by Customer_Name before exporting.
    Streams a CSV file download containing all matching Norms records.
    """
    customer_filter = request.GET.get("customer", "").strip()

    qs = NormsDetails.objects.all().order_by("Sr_No")
    if customer_filter:
        qs = qs.filter(Customer_Name__iexact=customer_filter)

    response = HttpResponse(content_type="text/csv")
    filename = f"norms_export_{customer_filter or 'all'}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        "Sr_No", "Norms_Code", "Sheet_Name", "Customer_Name",
        "Cell_Location", "Cell_Value", "Location", "Export_Path",
    ])
    for n in qs:
        writer.writerow([
            n.Sr_No, n.Norms_Code or "", n.Sheet_Name or "",
            n.Customer_Name or "", n.Cell_Location or "", n.Cell_Value or "",
            n.Location or "", n.Export_Path or "",
        ])

    return response



# ---------------------------------------------------------------------------
# Internal Conversion API & Export
# ---------------------------------------------------------------------------

def _get_internal_conversion_raw_data(customer_id="", itemcreation_id="", year="", norm_type=None):
    """
    Fetches filtered records from CostingInternalConversion.
    - itemcreation_id is the primary filter (case-insensitive).
    - customer_id is optional; used only to narrow results further when present.
    - norm_type (mhr_category) matching is done in Python after fetching,
      using .strip().lower() so 'Lower', 'LOWER', 'lower' all match.
    - Falls back to BOPTab if CostingInternalConversion has no matching rows.
    """
    customer_id     = (customer_id     or "").strip()
    itemcreation_id = (itemcreation_id or "").strip()
    norm_type_lower = norm_type.strip().lower() if norm_type else None

    # itemcreation_id is mandatory — return early if absent
    if not itemcreation_id:
        return []

    from .models import CostingInternalConversion

    # Primary filter: itemcreation_id only (customer_id narrows only if provided)
    has_qs = False
    try:
        qs = CostingInternalConversion.objects.filter(itemcreation_id__iexact=itemcreation_id)
        if customer_id:
            qs_narrow = qs.filter(customer_id__iexact=customer_id)
            if qs_narrow.exists():
                qs = qs_narrow
        has_qs = qs.exists()
    except Exception as e:
        logger.debug(f"[INTERNAL CONVERSION] CostingInternalConversion query failed: {e}")
        has_qs = False
        qs = None

    # If empty or failed, try BOPTab fallback
    bop_qs = None
    if not has_qs:
        try:
            from apps.BOP.models import BOPTab
            bop_qs = BOPTab.objects.filter(itemcreation_id__iexact=itemcreation_id)
            if customer_id:
                bop_narrow = bop_qs.filter(customer_id__iexact=customer_id)
                if bop_narrow.exists():
                    bop_qs = bop_narrow
        except Exception:
            bop_qs = None

    if not has_qs and (not bop_qs or not bop_qs.exists()):
        return []

    # Deduplicate rows by description in Python
    dedup_dict = {}

    if has_qs and qs:
        try:
            for row in qs:
                desc = (row.description or "").strip()
                if not desc:
                    continue

                row_cat = (row.mhr_category or "").strip().lower()
                if norm_type_lower and row_cat and row_cat != norm_type_lower:
                    continue

                if desc not in dedup_dict:
                    dedup_dict[desc] = {
                        "description":      desc,
                        "run_time_sec":     float(row.run_time_sec or 0.0),
                        "boq":              float(row.boq or 1.0),
                        "mhr":              float(row.mhr or 0.0),
                        "mhr_lower":        float(row.mhr or 0.0),
                        "mhr_standard":     float(row.mhr or 0.0),
                        "customer_id":      row.customer_id or customer_id,
                        "itemcreation_id":  row.itemcreation_id or itemcreation_id,
                        "mhr_category":     row_cat or norm_type_lower or "lower",
                    }
        except Exception as e:
            logger.debug(f"[INTERNAL CONVERSION] Iterating CostingInternalConversion failed: {e}")

    elif bop_qs and bop_qs.exists():
        for bop in bop_qs:
            desc = (bop.description or f"Operation {bop.seq_no or ''}").strip()
            if not desc:
                continue
            if desc not in dedup_dict:
                dedup_dict[desc] = {
                    "description":      desc,
                    "run_time_sec":     float(bop.run_time_sec or 0.0),
                    "boq":              float(bop.boq or 1.0),
                    "mhr_lower":        float(bop.mhr_lower or 0.0),
                    "mhr_standard":     float(bop.mhr_higher or bop.mhr_year or 0.0),
                    "customer_id":      bop.customer_id or customer_id,
                    "itemcreation_id":  bop.itemcreation_id or itemcreation_id,
                    "mhr_category":     norm_type_lower or "lower",
                }

    return list(dedup_dict.values())


def _compute_table_variant(raw_rows, norm_type="lower"):
    """
    Computes automatic table columns for a norm type ('lower' or 'standard'):
    1. MHR
    2. Run_Time_Sec
    3. Per Hour Output = 3600 / Run_Time_Sec
    4. Rate/Unit = MHR / Per Hour Output
    5. Qnty (boq)
    6. Total = Rate/Unit * Qnty
    7. % Contribution = (Row Total / Sum of Total Column) * 100
    """
    rows = []
    total_sum = 0.0

    for r in raw_rows:
        desc = r.get("description", "")
        # Normalise the stored mhr_category for comparison
        row_cat = (r.get("mhr_category") or "").strip().lower()
        norm_type_lower = norm_type.strip().lower() if norm_type else "lower"

        if row_cat == norm_type_lower and r.get("mhr", 0.0):
            mhr = float(r.get("mhr", 0.0) or 0.0)
        else:
            mhr = float(r.get("mhr_lower" if norm_type_lower == "lower" else "mhr_standard", r.get("mhr", 0.0)) or 0.0)

        run_sec = float(r.get("run_time_sec", 0.0) or 0.0)
        boq = float(r.get("boq", 1.0) or 1.0)

        per_hour = round(3600.0 / run_sec, 2) if run_sec > 0 else 0.0
        rate_unit = round(mhr / per_hour, 4) if per_hour > 0 else 0.0
        row_total = round(rate_unit * boq, 2)

        total_sum += row_total

        rows.append({
            "description": desc,
            "mhr": mhr,
            "run_time_sec": run_sec,
            "perhouroutput": per_hour,
            "rateperunit": rate_unit,
            "boq": boq,
            "total": row_total,
            "contributionpercentage": 0.0,
            "mhr_category": norm_type,
            "customer_id": r.get("customer_id", ""),
            "itemcreation_id": r.get("itemcreation_id", ""),
        })

    if total_sum > 0:
        for row in rows:
            row["contributionpercentage"] = round((row["total"] / total_sum) * 100.0, 2)

    return rows, round(total_sum, 2)


@require_GET
def internal_conversion_data(request):
    """
    GET /CostingBCCal/internal-conversion/data/
    Params: customer_id, item_id, year
    Returns computed datasets for Lower Norms and Standard Norms.
    Returns empty lists if either customer_id or item_id is missing/empty.
    """
    customer_id = request.GET.get("customer_id", "").strip()
    # Accept both 'item_id' and 'item_creation_id' as parameter names
    item_id = (
        request.GET.get("item_id", "").strip() or
        request.GET.get("item_creation_id", "").strip()
    )
    year = request.GET.get("year", "2026").strip()

    # Only customer_id is optional — item_id is required to fetch data
    if not item_id:
        return JsonResponse({
            "success": True,
            "lower_norms": [],
            "lower_sum_total": 0.0,
            "standard_norms": [],
            "standard_sum_total": 0.0,
        })

    lower_raw = _get_internal_conversion_raw_data(customer_id, item_id, year, norm_type="lower")
    if not lower_raw:
        lower_raw = _get_internal_conversion_raw_data(customer_id, item_id, year)
    lower_rows, lower_sum = _compute_table_variant(lower_raw, norm_type="lower")

    standard_raw = _get_internal_conversion_raw_data(customer_id, item_id, year, norm_type="standard")
    if not standard_raw:
        standard_raw = _get_internal_conversion_raw_data(customer_id, item_id, year)
    standard_rows, standard_sum = _compute_table_variant(standard_raw, norm_type="standard")

    return JsonResponse({
        "success": True,
        "lower_norms": lower_rows,
        "lower_sum_total": lower_sum,
        "standard_norms": standard_rows,
        "standard_sum_total": standard_sum,
    })



@require_GET
def internal_conversion_export(request):
    """
    GET /CostingBCCal/internal-conversion/export/
    Params: norm_type ('lower'|'standard'), customer_id, item_id, year
    Exports openpyxl / Excel download file: InternalConversion_[NormType]_[ItemCreationID].xlsx
    """
    norm_type = request.GET.get("norm_type", "lower").strip().lower()
    customer_id = request.GET.get("customer_id", "").strip()
    item_id = request.GET.get("item_id", "ITEM").strip()
    year = request.GET.get("year", "2026").strip()

    norm_label = "LowerNorms" if norm_type == "lower" else "StandardNorms"
    filename = f"InternalConversion_{norm_label}_{item_id or 'ALL'}.xlsx"

    raw_data = _get_internal_conversion_raw_data(customer_id, item_id, year, norm_type=norm_type)
    if not raw_data:
        raw_data = _get_internal_conversion_raw_data(customer_id, item_id, year)

    rows, sum_total = _compute_table_variant(raw_data, norm_type=norm_type)


    headers = [
        "Description", "MHR", "Run_Time_Sec", "Per Hour Output",
        "Rate/Unit", "Qnty", "Total", "% Contribution"
    ]

    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Conversion_{norm_label}"

        # Header row
        ws.append(headers)
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="2E266D", end_color="2E266D", fill_type="solid")

        # Data rows
        for r in rows:
            ws.append([
                r["description"],
                r["mhr"],
                r["run_time_sec"],
                r["perhouroutput"],
                r["rateperunit"],
                r["boq"],
                r["total"],
                f"{r['contributionpercentage']}%"
            ])

        # Summary footer row
        ws.append(["TOTAL", "", "", "", "", "", sum_total, "100.0%"])
        footer_row_idx = len(rows) + 2
        for cell in ws[footer_row_idx]:
            cell.font = openpyxl.styles.Font(bold=True)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    except ImportError:
        # Fallback to CSV format if openpyxl is not installed in the Python environment
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="InternalConversion_{norm_label}_{item_id or "ALL"}.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        for r in rows:
            writer.writerow([
                r["description"],
                r["mhr"],
                r["run_time_sec"],
                r["perhouroutput"],
                r["rateperunit"],
                r["boq"],
                r["total"],
                f"{r['contributionpercentage']}%"
            ])
        writer.writerow(["TOTAL", "", "", "", "", "", sum_total, "100.0%"])
        return response


# ---------------------------------------------------------------------------
# DTAssignmentYearData & DTCategoryList HTMX Views
# ---------------------------------------------------------------------------

DEFAULT_DT_CATEGORIES = [
    {"category_name": "Project R&D Costs + Testing + Admin.", "currency": "INR"},
    {"category_name": "Project Tooling Costs", "currency": "INR"},
    {"category_name": "Project Investments", "currency": "INR"},
    {"category_name": "Quick Savings", "currency": "INR"},
    {"category_name": "Project R&D + Testing Recovery", "currency": "INR"},
    {"category_name": "Recovery R&D, Piece Price", "currency": "INR"},
    {"category_name": "Project Tooling Recovery Lump Sum", "currency": "INR"},
    {"category_name": "Project Tooling Recovery Piece Price", "currency": "INR"},
]

def load_assignment_year_data(request):
    """
    GET / POST /CostingBCCal/assignment-year-data/
    Loads Year Assignment Data for DT Entry or Consolidate View based on ?view_mode=
    """
    item_creation_id = (
        request.GET.get("item_creation_id", "").strip() or
        request.POST.get("item_creation_id", "").strip() or
        request.GET.get("item_id", "").strip() or
        request.POST.get("item_id", "").strip() or
        request.GET.get("itemcreation_id", "").strip() or
        request.POST.get("itemcreation_id", "").strip()
    )
    year_str = (
        request.GET.get("assignment_year", "").strip() or 
        request.POST.get("assignment_year", "").strip() or 
        request.GET.get("year", "").strip() or 
        "2026"
    )
    try:
        assignment_year = int(year_str)
    except (ValueError, TypeError):
        assignment_year = 2026

    view_mode = (
        request.GET.get("view_mode", "").strip() or 
        request.POST.get("view_mode", "").strip() or 
        "dt_entry"
    )

    from .models import DTAssignmentYearData, DTCategoryList

    # Fetch configured categories from DB, fallback to default list
    db_categories = []
    try:
        db_categories = list(DTCategoryList.objects.all().order_by("category_name"))
    except Exception:
        db_categories = []

    category_items = []
    if db_categories:
        for c in db_categories:
            c_name = getattr(c, "category_name", None) or getattr(c, "category", "")
            currency = getattr(c, "description", None) or "INR"
            if c_name:
                category_items.append({"category_name": c_name, "currency": currency})
    if not category_items:
        category_items = DEFAULT_DT_CATEGORIES

    # Fetch existing assignment costs for all years.
    # IMPORTANT: Use .values() instead of model instances to read the raw 'category'
    # column directly from tbl_dtassigmentyeardata WITHOUT performing an INNER JOIN
    # to tbl_dtcategorylist. If any FK value has no matching row in DTCategoryList
    # the ORM's implicit JOIN silently drops those assignment rows, causing blank
    # autofill even when data exists in the DB.
    cost_map_by_year = {}  # { (normalized_category_str, year_int): Decimal }
    min_db_year = None
    if item_creation_id:
        try:
            from django.db import connection
            # Use raw SQL with CAST so the query works whether itemcreation_id
            # is stored as INTEGER or TEXT in the database.
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT category, year, cost "
                    "FROM tbl_dtassigmentyeardata "
                    "WHERE CAST(itemcreation_id AS TEXT) = %s "
                    "   OR LTRIM(CAST(itemcreation_id AS TEXT), '0') = LTRIM(%s, '0')",
                    [str(item_creation_id), str(item_creation_id)]
                )
                raw_rows = cur.fetchall()
            logger.debug(
                "[DT] item_creation_id=%r → %d assignment rows fetched (raw SQL)",
                item_creation_id, len(raw_rows)
            )
            for raw_cat, yr, val in raw_rows:
                if yr is not None and raw_cat:
                    norm_key = _norm_cat(raw_cat)
                    cost_map_by_year[(norm_key, int(yr))] = val
                    logger.debug("  mapped (%r, %d) → %s", norm_key, int(yr), val)
        except Exception as exc:
            logger.warning("[DT] cost_map fetch failed for %r: %s", item_creation_id, exc)

    # Five-year cycle range for Consolidate View: selected year + 4 previous years
    # e.g. 2024 selected → [2024, 2023, 2022, 2021, 2020]
    consolidate_years = [assignment_year - i for i in range(5)]
    # Build DT Entry row list (single year)
    dt_entry_assignments = []
    for cat in category_items:
        cat_name = cat["category_name"]
        norm_key = _norm_cat(cat_name)          # same normalization as the map
        val = cost_map_by_year.get((norm_key, assignment_year), None)
        dt_entry_assignments.append({
            "category_name": cat_name,
            "currency": cat.get("currency", "INR"),
            "assigned_value": _safe_float(val),
        })

    # Build Consolidate View row list (multi-year columns)
    consolidate_assignments = []
    for cat in category_items:
        cat_name = cat["category_name"]
        norm_key = _norm_cat(cat_name)
        year_costs = []
        for y in consolidate_years:
            val = cost_map_by_year.get((norm_key, y), None)
            year_costs.append({
                "year": y,
                "cost": val,
                "formatted_cost": _safe_format_cost(val)
            })
        consolidate_assignments.append({
            "category_name": cat_name,
            "currency": cat.get("currency", "INR"),
            "year_costs": year_costs,
        })

    context = {
        "item_creation_id": item_creation_id,
        "assignment_year": assignment_year,
        "view_mode": view_mode,
        "assignments": dt_entry_assignments,
        "consolidate_years": consolidate_years,
        "consolidate_assignments": consolidate_assignments,
        "discount_rate": 10,
        "life_cycle": 5,
        "is_editing": False,
    }
    return render(request, "partials/subfrm_assignment_year_data.html", context)


@require_POST
def update_assignment_category(request):
    """
    POST /CostingBCCal/assignment-year-data/update/
    Saves category cost assignments for the selected item creation and year into tbl_dtassigmentyeardata.
    """
    item_creation_id = (
        request.POST.get("item_creation_id", "").strip() or
        request.GET.get("item_creation_id", "").strip() or
        request.POST.get("item_id", "").strip() or
        request.GET.get("item_id", "").strip()
    )
    customer_id = (
        request.POST.get("customer_id", "").strip() or
        request.GET.get("customer_id", "").strip()
    )
    year_str = (
        request.POST.get("assignment_year", "").strip() or
        request.GET.get("assignment_year", "").strip() or
        request.POST.get("year", "").strip() or
        "2026"
    )
    try:
        assignment_year = int(year_str)
    except (ValueError, TypeError):
        assignment_year = 2026

    categories = request.POST.getlist("categories[]")
    costs = request.POST.getlist("costs[]")

    if item_creation_id and categories:
        from django.db import connection

        # Map existing records for (item_creation_id, assignment_year) by normalized category name
        existing_map = {}
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT id, category FROM tbl_dtassigmentyeardata "
                    "WHERE (CAST(itemcreation_id AS TEXT) = %s OR LTRIM(CAST(itemcreation_id AS TEXT), '0') = LTRIM(%s, '0')) "
                    "  AND year = %s",
                    [str(item_creation_id), str(item_creation_id), assignment_year]
                )
                for r_id, r_cat in cur.fetchall():
                    if r_cat:
                        existing_map[_norm_cat(r_cat)] = r_id
        except Exception as fetch_exc:
            logger.warning("[update_assignment_category] fetch existing failed: %s", fetch_exc)

        for idx, cat_name in enumerate(categories):
            cat_name = cat_name.strip()
            if not cat_name:
                continue
            cost_val_str = costs[idx].strip() if idx < len(costs) else ""
            cost_val = _safe_float(cost_val_str)

            norm_input = _norm_cat(cat_name)
            existing_id = existing_map.get(norm_input)

            try:
                with connection.cursor() as cur:
                    if existing_id:
                        if cost_val is not None:
                            cur.execute(
                                "UPDATE tbl_dtassigmentyeardata SET cost = %s WHERE id = %s",
                                [cost_val, existing_id]
                            )
                        else:
                            cur.execute("DELETE FROM tbl_dtassigmentyeardata WHERE id = %s", [existing_id])
                    else:
                        if cost_val is not None:
                            cur.execute(
                                "INSERT INTO tbl_dtassigmentyeardata (itemcreation_id, category, year, cost, customer_id) VALUES (%s, %s, %s, %s, %s)",
                                [str(item_creation_id), cat_name, assignment_year, cost_val, str(customer_id)]
                            )
            except Exception as sql_exc:
                logger.error("[update_assignment_category] SQL update failed for %s: %s", cat_name, sql_exc)

    return load_assignment_year_data(request)


@require_GET
def export_dt_consolidate(request):
    """
    GET /CostingBCCal/assignment-year-data/export/
    Exports Consolidate View 5-year table to Excel (.xls).
    """
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    year_str = request.GET.get("assignment_year", "").strip() or "2026"
    try:
        assignment_year = int(year_str)
    except (ValueError, TypeError):
        assignment_year = 2026

    # Selected year + 4 previous years (matches Consolidate View display)
    consolidate_years = [assignment_year - i for i in range(5)]

    cost_map_by_year = {}
    if item_creation_id:
        try:
            from django.db import connection
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT category, year, cost "
                    "FROM tbl_dtassigmentyeardata "
                    "WHERE CAST(itemcreation_id AS TEXT) = %s "
                    "   OR LTRIM(CAST(itemcreation_id AS TEXT), '0') = LTRIM(%s, '0')",
                    [str(item_creation_id), str(item_creation_id)]
                )
                for raw_cat, yr, val in cur.fetchall():
                    if raw_cat and yr is not None:
                        norm_key = _norm_cat(raw_cat)
                        cost_map_by_year[(norm_key, int(yr))] = val
        except Exception as exc:
            logger.warning("[DT] export cost_map fetch failed: %s", exc)

    # Build Excel HTML Document
    html_out = []
    html_out.append('<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">')
    html_out.append('<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
    html_out.append('<!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet>')
    html_out.append('<x:Name>Consolidate View</x:Name>')
    html_out.append('<x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions>')
    html_out.append('</x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->')
    html_out.append('<style>')
    html_out.append('table { border-collapse: collapse; font-family: Arial, sans-serif; font-size: 10pt; }')
    html_out.append('th, td { border: 1px solid #9ca3af; padding: 6px 12px; }')
    html_out.append('th { background-color: #9cbde4; font-weight: bold; text-align: center; color: #1f2937; }')
    html_out.append('.info-header { background-color: #eff6ff; font-weight: bold; }')
    html_out.append('.num { text-align: right; }')
    html_out.append('</style></head><body>')

    # Top parameters box
    html_out.append('<table>')
    html_out.append('<tr><td class="info-header">Discount Rate(in %) :</td><td style="text-align:center; font-weight:bold;">10</td></tr>')
    html_out.append('<tr><td class="info-header">Life Cycle(Years) :</td><td style="text-align:center; font-weight:bold;">5</td></tr>')
    html_out.append('</table><br>')

    # Table Header
    html_out.append('<table><thead><tr>')
    html_out.append('<th>Category</th><th>Currency</th>')
    for y in consolidate_years:
        html_out.append(f'<th>{y}</th>')
    html_out.append('</tr></thead><tbody>')

    # Table Rows
    for cat in DEFAULT_DT_CATEGORIES:
        c_name = cat["category_name"]
        norm_key = _norm_cat(c_name)
        currency = cat.get("currency", "INR")
        html_out.append(f'<tr><td>{c_name}</td><td style="text-align:center;">{currency}</td>')
        for y in consolidate_years:
            val = cost_map_by_year.get((norm_key, y), None)
            formatted = _safe_format_cost(val)
            html_out.append(f'<td class="num">{formatted}</td>')
        html_out.append('</tr>')

    html_out.append('</tbody></table></body></html>')

    content = "\n".join(html_out)
    response = HttpResponse(content, content_type="application/vnd.ms-excel")
    filename = f"Consolidate_View_{item_creation_id or 'ALL'}_{assignment_year}.xls"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

# ---------------------------------------------------------------------------
# API: Fetch cost data from tbl_dtassigmentyeardata by item number + category
# ---------------------------------------------------------------------------

@require_GET
def get_cost_by_item_category(request):
    """
    GET /CostingBCCal/get-cost/
    Params: item_creation_id=<str>, year=<int>
    Returns: { "costs": { "<category>": <cost_value>, ... }, "year": <int> }
    Fetches cost data from tbl_dtassigmentyeardata filtered by item_creation_id
    and year, keyed by category name. Used for autofilling the cost column in
    the DT Entry and Consolidate View tables.
    """
    item_creation_id_raw = (
        request.GET.get("item_creation_id", "").strip() or
        request.GET.get("item_id", "").strip() or
        request.GET.get("itemcreation_id", "").strip()
    )
    year_str = (
        request.GET.get("year", "").strip() or
        request.GET.get("assignment_year", "").strip() or
        "2026"
    )
    try:
        year = int(year_str)
    except (ValueError, TypeError):
        year = 2026

    if not item_creation_id_raw:
        return JsonResponse({"costs": {}, "year": year, "error": "item_creation_id is required"}, status=400)

    clean_id = str(item_creation_id_raw)
    unpadded_id = clean_id.lstrip("0") or "0"

    from django.db import connection

    costs = {}
    try:
        # Use raw SQL with CAST so the query works whether itemcreation_id
        # is stored as INTEGER or TEXT in the database.
        with connection.cursor() as cur:
            cur.execute(
                "SELECT category, year, cost "
                "FROM tbl_dtassigmentyeardata "
                "WHERE (CAST(itemcreation_id AS TEXT) = %s OR LTRIM(CAST(itemcreation_id AS TEXT), '0') = %s) AND year = %s",
                [clean_id, unpadded_id, year]
            )
            for row in cur.fetchall():
                category_name = (row[0] or "").strip()
                cost_val = _safe_float(row[2])
                if category_name:
                    # Clean unescaped category name for exact string lookup
                    clean_name = html.unescape(category_name).replace("&amp;", "&").strip()
                    costs[clean_name] = cost_val
                    # Unified normalized key for flexible matching
                    norm_key = _norm_cat(category_name)
                    costs[norm_key] = cost_val
    except Exception as exc:
        logger.warning("[get_cost_by_item_category] query failed for %r year=%d: %s", clean_id, year, exc)
        return JsonResponse({"costs": {}, "year": year, "error": str(exc)}, status=500)

    return JsonResponse({"costs": costs, "year": year})


from django.http import JsonResponse
def dump_db(request):
    import json
    from django.db import connection
    out = []
    with connection.cursor() as cur:
        cur.execute("SELECT itemcreation_id, category, year, cost FROM tbl_dtassigmentyeardata ORDER BY itemcreation_id, category, year")
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            d = dict(zip(cols, r))
            d['cost'] = _safe_float(d['cost'])
            out.append(d)
    return JsonResponse({"data": out})


@require_GET
def boc_debug(request):
    """Diagnostic: shows raw BOM data for a customer+item to help debug autofill.

    GET /CostingBCCal/boc/debug/?customer_id=X&item_creation_id=Y
    """
    from django.db import connection

    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()

    result = {}

    # ── tbl_bomcreation ──────────────────────────────────────────────
    with connection.cursor() as cur:
        cur.execute("""
            SELECT "BOMCreation_Id", "Customer_ID", "ItemCreation_Id", "Remark", "Table_Id"
            FROM tbl_bomcreation
            WHERE LOWER("Customer_ID") = LOWER(%s)
              AND LOWER("ItemCreation_Id") = LOWER(%s)
            LIMIT 20
        """, [customer_id, item_creation_id])
        cols = [d[0] for d in cur.description]
        result["bomcreation_rows"] = [dict(zip(cols, r)) for r in cur.fetchall()]

        # Also get distinct customer/item combos if no rows found
        if not result["bomcreation_rows"]:
            cur.execute('SELECT DISTINCT "Customer_ID", "ItemCreation_Id" FROM tbl_bomcreation LIMIT 20')
            c2 = [d[0] for d in cur.description]
            result["bomcreation_samples"] = [dict(zip(c2, r)) for r in cur.fetchall()]

    # ── tbl_bomcreation_partselection categorisation values ──────────
    with connection.cursor() as cur:
        try:
            cur.execute("""
                SELECT DISTINCT ps."Categorisation", COUNT(*) AS cnt
                FROM tbl_bomcreation_partselection ps
                INNER JOIN tbl_bomcreation bc
                    ON ps."BOMCreation_ID" = bc."BOMCreation_Id"
                WHERE LOWER(bc."Customer_ID") = LOWER(%s)
                  AND LOWER(bc."ItemCreation_Id") = LOWER(%s)
                GROUP BY ps."Categorisation"
            """, [customer_id, item_creation_id])
            result["partselection_categorisations"] = [
                {"categorisation": r[0], "count": r[1]} for r in cur.fetchall()
            ]
        except Exception as e:
            result["partselection_error"] = str(e)

    # ── Service call ─────────────────────────────────────────────────
    try:
        from .services import fetch_boc_part_details
        local_rows    = fetch_boc_part_details(customer_id, item_creation_id, "LOCAL BOC")
        imported_rows = fetch_boc_part_details(customer_id, item_creation_id, "IMPORTED BOC")
        result["service_local_count"]    = len(local_rows)
        result["service_imported_count"] = len(imported_rows)
        result["service_local_sample"]    = local_rows[:3]
        result["service_imported_sample"] = imported_rows[:3]
    except Exception as e:
        result["service_error"] = str(e)

    # ── zQry_OfferSheet_PartDetails view exists? ─────────────────────
    with connection.cursor() as cur:
        cur.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE LOWER(table_name) = 'zqry_offersheet_partdetails'
        """)
        r = cur.fetchone()
        result["zqry_view_exists"] = bool(r)

    return JsonResponse(result, json_dumps_params={"indent": 2})


# ---------------------------------------------------------------------------
# BOC: get_boc_tab_data  — fetch from ztbl_offersheet_boc (LOCAL BOC only)
# ---------------------------------------------------------------------------

def _fetch_boc_data_for_response(customer_id_str: str, item_creation_id_str: str, boc_type: str, categorisation: str) -> list[dict[str, Any]]:
    """Helper to fetch saved BOC rows from OfferSheetBOC or fallback to fetch_boc_part_details."""
    try:
        item_id_int = int(item_creation_id_str)
        saved_qs = OfferSheetBOC.objects.filter(
            customer_id=customer_id_str,
            itemcreation_id=item_id_int,
            boc_type=boc_type,
        ).order_by("id")
    except (ValueError, TypeError):
        saved_qs = OfferSheetBOC.objects.none()

    if saved_qs.exists():
        rows = []
        seen_keys = set()
        for item in saved_qs:
            p_num = (item.part_number or "").strip()
            desc  = (item.description or "").strip()
            uom   = (item.unit_of_measure_code or "").strip()
            qty   = float(item.quantity or 0.0)

            key = (p_num.lower(), desc.lower(), uom.lower(), qty)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            settle = float(item.settle_price or 0.0)
            cost = float(item.cost or round(qty * settle, 4))
            rows.append({
                "id":             item.id,
                "part_number":    p_num,
                "description":    desc,
                "uom_code":       uom,
                "quantity":       qty,
                "internal_rate":  float(item.internal_cost or 0.0),
                "settle_price":   settle,
                "cost":           cost,
                "categorisation": item.categorisation or f"{boc_type} BOC",
            })
        return rows

    # Fallback to initial read via fetch_boc_part_details (deduplicated)
    from .services import fetch_boc_part_details
    raw_rows = fetch_boc_part_details(customer_id_str, str(item_creation_id_str), categorisation)

    rows = []
    for idx, item in enumerate(raw_rows, start=1):
        qty = float(item.get("quantity") or item.get("Quantity") or 0.0)
        settle = float(item.get("settle_price") or item.get("Settle Price") or 0.0)
        cost = round(qty * settle, 4)
        rows.append({
            "id":             idx,
            "part_number":    item.get("part_number") or item.get("Part_Number") or "",
            "description":    item.get("description") or item.get("Description") or "",
            "uom_code":       item.get("uom_code") or item.get("Unit_of_Measure_Code") or "",
            "quantity":       qty,
            "internal_rate":  float(item.get("internal_rate") or item.get("internal_cost") or item.get("Internal_Cost") or 0.0),
            "settle_price":   settle,
            "cost":           cost,
            "categorisation": item.get("categorisation") or item.get("Categorisation") or f"{boc_type} BOC",
        })
    return rows


@require_GET
def get_boc_tab_data(request):
    """Return LOCAL BOC and IMPORTED BOC rows as JSON.

    Mirrors the MS Access SQL queries for LOCAL BOC and IMPORTED BOC.
    """
    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()

    if not customer_id or not item_creation_id:
        return JsonResponse(
            {"status": "error", "message": "Both 'customer_id' and 'item_creation_id' are required."},
            status=400,
        )

    try:
        customer_id_str = str(customer_id).strip()
        local_boc    = _fetch_boc_data_for_response(customer_id_str, item_creation_id, "Local", "LOCAL BOC")
        imported_boc = _fetch_boc_data_for_response(customer_id_str, item_creation_id, "Imported", "IMPORTED BOC")

        return JsonResponse({
            "status": "success",
            "local_boc": local_boc,
            "imported_boc": imported_boc,
        })

    except Exception as exc:
        logger.exception(
            "[get_boc_tab_data] Unexpected error for customer=%r item=%r",
            customer_id,
            item_creation_id,
        )
        return JsonResponse(
            {"status": "error", "message": f"Server error: {exc}"},
            status=500,
        )


# ---------------------------------------------------------------------------
# BOC: save_local_boc_data — Save / Update Local BOC records
# ---------------------------------------------------------------------------

@require_POST
@transaction.atomic
def save_local_boc_data(request):
    """Save or update Local BOC records into ztbl_offersheet_boc."""
    try:
        # ── Parse request body ────────────────────────────────────────────
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)

        customer_id      = payload.get("customer_id")
        item_creation_id = payload.get("item_creation_id")
        rows             = payload.get("rows", [])

        # ── Validate required top-level fields ───────────────────────────
        if customer_id is None or item_creation_id is None:
            return JsonResponse(
                {"status": "error", "message": "'customer_id' and 'item_creation_id' are required."},
                status=400,
            )

        # Normalise IDs to strings (customer_id) and int (itemcreation_id)
        customer_id_str = str(customer_id).strip()
        try:
            item_id_int = int(item_creation_id)
        except (ValueError, TypeError):
            return JsonResponse(
                {"status": "error", "message": "'item_creation_id' must be a valid integer."},
                status=400,
            )

        updater = None
        if hasattr(request, "user") and request.user.is_authenticated:
            updater = request.user.get_full_name() or request.user.get_username()

        # Delete existing saved rows for this customer & item to prevent duplicate accumulation
        OfferSheetBOC.objects.filter(
            customer_id=customer_id_str,
            itemcreation_id=item_id_int,
            boc_type="Local",
        ).delete()

        # Bulk create exact rows submitted by the UI
        boc_objects = []
        for row in rows:
            part_number = str(row.get("part_number")  or "").strip()
            description = str(row.get("description")  or "").strip()
            uom_code    = str(row.get("uom_code") or row.get("unit_of_measure_code") or "").strip()

            try:
                quantity = float(row.get("quantity") or 0.0)
            except (ValueError, TypeError):
                quantity = 0.0

            try:
                rate_raw      = row.get("internal_rate") if row.get("internal_rate") is not None else row.get("internal_cost")
                internal_cost = float(rate_raw or 0.0)
            except (ValueError, TypeError):
                internal_cost = 0.0

            try:
                settle_price = float(row.get("settle_price") or 0.0)
            except (ValueError, TypeError):
                settle_price = 0.0

            cost = round(quantity * settle_price, 4)

            create_data = {
                "part_number":          part_number,
                "description":          description,
                "unit_of_measure_code": uom_code,
                "quantity":             quantity,
                "internal_cost":        internal_cost,
                "settle_price":         settle_price,
                "cost":                 cost,
                "categorisation":       "Local BOC",
                "customer_id":          customer_id_str,
                "itemcreation_id":      item_id_int,
                "boc_type":             "Local",
            }
            if updater:
                create_data["update_by"] = updater
            boc_objects.append(OfferSheetBOC(**create_data))

        if boc_objects:
            OfferSheetBOC.objects.bulk_create(boc_objects)

        return JsonResponse({"status": "success", "message": "Local BOC records saved successfully."})

    except Exception as exc:
        logger.exception("[save_local_boc_data] Unexpected error: %s", exc)
        return JsonResponse({"status": "error", "message": f"Server error: {str(exc)}"}, status=500)


# ---------------------------------------------------------------------------
# BOC: get_imported_boc_tab_data — fetch from ztbl_offersheet_boc (IMPORTED BOC)
# ---------------------------------------------------------------------------

@require_GET
def get_imported_boc_tab_data(request):
    """Return IMPORTED BOC rows as JSON.

    Mirrors the MS Access SQL:
        SELECT DISTINCT
            t1.Part_Number,
            t1.Description,
            t1.Unit_of_Measure_Code,
            t1.Quantity,
            t1.Internal_Cost,
            Nz(t1.[Settle Price], 0) AS [Settle Price],
            (t1.Quantity * Nz(t1.[Settle Price], 0)) AS Cost,
            t1.Categorisation,
            t1.Customer_ID,
            t1.ItemCreation_Id,
            t1.BOMCreation_ID
        FROM zQry_OfferSheet_PartDetails AS t1
        LEFT JOIN tbl_BomCreation AS t2
            ON (t1.BOMCreation_ID = t2.BOMCreation_ID) AND (t1.Table_id = t2.table_id)
        WHERE
            t1.Categorisation = 'IMPORTED BOC'
            AND t1.Customer_ID = <Customer_ID>
            AND t1.ItemCreation_Id = <ItemCreation_ID>;
    """
    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()

    if not customer_id or not item_creation_id:
        return JsonResponse(
            {"status": "error", "message": "Both 'customer_id' and 'item_creation_id' are required."},
            status=400,
        )

    try:
        customer_id_str = str(customer_id).strip()
        imported_boc = _fetch_boc_data_for_response(customer_id_str, item_creation_id, "Imported", "IMPORTED BOC")
        return JsonResponse({"status": "success", "imported_boc": imported_boc})

    except Exception as exc:
        logger.exception(
            "[get_imported_boc_tab_data] Unexpected error for customer=%r item=%r",
            customer_id,
            item_creation_id,
        )
        return JsonResponse(
            {"status": "error", "message": f"Server error: {exc}"},
            status=500,
        )


# ---------------------------------------------------------------------------
# BOC: save_imported_boc_data — Save / Update Imported BOC records
# ---------------------------------------------------------------------------

@require_POST
@transaction.atomic
def save_imported_boc_data(request):
    """Save or update Imported BOC records into ztbl_offersheet_boc."""
    try:
        # ── Parse request body ────────────────────────────────────────────
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)

        customer_id      = payload.get("customer_id")
        item_creation_id = payload.get("item_creation_id")
        rows             = payload.get("rows", [])

        # ── Validate required top-level fields ───────────────────────────
        if customer_id is None or item_creation_id is None:
            return JsonResponse(
                {"status": "error", "message": "'customer_id' and 'item_creation_id' are required."},
                status=400,
            )

        # Normalise IDs to strings (customer_id) and int (itemcreation_id)
        customer_id_str = str(customer_id).strip()
        try:
            item_id_int = int(item_creation_id)
        except (ValueError, TypeError):
            return JsonResponse(
                {"status": "error", "message": "'item_creation_id' must be a valid integer."},
                status=400,
            )

        updater = None
        if hasattr(request, "user") and request.user.is_authenticated:
            updater = request.user.get_full_name() or request.user.get_username()

        # Delete existing saved rows for this customer & item to prevent duplicate accumulation
        OfferSheetBOC.objects.filter(
            customer_id=customer_id_str,
            itemcreation_id=item_id_int,
            boc_type="Imported",
        ).delete()

        # Bulk create exact rows submitted by the UI
        boc_objects = []
        for row in rows:
            part_number = str(row.get("part_number")  or "").strip()
            description = str(row.get("description")  or "").strip()
            uom_code    = str(row.get("uom_code") or row.get("unit_of_measure_code") or "").strip()

            try:
                quantity = float(row.get("quantity") or 0.0)
            except (ValueError, TypeError):
                quantity = 0.0

            try:
                rate_raw      = row.get("internal_rate") if row.get("internal_rate") is not None else row.get("internal_cost")
                internal_cost = float(rate_raw or 0.0)
            except (ValueError, TypeError):
                internal_cost = 0.0

            try:
                settle_price = float(row.get("settle_price") or 0.0)
            except (ValueError, TypeError):
                settle_price = 0.0

            cost = round(quantity * settle_price, 4)

            create_data = {
                "part_number":          part_number,
                "description":          description,
                "unit_of_measure_code": uom_code,
                "quantity":             quantity,
                "internal_cost":        internal_cost,
                "settle_price":         settle_price,
                "cost":                 cost,
                "categorisation":       "Imported BOC",
                "customer_id":          customer_id_str,
                "itemcreation_id":      item_id_int,
                "boc_type":             "Imported",
            }
            if updater:
                create_data["update_by"] = updater
            boc_objects.append(OfferSheetBOC(**create_data))

        if boc_objects:
            OfferSheetBOC.objects.bulk_create(boc_objects)

        return JsonResponse({"status": "success", "message": "Imported BOC records saved successfully."})

    except Exception as exc:
        logger.exception("[save_imported_boc_data] Unexpected error: %s", exc)
        return JsonResponse({"status": "error", "message": f"Server error: {str(exc)}"}, status=500)


# ---------------------------------------------------------------------------
# BOC: process_boc_action
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def process_boc_action(request):
    """Process and sync BOC (Bill of Components) rows for a given item.

    Accepts a JSON body or form-encoded POST with the following fields:
        customer_id      (str, required)
        item_creation_id (str, required)
        rm_flag          (str, required) — e.g. 'RM', 'Tube'
        items            (list, optional) — source BOM lines; defaults to []

    Each item in *items* may contain:
        part_number       (str, optional)
        raw_material_desc (str)
        tube_size         (str, optional)
        unit              (str)
        internal_cost     (numeric, optional)
        rate_per_unit     (numeric)
        qnty              (numeric)

    Returns
    -------
    200 JSON  { "status": "success", "inserted": <int> }
    400 JSON  { "status": "error",   "message": <str> }   — validation failures
    500 JSON  { "status": "error",   "message": <str> }   — unexpected server errors
    """
    from django.core.exceptions import ValidationError as DjValidationError
    from .services import generate_or_sync_boc

    # ── Parse request body ─────────────────────────────────────────────────
    content_type = request.content_type or ""
    if "application/json" in content_type:
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, ValueError) as exc:
            return JsonResponse(
                {"status": "error", "message": f"Invalid JSON body: {exc}"},
                status=400,
            )
    else:
        payload = request.POST

    customer_id      = str(payload.get("customer_id", "")).strip()
    item_creation_id = str(payload.get("item_creation_id", "")).strip()
    rm_flag          = str(payload.get("rm_flag", "")).strip()
    source_items     = payload.get("items", [])

    # Basic input validation
    missing = [k for k, v in [
        ("customer_id", customer_id),
        ("item_creation_id", item_creation_id),
        ("rm_flag", rm_flag),
    ] if not v]
    if missing:
        return JsonResponse(
            {"status": "error", "message": f"Missing required fields: {', '.join(missing)}"},
            status=400,
        )

    if not isinstance(source_items, list):
        return JsonResponse(
            {"status": "error", "message": "'items' must be a list."},
            status=400,
        )

    # ── Delegate to service ────────────────────────────────────────────────
    try:
        inserted = generate_or_sync_boc(
            customer_id=customer_id,
            item_creation_id=item_creation_id,
            user=request.user,
            source_items=source_items,
            rm_flag=rm_flag,
        )
    except DjValidationError as exc:
        return JsonResponse(
            {"status": "error", "message": exc.message},
            status=400,
        )
    except Exception as exc:
        logger.exception(
            "[process_boc_action] Unexpected error for customer=%r item=%r rm_flag=%r",
            customer_id,
            item_creation_id,
            rm_flag,
        )
        return JsonResponse(
            {"status": "error", "message": f"An unexpected server error occurred: {exc}"},
            status=500,
        )

    return JsonResponse({"status": "success", "inserted": inserted})


# ---------------------------------------------------------------------------
# BOC: download_offer_sheet_excel
# ---------------------------------------------------------------------------

@require_GET
def download_offer_sheet_excel(request):
    """Stream an Excel (.xlsx) export of OfferSheetRMConversion for a customer+item.

    Query Parameters
    ----------------
    customer_id      (str, required)
    item_creation_id (str, required)

    Returns
    -------
    200 xlsx  Content-Disposition: attachment; filename="BOC_<customer>_<item>.xlsx"
    400 JSON  { "error": <str> }  — missing parameters
    500 JSON  { "error": <str> }  — unexpected server errors
    """
    from .services import export_boc_to_excel

    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()

    if not customer_id or not item_creation_id:
        return JsonResponse(
            {"error": "Both 'customer_id' and 'item_creation_id' query parameters are required."},
            status=400,
        )

    try:
        buffer = export_boc_to_excel(customer_id=customer_id, item_creation_id=item_creation_id)
    except Exception as exc:
        logger.exception(
            "[download_offer_sheet_excel] Export failed for customer=%r item=%r",
            customer_id,
            item_creation_id,
        )
        return JsonResponse(
            {"error": f"Export failed: {exc}"},
            status=500,
        )

    filename = f"BOC_{customer_id}_{item_creation_id}.xlsx"
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response





@require_GET
def get_items_by_customer(request):
    """Fetch items from ItemCard filtered by customer_id or customer_name."""
    customer_id = (
        request.GET.get("customer_id", "").strip()
        or request.GET.get("customer", "").strip()
        or request.session.get("active_customer_id", "").strip()
    )

    qs = ItemCard.objects.all()
    if customer_id:
        qs = qs.filter(
            Q(customer_id__iexact=customer_id)
            | Q(customer_vendor_code__iexact=customer_id)
        )

    items = list(qs.order_by("no").values("no", "description", "customer_id").distinct())

    formatted_items = [
        {
            "id": item["no"],
            "item_number": item["no"],
            "description": item["description"] or "",
            "customer_id": item["customer_id"] or "",
        }
        for item in items
    ]

    return JsonResponse({
        "status": "success",
        "customer_id": customer_id,
        "items": formatted_items,
    })


# ---------------------------------------------------------------------------
# BOC: get_bop_descriptions — Descriptions for IMPORTED BOC Data Entry dropdown
# ---------------------------------------------------------------------------

@require_GET
def get_bop_descriptions(request):
    """Return unique description list with tube_size and rate_per_unit
    for the 'Data Entry: IMPORTED BOC' dropdown.

    Implements the requested MS Access filtering logic:
    SELECT SubCategory_Name, Tube_Size, SubCategory_Cost 
    FROM zQry_OfferSheet_ConversionDE 
    WHERE SubCategory_Name Is Not Null And Customer_Id=...
    """
    from django.db import connection

    customer_id = request.GET.get('customer_id', '').strip()

    if not customer_id:
        return JsonResponse(
            {'status': 'error', 'message': "'customer_id' is required."},
            status=400,
        )

    # Sometimes UI passes 'CUST 005' but DB expects 'CUST-005'
    customer_id_db = customer_id.replace(" ", "-") if " " in customer_id else customer_id

    descriptions = []
    seen = set()

    try:
        # Strategy 1: The exact view requested by the user
        with connection.cursor() as cursor:
            # Try both exact match and hyphenated match
            cursor.execute("""
                SELECT "SubCategory_Name", "Tube_Size", "SubCategory_Cost"
                FROM "zQry_OfferSheet_ConversionDE"
                WHERE "SubCategory_Name" IS NOT NULL
                AND (LOWER("Customer_Id") = LOWER(%s) OR LOWER("Customer_Id") = LOWER(%s))
            """, [customer_id, customer_id_db])
            
            for row in cursor.fetchall():
                desc = (row[0] or '').strip()
                if not desc or desc in seen:
                    continue
                seen.add(desc)
                descriptions.append({
                    'description': desc,
                    'tube_size':   str(row[1] or '').strip(),
                    'unit':        '',  # Query doesn't provide unit
                    'rate':        float(row[2] or 0.0),
                })

        if descriptions:
            return JsonResponse({'status': 'success', 'descriptions': descriptions})

    except Exception as e:
        logger.debug(f"[get_bop_descriptions] Strategy 1 failed (zQry_OfferSheet_ConversionDE): {e}")

    # Strategy 2 (fallback): Read from tbl_offersheetrmconversion (ignoring item_creation_id like the SQL)
    try:
        qs = (
            OfferSheetRMConversion.objects
            .filter(
                Q(customer_id__iexact=customer_id) | Q(customer_id__iexact=customer_id_db),
                raw_material_desc__isnull=False
            )
            .values('raw_material_desc', 'tube_size', 'unit', 'rate_per_unit')
            .order_by('raw_material_desc')
            .distinct()
        )
        for row in qs:
            desc = (row['raw_material_desc'] or '').strip()
            if desc and desc not in seen:
                seen.add(desc)
                descriptions.append({
                    'description': desc,
                    'tube_size':   (row['tube_size']    or '').strip(),
                    'unit':        (row['unit']          or '').strip(),
                    'rate':        float(row['rate_per_unit'] or 0),
                })
        
        return JsonResponse({'status': 'success', 'descriptions': descriptions})

    except Exception as exc:
        logger.exception('[get_bop_descriptions] Error for customer=%r', customer_id)
        return JsonResponse({'status': 'error', 'message': f'Server error: {exc}'}, status=500)


# ---------------------------------------------------------------------------
# BOC: Over View Data (Local & Imported)
# ---------------------------------------------------------------------------

@require_GET
def get_overview_boc_data(request):
    """Fetch Overview data from ztbl_offersheet_boc based on boc_type.
    Used for 'Over View' section in BOC tab (Local BOC & Imported BOC).
    Reads from the same table that save_local_boc_data / save_imported_boc_data write to.
    """
    customer_id = request.GET.get('customer_id', '').strip()
    item_creation_id = request.GET.get('item_creation_id', '').strip()
    rm_flag = request.GET.get('rm_flag', 'LOCAL BOC').strip()

    if not customer_id:
        return JsonResponse({'status': 'error', 'message': 'Missing customer ID'}, status=400)

    try:
        # Determine boc_type from rm_flag
        flag_upper = rm_flag.upper()
        if 'IMPORT' in flag_upper:
            boc_type = 'Imported'
        else:
            boc_type = 'Local'

        # Build customer filter — accept both raw customer_id and CUST-XXX format
        cust_filter = Q(customer_id__iexact=customer_id)
        if '-' in customer_id:
            num_part = customer_id.split('-')[-1].lstrip('0')
            if num_part:
                cust_filter |= Q(customer_id__iexact=num_part)
        elif customer_id.isdigit():
            padded = f"CUST-{int(customer_id):03d}"
            cust_filter |= Q(customer_id__iexact=padded)

        qs = OfferSheetBOC.objects.filter(cust_filter, boc_type=boc_type)

        if item_creation_id:
            # Try to match as integer (OfferSheetBOC.itemcreation_id is BigIntegerField)
            try:
                item_id_int = int(item_creation_id)
                qs = qs.filter(itemcreation_id=item_id_int)
            except (ValueError, TypeError):
                qs = qs.none()

        qs = qs.order_by('id')

        data = []
        for row in qs:
            data.append({
                'id': row.id,
                'description': (row.description or '').strip(),
                'tube_size': (row.part_number or '').strip(),
                'unit': (row.unit_of_measure_code or '').strip(),
                'rate': float(row.settle_price or 0.0),
                'quantity': float(row.quantity or 0.0),
                'total_cost': float(row.cost or 0.0),
            })

        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        logger.exception("[get_overview_boc_data] Error")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def delete_overview_boc_record(request):
    """Delete a record from ztbl_offersheet_boc by ID (Over View table delete)."""
    try:
        import json
        body = json.loads(request.body)
        record_id = body.get('id')
        if not record_id:
            return JsonResponse({'status': 'error', 'message': 'Missing ID'}, status=400)

        deleted_count, _ = OfferSheetBOC.objects.filter(id=record_id).delete()
        if deleted_count > 0:
            return JsonResponse({'status': 'success', 'message': 'Record deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)

    except Exception as e:
        logger.exception("[delete_overview_boc_record] Error")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ---------------------------------------------------------------------------
# RM + Conversion: btn_RMConversion_Click & Associated Endpoints
# ---------------------------------------------------------------------------

@csrf_exempt
def process_rm_conversion(request):
    """Replicates MS Access btn_RMConversion_Click:
    1. Delete from ztbl_OfferSheet_BOC Where BOC_Type='RM' (filtered by customer & item).
    2. INSERT INTO ztbl_OfferSheet_BOC (...) SELECT ... FROM zQry_OfferSheet_BOC_RM / Raw Material items.
    3. Return the populated RM rows for ChildBoc_RM (table-rm-bom).
    """
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            payload = {}
        customer_id = payload.get("customer_id") or request.POST.get("customer_id")
        item_creation_id = payload.get("item_creation_id") or request.POST.get("item_creation_id")
    else:
        customer_id = request.GET.get("customer_id")
        item_creation_id = request.GET.get("item_creation_id")

    if not customer_id or not item_creation_id:
        return JsonResponse(
            {"status": "error", "message": "'customer_id' and 'item_creation_id' are required."},
            status=400,
        )

    customer_id_str = str(customer_id).strip()
    try:
        item_id_int = int(str(item_creation_id).strip().lstrip("0") or "0")
    except (ValueError, TypeError):
        try:
            item_id_int = int(item_creation_id)
        except (ValueError, TypeError):
            item_id_int = 0

    updater = "USER"
    if hasattr(request, "user") and request.user.is_authenticated:
        updater = request.user.get_full_name() or request.user.get_username()

    try:
        with transaction.atomic():
            # 1. Delete from ztbl_OfferSheet_BOC where BOC_Type='RM' for this customer & item
            cust_q = Q(customer_id__iexact=customer_id_str)
            if '-' in customer_id_str:
                num_part = customer_id_str.split('-')[-1].lstrip('0')
                if num_part:
                    cust_q |= Q(customer_id__iexact=num_part)
            elif customer_id_str.isdigit():
                cust_q |= Q(customer_id__iexact=f"CUST-{int(customer_id_str):03d}")

            OfferSheetBOC.objects.filter(
                cust_q,
                itemcreation_id=item_id_int,
                boc_type="RM",
            ).delete()

            # 2. Fetch Raw Material items from BOM / PartDetails
            from .services import fetch_boc_part_details
            raw_items = fetch_boc_part_details(customer_id_str, str(item_creation_id).strip(), "Raw Material")
            if not raw_items:
                raw_items = fetch_boc_part_details(customer_id_str, str(item_creation_id).strip(), "RM")

            boc_objects = []
            seen_keys = set()
            for r in raw_items:
                p_num = str(r.get("part_number") or r.get("Part_Number") or "").strip()
                desc = str(r.get("description") or r.get("Description") or "").strip()
                uom = str(r.get("uom_code") or r.get("Unit_of_Measure_Code") or "").strip()
                qty = float(r.get("quantity") or r.get("Quantity") or 0.0)

                key = (p_num.lower(), desc.lower(), uom.lower(), qty)
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                internal_cost = float(r.get("internal_rate") or r.get("internal_cost") or r.get("Internal_Cost") or 0.0)
                settle_price = float(r.get("settle_price") or r.get("Settle Price") or 0.0)
                cost = float(r.get("cost") or r.get("Cost") or round(qty * settle_price, 4))
                cat = str(r.get("categorisation") or r.get("Categorisation") or "Raw Material").strip()

                boc_objects.append(OfferSheetBOC(
                    part_number=p_num,
                    description=desc,
                    unit_of_measure_code=uom,
                    quantity=qty,
                    internal_cost=internal_cost,
                    settle_price=settle_price,
                    cost=cost,
                    categorisation=cat,
                    customer_id=customer_id_str,
                    itemcreation_id=item_id_int,
                    boc_type="RM",
                    update_by=updater,
                ))

            if boc_objects:
                OfferSheetBOC.objects.bulk_create(boc_objects)

        # 3. Read back records for response
        saved_rows = OfferSheetBOC.objects.filter(
            cust_q,
            itemcreation_id=item_id_int,
            boc_type="RM",
        ).order_by("id")

        rows = []
        for item in saved_rows:
            rows.append({
                "id": item.id,
                "part_number": item.part_number or "",
                "description": item.description or "",
                "uom_code": item.unit_of_measure_code or "",
                "quantity": float(item.quantity or 0.0),
                "internal_cost": float(item.internal_cost or 0.0),
                "settle_price": float(item.settle_price or 0.0),
                "cost": float(item.cost or 0.0),
                "categorisation": item.categorisation or "Raw Material",
            })

        return JsonResponse({
            "status": "success",
            "message": f"RM Conversion completed. {len(rows)} records processed.",
            "rm_bom": rows,
        })

    except Exception as exc:
        logger.exception("[process_rm_conversion] Unexpected error: %s", exc)
        return JsonResponse({"status": "error", "message": f"Server error: {str(exc)}"}, status=500)


@csrf_exempt
def get_rm_bom_tab_data(request):
    """Fetch RM BOM rows for table-rm-bom.
    If already converted in ztbl_offersheet_boc, returns them; otherwise triggers conversion.
    Accepts both POST (JSON body) and GET (query params).
    """
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            payload = {}
        customer_id = (payload.get("customer_id") or request.POST.get("customer_id", "")).strip()
        item_creation_id = (payload.get("item_creation_id") or request.POST.get("item_creation_id", "")).strip()
    else:
        customer_id = request.GET.get("customer_id", "").strip()
        item_creation_id = request.GET.get("item_creation_id", "").strip()

    if not customer_id or not item_creation_id:
        return JsonResponse(
            {"status": "error", "message": "Both 'customer_id' and 'item_creation_id' are required."},
            status=400,
        )

    try:
        customer_id_str = str(customer_id).strip()
        try:
            item_id_int = int(item_creation_id.lstrip("0") or "0")
        except (ValueError, TypeError):
            item_id_int = 0

        cust_q = Q(customer_id__iexact=customer_id_str)
        if '-' in customer_id_str:
            num_part = customer_id_str.split('-')[-1].lstrip('0')
            if num_part:
                cust_q |= Q(customer_id__iexact=num_part)
        elif customer_id_str.isdigit():
            cust_q |= Q(customer_id__iexact=f"CUST-{int(customer_id_str):03d}")

        existing = OfferSheetBOC.objects.filter(
            cust_q,
            itemcreation_id=item_id_int,
            boc_type="RM",
        ).order_by("id")

        if existing.exists():
            rows = []
            for item in existing:
                rows.append({
                    "id": item.id,
                    "part_number": item.part_number or "",
                    "description": item.description or "",
                    "uom_code": item.unit_of_measure_code or "",
                    "quantity": float(item.quantity or 0.0),
                    "internal_cost": float(item.internal_cost or 0.0),
                    "settle_price": float(item.settle_price or 0.0),
                    "cost": float(item.cost or 0.0),
                    "categorisation": item.categorisation or "Raw Material",
                })
            return JsonResponse({"status": "success", "rm_bom": rows})

        # Not yet converted, run conversion
        return process_rm_conversion(request)

    except Exception as exc:
        logger.exception("[get_rm_bom_tab_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_POST
@csrf_exempt
@transaction.atomic
def save_rm_bom_data(request):
    """Save or update edited RM BOM records in ztbl_offersheet_boc (#btn-save-rm-details)."""
    try:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)

        customer_id = payload.get("customer_id")
        item_creation_id = payload.get("item_creation_id")
        rows = payload.get("rows", [])

        if not customer_id or not item_creation_id:
            return JsonResponse(
                {"status": "error", "message": "'customer_id' and 'item_creation_id' are required."},
                status=400,
            )

        customer_id_str = str(customer_id).strip()
        try:
            item_id_int = int(str(item_creation_id).strip().lstrip("0") or "0")
        except (ValueError, TypeError):
            item_id_int = 0

        updater = "USER"
        if hasattr(request, "user") and request.user.is_authenticated:
            updater = request.user.get_full_name() or request.user.get_username()

        # Delete existing saved RM rows
        cust_q = Q(customer_id__iexact=customer_id_str)
        if '-' in customer_id_str:
            num_part = customer_id_str.split('-')[-1].lstrip('0')
            if num_part:
                cust_q |= Q(customer_id__iexact=num_part)
        elif customer_id_str.isdigit():
            cust_q |= Q(customer_id__iexact=f"CUST-{int(customer_id_str):03d}")

        OfferSheetBOC.objects.filter(
            cust_q,
            itemcreation_id=item_id_int,
            boc_type="RM",
        ).delete()

        boc_objects = []
        for r in rows:
            p_num = str(r.get("part_number") or "").strip()
            desc = str(r.get("description") or "").strip()
            uom = str(r.get("uom_code") or r.get("unit_of_measure_code") or "").strip()
            try:
                qty = float(r.get("quantity") or 0.0)
            except (ValueError, TypeError):
                qty = 0.0
            try:
                icost = float(r.get("internal_cost") or r.get("internal_rate") or 0.0)
            except (ValueError, TypeError):
                icost = 0.0
            try:
                sprice = float(r.get("settle_price") or 0.0)
            except (ValueError, TypeError):
                sprice = 0.0

            cost = round(qty * sprice, 4)

            boc_objects.append(OfferSheetBOC(
                part_number=p_num,
                description=desc,
                unit_of_measure_code=uom,
                quantity=qty,
                internal_cost=icost,
                settle_price=sprice,
                cost=cost,
                categorisation="Raw Material",
                customer_id=customer_id_str,
                itemcreation_id=item_id_int,
                boc_type="RM",
                update_by=updater,
            ))

        if boc_objects:
            OfferSheetBOC.objects.bulk_create(boc_objects)

        return JsonResponse({"status": "success", "message": "RM BOM records saved successfully."})

    except Exception as exc:
        logger.exception("[save_rm_bom_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_GET
def get_rm_material_options(request):
    """Return dropdown options for Data Entry : Raw Material (#rm-entry-desc).
    Mirrors MS Access query:
        SELECT tbl_BOM_PartDetails_Master.[Part Description], tbl_BOM_PartDetails_Master.[Part No],
               tbl_BOM_PartDetails_Master.Customer, tbl_BOM_PartDetails_Master.[Base of Measure],
               tbl_BOM_PartDetails_Master.[Settle Price], tbl_BOM_PartDetails_Master.Categorisation 
        FROM tbl_BOM_PartDetails_Master 
        WHERE Categorisation = 'Raw Material' AND Customer = Forms!frm_Main!txtBox_CustCode;
    """
    customer_id = request.GET.get("customer_id", "").strip()

    try:
        from apps.BOM.models import BOMPartDetailsMaster
        qs = BOMPartDetailsMaster.objects.filter(categorisation__iexact="Raw Material")

        if customer_id:
            # Check customer code / id / name
            cust_filter = Q(customer__iexact=customer_id)
            if '-' in customer_id:
                num_part = customer_id.split('-')[-1].lstrip('0')
                if num_part:
                    cust_filter |= Q(customer__iexact=num_part)
            elif customer_id.isdigit():
                cust_filter |= Q(customer__iexact=f"CUST-{int(customer_id):03d}")

            # Also resolve customer name if CustomerInfo exists
            try:
                c_info = CustomerInfo.objects.filter(cust_filter).first()
                if c_info and c_info.customer_name:
                    cust_filter |= Q(customer__iexact=c_info.customer_name)
            except Exception:
                pass

            cust_qs = qs.filter(cust_filter)
            if cust_qs.exists():
                qs = cust_qs

        materials = []
        seen = set()
        for item in qs.order_by("part_description")[:500]:
            desc = (item.part_description or "").strip()
            part_no = (item.part_no or "").strip()
            uom = (item.base_unit_of_measure or "").strip()
            rate = float(item.settle_price or item.cost_price or item.rate or 0.0)

            key = (desc.lower(), part_no.lower())
            if key in seen:
                continue
            seen.add(key)

            display_name = f"{part_no} - {desc}" if part_no and desc and part_no != desc else (desc or part_no)
            materials.append({
                "part_no": part_no,
                "part_description": desc,
                "display_name": display_name,
                "unit": uom,
                "settle_price": rate,
            })

        return JsonResponse({"status": "success", "materials": materials})

    except Exception as exc:
        logger.exception("[get_rm_material_options] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_GET
def get_rm_overview_data(request):
    """Fetch Over View Table 1: Raw Material records.
    Mirrors MS Access query:
        SELECT tbl_OfferSheetRMConversion.ID, tbl_OfferSheetRMConversion.[Raw_Material Description],
               tbl_OfferSheetRMConversion.[Tube Size], tbl_OfferSheetRMConversion.Unit,
               tbl_OfferSheetRMConversion.RatePerUnit, tbl_OfferSheetRMConversion.Qnty,
               tbl_OfferSheetRMConversion.Total_Cost, tbl_OfferSheetRMConversion.Customer_Id,
               tbl_OfferSheetRMConversion.ItemCreation_Id, tbl_OfferSheetRMConversion.RM_Flag
        FROM tbl_OfferSheetRMConversion
        WHERE Customer_Id = <Customer_ID> AND ItemCreation_Id = <ItemCreation_ID> AND RM_Flag = 'LOCAL BOC';
    """
    customer_id = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()

    if not customer_id:
        return JsonResponse({"status": "error", "message": "customer_id is required."}, status=400)

    try:
        cust_filter = Q(customer_id__iexact=customer_id)
        if '-' in customer_id:
            num_part = customer_id.split('-')[-1].lstrip('0')
            if num_part:
                cust_filter |= Q(customer_id__iexact=num_part)
        elif customer_id.isdigit():
            cust_filter |= Q(customer_id__iexact=f"CUST-{int(customer_id):03d}")

        qs = OfferSheetRMConversion.objects.filter(
            cust_filter,
            rm_flag__iexact="LOCAL BOC",
        )

        if item_creation_id:
            item_clean = item_creation_id.strip()
            item_num = item_clean.lstrip('0')
            item_q = Q(item_creation_id__iexact=item_clean)
            if item_num:
                item_q |= Q(item_creation_id__iexact=item_num)
            qs = qs.filter(item_q)

        qs = qs.order_by("id")

        data = []
        subtotal = 0.0
        for row in qs:
            t_cost = float(row.total_cost or 0.0)
            subtotal += t_cost
            data.append({
                "id": row.id,
                "raw_material_desc": (row.raw_material_desc or "").strip(),
                "tube_size": (row.tube_size or "").strip(),
                "unit": (row.unit or "").strip(),
                "rate_per_unit": float(row.rate_per_unit or 0.0),
                "qnty": float(row.qnty or 0.0),
                "total_cost": t_cost,
            })

        return JsonResponse({
            "status": "success",
            "data": data,
            "subtotal": round(subtotal, 2),
        })

    except Exception as exc:
        logger.exception("[get_rm_overview_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


def get_conversion_cost_data(request):
    """Fetch Conversion Cost rows using the BOP Join query:
        SELECT t1.Categorisation, t1.CostPerQnty AS CostPerQnty, Sum(t1.BOQ) AS Quantity,
               t1.CostPerQnty*Sum(t1.BOQ) AS Total_Cost, tbl_BopCreation.Customer_ID, tbl_BopCreation.ItemCreation_Id
        FROM tbl_BopCreation INNER JOIN tbl_BOP_Tab AS t1
          ON (tbl_BopCreation.Table_Id = t1.Table_Id)
          AND (tbl_BopCreation.Customer_ID = t1.Customer_ID)
          AND (tbl_BopCreation.ItemCreation_Id = t1.ItemCreation_Id)
        WHERE tbl_BopCreation.Customer_ID = <customer_id> AND tbl_BopCreation.ItemCreation_Id = <item_id>
        GROUP BY t1.Categorisation, t1.CostPerQnty, tbl_BopCreation.Customer_ID, tbl_BopCreation.ItemCreation_Id;

    Also checks tbl_OfferSheetRMConversion (RM_Flag = 'ConversionCost') for any previously saved overrides.
    """
    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()

    if not customer_id:
        return JsonResponse({"status": "error", "message": "customer_id is required."}, status=400)

    try:
        # Build candidate sets for flexible matching
        cust_candidates = [customer_id.lower()]
        if '-' in customer_id:
            num_part = customer_id.split('-')[-1].lstrip('0')
            if num_part:
                cust_candidates.append(num_part.lower())
                cust_candidates.append(f"cust-{int(num_part):03d}".lower())
        elif customer_id.isdigit():
            num_int = int(customer_id)
            cust_candidates.append(str(num_int).lower())
            cust_candidates.append(f"cust-{num_int:03d}".lower())
            cust_candidates.append(f"{num_int:03d}".lower())
        cust_candidates = list(dict.fromkeys(cust_candidates))

        item_candidates = []
        if item_creation_id:
            item_candidates.append(item_creation_id.lower())
            if item_creation_id.isdigit():
                item_int = int(item_creation_id)
                item_candidates.append(str(item_int).lower())
                item_candidates.append(f"{item_int:03d}".lower())
        item_candidates = list(dict.fromkeys(item_candidates))

        data     = []
        subtotal = 0.0

        # 1. First check if there are saved ConversionCost records in tbl_OfferSheetRMConversion
        cust_filter = Q(customer_id__iexact=customer_id)
        if '-' in customer_id:
            num_part = customer_id.split('-')[-1].lstrip('0')
            if num_part:
                cust_filter |= Q(customer_id__iexact=num_part)
        elif customer_id.isdigit():
            cust_filter |= Q(customer_id__iexact=f"CUST-{int(customer_id):03d}")

        saved_qs = OfferSheetRMConversion.objects.filter(
            cust_filter,
            rm_flag__iexact="ConversionCost",
        )
        if item_creation_id:
            item_clean = item_creation_id.strip()
            item_num   = item_clean.lstrip('0')
            item_q     = Q(item_creation_id__iexact=item_clean)
            if item_num:
                item_q |= Q(item_creation_id__iexact=item_num)
            saved_qs = saved_qs.filter(item_q)

        saved_qs = saved_qs.order_by("id")

        if saved_qs.exists():
            for row in saved_qs:
                t_cost    = float(row.total_cost or 0.0)
                subtotal += t_cost
                data.append({
                    "id":                row.id,
                    "raw_material_desc": (row.raw_material_desc or "").strip(),
                    "tube_size":         (row.tube_size or "").strip(),
                    "unit":              (row.unit or "").strip() or "NOS",
                    "rate_per_unit":     float(row.rate_per_unit or 0.0),
                    "qnty":              float(row.qnty or 0.0),
                    "total_cost":        t_cost,
                    "source":            "saved_offersheet",
                })
        else:
            # 2. Execute BOP Join Query
            try:
                cust_placeholders = ','.join(['%s'] * len(cust_candidates))
                params = list(cust_candidates)

                item_clause = ""
                if item_candidates:
                    item_placeholders = ','.join(['%s'] * len(item_candidates))
                    item_clause = f"AND LOWER(TRIM(CAST(tbl_bopcreation.itemcreation_id AS VARCHAR))) IN ({item_placeholders})"
                    params.extend(item_candidates)

                bop_sql = f"""
                    SELECT 
                        COALESCE(t1.categorisation, '') AS categorisation, 
                        COALESCE(t1.costperqnty, 0) AS cost_per_qnty, 
                        SUM(COALESCE(t1.boq, 0)) AS quantity, 
                        (COALESCE(t1.costperqnty, 0) * SUM(COALESCE(t1.boq, 0))) AS total_cost, 
                        tbl_bopcreation.customer_id, 
                        tbl_bopcreation.itemcreation_id,
                        MIN(t1.id) AS min_id
                    FROM tbl_bopcreation 
                    INNER JOIN tbl_bop_tab AS t1 
                        ON (tbl_bopcreation.table_id = t1.table_id) 
                        AND (LOWER(TRIM(CAST(tbl_bopcreation.customer_id AS VARCHAR))) = LOWER(TRIM(CAST(t1.customer_id AS VARCHAR)))) 
                        AND (LOWER(TRIM(CAST(tbl_bopcreation.itemcreation_id AS VARCHAR))) = LOWER(TRIM(CAST(t1.itemcreation_id AS VARCHAR))))
                    WHERE 
                        LOWER(TRIM(CAST(tbl_bopcreation.customer_id AS VARCHAR))) IN ({cust_placeholders})
                        AND t1.categorisation IS NOT NULL 
                        AND TRIM(t1.categorisation) <> ''
                        {item_clause}
                    GROUP BY t1.categorisation, t1.costperqnty, tbl_bopcreation.customer_id, tbl_bopcreation.itemcreation_id
                    ORDER BY t1.categorisation;
                """

                with connection.cursor() as cursor:
                    cursor.execute(bop_sql, params)
                    rows = cursor.fetchall()
                    for r in rows:
                        cat_desc = (r[0] or "").strip()
                        cpq      = float(r[1] or 0.0)
                        qty      = float(r[2] or 0.0)
                        t_cost   = float(r[3] or (cpq * qty))
                        row_id   = r[6]
                        subtotal += t_cost
                        data.append({
                            "id":                row_id,
                            "raw_material_desc": cat_desc,
                            "tube_size":         "",
                            "unit":              "NOS",
                            "rate_per_unit":     cpq,
                            "qnty":              qty,
                            "total_cost":        t_cost,
                            "source":            "bop_tab",
                        })
            except Exception as bop_err:
                logger.warning("[get_conversion_cost_data] BOP query warning: %s", bop_err)

        return JsonResponse({
            "status":   "success",
            "data":     data,
            "subtotal": round(subtotal, 2),
        })

    except Exception as exc:
        logger.exception("[get_conversion_cost_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_POST
@csrf_exempt
@transaction.atomic
def save_conversion_cost_data(request):
    """Save / update Conversion Cost records in tbl_offersheetrmconversion (#btn-save-conversion-details)."""
    try:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)

        customer_id = payload.get("customer_id")
        item_creation_id = payload.get("item_creation_id")
        rows = payload.get("rows", [])

        if not customer_id or not item_creation_id:
            return JsonResponse(
                {"status": "error", "message": "'customer_id' and 'item_creation_id' are required."},
                status=400,
            )

        customer_id_str = str(customer_id).strip()
        item_id_str = str(item_creation_id).strip()

        # Delete existing saved ConversionCost rows in OfferSheetRMConversion
        cust_q = Q(customer_id__iexact=customer_id_str)
        if '-' in customer_id_str:
            num_part = customer_id_str.split('-')[-1].lstrip('0')
            if num_part:
                cust_q |= Q(customer_id__iexact=num_part)
        elif customer_id_str.isdigit():
            cust_q |= Q(customer_id__iexact=f"CUST-{int(customer_id_str):03d}")

        item_q = Q(item_creation_id__iexact=item_id_str)
        item_num = item_id_str.lstrip('0')
        if item_num:
            item_q |= Q(item_creation_id__iexact=item_num)

        OfferSheetRMConversion.objects.filter(
            cust_q,
            item_q,
            rm_flag__iexact="ConversionCost",
        ).delete()

        rm_objects = []
        for r in rows:
            desc = str(r.get("raw_material_desc") or r.get("description") or r.get("categorisation") or "").strip()
            if not desc:
                continue
            unit = str(r.get("unit") or "NOS").strip()
            try:
                qty = float(r.get("quantity") or r.get("qnty") or 0.0)
            except (ValueError, TypeError):
                qty = 0.0
            try:
                rpu = float(r.get("rate_per_unit") or r.get("cost_per_qnty") or 0.0)
            except (ValueError, TypeError):
                rpu = 0.0

            total_cost = round(qty * rpu, 2)

            rm_objects.append(OfferSheetRMConversion(
                raw_material_desc=desc,
                tube_size="",
                unit=unit,
                rate_per_unit=rpu,
                qnty=qty,
                total_cost=total_cost,
                rm_flag="ConversionCost",
                customer_id=customer_id_str,
                item_creation_id=item_id_str,
            ))

        if rm_objects:
            OfferSheetRMConversion.objects.bulk_create(rm_objects)

        return JsonResponse({"status": "success", "message": "Conversion Cost records saved successfully."})

    except Exception as exc:
        logger.exception("[save_conversion_cost_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_POST
@csrf_exempt
def add_rm_conversion_entry(request):
    """Add a new Data Entry : Raw Material row into tbl_OfferSheetRMConversion (#btn-rm-add-entry)."""
    try:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)

        customer_id = payload.get("customer_id", "").strip()
        item_creation_id = payload.get("item_creation_id", "").strip()
        raw_material_desc = payload.get("raw_material_desc", "").strip()
        tube_size = payload.get("tube_size", "").strip()
        unit = payload.get("unit", "").strip()
        rm_flag = payload.get("rm_flag", "LOCAL BOC").strip() or "LOCAL BOC"

        try:
            rate_per_unit = float(payload.get("rate_per_unit") or 0.0)
        except (ValueError, TypeError):
            rate_per_unit = 0.0

        try:
            qnty = float(payload.get("qnty") or 0.0)
        except (ValueError, TypeError):
            qnty = 0.0

        total_cost = round(rate_per_unit * qnty, 2)

        if not customer_id or not raw_material_desc:
            return JsonResponse(
                {"status": "error", "message": "Customer ID and Material Description are required."},
                status=400,
            )

        from datetime import date
        record = OfferSheetRMConversion.objects.create(
            part_number=tube_size or None,
            raw_material_desc=raw_material_desc,
            tube_size=tube_size,
            unit=unit,
            rate_per_unit=rate_per_unit,
            qnty=qnty,
            total_cost=total_cost,
            rm_flag=rm_flag,
            customer_id=customer_id,
            item_creation_id=item_creation_id,
            process_date=date.today(),
        )

        return JsonResponse({
            "status": "success",
            "message": "Raw material added successfully.",
            "record_id": record.id,
        })

    except Exception as exc:
        logger.exception("[add_rm_conversion_entry] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_POST
@csrf_exempt
def delete_rm_conversion_entry(request):
    """Delete a record from tbl_offersheetrmconversion by ID."""
    try:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)

        record_id = payload.get("id")
        if not record_id:
            return JsonResponse({"status": "error", "message": "Missing record ID."}, status=400)

        deleted_count, _ = OfferSheetRMConversion.objects.filter(id=record_id).delete()
        if deleted_count > 0:
            return JsonResponse({"status": "success", "message": "Record deleted successfully."})
        else:
            return JsonResponse({"status": "error", "message": "Record not found."}, status=404)

    except Exception as exc:
        logger.exception("[delete_rm_conversion_entry] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


# ---------------------------------------------------------------------------
# Tooling Cost: Internal Tooling Cost & Recovery Tooling Cost
# ---------------------------------------------------------------------------

def _fetch_tooling_rows(customer_id: str, item_creation_id: str, assignment_year: str = ""):
    """Helper to fetch rows from tbl_bop_tolling matching customer, item, and year."""
    cust_candidates = [customer_id.lower()]
    if '-' in customer_id:
        num_part = customer_id.split('-')[-1].lstrip('0')
        if num_part:
            cust_candidates.append(num_part.lower())
            cust_candidates.append(f"cust-{int(num_part):03d}".lower())
    elif customer_id.isdigit():
        num_int = int(customer_id)
        cust_candidates.append(str(num_int).lower())
        cust_candidates.append(f"cust-{num_int:03d}".lower())
        cust_candidates.append(f"{num_int:03d}".lower())
    cust_candidates = list(dict.fromkeys(cust_candidates))

    item_candidates = []
    if item_creation_id:
        item_candidates.append(item_creation_id.lower())
        if item_creation_id.isdigit():
            item_int = int(item_creation_id)
            item_candidates.append(str(item_int).lower())
            item_candidates.append(f"{item_int:08d}".lower())
            item_candidates.append(f"{item_int:03d}".lower())
    item_candidates = list(dict.fromkeys(item_candidates))

    cust_placeholders = ','.join(['%s'] * len(cust_candidates))
    params = list(cust_candidates)

    item_clause = ""
    if item_candidates:
        item_placeholders = ','.join(['%s'] * len(item_candidates))
        item_clause = f"AND LOWER(TRIM(CAST(itemcreation_id AS VARCHAR))) IN ({item_placeholders})"
        params.extend(item_candidates)

    year_clause = ""
    year_params = []
    if assignment_year and str(assignment_year).strip().isdigit():
        year_val = int(str(assignment_year).strip())
        year_clause = "AND (entry_date IS NULL OR EXTRACT(YEAR FROM entry_date) = %s)"
        year_params = [year_val]

    sql = f"""
        SELECT 
            COALESCE(tool_description, '') AS tool_description,
            COALESCE(uom, '') AS uom,
            COALESCE(unit_cost, 0) AS unit_cost,
            COALESCE(qty_required, 0) AS qty_required,
            COALESCE(total_estimate, 0) AS total_estimate,
            COALESCE(settled_price, 0) AS settled_price,
            COALESCE(total_settledprice, 0) AS total_settledprice,
            id,
            entry_date
        FROM tbl_bop_tolling
        WHERE 
            LOWER(TRIM(CAST(customer_id AS VARCHAR))) IN ({cust_placeholders})
            {item_clause}
            {year_clause}
        ORDER BY id;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, params + year_params)
        rows = cursor.fetchall()
        # If filtered by year returned nothing, try without year filter
        if not rows and year_clause:
            cursor.execute(
                f"""
                SELECT 
                    COALESCE(tool_description, '') AS tool_description,
                    COALESCE(uom, '') AS uom,
                    COALESCE(unit_cost, 0) AS unit_cost,
                    COALESCE(qty_required, 0) AS qty_required,
                    COALESCE(total_estimate, 0) AS total_estimate,
                    COALESCE(settled_price, 0) AS settled_price,
                    COALESCE(total_settledprice, 0) AS total_settledprice,
                    id,
                    entry_date
                FROM tbl_bop_tolling
                WHERE 
                    LOWER(TRIM(CAST(customer_id AS VARCHAR))) IN ({cust_placeholders})
                    {item_clause}
                ORDER BY id;
                """,
                params
            )
            rows = cursor.fetchall()

    # Build two result sets from same rows: internal (unit_cost/total_estimate) & recovery (settled_price/total_settledprice)
    internal_data = []
    internal_subtotal = 0.0
    recovery_data = []
    recovery_subtotal = 0.0

    for r in rows:
        tdesc     = (r[0] or "").strip()
        uom       = (r[1] or "").strip()
        ucost     = float(r[2] or 0.0)
        qty       = float(r[3] or 0.0)
        tot_est   = float(r[4] or (ucost * qty))
        if tot_est == 0.0 and (ucost * qty) > 0:
            tot_est = ucost * qty
        settled   = float(r[5] or 0.0)
        tot_sett  = float(r[6] or (settled * qty))
        if tot_sett == 0.0 and (settled * qty) > 0:
            tot_sett = settled * qty
        row_id    = r[7]
        edate     = str(r[8]) if r[8] else ""

        internal_subtotal += tot_est
        internal_data.append({
            "id":               row_id,
            "tool_description": tdesc,
            "uom":              uom,
            "unit_cost":        ucost,
            "qty_required":     qty,
            "total_estimate":   tot_est,
            "entry_date":       edate,
        })

        recovery_subtotal += tot_sett
        recovery_data.append({
            "id":               row_id,
            "tool_description": tdesc,
            "uom":              uom,
            "settled_price":    settled,
            "qty_required":     qty,
            "total_settledprice": tot_sett,
            "entry_date":       edate,
        })

    return internal_data, internal_subtotal, recovery_data, recovery_subtotal


@require_GET
def get_tooling_cost_data(request):
    """Fetch Internal Tooling Cost rows from tbl_bop_tolling (unit_cost / total_estimate)."""
    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    assignment_year  = request.GET.get("assignment_year", "").strip()

    if not customer_id:
        return JsonResponse({"status": "error", "message": "customer_id is required."}, status=400)

    try:
        data, subtotal, _, _ = _fetch_tooling_rows(customer_id, item_creation_id, assignment_year)
        return JsonResponse({
            "status":   "success",
            "data":     data,
            "subtotal": round(subtotal, 2),
        })
    except Exception as exc:
        logger.exception("[get_tooling_cost_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_GET
def get_recovery_tooling_cost_data(request):
    """Fetch Recovery Tooling Cost rows from tbl_bop_tolling (settled_price / total_settledprice).

    Mirrors Access query:
        SELECT Tool_Description, UOM, Settled_Price, Qty_Required, Total_SettledPrice
        FROM tbl_BOP_Tolling
        WHERE Year(Entry_Date)=AssignmentYear AND Customer_ID=cust AND ItemCreation_ID=item
        ORDER BY Tool_Description;
    """
    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    assignment_year  = request.GET.get("assignment_year", "").strip()

    if not customer_id:
        return JsonResponse({"status": "error", "message": "customer_id is required."}, status=400)

    try:
        _, _, data, subtotal = _fetch_tooling_rows(customer_id, item_creation_id, assignment_year)
        # Sort by tool_description (mirrors ORDER BY Tool_Description in Access query)
        data = sorted(data, key=lambda x: (x.get("tool_description") or "").lower())
        return JsonResponse({
            "status":   "success",
            "data":     data,
            "subtotal": round(subtotal, 2),
        })
    except Exception as exc:
        logger.exception("[get_recovery_tooling_cost_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_GET
def export_internal_tooling_cost(request):
    """Export Internal Tooling Cost table to Excel (.xls)."""
    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    assignment_year  = request.GET.get("assignment_year", "").strip() or "2026"

    try:
        data, subtotal, _, _ = _fetch_tooling_rows(customer_id, item_creation_id, assignment_year)

        html_out = [
            '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">',
            '<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
            '<!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet>',
            '<x:Name>Internal Tooling Cost</x:Name>',
            '<x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions>',
            '</x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->',
            '<style>',
            'table { border-collapse: collapse; font-family: Arial, sans-serif; font-size: 10pt; }',
            'th, td { border: 1px solid #9ca3af; padding: 6px 12px; }',
            'th { background-color: #9cbde4; font-weight: bold; text-align: center; color: #1f2937; }',
            '.header-title { background-color: #1e3a8a; color: #ffffff; font-weight: bold; font-size: 12pt; padding: 8px; }',
            '.info-header { background-color: #eff6ff; font-weight: bold; }',
            '.num { text-align: right; }',
            '.subtotal-row { background-color: #f1f5f9; font-weight: bold; }',
            '</style></head><body>',
            '<table>',
            f'<tr><td colspan="5" class="header-title">Data Tooling : Internal Tooling Cost</td></tr>',
            f'<tr><td class="info-header">Customer Code :</td><td>{customer_id}</td><td class="info-header">Item ID :</td><td colspan="2">{item_creation_id}</td></tr>',
            f'<tr><td class="info-header">Assignment Year :</td><td colspan="4">{assignment_year}</td></tr>',
            '</table><br>',
            '<table><thead><tr>',
            '<th style="width: 300px; text-align: left;">Tootl Description</th>',
            '<th style="width: 80px;">UOM</th>',
            '<th style="width: 120px; text-align: right;">Unit Cost</th>',
            '<th style="width: 100px; text-align: right;">Qnty</th>',
            '<th style="width: 130px; text-align: right;">Total Cost</th>',
            '</tr></thead><tbody>',
        ]

        if not data:
            html_out.append('<tr><td colspan="5" style="text-align:center; color:#6b7280;">No Tooling Cost records found.</td></tr>')
        else:
            for row in data:
                tdesc = row.get("tool_description", "")
                uom   = row.get("uom", "NOS")
                ucost = f"{row.get('unit_cost', 0):.2f}"
                qty   = f"{row.get('qty_required', 0):.2f}"
                tot   = f"{row.get('total_estimate', 0):.2f}"
                html_out.append(f'<tr><td>{tdesc}</td><td style="text-align:center;">{uom}</td><td class="num">{ucost}</td><td class="num">{qty}</td><td class="num">{tot}</td></tr>')

        html_out.append(f'<tr class="subtotal-row"><td colspan="4" style="text-align:right;">Sub Total :</td><td class="num">{subtotal:.2f}</td></tr>')
        html_out.append('</tbody></table></body></html>')

        content = "\n".join(html_out)
        response = HttpResponse(content, content_type="application/vnd.ms-excel")
        filename = f"Internal_Tooling_Cost_{item_creation_id or customer_id}_{assignment_year}.xls"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as exc:
        logger.exception("[export_internal_tooling_cost] Error: %s", exc)
        return HttpResponse(f"Error generating export: {exc}", status=500)




@require_GET
def export_recovery_tooling_cost(request):
    """Export Recovery Tooling Cost table to Excel (.xls) using settled_price / total_settledprice."""
    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    assignment_year  = request.GET.get("assignment_year", "").strip() or "2026"

    try:
        _, _, data, subtotal = _fetch_tooling_rows(customer_id, item_creation_id, assignment_year)
        data = sorted(data, key=lambda x: (x.get("tool_description") or "").lower())

        html_out = [
            '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">',
            '<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
            '<!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet>',
            '<x:Name>Recovery Tooling Cost</x:Name>',
            '<x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions>',
            '</x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->',
            '<style>',
            'table { border-collapse: collapse; font-family: Arial, sans-serif; font-size: 10pt; }',
            'th, td { border: 1px solid #9ca3af; padding: 6px 12px; }',
            'th { background-color: #9cbde4; font-weight: bold; text-align: center; color: #1f2937; }',
            '.header-title { background-color: #1e3a8a; color: #ffffff; font-weight: bold; font-size: 12pt; padding: 8px; }',
            '.info-header { background-color: #eff6ff; font-weight: bold; }',
            '.num { text-align: right; }',
            '.subtotal-row { background-color: #f1f5f9; font-weight: bold; }',
            '</style></head><body>',
            '<table>',
            f'<tr><td colspan="5" class="header-title">Data Tooling : Recovery Tooling Cost</td></tr>',
            f'<tr><td class="info-header">Customer Code :</td><td>{customer_id}</td><td class="info-header">Item ID :</td><td colspan="2">{item_creation_id}</td></tr>',
            f'<tr><td class="info-header">Assignment Year :</td><td colspan="4">{assignment_year}</td></tr>',
            '</table><br>',
            '<table><thead><tr>',
            '<th style="width: 300px; text-align: left;">Tool Description</th>',
            '<th style="width: 80px;">UOM</th>',
            '<th style="width: 120px; text-align: right;">Unit Cost</th>',
            '<th style="width: 100px; text-align: right;">Qnty</th>',
            '<th style="width: 130px; text-align: right;">Total Cost</th>',
            '</tr></thead><tbody>',
        ]

        if not data:
            html_out.append('<tr><td colspan="5" style="text-align:center; color:#6b7280;">No Recovery Tooling Cost records found.</td></tr>')
        else:
            for row in data:
                tdesc = row.get("tool_description", "")
                uom   = row.get("uom", "NOS")
                ucost = f"{row.get('settled_price', 0):.2f}"
                qty   = f"{row.get('qty_required', 0):.2f}"
                tot   = f"{row.get('total_settledprice', 0):.2f}"
                html_out.append(f'<tr><td>{tdesc}</td><td style="text-align:center;">{uom}</td><td class="num">{ucost}</td><td class="num">{qty}</td><td class="num">{tot}</td></tr>')

        html_out.append(f'<tr class="subtotal-row"><td colspan="4" style="text-align:right;">Sub Total :</td><td class="num">{subtotal:.2f}</td></tr>')
        html_out.append('</tbody></table></body></html>')

        content = "\n".join(html_out)
        response = HttpResponse(content, content_type="application/vnd.ms-excel")
        filename = f"Recovery_Tooling_Cost_{item_creation_id or customer_id}_{assignment_year}.xls"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as exc:
        logger.exception("[export_recovery_tooling_cost] Error: %s", exc)
        return HttpResponse(f"Error generating export: {exc}", status=500)


# ---------------------------------------------------------------------------
# Transport Cost Views (tbl_OfferSheet_TransCost)
# ---------------------------------------------------------------------------

PARTICULARS_PART1 = [
    'CFT of BOX (1 cft = 12 Kg)',
    'Freight Rs.2.20/Kg',
    'Freight charges/Vehicle rate',
    'Docket charges',
    'Pickup charges',
    'Door Delivery/DOD Charges',
    'LR charges/invoice',
    'Service charges & Other',
]

PARTICULARS_PART2 = [
    'Cubic Meter/CBM of Vehicle',
    'CBM Freight Cost',
    'Cubic Meter/CBM of Packing Box (MM)',
    'Capacity Utilisation of Truck Space/CBM Rate',
    'Quantity/Box/No of Parts in one Box',
    'No of box/Trip',
    'Total Qty per trip',
    'Total tube in meter',
]


@require_GET
def get_transport_cost_data(request):
    """Fetch transport cost data from tbl_offersheet_transcost."""
    customer_id = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    cust_code = request.GET.get("cust_code", "").strip()

    if not customer_id or not item_creation_id:
        return JsonResponse({"status": "error", "message": "customer_id and item_creation_id are required."}, status=400)

    try:
        qs = OfferSheetTransCost.objects.filter(
            customer_id=customer_id,
            itemcreation_id=item_creation_id
        )
        if cust_code:
            qs = qs.filter(cust_code=cust_code)

        data_dict = {}
        for row in qs:
            data_dict[row.particular] = float(row.total_cost or 0.0)

        # Calculate CT (Total Transportation Cost/Trip)
        ct_total = sum(data_dict.get(p, 0.0) for p in PARTICULARS_PART1)

        # Calculate CQ (Transportation Cost/Quantity) based on cust_code logic from Access VBA
        code_upper = (cust_code or "").upper()
        cq_val = 0.0
        cq3 = data_dict.get('Cubic Meter/CBM of Packing Box (MM)', 0.0)
        cq4 = data_dict.get('Capacity Utilisation of Truck Space/CBM Rate', 0.0)
        cq5 = data_dict.get('Quantity/Box/No of Parts in one Box', 0.0)
        cq7 = data_dict.get('Total Qty per trip', 0.0)
        ct3 = data_dict.get('Freight charges/Vehicle rate', 0.0)

        if code_upper == "TML":
            if cq5 != 0:
                cq_val = (cq3 * cq4) / cq5
        elif code_upper in ["CNH", "FML"]:
            if cq5 != 0:
                cq_val = ct_total / cq5
        elif code_upper == "ION":
            if (cq4 * cq5) != 0:
                cq_val = ct3 / (cq4 * cq5)
        else:
            if cq7 != 0:
                cq_val = ct_total / cq7

        return JsonResponse({
            "status": "success",
            "exists": len(data_dict) > 0,
            "data": data_dict,
            "ct_total": round(ct_total, 2),
            "cq_val": round(cq_val, 4),
        })

    except Exception as exc:
        logger.exception("[get_transport_cost_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@csrf_exempt
@require_POST
def save_transport_cost_data(request):
    """Insert or update transport cost records in tbl_offersheet_transcost."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        customer_id = payload.get("customer_id", "").strip()
        item_creation_id = payload.get("item_creation_id", "").strip()
        cust_code = payload.get("cust_code", "").strip()
        costs = payload.get("costs", {})

        if not customer_id or not item_creation_id:
            return JsonResponse({"status": "error", "message": "customer_id and item_creation_id are required."}, status=400)

        all_particulars = PARTICULARS_PART1 + PARTICULARS_PART2

        with transaction.atomic():
            for particular in all_particulars:
                cost_val = Decimal(str(costs.get(particular, 0.0) or 0.0))
                
                # Check if record exists
                existing = OfferSheetTransCost.objects.filter(
                    customer_id=customer_id,
                    itemcreation_id=item_creation_id,
                    particular=particular
                )
                if cust_code:
                    existing = existing.filter(cust_code=cust_code)

                if existing.exists():
                    existing.update(total_cost=cost_val, cust_code=cust_code or F('cust_code'))
                else:
                    OfferSheetTransCost.objects.create(
                        particular=particular,
                        total_cost=cost_val,
                        cust_code=cust_code,
                        customer_id=customer_id,
                        itemcreation_id=item_creation_id
                    )

        return JsonResponse({"status": "success", "message": "Transport cost saved successfully."})

    except Exception as exc:
        logger.exception("[save_transport_cost_data] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


# ---------------------------------------------------------------------------
# Offer Sheet Download View (Multi-sheet Excel Workbook)
# ---------------------------------------------------------------------------

@require_GET
def download_offer_sheet(request):
    """Generates and downloads full Offer Sheet Excel workbook with all 7 worksheets:
    1. Internal Conversion
    2. Local & Imported BOC
    3. RM & Conversion
    4. Tooling Cost
    5. Consolidate Data View
    6. Transport Cost
    7. Final Cost
    """
    customer_id      = request.GET.get("customer_id", "").strip()
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    cust_code        = request.GET.get("cust_code", "").strip() or customer_id
    year             = request.GET.get("year", "2026").strip()

    if not customer_id or not item_creation_id:
        return HttpResponse("Invalid Selection: Customer ID and Item Creation ID are required.", status=400)

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        wb.remove(wb.active) # Remove default sheet

        # Styles
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        sub_fill    = PatternFill(start_color="9CBDE4", end_color="9CBDE4", fill_type="solid")
        sub_font    = Font(name="Arial", size=10, bold=True, color="1F2937")
        total_fill  = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        total_font  = Font(name="Arial", size=10, bold=True, color="000000")
        thin_border = Border(
            left=Side(style='thin', color='D1D5DB'),
            right=Side(style='thin', color='D1D5DB'),
            top=Side(style='thin', color='D1D5DB'),
            bottom=Side(style='thin', color='D1D5DB')
        )

        # Part Number lookup
        part_no = ""
        try:
            part_obj = OfferSheetPartDetails.objects.filter(customer_id=customer_id, itemcreation_id=item_creation_id).first()
            if part_obj and hasattr(part_obj, 'part_number'):
                part_no = part_obj.part_number or ""
        except Exception:
            pass

        # -------------------------------------------------------------------
        # Sheet 1: Internal Conversion
        # -------------------------------------------------------------------
        ws1 = wb.create_sheet(title="Internal Conversion")
        ws1.append([f"Customer Code: {cust_code} | Customer ID: {customer_id} | Item ID: {item_creation_id} | Year: {year}"])
        ws1.merge_cells("A1:H1")
        ws1["A1"].font = header_font
        ws1["A1"].fill = header_fill

        headers1 = ["Description", "MHR", "Run Time (Sec)", "Per Hour Output", "Rate/Unit", "Quantity", "Total Cost", "% Contribution"]
        ws1.append(headers1)
        for cell in ws1[2]:
            cell.font = sub_font
            cell.fill = sub_fill

        raw_data = _get_internal_conversion_raw_data(customer_id, item_creation_id, year, norm_type="lower")
        if not raw_data:
            raw_data = _get_internal_conversion_raw_data(customer_id, item_creation_id, year)
        rows1, sum_total1 = _compute_table_variant(raw_data, norm_type="lower")

        for r in rows1:
            ws1.append([
                r.get("description", ""),
                r.get("mhr", 0),
                r.get("run_time_sec", 0),
                r.get("per_hour_output", 0),
                r.get("rate_per_unit", 0),
                r.get("qnty", 0),
                r.get("total", 0),
                r.get("pct_contrib", 0)
            ])

        ws1.append(["Total Internal Conversion", "", "", "", "", "", round(sum_total1, 2), "100.00%"])
        for cell in ws1[ws1.max_row]:
            cell.font = total_font
            cell.fill = total_fill

        # -------------------------------------------------------------------
        # Sheet 2: Local & Imported BOC
        # -------------------------------------------------------------------
        ws2 = wb.create_sheet(title="Local & Imported BOC")
        ws2.append([f"Local & Imported BOC — Cust: {customer_id} | Item: {item_creation_id}"])
        ws2.merge_cells("A1:G1")
        ws2["A1"].font = header_font
        ws2["A1"].fill = header_fill

        headers2 = ["BOC Type", "Part Number", "Description", "Unit", "Quantity", "Internal Cost", "Total Cost"]
        ws2.append(headers2)
        for cell in ws2[2]:
            cell.font = sub_font
            cell.fill = sub_fill

        item_id_val = item_creation_id
        try:
            item_id_val = int(item_creation_id)
        except (ValueError, TypeError):
            pass

        boc_qs = OfferSheetBOC.objects.filter(customer_id=customer_id, itemcreation_id=item_id_val)
        boc_total = 0.0
        for b in boc_qs:
            tot = float(getattr(b, 'cost', None) or getattr(b, 'internal_cost', None) or 0.0)
            boc_total += tot
            ws2.append([
                getattr(b, 'boc_type', 'Local') or 'Local',
                getattr(b, 'part_number', '') or '',
                getattr(b, 'description', '') or '',
                getattr(b, 'unit_of_measure_code', 'NOS') or 'NOS',
                getattr(b, 'quantity', 0) or 0,
                getattr(b, 'internal_cost', 0.0) or 0.0,
                round(tot, 2)
            ])

        ws2.append(["Total BOC Cost", "", "", "", "", "", round(boc_total, 2)])
        for cell in ws2[ws2.max_row]:
            cell.font = total_font
            cell.fill = total_fill

        # -------------------------------------------------------------------
        # Sheet 3: RM & Conversion
        # -------------------------------------------------------------------
        ws3 = wb.create_sheet(title="RM & Conversion")
        ws3.append([f"RM & Conversion Details — Cust: {customer_id} | Item: {item_creation_id}"])
        ws3.merge_cells("A1:G1")
        ws3["A1"].font = header_font
        ws3["A1"].fill = header_fill

        headers3 = ["Part Number", "Raw Material Description", "Tube Size", "Unit", "Rate / Unit", "Quantity", "Total Cost"]
        ws3.append(headers3)
        for cell in ws3[2]:
            cell.font = sub_font
            cell.fill = sub_fill

        rm_qs = OfferSheetRMConversion.objects.filter(customer_id=customer_id, item_creation_id=item_creation_id)
        rm_total = 0.0
        for rm in rm_qs:
            tot = float(rm.total_cost or 0.0)
            rm_total += tot
            ws3.append([
                rm.part_number or "",
                rm.raw_material_desc or "",
                rm.tube_size or "",
                rm.unit or "KG",
                float(rm.rate_per_unit or 0.0),
                float(rm.qnty or 0.0),
                round(tot, 2)
            ])

        ws3.append(["Total RM & Conversion", "", "", "", "", "", round(rm_total, 2)])
        for cell in ws3[ws3.max_row]:
            cell.font = total_font
            cell.fill = total_fill

        # -------------------------------------------------------------------
        # Sheet 4: Tooling Cost
        # -------------------------------------------------------------------
        ws4 = wb.create_sheet(title="Tooling Cost")
        ws4.append([f"Tooling Cost — Cust: {customer_id} | Item: {item_creation_id}"])
        ws4.merge_cells("A1:E1")
        ws4["A1"].font = header_font
        ws4["A1"].fill = header_fill

        ws4.append(["Part Number:", part_no, "", "", ""])
        ws4["A2"].font = sub_font

        headers4 = ["Tool Description", "UOM", "Unit Cost", "Qty Required", "Total Estimate"]
        ws4.append(headers4)
        for cell in ws4[3]:
            cell.font = sub_font
            cell.fill = sub_fill

        internal_rows, tooling_subtotal, _, _ = _fetch_tooling_rows(customer_id, item_creation_id, year)
        for t in internal_rows:
            ws4.append([
                t.get("tool_description", ""),
                t.get("uom", "NOS"),
                float(t.get("unit_cost", 0.0)),
                float(t.get("qty_required", 0.0)),
                float(t.get("total_estimate", 0.0))
            ])

        ws4.append(["Sub Total Tooling Cost", "", "", "", round(tooling_subtotal, 2)])
        for cell in ws4[ws4.max_row]:
            cell.font = total_font
            cell.fill = total_fill

        # -------------------------------------------------------------------
        # Sheet 5: Consolidate Data View
        # -------------------------------------------------------------------
        ws5 = wb.create_sheet(title="Consolidate Data View")
        ws5.append([f"Consolidated Data View — Cust: {customer_id} | Item: {item_creation_id}"])
        ws5.merge_cells("A1:C1")
        ws5["A1"].font = header_font
        ws5["A1"].fill = header_fill

        ws5.append(["Part Number:", part_no, ""])
        ws5["A2"].font = sub_font

        headers5 = ["Cost Head Particulars", "Total Cost", "Remark"]
        ws5.append(headers5)
        for cell in ws5[3]:
            cell.font = sub_font
            cell.fill = sub_fill

        ws5.append(["1. Internal Conversion Cost", round(sum_total1, 2), "Sheet: Internal Conversion"])
        ws5.append(["2. Local & Imported BOC Cost", round(boc_total, 2), "Sheet: Local & Imported BOC"])
        ws5.append(["3. RM & Conversion Cost", round(rm_total, 2), "Sheet: RM & Conversion"])
        ws5.append(["4. Tooling Cost", round(tooling_subtotal, 2), "Sheet: Tooling Cost"])

        # Fetch Transport Cost total
        trans_qs = OfferSheetTransCost.objects.filter(customer_id=customer_id, itemcreation_id=item_creation_id)
        trans_map = {tr.particular: float(tr.total_cost or 0.0) for tr in trans_qs}
        trans_total = sum(trans_map.values())
        ws5.append(["5. Transport Cost", round(trans_total, 2), "Sheet: Transport Cost"])

        grand_total = sum_total1 + boc_total + rm_total + tooling_subtotal + trans_total
        ws5.append(["Grand Total Cost", round(grand_total, 2), "All Heads Combined"])
        for cell in ws5[ws5.max_row]:
            cell.font = total_font
            cell.fill = total_fill

        # -------------------------------------------------------------------
        # Sheet 6: Transport Cost
        # -------------------------------------------------------------------
        ws6 = wb.create_sheet(title="Transport Cost")
        ws6.append([f"Transport Cost — Cust: {customer_id} | Item: {item_creation_id}"])
        ws6.merge_cells("A1:D1")
        ws6["A1"].font = header_font
        ws6["A1"].fill = header_fill

        ws6.append(["Part Number:", part_no, "", ""])
        ws6["A2"].font = sub_font

        headers6 = ["Particular Description", "Cost Value", "Category", "Customer Code"]
        ws6.append(headers6)
        for cell in ws6[3]:
            cell.font = sub_font
            cell.fill = sub_fill

        for p_name in PARTICULARS_PART1:
            ws6.append([p_name, round(trans_map.get(p_name, 0.0), 2), "Part 1 (Trip)", cust_code])
        for p_name in PARTICULARS_PART2:
            ws6.append([p_name, round(trans_map.get(p_name, 0.0), 2), "Part 2 (Quantity)", cust_code])

        ws6.append(["Total Transport Cost", round(trans_total, 2), "Combined", cust_code])
        for cell in ws6[ws6.max_row]:
            cell.font = total_font
            cell.fill = total_fill

        # -------------------------------------------------------------------
        # Sheet 7: Final Cost
        # -------------------------------------------------------------------
        ws7 = wb.create_sheet(title="Final Cost")
        ws7.append([f"Final Cost Summary — Cust: {customer_id} | Item: {item_creation_id}"])
        ws7.merge_cells("A1:B1")
        ws7["A1"].font = header_font
        ws7["A1"].fill = header_fill

        ws7.append(["Customer Code", cust_code])
        ws7.append(["Customer ID", customer_id])
        ws7.append(["Item Creation ID", item_creation_id])
        ws7.append(["Part Number", part_no])
        ws7.append(["Assignment Year", year])
        ws7.append(["Net Unit Cost", round(grand_total, 2)])
        ws7.append(["Status", "Completed / Verified"])
        for cell in ws7[ws7.max_row]:
            cell.font = total_font

        # Auto-adjust column widths for all sheets
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

        # Stream response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"OfferSheet_{customer_id}_{item_creation_id}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    except Exception as exc:
        logger.exception("[download_offer_sheet] Error: %s", exc)
        return HttpResponse(f"Error generating offer sheet download: {exc}", status=500)


# ---------------------------------------------------------------------------
# Submit RFQ Completion
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def submit_rfq_completion(request):
    """
    Validates BOM and BOP approval, then updates or inserts the RFQ completion status.
    """
    try:
        data = json.loads(request.body)
        customer_id = data.get("customer_id")
        item_creation_id = data.get("itemcreation_id")
        is_completed = "Yes" if data.get("is_completed") else "No"
        customer_name = data.get("customername", "")
        
        if not customer_id or not item_creation_id:
            return JsonResponse({"status": "error", "message": "Missing Customer ID or Item Creation ID."}, status=400)
            
        # Validate BOM and BOP
        bom_remark = BomCreation.objects.filter(
            customer_id=customer_id, 
            item_creation_id=item_creation_id
        ).values_list("remark", flat=True).first()
        
        bop_remark = BopCreation.objects.filter(
            customer_id=customer_id, 
            itemcreation_id=item_creation_id
        ).values_list("action_status", flat=True).first()
        
        if bom_remark != "Approved":
            return JsonResponse({
                "status": "error",
                "message": f"BOM is not approved.\n\nCurrent Status : {bom_remark or 'None'}"
            })
            
        if bop_remark != "Approved":
            return JsonResponse({
                "status": "error",
                "message": f"BOP is not approved.\n\nCurrent Status : {bop_remark or 'None'}"
            })
            
        # Get creation IDs
        bom_creation_id = BomCreation.objects.filter(
            customer_id=customer_id, 
            item_creation_id=item_creation_id
        ).values_list("bomcreation_id", flat=True).first()
        
        bop_creation_id = BopCreation.objects.filter(
            customer_id=customer_id, 
            itemcreation_id=item_creation_id
        ).values_list("bopcreation_id", flat=True).first()
        
        # Look up BOC Creation ID
        from apps.BOC.models import BOCCreation
        boc_creation_id = BOCCreation.objects.filter(
            customer_id=customer_id, 
            itemcreation_id=item_creation_id
        ).values_list("boc_creation_id", flat=True).first()
        
        from django.utils import timezone
        
        # Update or Insert in RFQDetails proxy model
        from apps.CostingBCCal.models import RFQDetails
        rfq, created = RFQDetails.objects.get_or_create(
            customer_id=customer_id,
            itemcreation_id=item_creation_id,
            defaults={
                "customername": customer_name,
                "bomcreation_id": bom_creation_id,
                "bopcreation_id": bop_creation_id,
                "boc_creation_id": boc_creation_id,
                "is_completed": is_completed,
                "action_date": timezone.now(),
                "updated_by": request.user.username if request.user.is_authenticated else "SYSTEM"
            }
        )
        
        if not created:
            rfq.is_completed = is_completed
            rfq.action_date = timezone.now()
            rfq.updated_by = request.user.username if request.user.is_authenticated else "SYSTEM"
            rfq.save()
            
        return JsonResponse({"status": "success", "message": "RFQ completion status saved successfully."})
        
    except Exception as exc:
        logger.exception("[submit_rfq_completion] Error: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)
