from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from urllib.parse import urlencode
from .models import Opportunity
from apps.item_creation.models import ItemCard
from .models import CustomerInfo, OppSalesPeople, OppSalesCycles, OppSegment, OpportunityMaster, OpportunityMasterECN
from django.utils.timezone import now
from django.db.models import Max

from django.shortcuts import render, redirect  # Add redirect to your imports
from .forms import SendItemEmailForm
from config.decorators import require_active_customer

@require_active_customer
def opportunity_creation(request):
    # 1. Extract values from the active customer session
    customer_id = request.active_customer['id']
    customer_name = request.active_customer['name']

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            Opportunity.objects.create(
                projectName=request.POST.get('projectName'),
                customerName=request.POST.get('customerName'),
                contactName=request.POST.get('contactName'),
                contactNo=request.POST.get('contactNo'),
                itemNo=request.POST.get('itemNo'),
                custId=request.POST.get('custId'),
                estimatedSalesPrice=request.POST.get('estimatedSalesPrice') or 0,
                nominatedPrice=request.POST.get('nominatedPrice') or 0,
                creationDate=request.POST.get('creationDate') or None,
                status=request.POST.get('status'),
                remarks=request.POST.get('remarks'),
            )
            
    from django.shortcuts import render

# Existing views...

def opportunitycreation_ecn(request):
    """
    Render the ECN Request For Opportunity Creation page.
    """
    return render(request, "opportunities/frm_opportunitycreation_ecn.html")



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

    result = [
        {"code": d["code"], "name": d["name"]}
        for d in data
    ]

    return JsonResponse({"data": result})

def get_sales_cycles(request):
    data = OppSalesCycles.objects.all().values(
        "code", "description", "probability_calculation"
    )

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

    result = [
        {
            "no": d["no"],
            "description": d["description"]
        }
        for d in data
    ]

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
            # ✅ FETCH LAST ECN (IMPORTANT)
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

