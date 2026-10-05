import json
import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.db.models import Max
from config.decorators import require_active_customer

from .models import BlanketSO, BSOSalesLine
from apps.BOC.models import BocItemCard
from apps.item_creation.models import ItemCard, UnitOfMeasure
from apps.opportunities.models import OpportunityMaster, CustomerInfo


def _cust_variants(customer_id):
    """Return ID variants (padded, stripped) for flexible matching."""
    clean_id = customer_id.strip()
    padded_id = clean_id.zfill(8) if clean_id.isdigit() else clean_id
    lstrip_id = clean_id.lstrip('0') or clean_id
    return list(dict.fromkeys([clean_id, padded_id, lstrip_id]))


def _item_variants(item_no):
    """Return item No variants for flexible matching."""
    clean = item_no.strip()
    padded = clean.zfill(8) if clean.isdigit() else clean
    lstripped = clean.lstrip('0') or clean
    return list(dict.fromkeys([clean, padded, lstripped]))


def _format_date_iso(val):
    """Normalize date strings or date objects into YYYY-MM-DD for HTML5 inputs."""
    if not val:
        return ''
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip()
    if not s:
        return ''
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%b-%Y', '%d-%b-%y'):
        try:
            return datetime.datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return s


def _get_customer_items(customer_id):
    """
    Return list of dicts {no, description} for the active customer.
    Mirrors VBA: SELECT No, Description FROM tbl_ItemCard WHERE CustomerID = [customer_id]
    Also unions items across OpportunityMaster, BOC, BlanketSO, BSOSalesLine so no customer items are missed.
    """
    items_map = {}
    if not customer_id:
        return []
    variants = _cust_variants(customer_id)

    # 1. ItemCard
    for r in ItemCard.objects.filter(customer_id__in=variants).values('no', 'description'):
        no = str(r['no'] or '').strip()
        if no:
            items_map[no] = (r['description'] or '').strip()

    # 2. BocItemCard
    for r in BocItemCard.objects.filter(customerid__in=variants).values('no', 'part_name'):
        no = str(r['no'] or '').strip()
        if no and (no not in items_map or not items_map[no]):
            items_map[no] = (r['part_name'] or '').strip()

    # 3. OpportunityMaster
    for r in OpportunityMaster.objects.filter(customer_id__in=variants).values('item_no', 'part_name'):
        no = str(r['item_no'] or '').strip()
        if no and (no not in items_map or not items_map[no]):
            items_map[no] = (r['part_name'] or '').strip()

    # 4. BlanketSO & BSOSalesLine
    for r in BlanketSO.objects.filter(customer_id__in=variants).values_list('item_creation_id', flat=True).distinct():
        no = str(r or '').strip()
        if no and no not in items_map:
            items_map[no] = ''

    for r in BSOSalesLine.objects.filter(customer_id__in=variants).values('item_creation_id', 'description').distinct():
        no = str(r['item_creation_id'] or '').strip()
        if no and (no not in items_map or not items_map[no]):
            items_map[no] = (r['description'] or '').strip()

    # 5. Raw SQL fallback for tbl_boc_creation
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT itemcreation_id FROM tbl_boc_creation WHERE customer_id IN %s",
                [tuple(variants)]
            )
            for row in cursor.fetchall():
                no = str(row[0] or '').strip()
                if no and no not in items_map:
                    items_map[no] = ''
    except Exception:
        pass

    return [{'no': k, 'description': v} for k, v in sorted(items_map.items(), key=lambda x: str(x[0]))]


@require_active_customer
def BlanketSales_form(request):
    customer_id = request.session.get('active_customer_id', '')
    customer_name = request.session.get('active_customer_name', '')
    cust_vars = _cust_variants(customer_id)

    # Items filtered by customer (mirrors VBA Cmb_Item_no rowsource)
    items = _get_customer_items(customer_id)

    # BSO numbers for this customer (mirrors VBA: WHERE Customer_ID = [customer_id])
    bso_numbers = list(
        BlanketSO.objects.filter(customer_id__in=cust_vars)
        .values_list('bso_creation_id', flat=True)
        .distinct()
        .order_by('bso_creation_id')
    )

    # Location code dropdown – mirrors VBA: SELECT [Location Code] FROM tbl_BSO_LocationCode
    location_options = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT location_code FROM tbl_bso_locationcode "
                "WHERE location_code IS NOT NULL ORDER BY location_code"
            )
            location_options = [r[0] for r in cursor.fetchall() if r[0]]
    except Exception:
        pass
    if not location_options:
        location_options = ['LOCATION 1', 'LOCATION 2', 'PLANT 1', 'DEFAULT']

    status_options = ['Open', 'Released', 'Pending Approval', 'Closed']

    uom_list = list(UnitOfMeasure.objects.values_list('code', flat=True).distinct())
    if not uom_list:
        uom_list = ['NOS', 'PCS', 'SET', 'MTR', 'KG']

    # HSN/SAC codes – mirrors VBA: SELECT Code FROM tbl_ItemCard_Invoice
    hsn_codes = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT code FROM tbl_itemcard_invoice "
                "WHERE code IS NOT NULL ORDER BY code"
            )
            hsn_codes = [r[0] for r in cursor.fetchall() if r[0]]
    except Exception:
        pass

    today_formatted = datetime.date.today().strftime('%Y-%m-%d')

    return render(request, "BlanketSales/BlanketSales_form.html", {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "items": items,
        "bso_numbers": bso_numbers,
        "location_options": location_options,
        "status_options": status_options,
        "uom_list": uom_list,
        "hsn_codes": hsn_codes,
        "today_date": today_formatted,
    })


@require_active_customer
def get_item_customer_details(request):
    """
    Called when Item No is selected (mirrors VBA Cmb_Item_no_AfterUpdate).
    Returns autofill data and BSO dropdown (filtered by customer only, matching VBA query).
    """
    item_no = request.GET.get('item_no', '').strip()
    customer_id = request.session.get('active_customer_id', '').strip()
    customer_name = request.session.get('active_customer_name', '').strip()

    if not item_no or not customer_id:
        return JsonResponse({'error': 'Missing item_no or active customer'}, status=400)

    cust_vars = _cust_variants(customer_id)
    item_vars = _item_variants(item_no)

    opp = OpportunityMaster.objects.filter(item_no__in=item_vars).first()
    cust_info = CustomerInfo.objects.filter(customer_id__in=cust_vars).first()
    item_card = ItemCard.objects.filter(no__in=item_vars).first()

    sellto_contact = (opp.contact_name if opp and opp.contact_name else '')
    country_region_code = ''
    post_code = ''
    if cust_info:
        country_region_code = getattr(cust_info, 'country_region_code', '') or ''
        post_code = getattr(cust_info, 'post_code', '') or ''
        if not sellto_contact and getattr(cust_info, 'contact', None):
            sellto_contact = cust_info.contact

    # Preceding line item for customer or item
    prev_line = (
        BSOSalesLine.objects.filter(customer_id__in=cust_vars, item_creation_id__in=item_vars).order_by('-id_field').first()
        or BSOSalesLine.objects.filter(customer_id__in=cust_vars).order_by('-id_field').first()
    )

    line_no_field = opp.last_ecn_no or opp.item_no if opp else item_no
    line_description = ''
    if item_card and item_card.description:
        line_description = item_card.description
    elif opp and opp.part_name:
        line_description = opp.part_name
    elif prev_line and prev_line.description:
        line_description = prev_line.description

    unit_of_measure = ''
    if item_card and item_card.base_unit_of_measure:
        unit_of_measure = item_card.base_unit_of_measure
    elif prev_line and prev_line.unit_of_measure_code:
        unit_of_measure = prev_line.unit_of_measure_code

    line_location_code = prev_line.location_code if prev_line and prev_line.location_code else ''
    line_plant_code = (
        prev_line.plant_code if prev_line and prev_line.plant_code
        else (opp.plant_loc if opp and opp.plant_loc else '')
    )
    salesperson_code = opp.salesperson_code if opp and opp.salesperson_code else ''
    plant_code = opp.plant_loc if opp and opp.plant_loc else line_plant_code

    gst_group_code = getattr(item_card, 'gst_group_code', '') or ''
    hsn_sac_code = getattr(item_card, 'hsn', '') or ''
    unit_price = (
        float(prev_line.unit_price_excl_tax) if prev_line and prev_line.unit_price_excl_tax is not None
        else (float(item_card.unit_price) if item_card and item_card.unit_price else '')
    )
    rm_base = float(prev_line.rm_base) if prev_line and prev_line.rm_base is not None else ''
    boc_base = float(prev_line.boc_base) if prev_line and prev_line.boc_base is not None else ''
    shipment_date = _format_date_iso(prev_line.shipment_date) if prev_line and prev_line.shipment_date else ''
    price_from_date = _format_date_iso(prev_line.price_from_date) if prev_line and prev_line.price_from_date else ''
    price_to_date = _format_date_iso(prev_line.price_to_date) if prev_line and prev_line.price_to_date else ''

    # BSO dropdown: SELECT BSOCreationID FROM tbl_BlanketSO WHERE Customer_ID = [customer_id]
    bso_numbers = list(
        BlanketSO.objects.filter(customer_id__in=cust_vars)
        .values_list('bso_creation_id', flat=True)
        .distinct()
        .order_by('bso_creation_id')
    )

    existing_bso = BlanketSO.objects.filter(
        item_creation_id__in=item_vars, customer_id__in=cust_vars
    ).order_by('-bso_creation_id').first()

    data = {
        'sellto_contact': sellto_contact,
        'sellto_country_region_code': country_region_code,
        'sellto_post_code': post_code,
        'shipto_code': post_code,
        'billto_post_code': post_code,
        'shipto_contact': sellto_contact,
        'shipto_country_region_code': country_region_code,
        'shipto_name': customer_name,
        'shipto_post_code': post_code,
        'salesperson_code': salesperson_code,
        'plant_code': plant_code,
        'line_defaults': {
            'no': line_no_field,
            'description': line_description,
            'unit_of_measure_code': unit_of_measure,
            'location_code': line_location_code,
            'plant_code': line_plant_code,
            'document_type': 'Blanket Order',
            'sellto_customer_no': customer_id,
            'gst_group_code': gst_group_code,
            'hsn_sac_code': hsn_sac_code,
            'unit_price_excl_tax': unit_price,
            'rm_base': rm_base,
            'boc_base': boc_base,
            'shipment_date': shipment_date,
            'price_from_date': price_from_date,
            'price_to_date': price_to_date,
        },
        'bso_numbers': bso_numbers,
        'has_existing_bso': existing_bso is not None,
    }

    if existing_bso:
        data['bso_data'] = {
            'bso_creation_id': existing_bso.bso_creation_id or '',
            'no': existing_bso.no or '',
            'document_date': _format_date_iso(existing_bso.document_date),
            'sellto_customer_no': existing_bso.sellto_customer_no or customer_id,
            'billto_customer_no': existing_bso.billto_customer_no or customer_id,
            'sellto_customer_name': existing_bso.sellto_customer_name or customer_name,
            'order_date': _format_date_iso(existing_bso.order_date),
            'external_document_no': existing_bso.external_document_no or '',
            'location_code': existing_bso.location_code or '',
            'status': existing_bso.status or 'Open',
            'billto_name': existing_bso.billto_name or customer_name,
            'billto_post_code': existing_bso.billto_post_code or post_code,
            'currency_code': existing_bso.currency_code or 'INR',
            'plant_code': existing_bso.plant_code or plant_code,
            'salesperson_code': existing_bso.salesperson_code or salesperson_code,
            'sellto_contact': existing_bso.sellto_contact or sellto_contact,
            'sellto_country_region_code': existing_bso.sellto_country_region_code or country_region_code,
            'sellto_post_code': existing_bso.sellto_post_code or post_code,
            'shipto_code': existing_bso.shipto_code or post_code,
            'shipto_contact': existing_bso.shipto_contact or sellto_contact,
            'shipto_country_region_code': existing_bso.shipto_country_region_code or country_region_code,
            'shipto_name': existing_bso.shipto_name or customer_name,
            'shipto_post_code': existing_bso.shipto_post_code or post_code,
            'table_id': str(existing_bso.table_id or 1),
            'bso_row_id': existing_bso.bso_row_id or 1,
            'item_creation_id': existing_bso.item_creation_id or item_no,
        }

    return JsonResponse(data)


@require_active_customer
def get_blanketso_details(request):
    """
    Retrieve BlanketSO details and Table IDs when BSO is selected.
    Table ID query mirrors VBA: SELECT DISTINCT Table_Id FROM tbl_BSO_SalesLines
    WHERE ItemCreation_Id = Cmb_Item_no AND BSOCreationID = Cmb_BSOCreationID
    """
    bso_id = request.GET.get('bso_creation_id', '').strip()
    item_no = request.GET.get('item_no', '').strip()

    if not bso_id:
        return JsonResponse({'error': 'Missing bso_creation_id'}, status=400)

    blanket = BlanketSO.objects.filter(bso_creation_id=bso_id).first()
    if not blanket:
        blanket = BlanketSO.objects.filter(bso_creation_id__iexact=bso_id).first()
    if not blanket:
        return JsonResponse({'error': 'BlanketSO not found'}, status=404)

    target_item = (blanket.item_creation_id or item_no).strip()

    # Table IDs from SalesLines, filtered by item+BSO (mirrors VBA Cmb_TableID rowsource)
    tbl_qs = BSOSalesLine.objects.filter(blanket_so_id=blanket.bso_creation_id)
    if target_item:
        tbl_qs_item = tbl_qs.filter(item_creation_id__in=_item_variants(target_item))
        if tbl_qs_item.exists():
            tbl_qs = tbl_qs_item

    table_ids = list(tbl_qs.values_list('table_id', flat=True).distinct())
    clean_table_ids = sorted(
        [str(t) for t in table_ids if t is not None and str(t).strip()],
        key=lambda x: int(x) if x.isdigit() else x
    )
    if blanket.table_id and str(blanket.table_id) not in clean_table_ids:
        clean_table_ids.append(str(blanket.table_id))
    if not clean_table_ids:
        clean_table_ids = ['1']

    # Build line defaults for this BSO and target item
    cust_vars = _cust_variants(blanket.customer_id or request.session.get('active_customer_id', ''))
    target_vars = _item_variants(target_item) if target_item else []
    bso_item_card = ItemCard.objects.filter(no__in=target_vars).first() if target_vars else None
    bso_opp = OpportunityMaster.objects.filter(item_no__in=target_vars).first() if target_vars else None
    bso_prev_line = (
        tbl_qs.order_by('-id_field').first()
        or BSOSalesLine.objects.filter(customer_id__in=cust_vars, item_creation_id__in=target_vars).order_by('-id_field').first()
        or BSOSalesLine.objects.filter(customer_id__in=cust_vars).order_by('-id_field').first()
    )

    bso_line_no = (
        bso_prev_line.line_no_field if bso_prev_line and bso_prev_line.line_no_field
        else (bso_opp.last_ecn_no or bso_opp.item_no if bso_opp else target_item)
    )
    bso_desc = (
        (bso_item_card.description if bso_item_card and bso_item_card.description else None)
        or (bso_opp.part_name if bso_opp and bso_opp.part_name else None)
        or (bso_prev_line.description if bso_prev_line else '')
    )
    bso_uom = (
        (bso_item_card.base_unit_of_measure if bso_item_card and bso_item_card.base_unit_of_measure else None)
        or (bso_prev_line.unit_of_measure_code if bso_prev_line else '')
    )
    bso_loc = (bso_prev_line.location_code if bso_prev_line and bso_prev_line.location_code else blanket.location_code) or ''
    bso_plant = (bso_prev_line.plant_code if bso_prev_line and bso_prev_line.plant_code else blanket.plant_code) or ''
    bso_gst = getattr(bso_item_card, 'gst_group_code', '') or ''
    bso_hsn = getattr(bso_item_card, 'hsn', '') or ''
    bso_price = (
        float(bso_prev_line.unit_price_excl_tax) if bso_prev_line and bso_prev_line.unit_price_excl_tax is not None
        else (float(bso_item_card.unit_price) if bso_item_card and bso_item_card.unit_price else '')
    )
    bso_rm = float(bso_prev_line.rm_base) if bso_prev_line and bso_prev_line.rm_base is not None else ''
    bso_boc = float(bso_prev_line.boc_base) if bso_prev_line and bso_prev_line.boc_base is not None else ''
    bso_ship_dt = _format_date_iso(bso_prev_line.shipment_date) if bso_prev_line and bso_prev_line.shipment_date else ''
    bso_price_from = _format_date_iso(bso_prev_line.price_from_date) if bso_prev_line and bso_prev_line.price_from_date else ''
    bso_price_to = _format_date_iso(bso_prev_line.price_to_date) if bso_prev_line and bso_prev_line.price_to_date else ''

    data = {
        'no': blanket.no or '',
        'document_date': _format_date_iso(blanket.document_date),
        'sellto_customer_no': blanket.sellto_customer_no or '',
        'billto_customer_no': blanket.billto_customer_no or '',
        'sellto_customer_name': blanket.sellto_customer_name or '',
        'order_date': _format_date_iso(blanket.order_date),
        'external_document_no': blanket.external_document_no or '',
        'location_code': blanket.location_code or '',
        'status': blanket.status or '',
        'billto_name': blanket.billto_name or '',
        'billto_post_code': blanket.billto_post_code or '',
        'currency_code': blanket.currency_code or 'INR',
        'plant_code': blanket.plant_code or '',
        'posting_date': _format_date_iso(blanket.posting_date),
        'salesperson_code': blanket.salesperson_code or '',
        'sellto_contact': blanket.sellto_contact or '',
        'sellto_country_region_code': blanket.sellto_country_region_code or '',
        'sellto_post_code': blanket.sellto_post_code or '',
        'shipto_code': blanket.shipto_code or '',
        'shipto_contact': blanket.shipto_contact or '',
        'shipto_country_region_code': blanket.shipto_country_region_code or '',
        'shipto_name': blanket.shipto_name or '',
        'shipto_post_code': blanket.shipto_post_code or '',
        'bso_creation_id': blanket.bso_creation_id or '',
        'bso_row_id': blanket.bso_row_id or 1,
        'item_creation_id': target_item,
        'customer_id': blanket.customer_id or '',
        'table_id': str(blanket.table_id or 1),
        'table_ids': clean_table_ids,
        'line_defaults': {
            'no': bso_line_no or '',
            'description': bso_desc or '',
            'unit_of_measure_code': bso_uom or '',
            'location_code': bso_loc,
            'plant_code': bso_plant,
            'document_type': 'Blanket Order',
            'sellto_customer_no': blanket.sellto_customer_no or blanket.customer_id or '',
            'gst_group_code': bso_gst,
            'hsn_sac_code': bso_hsn,
            'unit_price_excl_tax': bso_price,
            'rm_base': bso_rm,
            'boc_base': bso_boc,
            'shipment_date': bso_ship_dt,
            'price_from_date': bso_price_from,
            'price_to_date': bso_price_to,
        },
    }
    return JsonResponse(data)


@require_active_customer
def get_hsn_codes(request):
    """Return HSN/SAC code list. Mirrors VBA: SELECT Code FROM tbl_ItemCard_Invoice"""
    codes = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT code FROM tbl_itemcard_invoice "
                "WHERE code IS NOT NULL ORDER BY code"
            )
            codes = [r[0] for r in cursor.fetchall() if r[0]]
    except Exception as e:
        return JsonResponse({'error': str(e), 'codes': []})
    return JsonResponse({'codes': codes})


@csrf_exempt
@require_POST
@require_active_customer
def create_blanketso(request):
    """Create a new BlanketSO record (mirrors VBA btn_BSOCreate_Click)."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '').strip()
    customer_name = request.session.get('active_customer_name', '').strip()
    item_creation_id = (body.get('item_no', '') or body.get('item_creation_id', '')).strip()

    if not customer_id:
        return JsonResponse({'error': 'Active customer session missing'}, status=400)
    if not item_creation_id:
        return JsonResponse({'error': 'Item No is required'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COALESCE(MAX(bso_rowid), 0) FROM tbl_blanketso "
            "WHERE itemcreation_id = %s AND customer_id = %s",
            [item_creation_id, customer_id]
        )
        row = cursor.fetchone()
        int_bso_row_id = (row[0] if row else 0) + 1

    user_bso_id = (body.get('bso_creation_id') or '').strip()
    now_str = datetime.datetime.now().strftime('%Y%m%d')
    bso_creation_id = user_bso_id if user_bso_id else f"BSO_{now_str}{int_bso_row_id}"
    table_id = str(body.get('table_id') or '1')

    try:
        BlanketSO.objects.create(
            bso_creation_id=bso_creation_id,
            bso_row_id=int_bso_row_id,
            item_creation_id=item_creation_id,
            customer_id=customer_id,
            customer_name=customer_name,
            table_id=table_id,
            no=body.get('no', ''),
            document_date=body.get('document_date') or None,
            sellto_customer_no=body.get('sellto_customer_no') or customer_id,
            billto_customer_no=body.get('billto_customer_no') or customer_id,
            sellto_customer_name=body.get('sellto_customer_name') or customer_name,
            order_date=body.get('order_date') or None,
            external_document_no=body.get('external_document_no', ''),
            location_code=body.get('location_code', ''),
            status=body.get('status', 'Open'),
            billto_name=body.get('billto_name') or customer_name,
            billto_post_code=body.get('billto_post_code', ''),
            currency_code=body.get('currency_code', 'INR'),
            plant_code=body.get('plant_code', ''),
            posting_date=body.get('posting_date') or None,
            salesperson_code=body.get('salesperson_code', ''),
            sellto_contact=body.get('sellto_contact', ''),
            sellto_country_region_code=body.get('sellto_country_region_code', ''),
            sellto_post_code=body.get('sellto_post_code', ''),
            shipto_code=body.get('shipto_code', ''),
            shipto_contact=body.get('shipto_contact', ''),
            shipto_country_region_code=body.get('shipto_country_region_code', ''),
            shipto_name=body.get('shipto_name') or customer_name,
            shipto_post_code=body.get('shipto_post_code', ''),
        )
    except Exception as e:
        return JsonResponse({'error': f'Failed to create BlanketSO: {str(e)}'}, status=500)

    return JsonResponse({
        'success': True,
        'bso_creation_id': bso_creation_id,
        'table_id': table_id,
        'bso_row_id': int_bso_row_id,
    })


@csrf_exempt
@require_POST
@require_active_customer
def save_blanketso(request):
    """Update an existing BlanketSO record (mirrors VBA btn_BSOSave_Click)."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    bso_creation_id = body.get('bso_creation_id', '').strip()
    if not bso_creation_id:
        return JsonResponse({'error': 'bso_creation_id is required'}, status=400)

    table_id = str(body.get('table_id') or '1')
    updated = BlanketSO.objects.filter(bso_creation_id=bso_creation_id).update(
        no=body.get('no') or None,
        document_date=body.get('document_date') or None,
        sellto_customer_no=body.get('sellto_customer_no') or None,
        billto_customer_no=body.get('billto_customer_no') or None,
        sellto_customer_name=body.get('sellto_customer_name') or None,
        order_date=body.get('order_date') or None,
        external_document_no=body.get('external_document_no') or None,
        location_code=body.get('location_code') or None,
        status=body.get('status') or None,
        billto_name=body.get('billto_name') or None,
        billto_post_code=body.get('billto_post_code') or None,
        currency_code=body.get('currency_code') or 'INR',
        plant_code=body.get('plant_code') or None,
        posting_date=body.get('posting_date') or None,
        salesperson_code=body.get('salesperson_code') or None,
        sellto_contact=body.get('sellto_contact') or None,
        sellto_country_region_code=body.get('sellto_country_region_code') or None,
        sellto_post_code=body.get('sellto_post_code') or None,
        shipto_code=body.get('shipto_code') or None,
        shipto_contact=body.get('shipto_contact') or None,
        shipto_country_region_code=body.get('shipto_country_region_code') or None,
        shipto_name=body.get('shipto_name') or None,
        shipto_post_code=body.get('shipto_post_code') or None,
        table_id=table_id,
    )
    if updated == 0:
        return JsonResponse({'error': 'BlanketSO not found'}, status=404)
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
@require_active_customer
def create_bso_table(request):
    """Create new Table ID for a BSO (mirrors VBA btn_BSOCreateTable_Click)."""
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    bso_creation_id = body.get('bso_creation_id', '').strip()
    item_no = body.get('item_no', '').strip()

    if not bso_creation_id:
        return JsonResponse({'error': 'bso_creation_id is required'}, status=400)

    qs = BSOSalesLine.objects.filter(blanket_so_id=bso_creation_id)
    if item_no:
        qs = qs.filter(item_creation_id__in=_item_variants(item_no))

    existing_tids = list(qs.values_list('table_id', flat=True))
    int_ids = []
    for tid in existing_tids:
        try:
            if tid:
                int_ids.append(int(tid))
        except (ValueError, TypeError):
            pass
    new_table_id = (max(int_ids) if int_ids else 0) + 1
    return JsonResponse({'success': True, 'table_id': str(new_table_id)})


@require_active_customer
def get_bso_lines(request):
    """
    Return sales lines filtered by BSO, item, and table_id.
    Mirrors VBA Func_ShowBSOLineItem SQL query.
    """
    bso_id = request.GET.get('bso_creation_id', '').strip()
    item_no = request.GET.get('item_no', '').strip()
    table_id = request.GET.get('table_id')
    if table_id is not None:
        table_id = str(table_id).strip()

    if not bso_id:
        return JsonResponse({'records': []})

    qs = BSOSalesLine.objects.filter(blanket_so_id=bso_id)
    if not qs.exists():
        qs = BSOSalesLine.objects.filter(blanket_so_id__iexact=bso_id)

    # ── Mirror VBA: WHERE ItemCreation_Id=X AND BSOCreationID=Y AND Table_Id=Z ──
    # Step 1: filter by item_no FIRST (primary key for line grouping in VBA)
    if item_no:
        qs_item = qs.filter(item_creation_id__in=_item_variants(item_no))
        if qs_item.exists():
            qs = qs_item
        else:
            # Fallback: try BSO's own item_creation_id
            blanket = BlanketSO.objects.filter(bso_creation_id=bso_id).first()
            if blanket and blanket.item_creation_id:
                qs_blanket_item = qs.filter(
                    item_creation_id__in=_item_variants(blanket.item_creation_id)
                )
                if qs_blanket_item.exists():
                    qs = qs_blanket_item
            # If still no match, keep all lines for this BSO (don't return empty)

    # Step 2: filter by table_id (sub-group within item+BSO)
    if table_id:
        qs_table = qs.filter(table_id=table_id)
        if qs_table.exists():
            qs = qs_table
        # If no lines for this table_id, show all remaining lines (item-filtered)

    lines = list(qs.order_by('line_no').values(
        'id_field', 'document_type', 'document_no', 'sellto_customer_no',
        'line_type', 'line_no', 'line_no_field', 'description', 'location_code',
        'reserve', 'quantity', 'unit_of_measure_code', 'unit_price_excl_tax',
        'line_amount_excl_tax', 'line_discount', 'shipment_date',
        'outstanding_quantity',
        'price_from_date', 'price_to_date', 'remarks',
        'plant_code', 'rm_base', 'boc_base', 'table_id', 'item_creation_id',
    ))

    # Pre-fetch item cards for GST and HSN codes
    line_item_ids = [l['item_creation_id'] for l in lines if l.get('item_creation_id')]
    item_cards_map = {}
    if line_item_ids:
        for ic in ItemCard.objects.filter(no__in=line_item_ids):
            item_cards_map[ic.no] = ic

    for line in lines:
        for f in ('shipment_date', 'price_from_date', 'price_to_date'):
            if line.get(f):
                line[f] = _format_date_iso(line[f])
        for f in ('quantity', 'unit_price_excl_tax', 'line_amount_excl_tax',
                  'line_discount', 'outstanding_quantity', 'rm_base', 'boc_base'):
            if line.get(f) is not None:
                try:
                    line[f] = float(line[f])
                except (ValueError, TypeError):
                    pass
        line['qty_to_ship'] = None
        line['qty_shipped'] = None
        line['qty_invoiced'] = None

        ic = item_cards_map.get(line.get('item_creation_id'))
        if not ic and item_no:
            ic = ItemCard.objects.filter(no__in=_item_variants(item_no)).first()
        line['gst_group_code'] = getattr(ic, 'gst_group_code', '') or ''
        line['hsn_sac_code'] = getattr(ic, 'hsn', '') or ''
        if not line.get('description') and ic and ic.description:
            line['description'] = ic.description

    return JsonResponse({'records': lines})


@csrf_exempt
@require_POST
@require_active_customer
def add_bso_line(request):
    """
    Add a new sales line (mirrors VBA btnAdd_BSO_Click).
    Auto-calculates LineAmountExclTax = Qty * UnitPrice,
    OutstandingQty = Qty - QtyInvoiced.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    bso_creation_id = body.get('bso_creation_id', '').strip()
    customer_id = request.session.get('active_customer_id', '').strip()
    customer_name = request.session.get('active_customer_name', '').strip()
    item_creation_id = body.get('item_no', '').strip()
    table_id = str(body.get('table_id') or '1')

    if not bso_creation_id:
        return JsonResponse({'error': 'bso_creation_id is required'}, status=400)
    if not body.get('quantity'):
        return JsonResponse({'error': 'Quantity cannot be blank'}, status=400)
    if not body.get('price_to_date'):
        return JsonResponse({'error': 'PriceToDate cannot be blank'}, status=400)

    blanket = BlanketSO.objects.filter(bso_creation_id=bso_creation_id).first()
    if not blanket:
        return JsonResponse({'error': 'Parent BlanketSO not found'}, status=404)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COALESCE(MAX(lineno), 0) FROM tbl_bso_saleslines WHERE bsocreationid = %s",
            [bso_creation_id]
        )
        row = cursor.fetchone()
        next_line_no = float((row[0] if row else 0)) + 10000

    quantity = body.get('quantity')
    unit_price = body.get('unit_price_excl_tax')
    line_amount = body.get('line_amount_excl_tax')
    if quantity and unit_price and not line_amount:
        try:
            line_amount = float(quantity) * float(unit_price)
        except (ValueError, TypeError):
            pass

    qty_invoiced = body.get('qty_invoiced')
    outstanding_qty = body.get('outstanding_quantity')
    if outstanding_qty is None and quantity and qty_invoiced:
        try:
            outstanding_qty = float(quantity) - float(qty_invoiced)
        except (ValueError, TypeError):
            pass

    remarks = body.get('remarks') or 'NA'

    try:
        line = BSOSalesLine.objects.create(
            blanket_so=blanket,
            item_creation_id=item_creation_id,
            customer_id=customer_id,
            customer_name=customer_name,
            table_id=table_id,
            document_type=body.get('document_type', 'Blanket Order'),
            document_no=body.get('document_no', ''),
            sellto_customer_no=body.get('sellto_customer_no', customer_id),
            line_type=body.get('line_type', 'Item'),
            line_no=next_line_no,
            line_no_field=body.get('line_no_field') or body.get('no', ''),
            description=body.get('description', ''),
            location_code=body.get('location_code', ''),
            reserve=body.get('reserve', ''),
            quantity=quantity or None,
            unit_of_measure_code=body.get('unit_of_measure_code', ''),
            unit_price_excl_tax=unit_price or None,
            line_amount_excl_tax=line_amount or None,
            line_discount=body.get('line_discount') or None,
            shipment_date=body.get('shipment_date') or '',
            outstanding_quantity=outstanding_qty or None,
            price_from_date=body.get('price_from_date') or '',
            price_to_date=body.get('price_to_date') or '',
            remarks=remarks,
            plant_code=body.get('plant_code', ''),
            rm_base=body.get('rm_base') or None,
            boc_base=body.get('boc_base') or None,
        )
    except Exception as e:
        return JsonResponse({'error': f'Failed to add sales line: {str(e)}'}, status=500)

    return JsonResponse({'success': True, 'id': line.id_field, 'line_no': next_line_no})


@csrf_exempt
@require_POST
@require_active_customer
def save_bso_line(request):
    """Update an existing BSOSalesLine (mirrors VBA btnSave_BSO_Click)."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    line_id = body.get('id') or body.get('id_field')
    if not line_id:
        return JsonResponse({'error': 'Line id is required'}, status=400)

    quantity = body.get('quantity')
    unit_price = body.get('unit_price_excl_tax')
    line_amount = body.get('line_amount_excl_tax')
    if quantity and unit_price and not line_amount:
        try:
            line_amount = float(quantity) * float(unit_price)
        except (ValueError, TypeError):
            pass

    qty_invoiced = body.get('qty_invoiced')
    outstanding_qty = body.get('outstanding_quantity')
    if outstanding_qty is None and quantity and qty_invoiced:
        try:
            outstanding_qty = float(quantity) - float(qty_invoiced)
        except (ValueError, TypeError):
            pass

    updated = BSOSalesLine.objects.filter(id_field=line_id).update(
        line_type=body.get('line_type'),
        line_no_field=body.get('line_no_field') or body.get('no'),
        description=body.get('description'),
        location_code=body.get('location_code'),
        plant_code=body.get('plant_code'),
        unit_of_measure_code=body.get('unit_of_measure_code'),
        unit_price_excl_tax=unit_price or None,
        line_amount_excl_tax=line_amount or None,
        line_discount=body.get('line_discount') or None,
        shipment_date=body.get('shipment_date') or '',
        quantity=quantity or None,
        outstanding_quantity=outstanding_qty or None,
        price_from_date=body.get('price_from_date') or '',
        price_to_date=body.get('price_to_date') or '',
        remarks=body.get('remarks'),
        rm_base=body.get('rm_base') or None,
        boc_base=body.get('boc_base') or None,
    )
    if updated == 0:
        return JsonResponse({'error': 'Line item not found'}, status=404)
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
@require_active_customer
def delete_bso_line(request):
    """Delete a BSOSalesLine (mirrors VBA Cmd_DeleteBSOLine_Click)."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    line_id = body.get('id') or body.get('id_field')
    if not line_id:
        return JsonResponse({'error': 'Line id is required'}, status=400)

    deleted, _ = BSOSalesLine.objects.filter(id_field=line_id).delete()
    if deleted == 0:
        return JsonResponse({'error': 'Line item not found'}, status=404)
    return JsonResponse({'success': True})
