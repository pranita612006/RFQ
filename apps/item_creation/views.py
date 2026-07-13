from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from urllib.parse import urlencode
import datetime
import logging
from .models import ApplyTemplate, ItemCard, UnitOfMeasure, ItemCategory, ProductGroup, Cell, CellType, HSNCode
from .forms import SendItemEmailForm
from config.decorators import require_active_customer

logger = logging.getLogger(__name__)

@require_active_customer
# ✅ ECN Request Page
def item_creation_page(request):
    return render(request, "item_creation/item_creation_form.html")

def ecn_request_page(request):
    # Pass customer_id and customer_name if provided in query string
    return render(request, "item_creation/frm_itemcreation_ecn.html", {
        "customer_id": request.GET.get("customer_id"),
        "customer_name": request.GET.get("customer_name"),
    })

# ✅ Item Creation Form
def item_creation_form(request):
    selected_customer_id = request.active_customer['id']
    selected_name = request.active_customer['name']

    template_names = ApplyTemplate.objects.values_list("template_name", flat=True)

    # ✅ FETCH UOM DATA
    uoms = UnitOfMeasure.objects.all()
    item_categories = ItemCategory.objects.all()
    product_groups = ProductGroup.objects.all()
    cells = Cell.objects.all()
    hsn_codes = HSNCode.objects.all()
    cell_types = CellType.objects.all()

    items = []
    first_item_no = ""
    if selected_customer_id:
        items = list(ItemCard.objects.filter(customer_id=selected_customer_id).values_list("no", flat=True))
        if items:
            first_item_no = items[0]

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
        "first_item_no": first_item_no,
    })

# ✅ Get Template Data
def get_template_data(request):
    template_name = request.GET.get("template_name", "")
    try:
        t = ApplyTemplate.objects.get(template_name=template_name)
        return JsonResponse({
            "item_category_code": getattr(t, 'item_category_code', "") or "",
            "costing_method": getattr(t, 'costing_method', "") or "",
            "inventory_posting_group": getattr(t, 'inventory_posting_group', "") or "",
            "price_profit_calculation": getattr(t, 'price_profit_calculation', "") or "",
            "gen_prod_posting_group": getattr(t, 'gen_prod_posting_group', "") or "",
            "replenishment_system": getattr(t, 'replenishment_system', "") or "",
            "qc_applicable": getattr(t, 'qc_applicable', "") or "",
            "manufacturing_policy": getattr(t, 'manufacturing_policy', "") or "",
            "assembly_policy": getattr(t, 'assembly_policy', "") or "",
            "reordering_policy": getattr(t, 'reordering_policy', "") or "",
            "include_inventory": getattr(t, 'include_inventory', "") or "",
            "gst_credit": getattr(t, 'gst_credit', "") or "",
            "flushing_method": getattr(t, 'flushing_method', "") or "",
            "template_applied": getattr(t, 'template_name', "") or "",
            "rounding_precision": getattr(t, 'rounding_precision', "") or "",
            "gst_group_code": getattr(t, 'gst_group_code', "") or "",
        })
    except ApplyTemplate.DoesNotExist:
        return JsonResponse({"error": "Template not found"}, status=404)
    except Exception as e:
        logger.exception("Error in get_template_data for %s", template_name)
        return JsonResponse({"error": str(e)}, status=500)

# ✅ Get Item Details
def get_item_details(request):
    item_no = request.GET.get("item_no", "").strip()
    cust_id = request.GET.get("customer_id", "").strip()

    if not item_no:
        return JsonResponse({"error": "Missing item_no"}, status=400)

    query = {"no": item_no}
    if cust_id:
        query["customer_id"] = cust_id

    try:
        item = ItemCard.objects.filter(**query).first()

        if not item:
            return JsonResponse({"error": "Item not found"}, status=404)

        # Handle date separately
        last_modified = ""
        if getattr(item, "lastModifiedDate", None):
            try:
                if hasattr(item.lastModifiedDate, "strftime"):
                    last_modified = item.lastModifiedDate.strftime("%Y-%m-%d")
                else:
                    date_str = str(item.lastModifiedDate).strip()
                    parsed_date = None
                    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S'):
                        try:
                            parsed_date = datetime.datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    if parsed_date:
                        last_modified = parsed_date.strftime("%Y-%m-%d")
                    else:
                        last_modified = date_str
            except Exception:
                last_modified = ""

        return JsonResponse({
            "no": getattr(item, "no", "") or "",
            "description": getattr(item, "description", "") or "",
            "base_unit_of_measure": getattr(item, "base_unit_of_measure", "") or "",
            "shelf_no": getattr(item, "shelf_no", "") or "",
            "cell": getattr(item, "cell", "") or "",
            "cell_type": getattr(item, "cell_type", "") or "",
            "item_category_code": getattr(item, "item_category_code", "") or "",
            "product_group_code": getattr(item, "product_group_code", "") or "",
            "status": getattr(item, "status", "") or "",
            "fixture": getattr(item, "fixture", "") or "",
            "noofparts": getattr(item, "noofparts", "") or "",
            "noofmeet": getattr(item, "noofmeet", "") or "",
            "revision": getattr(item, "revision", "") or "",
            "custVenderCode": getattr(item, "custVenderCode", "") or "",
            "hsn": getattr(item, "hsn", "") or "",
            "lastModifiedDate": last_modified
        })

    except Exception as e:
        logger.exception("Error in get_item_details for %s", item_no)
        return JsonResponse({"error": str(e)}, status=500)


def send_item_email(request):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
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
    
    item_details = {
        "Item No": request.POST.get("no", ""),
        "Description": request.POST.get("description", ""),
        "Customer ID": customer_id,
        "Customer Name": customer_name,
        "Base Unit of Measure": request.POST.get("base_unit_of_measure", ""),
        "Status": request.POST.get("status", ""),
        "Revision No": request.POST.get("revision", ""),
        "HSN/SAC Code": request.POST.get("hsn", ""),
        "Last Modified Date": request.POST.get("lastModifiedDate", ""),
    }

    html_body = render_to_string(
        "item_creation/emails/item_details_email.html",
        {"item_details": item_details},
    )

    email = EmailMultiAlternatives(
        subject=f"Item Details - {item_details['Item No']}",
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
