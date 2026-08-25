import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from config.decorators import require_active_customer
from django.db import connection
from .models import BocItemCard, BocCreation, BocCreationEcn, BocStatus, SupplierList
from apps.BOM.models import BOMPartDetailsMaster

@require_active_customer
def BOC_form(request):
    customer_id = request.session.get('active_customer_id', '')
    customer_name = request.session.get('active_customer_name', '')
    
    item_nos = []
    if customer_id:
        item_nos = list(BocItemCard.objects.filter(customerid=customer_id).values_list('no', flat=True).distinct())
            
    from apps.BOP.models import BOPToolingMaster
    tooling_options = list(BOPToolingMaster.objects.values('id', 'tool_description', 'unit_cost'))
    
    suppliers = list(SupplierList.objects.values('no', 'name').order_by('name'))

    return render(request, "BOC/BOC_form.html", {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "item_nos": item_nos,
        "tooling_options": tooling_options,
        "suppliers": suppliers,
    })

@require_active_customer
def get_item_details(request):
    item_no = request.GET.get('item_no')
    customer_id = request.session.get('active_customer_id')
    
    if not item_no or not customer_id:
        return JsonResponse({'error': 'Missing item_no or customer_id'}, status=400)
        
    item_no_clean  = item_no.strip()
    item_no_padded = item_no_clean.zfill(8) if item_no_clean.isdigit() else item_no_clean
    item_no_lstrip = item_no_clean.lstrip('0') or item_no_clean
    
    variants = [item_no_clean, item_no_padded, item_no_lstrip]
    
    data = {
        'drg_revno': '',
        'drg_revdate': '',
        'customer_partsetno': '',
        'part_name': '',
        'project': '',
        'project_sopdate': '',
        'rfq_no': '',
        'annual_volume': '',
        'customer_drgno': ''
    }
    
    boc = None
    for variant in variants:
        boc = BocCreation.objects.filter(itemcreation_id=variant, customer_id=customer_id).first()
        if boc:
            break
            
    if boc:
        data['drg_revno'] = boc.drg_revno or ''
        data['drg_revdate'] = str(boc.drg_revdate) if boc.drg_revdate else ''
        data['customer_partsetno'] = boc.customer_partsetno or ''
        data['part_name'] = boc.part_name or ''
        data['project'] = boc.project or ''
        data['project_sopdate'] = str(boc.project_sopdate) if boc.project_sopdate else ''
        data['rfq_no'] = boc.rfq_no or ''
        data['annual_volume'] = str(boc.annual_volume) if boc.annual_volume else ''
        data['customer_drgno'] = boc.customer_drgno or ''

    return JsonResponse(data)

@require_active_customer
def get_boc_nos(request):
    item_no = request.GET.get('item_no')
    customer_id = request.session.get('active_customer_id')

    if not item_no or not customer_id:
        return JsonResponse({'boc_nos': []}, status=400)

    item_no_clean  = item_no.strip()
    item_no_padded = item_no_clean.zfill(8) if item_no_clean.isdigit() else item_no_clean
    item_no_lstrip = item_no_clean.lstrip('0') or item_no_clean
    
    variants = [item_no_clean, item_no_padded, item_no_lstrip]

    boc_nos = []
    for variant in variants:
        boc_nos = list(
            BocCreation.objects
            .filter(itemcreation_id=variant, customer_id=customer_id)
            .values_list('boc_creation_id', flat=True)
            .distinct()
        )
        if boc_nos:
            break

    return JsonResponse({'boc_nos': boc_nos})


@require_active_customer
def get_boc_details(request):
    """Return table_id and ecn_id from tbl_boc_creation_ecn for a given boc_creation_id."""
    boc_no = request.GET.get('boc_no', '').strip()

    if not boc_no:
        return JsonResponse({'error': 'Missing boc_no'}, status=400)

    # Use raw SQL to get the latest ECN for this BOC
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_id, ecn_id 
            FROM tbl_boc_creation_ecn 
            WHERE boc_creation_id = %s 
            ORDER BY CAST(NULLIF(REGEXP_REPLACE(ecn_id, '[^0-9]', '', 'g'), '') AS INTEGER) DESC NULLS LAST
            LIMIT 1
            """,
            [boc_no]
        )
        row = cursor.fetchone()

    table_id = row[0] or '' if row else ''
    ecn_id   = row[1] or '' if row else ''

    print(f"[get_boc_details] boc_no={boc_no!r} → table_id={table_id!r}, ecn_id={ecn_id!r}")

    return JsonResponse({'table_id': table_id, 'ecn_id': ecn_id})


@csrf_exempt
@require_POST
@require_active_customer
def create_boc(request):
    """Create a new BOC record in tbl_boc_creation."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id   = request.session.get('active_customer_id', '')
    customer_name = request.session.get('active_customer_name', '')
    boc_no        = body.get('boc_no', '').strip()
    item_no       = body.get('item_no', '').strip()

    if not boc_no:
        return JsonResponse({'error': 'BOC NO is required'}, status=400)
    if not item_no:
        return JsonResponse({'error': 'Item Number is required'}, status=400)

    # Check if BOC NO already exists
    if BocCreation.objects.filter(boc_creation_id=boc_no).exists():
        return JsonResponse({'error': f'BOC NO "{boc_no}" already exists'}, status=409)

    # Check if this item already has a BOC (one item → one BOC rule)
    item_no_clean  = item_no.strip()
    item_no_padded = item_no_clean.zfill(8) if item_no_clean.isdigit() else item_no_clean
    item_no_lstrip = item_no_clean.lstrip('0') or item_no_clean
    variants = [item_no_clean, item_no_padded, item_no_lstrip]

    existing = None
    for v in variants:
        existing = BocCreation.objects.filter(itemcreation_id=v, customer_id=customer_id).first()
        if existing:
            break
    if existing:
        return JsonResponse({'error': f'Item "{item_no}" already has BOC "{existing.boc_creation_id}"'}, status=409)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tbl_boc_creation
                (boc_creation_id, customer_id, customer_name, itemcreation_id,
                 customer_drgno, drg_revno, drg_revdate, customer_partsetno,
                 part_name, project, project_sopdate, rfq_no, annual_volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                boc_no,
                customer_id,
                customer_name,
                item_no,
                body.get('customer_drgno', '') or None,
                body.get('drg_revno', '') or None,
                body.get('drg_revdate', '') or None,
                body.get('customer_partsetno', '') or None,
                body.get('part_name', '') or None,
                body.get('project', '') or None,
                body.get('project_sopdate', '') or None,
                body.get('rfq_no', '') or None,
                body.get('annual_volume', '') or None,
            ]
        )

    print(f"[create_boc] Created BOC {boc_no!r} for item {item_no!r}, customer {customer_id!r}")
    return JsonResponse({'success': True, 'boc_no': boc_no})


@csrf_exempt
@require_POST
@require_active_customer
def save_boc(request):
    """Update an existing BOC record in tbl_boc_creation."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '')
    boc_no      = body.get('boc_no', '').strip()

    if not boc_no:
        return JsonResponse({'error': 'BOC NO is required'}, status=400)

    updated = BocCreation.objects.filter(
        boc_creation_id=boc_no, customer_id=customer_id
    ).update(
        customer_drgno    = body.get('customer_drgno') or None,
        drg_revno         = body.get('drg_revno') or None,
        drg_revdate       = body.get('drg_revdate') or None,
        customer_partsetno= body.get('customer_partsetno') or None,
        part_name         = body.get('part_name') or None,
        project           = body.get('project') or None,
        project_sopdate   = body.get('project_sopdate') or None,
        rfq_no            = body.get('rfq_no') or None,
        annual_volume     = body.get('annual_volume') or None,
    )

    if updated == 0:
        return JsonResponse({'error': 'BOC not found or permission denied'}, status=404)

    print(f"[save_boc] Updated BOC {boc_no!r} for customer {customer_id!r}")
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
@require_active_customer
def delete_boc(request):
    """Delete a BOC record from tbl_boc_creation."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '')
    boc_no      = body.get('boc_no', '').strip()

    if not boc_no:
        return JsonResponse({'error': 'BOC NO is required'}, status=400)

    deleted, _ = BocCreation.objects.filter(
        boc_creation_id=boc_no, customer_id=customer_id
    ).delete()

    if deleted == 0:
        return JsonResponse({'error': 'BOC not found or permission denied'}, status=404)

    print(f"[delete_boc] Deleted BOC {boc_no!r} for customer {customer_id!r}")
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
@require_active_customer
def ecn_boc(request):
    """Increment ECN for a BOC record.
    1. Find max ecn_id in tbl_boc_creation_ecn for this boc_creation_id (0 if none).
    2. new_ecn = max + 1.
    3. Insert new row into tbl_boc_creation_ecn.
    4. Update tbl_boc_creation with the edited field values.
    5. Return new_ecn_id.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '')
    boc_no      = body.get('boc_no', '').strip()

    if not boc_no:
        return JsonResponse({'error': 'BOC NO is required'}, status=400)

    # Verify the BOC belongs to this customer
    boc = BocCreation.objects.filter(boc_creation_id=boc_no, customer_id=customer_id).first()
    if not boc:
        return JsonResponse({'error': 'BOC not found or permission denied'}, status=404)

    # --- 1. Get current max ecn_id (stored as text, cast safely) ---
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT MAX(CAST(NULLIF(REGEXP_REPLACE(ecn_id, '[^0-9]', '', 'g'), '') AS INTEGER))
            FROM tbl_boc_creation_ecn
            WHERE boc_creation_id = %s
            """,
            [boc_no]
        )
        row = cursor.fetchone()

    current_ecn = row[0] if (row and row[0] is not None) else 0
    new_ecn     = current_ecn + 1
    table_id    = boc.table_id or ''

    # --- 2. Insert ECN snapshot row ---
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO tbl_boc_creation_ecn (boc_creation_id, table_id, ecn_id) VALUES (%s, %s, %s)",
            [boc_no, table_id, str(new_ecn)]
        )

    # --- 3. Update the main BOC record with the edited values ---
    BocCreation.objects.filter(
        boc_creation_id=boc_no, customer_id=customer_id
    ).update(
        customer_drgno     = body.get('customer_drgno') or None,
        drg_revno          = body.get('drg_revno') or None,
        drg_revdate        = body.get('drg_revdate') or None,
        customer_partsetno = body.get('customer_partsetno') or None,
        part_name          = body.get('part_name') or None,
        project            = body.get('project') or None,
        project_sopdate    = body.get('project_sopdate') or None,
        rfq_no             = body.get('rfq_no') or None,
        annual_volume      = body.get('annual_volume') or None,
    )

    print(f"[ecn_boc] BOC {boc_no!r} ECN incremented: {current_ecn} → {new_ecn}")
    return JsonResponse({'success': True, 'new_ecn_id': str(new_ecn), 'prev_ecn_id': str(current_ecn)})

@csrf_exempt
@require_POST
@require_active_customer
def send_approval_boc(request):
    """Send BOC for approval."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '')
    boc_no      = body.get('boc_no', '').strip()

    if not boc_no:
        return JsonResponse({'error': 'BOC NO is required'}, status=400)

    boc = BocCreation.objects.filter(boc_creation_id=boc_no, customer_id=customer_id).first()
    if not boc:
        return JsonResponse({'error': 'BOC not found or permission denied'}, status=404)

    # Attempt to update action_status or status via raw SQL to avoid model field missing errors
    # if the DB schema hasn't been updated yet (since user said 'dont change my DB')
    with connection.cursor() as cursor:
        try:
            cursor.execute("UPDATE tbl_boc_creation SET action_status = 'Sent for approval' WHERE boc_creation_id = %s AND customer_id = %s", [boc_no, customer_id])
        except Exception as e:
            # If action_status column doesn't exist, try status
            try:
                cursor.execute("UPDATE tbl_boc_creation SET status = 'Sent for approval' WHERE boc_creation_id = %s AND customer_id = %s", [boc_no, customer_id])
            except Exception as e2:
                print(f"[send_approval_boc] Could not update status field: {e2}")

    print(f"[send_approval_boc] BOC {boc_no!r} sent for approval by customer {customer_id!r}")
    return JsonResponse({'success': True})

@csrf_exempt
@require_POST
@require_active_customer
def add_boc_tooling(request):
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '')
    customer_name = request.session.get('active_customer_name', '')
    
    boc_no = body.get('boc_no')
    tool_desc = body.get('tool_description_boc')
    if not boc_no or not tool_desc:
        return JsonResponse({'error': 'BOC NO and Tool Description are required'}, status=400)
    
    try:
        from .models import BocTolling, BocTollingEcn
        
        BocTolling.objects.create(
            customer_id=customer_id,
            itemcreation_id=body.get('item_no'),
            boc_creationid=boc_no,
            tool_description_boc=tool_desc,
            unit_cost=body.get('unit_cost') or 0,
            qty_required=body.get('qty_required') or 0,
            total_estimate=body.get('total_estimate') or 0,
            table_id=body.get('table_id'),
            remark=body.get('remark')
        )
        
        BocTollingEcn.objects.create(
            customer_id=customer_id,
            itemcreation_id=body.get('item_no'),
            boc_creation_id=boc_no,

            tool_descriptionforboc=tool_desc,
            unit_cost=body.get('unit_cost') or 0,
            qty_required=body.get('qty_required') or 0,
            total_estimate=body.get('total_estimate') or 0,
            table_id=body.get('table_id'),
            ecn_id=body.get('ecn_id')
        )
    except Exception as e:
        print("Error in add_boc_tooling:", e)
        return JsonResponse({'error': str(e)}, status=500)
        
    return JsonResponse({'success': True})

@csrf_exempt
@require_POST
@require_active_customer
def save_boc_tooling(request):
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '')
    boc_no = body.get('boc_no')
    tool_desc = body.get('tool_description_boc')
    if not boc_no or not tool_desc:
        return JsonResponse({'error': 'BOC NO and Tool Description are required'}, status=400)
    
    try:
        from .models import BocTolling, BocTollingEcn
        
        BocTolling.objects.filter(
            boc_creationid=boc_no, 
            tool_description_boc=tool_desc, 
            customer_id=customer_id
        ).update(
            unit_cost=body.get('unit_cost') or 0,
            qty_required=body.get('qty_required') or 0,
            total_estimate=body.get('total_estimate') or 0,
            remark=body.get('remark'),
            table_id=body.get('table_id')
        )
        
        BocTollingEcn.objects.filter(
            boc_creation_id=boc_no, 
            tool_descriptionforboc=tool_desc, 
            customer_id=customer_id
        ).update(
            unit_cost=body.get('unit_cost') or 0,
            qty_required=body.get('qty_required') or 0,
            total_estimate=body.get('total_estimate') or 0,
            table_id=body.get('table_id'),
            ecn_id=body.get('ecn_id')
        )
    except Exception as e:
        print("Error in save_boc_tooling:", e)
        return JsonResponse({'error': str(e)}, status=500)
        
    return JsonResponse({'success': True})

@csrf_exempt
@require_POST
@require_active_customer
def delete_boc_tooling(request):
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    customer_id = request.session.get('active_customer_id', '')
    boc_no = body.get('boc_no')
    tool_desc = body.get('tool_description_boc')
    if not boc_no or not tool_desc:
        return JsonResponse({'error': 'BOC NO and Tool Description are required'}, status=400)
    
    try:
        from .models import BocTolling, BocTollingEcn
        
        BocTolling.objects.filter(
            boc_creationid=boc_no, 
            tool_description_boc=tool_desc, 
            customer_id=customer_id
        ).delete()
        
        BocTollingEcn.objects.filter(
            boc_creation_id=boc_no, 
            tool_descriptionforboc=tool_desc, 
            customer_id=customer_id
        ).delete()
    except Exception as e:
        print("Error in delete_boc_tooling:", e)
        return JsonResponse({'error': str(e)}, status=500)
        
    return JsonResponse({'success': True})

@require_active_customer
def get_prod_tooling(request):
    boc_no = request.GET.get('boc_no')
    if not boc_no:
        return JsonResponse({'records': []})
    from .models import BocTolling
    records = list(BocTolling.objects.filter(boc_creationid=boc_no).values(
        'id', 'tool_description_boc', 'unit_cost', 'qty_required', 'total_estimate', 'remark'
    ))
    return JsonResponse({'records': records})

@require_active_customer
def get_boc_status(request):
    boc_no = request.GET.get('boc_no')
    if not boc_no:
        return JsonResponse({'records': []})
    
    records = list(BocStatus.objects.filter(boc_creationid=boc_no).values(
        'id', 'boc', 'supplier', 'status', 'date_sent', 'comments', 
        'basic_price_quoted_by_supplier_in_rs', 'final_price_submission_date'
    ))
    return JsonResponse({'records': records})

@csrf_exempt
@require_POST
@require_active_customer
def save_boc_status(request):
    try:
        body = json.loads(request.body)
        customer_id = request.session.get('active_customer_id', '')
        customer_name = request.session.get('active_customer_name', '')
        
        # Determine if it's an update or create based on ID
        record_id = body.get('id')
        if record_id:
            obj = BocStatus.objects.get(id=record_id)
        else:
            obj = BocStatus()
            
        obj.customer_id = customer_id
        obj.customer_name = customer_name
        obj.itemcreation_id = body.get('item_no')
        obj.boc_creationid = body.get('boc_no')
        obj.boc = body.get('boc')
        obj.supplier = body.get('supplier')
        obj.status = body.get('status')
        obj.date_sent = body.get('date_sent') or None
        obj.comments = body.get('comments')
        
        price = body.get('basic_price')
        if price:
            obj.basic_price_quoted_by_supplier_in_rs = price
            
        obj.final_price_submission_date = body.get('final_price_date') or None
        obj.table_id = body.get('table_id')
        obj.save()
        return JsonResponse({'success': True})
    except Exception as e:
        print("Error saving boc status:", e)
        return JsonResponse({'error': str(e)}, status=500)

@require_active_customer
def get_bom_cost(request):
    boc_no = request.GET.get('boc_no')
    customer_id = request.session.get('active_customer_id', '')
    
    if not boc_no:
        return JsonResponse({'records': []})
        
    records = list(BOMPartDetailsMaster.objects.filter(customer=customer_id).values(
        'part_no', 'part_description', 'classification', 'cost_price', 'categorisation', 'base_unit_of_measure', 'part_status'
    ))
    return JsonResponse({'records': records})

@csrf_exempt
@require_POST
@require_active_customer
def save_bom_cost(request):
    try:
        body = json.loads(request.body)
        part_no = body.get('part_no')
        
        if not part_no:
            return JsonResponse({'error': 'Part No is required'}, status=400)
            
        obj, created = BOMPartDetailsMaster.objects.get_or_create(
            part_no=part_no,
            defaults={'customer': request.session.get('active_customer_id', '')}
        )
        
        obj.part_description = body.get('part_description', obj.part_description)
        obj.classification = body.get('classification', obj.classification)
        obj.categorisation = body.get('categorisation', obj.categorisation)
        obj.base_unit_of_measure = body.get('base_unit_of_measure', obj.base_unit_of_measure)
        obj.part_status = body.get('part_status', obj.part_status)
        
        cost_price = body.get('cost_price')
        if cost_price is not None and cost_price != "":
            obj.cost_price = cost_price
            
        obj.save()
        return JsonResponse({'success': True})
    except Exception as e:
        print("Error saving bom cost:", e)
        return JsonResponse({'error': str(e)}, status=500)

@require_active_customer
def get_bom_settle(request):
    boc_no = request.GET.get('boc_no')
    customer_id = request.session.get('active_customer_id', '')
    
    if not boc_no:
        return JsonResponse({'records': []})
        
    records = list(BOMPartDetailsMaster.objects.filter(customer=customer_id).values(
        'part_no', 'part_description', 'classification', 'settle_price', 'categorisation', 'base_unit_of_measure', 'part_status'
    ))
    return JsonResponse({'records': records})

@csrf_exempt
@require_POST
@require_active_customer
def save_bom_settle(request):
    try:
        body = json.loads(request.body)
        part_no = body.get('part_no')
        
        if not part_no:
            return JsonResponse({'error': 'Part No is required'}, status=400)
            
        obj, created = BOMPartDetailsMaster.objects.get_or_create(
            part_no=part_no,
            defaults={'customer': request.session.get('active_customer_id', '')}
        )
        
        obj.part_description = body.get('part_description', obj.part_description)
        obj.classification = body.get('classification', obj.classification)
        obj.categorisation = body.get('categorisation', obj.categorisation)
        obj.base_unit_of_measure = body.get('base_unit_of_measure', obj.base_unit_of_measure)
        obj.part_status = body.get('part_status', obj.part_status)
        
        settle_price = body.get('settle_price')
        if settle_price is not None and settle_price != "":
            obj.settle_price = settle_price
            
        obj.save()
        return JsonResponse({'success': True})
    except Exception as e:
        print("Error saving bom settle:", e)
        return JsonResponse({'error': str(e)}, status=500)
