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


def opportunitycreation_ecn(request):
    """
    Render the ECN Request For Opportunity Creation page.
    """
    customer_id = ""
    customer_name = ""
    if hasattr(request, 'active_customer') and request.active_customer:
        customer_id = request.active_customer.get('id', '')
        customer_name = request.active_customer.get('name', '')

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


def send_item_email(request):
    if request.method != "POST":
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
        messages.success(request, f"Opportunity details sent successfully to {recipient_email}.")
    except Exception as exc:
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

    try:
        opportunity = OpportunityMaster.objects.filter(item_no=val).values().first()

        if not opportunity and not val.startswith('0'):
            opportunity = OpportunityMaster.objects.filter(item_no='0'+val).values().first()

        if opportunity:
            # ✅ FETCH LAST ECN
            last_ecn = OpportunityMasterECN.objects.filter(
                item_no=opportunity["item_no"]
            ).order_by("-ecn_id").values_list("ecn_id", flat=True).first()

            opportunity["last_ecn_no"] = last_ecn

            # format dates
            for key, value in opportunity.items():
                if hasattr(value, 'strftime') and value:
                    opportunity[key] = value.strftime('%Y-%m-%d')

            return JsonResponse({"status": "success", "data": opportunity})

        return JsonResponse({"status": "error", "message": "Not found"}, status=404)

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