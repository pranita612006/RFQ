from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from urllib.parse import urlencode
from django.utils.timezone import now
from django.db.models import Max
from django.db import connection
import datetime

from .models import Opportunity, CustomerInfo, OppSalesPeople, OppSalesCycles, OppSegment, OpportunityMaster, OpportunityMasterECN
from apps.item_creation.models import ItemCard
from .forms import SendItemEmailForm
from config.decorators import require_active_customer

@require_active_customer
def opportunity_creation(request):
    # 1. Extract values from the active customer session
    customer_id = request.active_customer['id']
    customer_name = request.active_customer['name']

    # 2. Render the form/page for GET requests
    context = {
        "customer_id": customer_id,
        "customer_name": customer_name,
    }
    return render(request, "opportunities/opportunity_creation.html", context)


@require_active_customer
def opportunitycreation_ecn(request):
    """
    Render the ECN Request For Opportunity Creation page.
    """
    customer_id = request.active_customer['id']
    customer_name = request.active_customer['name']

    # Get item numbers for the search datalist
    items = []
    if customer_id:
        try:
            items_qs = ItemCard.objects.filter(customer_id=customer_id).values_list('no', flat=True)
            items = list(items_qs)
        except Exception:
            items = []

    context = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "items": items,
    }
    return render(request, "opportunities/frm_opportunitycreation_ecn.html", context)


def get_ecn_count(request):
    """
    GET: Return the number of ECN records for item_no + customer_id.
    Mirrors VBA: DCount check before deciding ORIGINAL vs REPLICATE.
    """
    item_no = request.GET.get("item_no", "").strip()
    customer_id = request.GET.get("customer_id", "").strip()
    if not item_no:
        return JsonResponse({"count": 0})
    try:
        with connection.cursor() as cur:
            if customer_id:
                cur.execute(
                    "SELECT COUNT(*) FROM tbl_opportunitymaster_ecn WHERE item_no=%s AND customerid=%s",
                    [item_no, customer_id],
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) FROM tbl_opportunitymaster_ecn WHERE item_no=%s",
                    [item_no],
                )
            row = cur.fetchone()
        return JsonResponse({"count": row[0] if row else 0})
    except Exception as e:
        return JsonResponse({"count": 0, "error": str(e)})


def get_ecn_details(request):
    """
    GET: Return ECN record details from tbl_opportunitymaster_ecn for autofill.
    """
    item_no = request.GET.get("item_no", "").strip()
    if not item_no:
        return JsonResponse({"status": "error", "message": "item_no required"}, status=400)
    try:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT ecn_id, ecn_type, item_no, customerid, customername,
                       creation_date, status, supply_location, segment_no, segment_description,
                       part_name, sop_date, drawing_revision_no, application, business,
                       annual_volume, annual_volume_2, annual_volume_3, annual_volume_4, annual_volume_5,
                       annual_volume_year, annual_volume_year_2, annual_volume_year_3,
                       annual_volume_year_4, annual_volume_year_5,
                       part_price_1, part_price_2, estimated_value,
                       salesperson_code, contact_no, contactname,
                       opportunity_received_date, status_date,
                       quotestatus, categorytype, project_name,
                       remarks, life_cycle_in_years,
                       sales_cycle_code, voss_plant_location, reason,
                       priority, closed, date_closed, no_2,
                       sales_goahead_date_for_tool
                FROM tbl_opportunitymaster_ecn
                WHERE item_no=%s
                ORDER BY ecn_id DESC LIMIT 1
            """, [item_no])
            cols = [c[0] for c in cur.description]
            row = cur.fetchone()
        if not row:
            return JsonResponse({"status": "error", "message": "Not found"}, status=404)
        data = dict(zip(cols, row))
        # Format dates
        for k, v in data.items():
            if hasattr(v, 'strftime') and v:
                data[k] = v.strftime('%Y-%m-%d')
        return JsonResponse({"status": "success", "data": data})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def get_opportunity_list(request):
    """
    Return JSON list of opportunities for table view below frm_OpportunityCreation.
    Mirrors SQL:
    SELECT tbl_OpportunityMaster.AttachmentOfReferenceDocs, tbl_OpportunityMaster.Item_No, tbl_OpportunityMaster.CustomerID,
           tbl_OpportunityMaster.CustomerName, tbl_OpportunityMaster.Project_Name, tbl_OpportunityMaster.Opportunity_Received_Date,
           tbl_OpportunityMaster.Salesperson_Code, tbl_OpportunityMaster.Contact_No, tbl_OpportunityMaster.ContactName,
           tbl_OpportunityMaster.Sales_Cycle_Code, tbl_OpportunityMaster.Creation_Date, tbl_OpportunityMaster.Status,
           tbl_OpportunityMaster.Supply_Location, tbl_OpportunityMaster.Segment_No, tbl_OpportunityMaster.Segment_Description,
           tbl_OpportunityMaster.Part_No, tbl_OpportunityMaster.Status_Date, tbl_OpportunityMaster.Part_Name,
           tbl_OpportunityMaster.SOP_Date, tbl_OpportunityMaster.Drawing_Revision_No, tbl_OpportunityMaster.Application,
           tbl_OpportunityMaster.Business, tbl_OpportunityMaster.Voss_Plant_Location, tbl_OpportunityMaster.Sales_Goahead_Date_for_tool,
           tbl_OpportunityMaster.Part_Price_1, tbl_OpportunityMaster.Part_Price_2, tbl_OpportunityMaster.Annual_Volume,
           tbl_OpportunityMaster.Annual_Volume_2, tbl_OpportunityMaster.Annual_Volume_3, tbl_OpportunityMaster.Annual_Volume_4
    FROM tbl_OpportunityMaster
    WHERE (((tbl_OpportunityMaster.Item_No)=[Forms]![frm_OpportunityCreation]![Cmb_Item_No]) AND ((tbl_OpportunityMaster.CustomerID)=[Forms]![frm_OpportunityCreation]![Txt_CustID]));
    """
    customer_id = (request.GET.get("customer_id") or "").strip()
    item_no = (request.GET.get("item_no") or "").strip()

    try:
        with connection.cursor() as cur:
            where_clauses = []
            params = []
            if customer_id:
                where_clauses.append("customerid = %s")
                params.append(customer_id)
            if item_no:
                where_clauses.append("item_no = %s")
                params.append(item_no)

            where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            try:
                cur.execute(f"""
                    SELECT 
                        COALESCE(attachmentofreferencedocs::text, '') AS attachmentofreferencedocs,
                        item_no, customerid, customername, project_name,
                        opportunity_received_date, salesperson_code, contact_no, contactname,
                        sales_cycle_code, creation_date, status, supply_location,
                        segment_no, segment_description, part_no, status_date,
                        part_name, sop_date, drawing_revision_no, application,
                        business, voss_plant_location, sales_goahead_date_for_tool,
                        part_price_1, part_price_2, annual_volume, annual_volume_2,
                        annual_volume_3, annual_volume_4
                    FROM tbl_opportunitymaster
                    {where_str}
                    ORDER BY item_no ASC
                """, params)
            except Exception:
                cur.execute(f"""
                    SELECT 
                        '' AS attachmentofreferencedocs,
                        item_no, customerid, customername, project_name,
                        opportunity_received_date, salesperson_code, contact_no, contactname,
                        sales_cycle_code, creation_date, status, supply_location,
                        segment_no, segment_description, part_no, status_date,
                        part_name, sop_date, drawing_revision_no, application,
                        business, voss_plant_location, sales_goahead_date_for_tool,
                        part_price_1, part_price_2, annual_volume, annual_volume_2,
                        annual_volume_3, annual_volume_4
                    FROM tbl_opportunitymaster
                    {where_str}
                    ORDER BY item_no ASC
                """, params)

            cols = [c[0].lower() for c in cur.description]
            rows = cur.fetchall()

            data = []
            for r in rows:
                row_dict = dict(zip(cols, r))
                for k, v in row_dict.items():
                    if hasattr(v, 'strftime') and v:
                        row_dict[k] = v.strftime('%Y-%m-%d')
                    elif v is None:
                        row_dict[k] = ""
                data.append(row_dict)

            return JsonResponse({"status": "success", "data": data})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e), "data": []})


def get_opportunity_ecn_list(request):
    """
    Return JSON list of ECN records matching user SQL:
    SELECT tbl_OpportunityMaster_ECN.ECN_ID, tbl_OpportunityMaster_ECN.ECN_TYPE, tbl_OpportunityMaster_ECN.CustomerID,
           tbl_OpportunityMaster_ECN.CustomerName, tbl_OpportunityMaster_ECN.Item_No, tbl_OpportunityMaster_ECN.No_2,
           tbl_OpportunityMaster_ECN.Creation_Date, tbl_OpportunityMaster_ECN.Status, tbl_OpportunityMaster_ECN.Priority,
           tbl_OpportunityMaster_ECN.Closed, tbl_OpportunityMaster_ECN.Date_Closed, tbl_OpportunityMaster_ECN.Segment_No,
           tbl_OpportunityMaster_ECN.Estimated_Closing_Date, tbl_OpportunityMaster_ECN.Sales_Cycle_Stage,
           tbl_OpportunityMaster_ECN.Estimated_Value, tbl_OpportunityMaster_ECN.Part_No, tbl_OpportunityMaster_ECN.Part_Name,
           tbl_OpportunityMaster_ECN.Opportunity_Received_Date, tbl_OpportunityMaster_ECN.Annual_Volume,
           tbl_OpportunityMaster_ECN.Drawing_Revision_No, tbl_OpportunityMaster_ECN.Business,
           tbl_OpportunityMaster_ECN.Life_Cycle_in_Years, tbl_OpportunityMaster_ECN.Competitor_Name,
           tbl_OpportunityMaster_ECN.Remarks, tbl_OpportunityMaster_ECN.Annual_Volume_2, tbl_OpportunityMaster_ECN.Annual_Volume_3,
           tbl_OpportunityMaster_ECN.Annual_Volume_4, tbl_OpportunityMaster_ECN.Annual_Volume_5, tbl_OpportunityMaster_ECN.Annual_Volume_Year,
           tbl_OpportunityMaster_ECN.Annual_Volume_Year_2, tbl_OpportunityMaster_ECN.Annual_Volume_Year_3,
           tbl_OpportunityMaster_ECN.Annual_Volume_Year_4, tbl_OpportunityMaster_ECN.Annual_Volume_Year_5,
           tbl_OpportunityMaster_ECN.Supply_Location, tbl_OpportunityMaster_ECN.Part_Price_1, tbl_OpportunityMaster_ECN.Category_of_Project,
           tbl_OpportunityMaster_ECN.Tooling_Payback_Date, tbl_OpportunityMaster_ECN.Part_Price_2,
           tbl_OpportunityMaster_ECN.Sales_Goahead_Date_for_tool, tbl_OpportunityMaster_ECN.Project_Name,
           tbl_OpportunityMaster_ECN.Drawing_No, tbl_OpportunityMaster_ECN.Customer_Name, tbl_OpportunityMaster_ECN.Upload_Status
    FROM tbl_OpportunityMaster_ECN
    WHERE (((tbl_OpportunityMaster_ECN.Item_No)=[Forms]![frm_OpportunityCreation_ECN]![Cmb_SearchOppNo]));
    """
    item_no = (request.GET.get("item_no") or "").strip()
    customer_id = (request.GET.get("customer_id") or "").strip()

    try:
        with connection.cursor() as cur:
            where_clauses = []
            params = []
            if item_no:
                where_clauses.append("item_no = %s")
                params.append(item_no)
            if customer_id:
                where_clauses.append("customerid = %s")
                params.append(customer_id)

            where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            try:
                cur.execute(f"""
                    SELECT 
                        ecn_id, ecn_type, customerid, customername, item_no, no_2,
                        creation_date, status, priority, closed, date_closed, segment_no,
                        estimated_closing_date, sales_cycle_stage, estimated_value, part_no,
                        part_name, opportunity_received_date, annual_volume, drawing_revision_no,
                        business, life_cycle_in_years, competitor_name, remarks, annual_volume_2,
                        annual_volume_3, annual_volume_4, annual_volume_5, annual_volume_year,
                        annual_volume_year_2, annual_volume_year_3, annual_volume_year_4,
                        annual_volume_year_5, supply_location, part_price_1, category_of_project,
                        tooling_payback_date, part_price_2, sales_goahead_date_for_tool,
                        project_name, drawing_no, customer_name, upload_status
                    FROM tbl_opportunitymaster_ecn
                    {where_str}
                    ORDER BY ecn_id ASC
                """, params)
            except Exception:
                cur.execute(f"SELECT * FROM tbl_opportunitymaster_ecn {where_str} ORDER BY ecn_id ASC", params)

            cols = [c[0].lower() for c in cur.description]
            rows = cur.fetchall()

            data = []
            for r in rows:
                row_dict = dict(zip(cols, r))
                for k, v in row_dict.items():
                    if hasattr(v, 'strftime') and v:
                        row_dict[k] = v.strftime('%Y-%m-%d')
                    elif v is None:
                        row_dict[k] = ""
                data.append(row_dict)

            return JsonResponse({"status": "success", "data": data})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e), "data": []})


def send_item_email(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.POST.get("ajax") == "1"

    if request.method != "POST":
        if is_ajax:
            return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)
        messages.error(request, "Invalid request method.")
        return redirect("opportunity_creation")

    form = SendItemEmailForm(request.POST)
    customer_id = request.POST.get("custId", "")
    customer_name = request.POST.get("customer_name", "")
    redirect_url = "{}?{}".format(
        reverse("opportunity_creation"),
        urlencode({"customer_id": customer_id, "name": customer_name}),
    )

    if not form.is_valid():
        if is_ajax:
            return JsonResponse({"status": "error", "message": "Please enter a valid recipient email address."}, status=400)
        messages.error(request, "Please enter a valid recipient email address.")
        return redirect(redirect_url)

    recipient_email = form.cleaned_data["recipient_email"]
    item_details = {
        "Item No / Part Number": request.POST.get("itemNo", ""),
        "Project Name": request.POST.get("projectName", ""),
        "Customer Name": request.POST.get("customer_name", ""),
        "Contact Name": request.POST.get("contactName", ""),
        "Contact No": request.POST.get("contactNo", ""),
        "Estimated Sales Price": request.POST.get("estimatedSalesPrice", ""),
        "Nominated Price": request.POST.get("nominatedPrice", ""),
        "Estimated Value (PA)": request.POST.get("estimatedValuePa", ""),
        "Estimated Value Euro": request.POST.get("estimatedValueEuro", ""),
        "Remarks": request.POST.get("remarks", ""),
        "Status": request.POST.get("status", ""),
    }

    html_body = render_to_string(
        "opportunities/emails/item_details_email.html",
        {"item_details": item_details},
    )

    email = EmailMultiAlternatives(
        subject="Opportunity Details",
        body="Please view this email in an HTML-supported client.",
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[recipient_email],
    )
    email.attach_alternative(html_body, "text/html")

    try:
        email.send()
        if is_ajax:
            return JsonResponse({"status": "success", "message": f"Opportunity details sent successfully to {recipient_email}."})
        messages.success(request, f"Opportunity details sent successfully to {recipient_email}.")
    except Exception as exc:
        if is_ajax:
            return JsonResponse({"status": "error", "message": f"Email could not be sent: {exc}"}, status=500)
        messages.error(request, f"Email could not be sent: {exc}")

    return redirect(redirect_url)


def get_item_numbers(request):
    customer_id = request.GET.get("customer_id", "")

    if not customer_id:
        return JsonResponse({"data": [], "city": "", "contact": "", "creation_date": ""})

    items = ItemCard.objects.filter(customer_id=customer_id)
    numbers = list(items.values_list("no", flat=True))

    customer = CustomerInfo.objects.filter(customer_id=customer_id).first()

    city = ""
    contact = ""
    creation_date = now().strftime("%Y-%m-%d")

    if customer:
        city = customer.city or ""
        contact = customer.contact or ""

    return JsonResponse({
        "data": numbers,
        "city": city,
        "contact": contact,
        "creation_date": creation_date
    })


def get_salespersons(request):
    data = OppSalesPeople.objects.all().values("code", "name")
    result = [{"code": d["code"], "name": d["name"]} for d in data]
    return JsonResponse({"data": result})


def get_sales_cycles(request):
    data = OppSalesCycles.objects.all().values("code", "description", "probability_calculation")
    result = [
        {
            "code": d["code"],
            "description": d["description"],
            "probability": d["probability_calculation"]
        }
        for d in data
    ]
    return JsonResponse({"data": result})


def get_segments(request):
    data = OppSegment.objects.all().values("no", "description")
    result = [{"no": d["no"], "description": d["description"]} for d in data]
    return JsonResponse({"data": result})


def get_opportunity_details(request):
    val = request.GET.get("item_no", "").strip()

    if not val:
        return JsonResponse({"status": "error"}, status=400)

    def _fmt(v):
        if hasattr(v, 'strftime') and v:
            return v.strftime('%Y-%m-%d')
        return v

    def _find(item_no):
        return OpportunityMaster.objects.filter(item_no=item_no).first()

    try:
        opp = _find(val)
        if not opp and not val.startswith('0'):
            opp = _find('0' + val)

        if not opp:
            return JsonResponse({"status": "error", "message": "Not found"}, status=404)

        # Count ECN records safely via raw SQL (avoids PK ordering crash)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM tbl_opportunitymaster_ecn WHERE item_no=%s",
                [opp.item_no]
            )
            row = cur.fetchone()
        last_ecn_count = row[0] if row else 0

        # Build response using Python attribute names (matches fillFromOpp in JS)
        data = {
            "item_no":          opp.item_no,
            "customer_id":      opp.customer_id,
            "customer_name_db": opp.customer_name_db,
            "project_name_db":  opp.project_name_db,
            "opp_received_date":_fmt(opp.opp_received_date),
            "contact_no":       opp.contact_no,
            "contact_name":     opp.contact_name,
            "creation_date":    _fmt(opp.creation_date),
            "status_date":      _fmt(opp.status_date),
            "status":           opp.status,
            "reason":           opp.reason,
            "plant_loc":        opp.plant_loc,
            "segment_no":       opp.segment_no,
            "segment_desc":     opp.segment_desc,
            "part_name":        opp.part_name,
            "sop_date":         _fmt(opp.sop_date),
            "drawing_rev":      opp.drawing_rev,
            "application":      opp.application,
            "business":         opp.business,
            "sales_goahead":    _fmt(opp.sales_goahead),
            "est_price":        opp.est_price,
            "est_val":          opp.est_val,
            "vol1":  opp.vol1,  "year1": opp.year1,
            "vol2":  opp.vol2,  "year2": opp.year2,
            "vol3":  opp.vol3,  "year3": opp.year3,
            "vol4":  opp.vol4,  "year4": opp.year4,
            "vol5":  opp.vol5,  "year5": opp.year5,
            "life_cycle":       opp.life_cycle,
            "remarks":          opp.remarks,
            "quote_status":     opp.quote_status,
            "cat_type":         opp.cat_type,
            "salesperson_code": opp.salesperson_code,
            "sales_cycle_code": opp.sales_cycle_code,
            "last_ecn_no":      last_ecn_count,
        }
        return JsonResponse({"status": "success", "data": data})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# ─── NEW VIEWS ────────────────────────────────────────────────────────────────

def _check_rfq_locked(customer_id, item_no):
    """Helper: returns True if the RFQ is closed for this customer+item."""
    try:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT is_completed FROM tbl_rfq_details WHERE customer_id=%s AND itemcreation_id=%s LIMIT 1",
                [customer_id, item_no],
            )
            row = cur.fetchone()
        return bool(row and row[0] is True)
    except Exception:
        return False


def check_rfq_lock(request):
    """
    GET: check if RFQ is locked for customer_id + item_no.
    Mirrors VBA: DLookup("Is_Completed", "tbl_RFQ_Details", ...)
    """
    customer_id = request.GET.get("customer_id", "").strip()
    item_no = request.GET.get("item_no", "").strip()
    if not customer_id or not item_no:
        return JsonResponse({"locked": False})
    return JsonResponse({"locked": _check_rfq_locked(customer_id, item_no)})


def add_opportunity(request):
    """
    POST: Insert new opportunity into tbl_opportunitymaster.
    Mirrors VBA: btn_AddOpportunity_Click
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    p = request.POST
    reason = (p.get("reason") or "").strip()
    if not reason:
        return JsonResponse({"status": "error", "message": "Please select the reason to save the opportunity!"})

    item_no = (p.get("itemNo") or "").strip()
    customer_id = (p.get("custId") or "").strip()
    if not item_no or not customer_id:
        return JsonResponse({"status": "error", "message": "Item No and Customer ID are required."})

    if _check_rfq_locked(customer_id, item_no):
        return JsonResponse({"status": "error", "message": "RFQ is closed. Cannot add opportunity."})

    def val(key, default=None):
        v = p.get(key)
        return v if v not in (None, "", " ") else default

    def fval(key):
        v = p.get(key)
        try:
            return float(v) if v not in (None, "", " ") else None
        except Exception:
            return None

    today = datetime.date.today().isoformat()
    last_modified = datetime.date.today().isoformat()

    try:
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO tbl_opportunitymaster (
                    item_no, customerid, customername,
                    opportunity_received_date, salesperson_code, contact_no,
                    sales_cycle_code, creation_date, status,
                    estimated_value, supply_location, segment_no, segment_description,
                    part_no, part_price_1, part_price_2, status_date,
                    part_name, sop_date,
                    annual_volume, annual_volume_2, annual_volume_3,
                    annual_volume_4, annual_volume_5,
                    annual_volume_year, annual_volume_year_2, annual_volume_year_3,
                    annual_volume_year_4, annual_volume_year_5,
                    drawing_revision_no, application, business, voss_plant_location,
                    life_cycle_in_years, tooling_payback_date, contactname,
                    remarks, reason, estimated_euro_conv, quotestatus, categorytype,
                    last_modified_date, project_name
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
            """, [
                item_no, customer_id, val("customer_name"),
                val("opportunityReceivedDate"), val("salespersonCode"), val("contactNo"),
                val("salesCycleCode"), val("creationDate") or today, val("status"),
                fval("estimatedValuePa"), val("supplyLocation"), val("segmentNo"), val("segmentDesc"),
                item_no, fval("estimatedSalesPrice"), fval("nominatedPrice"), val("statusDate"),
                val("partName"), val("sopDate"),
                val("annualVolume1", "0"), val("annualVolume2", "0"), val("annualVolume3", "0"),
                val("annualVolume4", "0"), val("annualVolume5", "0"),
                val("annualYear1"), val("annualYear2"), val("annualYear3"),
                val("annualYear4"), val("annualYear5"),
                val("drawingRev"), val("application"), val("business"), val("plantLocation"),
                val("lifeCycleYears"), val("salesGoaheadDate"), val("contactName"),
                val("remarks"), reason, fval("euroConversion"), val("quoteStatus"), val("categoryType"),
                last_modified, val("projectName"),
            ])
        return JsonResponse({"status": "success", "message": "Record saved!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def update_opportunity(request):
    """
    POST: Update existing opportunity.
    Mirrors VBA: Cmd_OppUpdate_Click
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    p = request.POST
    search_item_no = (p.get("searchItemNo") or p.get("itemNo") or "").strip()
    customer_id = (p.get("custId") or "").strip()

    if not search_item_no:
        return JsonResponse({"status": "error", "message": "Item No is required."})

    if _check_rfq_locked(customer_id, search_item_no):
        return JsonResponse({"status": "error", "message": "RFQ is closed. Cannot update opportunity."})

    def val(key, default=None):
        v = p.get(key)
        return v if v not in (None, "", " ") else default

    def fval(key):
        v = p.get(key)
        try:
            return float(v) if v not in (None, "", " ") else None
        except Exception:
            return None

    last_modified = datetime.date.today().isoformat()

    try:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE tbl_opportunitymaster SET
                    customerid=%s, customername=%s,
                    opportunity_received_date=%s, salesperson_code=%s, contact_no=%s,
                    sales_cycle_code=%s, creation_date=%s, status=%s,
                    estimated_value=%s, supply_location=%s, segment_no=%s, segment_description=%s,
                    part_price_1=%s, part_price_2=%s, status_date=%s,
                    part_name=%s, sop_date=%s,
                    annual_volume=%s, annual_volume_2=%s, annual_volume_3=%s,
                    annual_volume_4=%s, annual_volume_5=%s,
                    annual_volume_year=%s, annual_volume_year_2=%s, annual_volume_year_3=%s,
                    annual_volume_year_4=%s, annual_volume_year_5=%s,
                    drawing_revision_no=%s, application=%s, business=%s, voss_plant_location=%s,
                    life_cycle_in_years=%s, tooling_payback_date=%s, contactname=%s,
                    remarks=%s, reason=%s, estimated_euro_conv=%s, quotestatus=%s, categorytype=%s,
                    last_modified_date=%s, is_download=NULL, project_name=%s
                WHERE item_no=%s
            """, [
                customer_id, val("customer_name"),
                val("opportunityReceivedDate"), val("salespersonCode"), val("contactNo"),
                val("salesCycleCode"), val("creationDate"), val("status"),
                fval("estimatedValuePa"), val("supplyLocation"), val("segmentNo"), val("segmentDesc"),
                fval("estimatedSalesPrice"), fval("nominatedPrice"), val("statusDate"),
                val("partName"), val("sopDate"),
                val("annualVolume1", "0"), val("annualVolume2", "0"), val("annualVolume3", "0"),
                val("annualVolume4", "0"), val("annualVolume5", "0"),
                val("annualYear1"), val("annualYear2"), val("annualYear3"),
                val("annualYear4"), val("annualYear5"),
                val("drawingRev"), val("application"), val("business"), val("plantLocation"),
                val("lifeCycleYears"), val("salesGoaheadDate"), val("contactName"),
                val("remarks"), val("reason"), fval("euroConversion"),
                val("quoteStatus"), val("categoryType"),
                last_modified, val("projectName"),
                search_item_no,
            ])

            # Also sync ECN record
            cur.execute("""
                UPDATE tbl_opportunitymaster_ecn SET
                    customerid=%s, customername=%s,
                    opportunity_received_date=%s, salesperson_code=%s, contact_no=%s,
                    creation_date=%s, status=%s, estimated_value=%s,
                    supply_location=%s, segment_no=%s, segment_description=%s,
                    part_price_1=%s, part_price_2=%s, status_date=%s,
                    part_name=%s, sop_date=%s,
                    annual_volume=%s, annual_volume_2=%s, annual_volume_3=%s,
                    annual_volume_4=%s, annual_volume_5=%s,
                    annual_volume_year=%s, annual_volume_year_2=%s, annual_volume_year_3=%s,
                    annual_volume_year_4=%s, annual_volume_year_5=%s,
                    drawing_revision_no=%s, application=%s, business=%s,
                    contactname=%s, quotestatus=%s, categorytype=%s, project_name=%s
                WHERE item_no=%s
            """, [
                customer_id, val("customer_name"),
                val("opportunityReceivedDate"), val("salespersonCode"), val("contactNo"),
                val("creationDate"), val("status"), fval("estimatedValuePa"),
                val("supplyLocation"), val("segmentNo"), val("segmentDesc"),
                fval("estimatedSalesPrice"), fval("nominatedPrice"), val("statusDate"),
                val("partName"), val("sopDate"),
                val("annualVolume1", "0"), val("annualVolume2", "0"), val("annualVolume3", "0"),
                val("annualVolume4", "0"), val("annualVolume5", "0"),
                val("annualYear1"), val("annualYear2"), val("annualYear3"),
                val("annualYear4"), val("annualYear5"),
                val("drawingRev"), val("application"), val("business"),
                val("contactName"), val("quoteStatus"), val("categoryType"), val("projectName"),
                search_item_no,
            ])

        return JsonResponse({"status": "success", "message": "Record updated successfully!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def delete_opportunity(request):
    """
    POST: Delete opportunity and its ECN records.
    Mirrors VBA: Cmd_Delete_Click
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    item_no = (request.POST.get("itemNo") or "").strip()
    customer_id = (request.POST.get("custId") or "").strip()

    if not item_no or not customer_id:
        return JsonResponse({"status": "error", "message": "Item No and Customer ID are required."})

    if _check_rfq_locked(customer_id, item_no):
        return JsonResponse({"status": "error", "message": "RFQ is closed. Cannot delete opportunity."})

    try:
        with connection.cursor() as cur:
            cur.execute(
                "DELETE FROM tbl_opportunitymaster WHERE customerid=%s AND item_no=%s",
                [customer_id, item_no]
            )
            cur.execute(
                "DELETE FROM tbl_opportunitymaster_ecn WHERE customerid=%s AND item_no=%s",
                [customer_id, item_no]
            )
        return JsonResponse({"status": "success", "message": "Record deleted successfully!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def complete_opportunity(request):
    """
    POST: Mark opportunity as completed (completedon = today).
    Mirrors VBA: cmd_complete_Click
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    item_no = (request.POST.get("itemNo") or "").strip()
    customer_id = (request.POST.get("custId") or "").strip()

    if not item_no:
        return JsonResponse({"status": "error", "message": "Item No is required."})

    if _check_rfq_locked(customer_id, item_no):
        return JsonResponse({"status": "error", "message": "RFQ is closed. Cannot complete opportunity."})

    today = datetime.date.today().isoformat()
    try:
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE tbl_opportunitymaster SET completedon=%s WHERE item_no=%s",
                [today, item_no]
            )
        return JsonResponse({"status": "success", "message": "Completed!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def get_item_info(request):
    """
    GET: Return description/part name from tbl_itemcard for given item no.
    Mirrors VBA: Cmb_Item_no_AfterUpdate → DLookup("[Description]", "tbl_ItemCard", ...)
    """
    item_no = request.GET.get("item_no", "").strip()
    if not item_no:
        return JsonResponse({"description": ""})
    try:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT description FROM tbl_itemcard WHERE no=%s LIMIT 1",
                [item_no]
            )
            row = cur.fetchone()
        return JsonResponse({"description": row[0] if row else ""})
    except Exception as e:
        return JsonResponse({"description": "", "error": str(e)})


def save_ecn(request):
    """
    POST: Insert a new REPLICATE ECN record into tbl_opportunitymaster_ecn
    and sync the tbl_opportunitymaster record.
    Mirrors VBA: Cmd_OppUpdate_ECN_Click
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    p = request.POST
    item_no = (p.get("item_no") or "").strip()
    customer_id = (p.get("customer_id") or "").strip()
    if not item_no:
        return JsonResponse({"status": "error", "message": "Item No is required."})

    def val(key, default=None):
        v = p.get(key)
        return v if v not in (None, "", " ") else default

    def fval(key):
        v = p.get(key)
        try:
            return float(v) if v not in (None, "", " ") else None
        except Exception:
            return None

    try:
        with connection.cursor() as cur:
            # Get the current max ECN count for this item to determine new ECN ID
            cur.execute(
                "SELECT COUNT(*) FROM tbl_opportunitymaster_ecn WHERE item_no=%s",
                [item_no],
            )
            row = cur.fetchone()
            count = row[0] if row else 0
            new_ecn_id = f"ECN:{count}"

            # Insert new REPLICATE ECN row
            # Columns: 43 total (ecn_type is a literal, rest are params = 42 params)
            cur.execute("""
                INSERT INTO tbl_opportunitymaster_ecn (
                    ecn_id, ecn_type, item_no, customerid, customername,
                    project_name, opportunity_received_date, salesperson_code,
                    contact_no, contactname, sales_cycle_code, creation_date,
                    status, reason, status_date, supply_location,
                    segment_no, segment_description, part_name, sop_date,
                    drawing_revision_no, application, business, voss_plant_location,
                    sales_goahead_date_for_tool, part_price_1, part_price_2,
                    estimated_value, annual_volume, annual_volume_year,
                    annual_volume_2, annual_volume_year_2,
                    annual_volume_3, annual_volume_year_3,
                    annual_volume_4, annual_volume_year_4,
                    annual_volume_5, annual_volume_year_5,
                    life_cycle_in_years, remarks, quotestatus, categorytype
                ) VALUES (
                    %s, 'REPLICATE', %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s
                )
            """, [
                new_ecn_id, item_no, customer_id, val("customer_name"),
                val("project_name"), val("opportunity_received_date"), val("salesperson_code"),
                val("contact_no"), val("contactname"), val("sales_cycle_code"), val("creation_date"),
                val("status"), val("reason"), val("status_date"), val("supply_location"),
                val("segment_no"), val("segment_description"), val("part_name"), val("sop_date"),
                val("drawing_revision_no"), val("application"), val("business"), val("voss_plant_location"),
                val("sales_goahead_date"),
                fval("part_price_1"), fval("part_price_2"),
                fval("estimated_value"),
                val("annual_volume"), val("annual_volume_year"),
                val("annual_volume_2"), val("annual_volume_year_2"),
                val("annual_volume_3"), val("annual_volume_year_3"),
                val("annual_volume_4"), val("annual_volume_year_4"),
                val("annual_volume_5"), val("annual_volume_year_5"),
                val("life_cycle_in_years"), val("remarks"),
                val("quotestatus"), val("categorytype"),
            ])

            # Also sync tbl_opportunitymaster
            cur.execute("""
                UPDATE tbl_opportunitymaster SET
                    status=%s, reason=%s, status_date=%s,
                    estimated_value=%s, part_price_1=%s, part_price_2=%s,
                    salesperson_code=%s, sales_cycle_code=%s,
                    supply_location=%s, segment_no=%s, segment_description=%s,
                    part_name=%s, sop_date=%s, drawing_revision_no=%s,
                    application=%s, business=%s, voss_plant_location=%s,
                    life_cycle_in_years=%s, remarks=%s,
                    quotestatus=%s, categorytype=%s,
                    project_name=%s, contactname=%s
                WHERE item_no=%s
            """, [
                val("status"), val("reason"), val("status_date"),
                fval("estimated_value"), fval("part_price_1"), fval("part_price_2"),
                val("salesperson_code"), val("sales_cycle_code"),
                val("supply_location"), val("segment_no"), val("segment_description"),
                val("part_name"), val("sop_date"), val("drawing_revision_no"),
                val("application"), val("business"), val("voss_plant_location"),
                val("life_cycle_in_years"), val("remarks"),
                val("quotestatus"), val("categorytype"),
                val("project_name"), val("contactname"),
                item_no,
            ])

        return JsonResponse({
            "status": "success",
            "message": f"ECN record saved as {new_ecn_id}!",
            "new_ecn_id": new_ecn_id,
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def update_ecn(request):
    """
    POST: Update ECN record in tbl_opportunitymaster_ecn.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    p = request.POST
    item_no = (p.get("item_no") or "").strip()
    if not item_no:
        return JsonResponse({"status": "error", "message": "Item No is required."})

    def val(key, default=None):
        v = p.get(key)
        return v if v not in (None, "", " ") else default

    def fval(key):
        v = p.get(key)
        try:
            return float(v) if v not in (None, "", " ") else None
        except Exception:
            return None

    try:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE tbl_opportunitymaster_ecn SET
                    project_name=%s,
                    opportunity_received_date=%s, salesperson_code=%s, contact_no=%s,
                    contactname=%s, sales_cycle_code=%s, creation_date=%s,
                    status=%s, reason=%s, status_date=%s,
                    supply_location=%s, segment_no=%s, segment_description=%s,
                    part_name=%s, sop_date=%s, drawing_revision_no=%s,
                    application=%s, business=%s, voss_plant_location=%s,
                    sales_goahead_date_for_tool=%s,
                    part_price_1=%s, part_price_2=%s, estimated_value=%s,
                    annual_volume=%s, annual_volume_year=%s,
                    annual_volume_2=%s, annual_volume_year_2=%s,
                    annual_volume_3=%s, annual_volume_year_3=%s,
                    annual_volume_4=%s, annual_volume_year_4=%s,
                    annual_volume_5=%s, annual_volume_year_5=%s,
                    life_cycle_in_years=%s, remarks=%s,
                    quotestatus=%s, categorytype=%s
                WHERE item_no=%s
            """, [
                val("project_name"),
                val("opportunity_received_date"), val("salesperson_code"), val("contact_no"),
                val("contactname"), val("sales_cycle_code"), val("creation_date"),
                val("status"), val("reason"), val("status_date"),
                val("supply_location"), val("segment_no"), val("segment_description"),
                val("part_name"), val("sop_date"), val("drawing_revision_no"),
                val("application"), val("business"), val("voss_plant_location"),
                val("sales_goahead_date"),
                fval("part_price_1"), fval("part_price_2"), fval("estimated_value"),
                val("annual_volume"), val("annual_volume_year"),
                val("annual_volume_2"), val("annual_volume_year_2"),
                val("annual_volume_3"), val("annual_volume_year_3"),
                val("annual_volume_4"), val("annual_volume_year_4"),
                val("annual_volume_5"), val("annual_volume_year_5"),
                val("life_cycle_in_years"), val("remarks"),
                val("quotestatus"), val("categorytype"),
                item_no,
            ])
        return JsonResponse({"status": "success", "message": "ECN record updated successfully!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def delete_ecn(request):
    """
    POST: Delete ECN record from tbl_opportunitymaster_ecn.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    item_no = (request.POST.get("item_no") or "").strip()
    if not item_no:
        return JsonResponse({"status": "error", "message": "Item No is required."})

    try:
        with connection.cursor() as cur:
            cur.execute(
                "DELETE FROM tbl_opportunitymaster_ecn WHERE item_no=%s",
                [item_no]
            )
        return JsonResponse({"status": "success", "message": "ECN record deleted successfully!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})