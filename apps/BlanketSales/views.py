import json
import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from config.decorators import require_active_customer

from .models import BlanketSO, BSOSalesLine
from apps.BOC.models import BocItemCard
from apps.item_creation.models import ItemCard, UnitOfMeasure
from apps.opportunities.models import OpportunityMaster, CustomerInfo


@require_active_customer
def BlanketSales_form(request):
    customer_id = request.session.get('active_customer_id', '')
    customer_name = request.session.get('active_customer_name', '')

    # 1. Fetch Item numbers associated with this customer
    item_nos = []
    if customer_id:
        clean_id = customer_id.strip()
        padded_id = clean_id.zfill(8) if clean_id.isdigit() else clean_id
        lstrip_id = clean_id.lstrip('0') or clean_id
        variants = list(dict.fromkeys([clean_id, padded_id, lstrip_id]))

        # Try BocItemCard
        item_nos = list(BocItemCard.objects.filter(customerid__in=variants).values_list('no', flat=True).distinct())
        if not item_nos:
            item_nos = list(ItemCard.objects.filter(customer_id__in=variants).values_list('no', flat=True).distinct())
        if not item_nos:
            item_nos = list(OpportunityMaster.objects.filter(customer_id__in=variants).values_list('item_no', flat=True).distinct())

    # 2. Location options
    location_options = ['LOCATION 1', 'LOCATION 2', 'PLANT 1', 'DEFAULT']
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT locationcode FROM tbl_bso_locationcode WHERE locationcode IS NOT NULL")
            locs = [row[0] for row in cursor.fetchall() if row[0]]
            if locs:
                location_options = locs
    except Exception:
        pass

    # 3. Status options
    status_options = ['Open', 'Released', 'Pending Approval', 'Closed']

    # 4. Units of measure
    uom_list = list(UnitOfMeasure.objects.values_list('code', flat=True).distinct())
    if not uom_list:
        uom_list = ['NOS', 'PCS', 'SET', 'MTR', 'KG']

    today_formatted = datetime.date.today().strftime('%d-%b-%y')

    return render(request, "BlanketSales/BlanketSales_form.html", {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "item_nos": item_nos,
        "location_options": location_options,
        "status_options": status_options,
        "uom_list": uom_list,
        "today_date": today_formatted,
    })


@require_active_customer
def get_item_customer_details(request):
    """
    Called when an Item No is selected (matches Cmb_Item_no_AfterUpdate in VBA).
    Fetches Opportunity, Customer, Item Card, and existing BlanketSO records for autofill.
    """
    item_no = request.GET.get('item_no', '').strip()
    customer_id = request.session.get('active_customer_id', '').strip()
    customer_name = request.session.get('active_customer_name', '').strip()

    if not item_no or not customer_id:
        return JsonResponse({'error': 'Missing item_no or active customer'}, status=400)

    clean_id = customer_id
    padded_id = clean_id.zfill(8) if clean_id.isdigit() else clean_id
    lstrip_id = clean_id.lstrip('0') or clean_id
    cust_variants = list(dict.fromkeys([clean_id, padded_id, lstrip_id]))

    item_clean = item_no
    item_padded = item_clean.zfill(8) if item_clean.isdigit() else item_clean
    item_lstrip = item_clean.lstrip('0') or item_clean
    item_variants = list(dict.fromkeys([item_clean, item_padded, item_lstrip]))

    # Lookups matching VBA DLookup calls
    opp = OpportunityMaster.objects.filter(item_no__in=item_variants).first()
    cust_info = CustomerInfo.objects.filter(customer_id__in=cust_variants).first()
    item_card = ItemCard.objects.filter(no__in=item_variants).first()

    # sellto_contact from OpportunityMaster.contact_name
    sellto_contact = opp.contact_name if opp and opp.contact_name else ''
    
    # country/region code and postcode from CustomerInfo
    country_region_code = ''
    post_code = ''
    if cust_info:
        country_region_code = getattr(cust_info, 'country_region_code', '') or ''
        post_code = getattr(cust_info, 'post_code', '') or ''
        if not sellto_contact and getattr(cust_info, 'contact', None):
            sellto_contact = cust_info.contact

    # Line item defaults
    line_no_field = opp.last_ecn_no or opp.item_no if opp else item_no
    line_description = item_card.description if item_card and item_card.description else (opp.part_name if opp else '')
    
    unit_of_measure = ''
    if item_card and item_card.base_unit_of_measure:
        unit_of_measure = item_card.base_unit_of_measure

    # Location code and plant code from latest BSO Sales Line or Opportunity
    prev_line = BSOSalesLine.objects.filter(customer_id__in=cust_variants).last()
    line_location_code = prev_line.location_code if prev_line and prev_line.location_code else ''
    line_plant_code = prev_line.plant_code if prev_line and prev_line.plant_code else (opp.plant_loc if opp and opp.plant_loc else '')

    salesperson_code = opp.salesperson_code if opp and opp.salesperson_code else ''
    plant_code = opp.plant_loc if opp and opp.plant_loc else line_plant_code

    # Check existing BlanketSO for this Item and Customer
    existing_bso = None
    for iv in item_variants:
        for cv in cust_variants:
            existing_bso = BlanketSO.objects.filter(item_creation_id=iv, customer_id=cv).first()
            if existing_bso:
                break
        if existing_bso:
            break

    # Get list of all BSO numbers (bso_creation_id) for this item
    bso_numbers = list(
        BlanketSO.objects.filter(item_creation_id__in=item_variants, customer_id__in=cust_variants)
        .values_list('bso_creation_id', flat=True)
        .distinct()
    )

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
        # Line item defaults
        'line_defaults': {
            'no': line_no_field,
            'description': line_description,
            'unit_of_measure_code': unit_of_measure,
            'location_code': line_location_code,
            'plant_code': line_plant_code,
            'document_type': 'Blanket Order',
            'sellto_customer_no': customer_id,
        },
        'bso_numbers': bso_numbers,
        'has_existing_bso': existing_bso is not None,
    }

    if existing_bso:
        data['bso_data'] = {
            'bso_creation_id': existing_bso.bso_creation_id or '',
            'no': existing_bso.no or '',
            'document_date': str(existing_bso.document_date) if existing_bso.document_date else '',
            'sellto_customer_no': existing_bso.sellto_customer_no or customer_id,
            'billto_customer_no': existing_bso.billto_customer_no or customer_id,
            'sellto_customer_name': existing_bso.sellto_customer_name or customer_name,
            'order_date': str(existing_bso.order_date) if existing_bso.order_date else '',
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
            'table_id': existing_bso.table_id or 1,
            'bso_row_id': existing_bso.bso_row_id or 1,
        }

    return JsonResponse(data)


@require_active_customer
def get_blanketso_details(request):
    """Retrieve BlanketSO details by BSO creation ID (bso_creation_id)."""
    bso_id = request.GET.get('bso_creation_id', '').strip()
    if not bso_id:
        return JsonResponse({'error': 'Missing bso_creation_id'}, status=400)
    
    blanket = BlanketSO.objects.filter(bso_creation_id=bso_id).first()
    if not blanket:
        return JsonResponse({'error': 'BlanketSO not found'}, status=404)

    # Get distinct table_ids for this BSO
    table_ids = list(
        BlanketSO.objects.filter(bso_creation_id=bso_id)
        .values_list('table_id', flat=True)
        .distinct()
    )
    if not table_ids or table_ids == [None]:
        table_ids = [1]

    data = {
        'no': blanket.no or '',
        'document_date': str(blanket.document_date) if blanket.document_date else '',
        'sellto_customer_no': blanket.sellto_customer_no or '',
        'billto_customer_no': blanket.billto_customer_no or '',
        'sellto_customer_name': blanket.sellto_customer_name or '',
        'order_date': str(blanket.order_date) if blanket.order_date else '',
        'external_document_no': blanket.external_document_no or '',
        'location_code': blanket.location_code or '',
        'status': blanket.status or '',
        'billto_name': blanket.billto_name or '',
        'billto_post_code': blanket.billto_post_code or '',
        'currency_code': blanket.currency_code or 'INR',
        'plant_code': blanket.plant_code or '',
        'posting_date': str(blanket.posting_date) if blanket.posting_date else '',
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
        'item_creation_id': blanket.item_creation_id or '',
        'customer_id': blanket.customer_id or '',
        'table_id': blanket.table_id or 1,
        'table_ids': table_ids,
    }
    return JsonResponse(data)


@csrf_exempt
@require_POST
@require_active_customer
def create_blanketso(request):
    """Create a new BlanketSO record (matches btn_BSOCreate_Click in VBA)."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '').strip()
    customer_name = request.session.get('active_customer_name', '').strip()
    item_creation_id = body.get('item_no', '').strip() or body.get('item_creation_id', '').strip()

    if not customer_id:
        return JsonResponse({'error': 'Active customer session missing'}, status=400)
    if not item_creation_id:
        return JsonResponse({'error': 'Item No is required'}, status=400)

    # 1. Calculate intBSORowID = MAX(bso_row_id) + 1
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(MAX(bso_rowid), 0)
            FROM tbl_blanketso
            WHERE itemcreation_id = %s AND customer_id = %s
            """,
            [item_creation_id, customer_id]
        )
        row = cursor.fetchone()
        int_bso_row_id = (row[0] if row else 0) + 1

    # 2. Format sBSOCreationID = "BSO_" + yyyymmdd + intBSORowID
    now_str = datetime.datetime.now().strftime('%Y%m%d')
    bso_creation_id = f"BSO_{now_str}{int_bso_row_id}"
    table_id = 1

    # 3. Create or insert record
    try:
        blanket = BlanketSO.objects.create(
            bso_creation_id=bso_creation_id,
            bso_row_id=int_bso_row_id,
            item_creation_id=item_creation_id,
            customer_id=customer_id,
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
    """Update an existing BlanketSO record (matches btn_BSOSave_Click in VBA)."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    bso_creation_id = body.get('bso_creation_id', '').strip()
    customer_id = request.session.get('active_customer_id', '').strip()
    item_creation_id = body.get('item_no', '').strip() or body.get('item_creation_id', '').strip()

    if not bso_creation_id:
        return JsonResponse({'error': 'bso_creation_id is required'}, status=400)

    updated = BlanketSO.objects.filter(
        bso_creation_id=bso_creation_id
    ).update(
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
        table_id=body.get('table_id') or 1,
    )
    if updated == 0:
        return JsonResponse({'error': 'BlanketSO not found'}, status=404)
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
@require_active_customer
def create_bso_table(request):
    """Create a new Table ID for BSO (matches btn_BSOCreateTable_Click in VBA)."""
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    bso_creation_id = body.get('bso_creation_id', '').strip()
    item_creation_id = body.get('item_no', '').strip()

    if not bso_creation_id:
        return JsonResponse({'error': 'bso_creation_id is required'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(MAX(table_id), 0)
            FROM tbl_blanketso
            WHERE bso_creationid = %s
            """,
            [bso_creation_id]
        )
        row = cursor.fetchone()
        new_table_id = (row[0] if row else 0) + 1

    return JsonResponse({'success': True, 'table_id': new_table_id})


@require_active_customer
def get_bso_lines(request):
    """Return all sales lines for a given BlanketSO (matches Func_ShowBSOLineItems in VBA)."""
    bso_id = request.GET.get('bso_creation_id', '').strip()
    table_id = request.GET.get('table_id')

    if not bso_id:
        return JsonResponse({'records': []})

    qs = BSOSalesLine.objects.filter(blanket_so__bso_creation_id=bso_id)
    if table_id:
        try:
            qs = qs.filter(table_id=int(table_id))
        except (ValueError, TypeError):
            pass

    lines = list(qs.order_by('line_no').values(
        'id_field', 'document_type', 'document_no', 'sellto_customer_no', 'line_type', 'line_no',
        'line_no_field', 'description', 'location_code', 'reserve', 'quantity', 'unit_of_measure_code',
        'line_amount_excl_tax', 'shipment_date', 'outstanding_quantity', 'price_from_date',
        'price_to_date', 'remarks', 'unit_price_excl_tax', 'line_discount', 'plant_code',
        'rm_base', 'boc_base'
    ))
    return JsonResponse({'records': lines})


@csrf_exempt
@require_POST
@require_active_customer
def add_bso_line(request):
    """Add a new line item in tbl_bso_saleslines."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    bso_creation_id = body.get('bso_creation_id', '').strip()
    customer_id = request.session.get('active_customer_id', '').strip()
    item_creation_id = body.get('item_no', '').strip()
    table_id = body.get('table_id') or 1

    if not bso_creation_id:
        return JsonResponse({'error': 'bso_creation_id is required'}, status=400)

    blanket = BlanketSO.objects.filter(bso_creation_id=bso_creation_id).first()
    if not blanket:
        return JsonResponse({'error': 'Parent BlanketSO not found'}, status=404)

    # Calculate line_no (auto-increment: max + 10000 or max + 1)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(MAX(lineno), 0)
            FROM tbl_bso_saleslines
            WHERE bso_creationid = %s
            """,
            [bso_creation_id]
        )
        row = cursor.fetchone()
        next_line_no = (row[0] if row else 0) + 10000

    try:
        line = BSOSalesLine.objects.create(
            blanket_so=blanket,
            item_creation_id=item_creation_id,
            customer_id=customer_id,
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
            quantity=body.get('quantity') or None,
            unit_of_measure_code=body.get('unit_of_measure_code', ''),
            line_amount_excl_tax=body.get('line_amount_excl_tax') or None,
            shipment_date=body.get('shipment_date') or None,
            outstanding_quantity=body.get('outstanding_quantity') or None,
            price_from_date=body.get('price_from_date') or None,
            price_to_date=body.get('price_to_date') or None,
            remarks=body.get('remarks', ''),
            unit_price_excl_tax=body.get('unit_price_excl_tax') or None,
            line_discount=body.get('line_discount') or None,
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
    """Update an existing BSOSalesLine."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    line_id = body.get('id') or body.get('id_field')
    if not line_id:
        return JsonResponse({'error': 'Line id is required'}, status=400)

    updated = BSOSalesLine.objects.filter(id_field=line_id).update(
        line_no_field=body.get('line_no_field') or body.get('no'),
        description=body.get('description'),
        location_code=body.get('location_code'),
        plant_code=body.get('plant_code'),
        unit_of_measure_code=body.get('unit_of_measure_code'),
        price_from_date=body.get('price_from_date') or None,
        price_to_date=body.get('price_to_date') or None,
        line_amount_excl_tax=body.get('line_amount_excl_tax') or None,
        quantity=body.get('quantity') or None,
        outstanding_quantity=body.get('outstanding_quantity') or None,
        rm_base=body.get('rm_base') or None,
        boc_base=body.get('boc_base') or None,
        remarks=body.get('remarks'),
    )
    if updated == 0:
        return JsonResponse({'error': 'Line item not found'}, status=404)
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
@require_active_customer
def delete_bso_line(request):
    """Delete a BSOSalesLine."""
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
