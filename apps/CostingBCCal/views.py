import csv
import json
import logging

logger = logging.getLogger(__name__)

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from config.decorators import require_active_customer
from apps.customer_creation.models import CustomerInfo
from apps.item_creation.models import ItemCard
from .models import NormsDetails


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
    # Customer ID dropdown  (tbl_customerinfo)
    try:
        customers = list(
            CustomerInfo.objects.order_by("customer_id")
            .values_list("customer_id", flat=True)
        )
    except Exception:
        customers = []

    # Item Creation ID dropdown (tbl_itemcard — unique, sorted)
    try:
        item_ids = list(
            ItemCard.objects.order_by("no")
            .values_list("no", flat=True)
            .distinct()
        )
    except Exception:
        item_ids = []

    context = {
        "customers": customers,
        "item_ids":  item_ids,
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
    qs = CostingInternalConversion.objects.filter(itemcreation_id__iexact=itemcreation_id)
    if customer_id:
        qs_narrow = qs.filter(customer_id__iexact=customer_id)
        if qs_narrow.exists():          # only narrow if records actually exist
            qs = qs_narrow

    # If still empty, try BOPTab fallback
    bop_qs = None
    if not qs.exists():
        try:
            from apps.BOP.models import BOPTab
            bop_qs = BOPTab.objects.filter(itemcreation_id__iexact=itemcreation_id)
            if customer_id:
                bop_narrow = bop_qs.filter(customer_id__iexact=customer_id)
                if bop_narrow.exists():
                    bop_qs = bop_narrow
        except Exception:
            bop_qs = None

    if not qs.exists() and (not bop_qs or not bop_qs.exists()):
        return []

    # Deduplicate rows by description in Python
    dedup_dict = {}

    if qs.exists():
        for row in qs:
            desc = (row.description or "").strip()
            if not desc:
                continue

            # Case-insensitive mhr_category filtering in Python
            row_cat = (row.mhr_category or "").strip().lower()
            if norm_type_lower and row_cat and row_cat != norm_type_lower:
                continue  # skip rows that belong to the other norm type

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
    item_creation_id = (
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

    if not item_creation_id:
        return JsonResponse({"costs": {}, "year": year, "error": "item_creation_id is required"}, status=400)

    from .models import DTAssignmentYearData
    from django.db import connection

    costs = {}
    try:
        # Use raw SQL with CAST so the query works whether itemcreation_id
        # is stored as INTEGER or TEXT in the database.
        with connection.cursor() as cur:
            cur.execute(
                "SELECT category, year, cost "
                "FROM tbl_dtassigmentyeardata "
                "WHERE (CAST(itemcreation_id AS TEXT) = %s OR LTRIM(CAST(itemcreation_id AS TEXT), '0') = LTRIM(%s, '0')) AND year = %s",
                [str(item_creation_id), str(item_creation_id), year]
            )
            for row in cur.fetchall():
                category_name = (row[0] or "").strip()
                cost_val = _safe_float(row[2])
                if category_name:
                    norm_name = html.unescape(category_name).replace("&amp;", "&").strip()
                    costs[norm_name] = cost_val
    except Exception as exc:
        logger.warning("[get_cost_by_item_category] query failed for %r year=%d: %s", item_creation_id, year, exc)
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
