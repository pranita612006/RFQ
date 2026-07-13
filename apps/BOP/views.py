from django.utils import datastructures
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction, connection
from django.utils import timezone
from urllib.parse import urlencode
from config.decorators import require_active_customer
from apps.item_creation.models import ItemCard, Cell, CellType
from apps.BOM.models import BOMHeader
from .models import BOPToolingMaster
from .models import (
    BOPCreation, 
    BOPCreationECN, 
    BOPCellAlignment,
    BOPCellAlignmentType,
    OpportunityMaster,
    CustomerInfo,
    BOPTypeMaster,
    BOPTab,
    BOPTolling,
)
import traceback
import random
import json


def _item_creation_id_variants(item_creation_id):
    """Normalize Item Creation ID formats used across Access-linked tables."""
    raw = str(item_creation_id or "").strip()
    if not raw:
        return []
    variants = [raw]
    if raw.isdigit():
        variants.append(raw.zfill(8))
        variants.append(str(int(raw)))
    return list(dict.fromkeys(v for v in variants if v))


def _lookup_bom_from_rfq_details(item_variants, customer_id, bop_creation_id=""):
    """
    Access-equivalent lookups against tbl_rfq_details (RFQ master linkage).
    Preserves query order: by BOP id first, then by item + customer.
    """
    with connection.cursor() as cursor:
        if bop_creation_id:
            cursor.execute(
                """
                SELECT bomcreation_id, itemcreation_id
                FROM tbl_rfq_details
                WHERE bopcreation_id = %s
                  AND customer_id = %s
                  AND bomcreation_id IS NOT NULL
                  AND bomcreation_id <> ''
                LIMIT 1
                """,
                [bop_creation_id, customer_id],
            )
            row = cursor.fetchone()
            if row and row[0]:
                return row[0], row[1] or ""

        if item_variants:
            cursor.execute(
                """
                SELECT bomcreation_id, itemcreation_id
                FROM tbl_rfq_details
                WHERE customer_id = %s
                  AND itemcreation_id = ANY(%s)
                  AND bomcreation_id IS NOT NULL
                  AND bomcreation_id <> ''
                LIMIT 1
                """,
                [customer_id, item_variants],
            )
            row = cursor.fetchone()
            if row and row[0]:
                return row[0], row[1] or ""
    return "", ""


def _lookup_bom_from_bomcreation(item_variants, customer_id):
    """Fallback lookup in tbl_bomcreation when RFQ master row is absent."""
    if not item_variants:
        return "", ""
    bom = BOMHeader.objects.filter(
        item_creation_id__in=item_variants,
        customer_id=customer_id,
    ).first()
    if not bom:
        bom = BOMHeader.objects.filter(item_creation_id__in=item_variants).first()
    if bom:
        return bom.bom_creation_id or "", bom.item_creation_id or ""
    return "", ""


@require_active_customer
def resolve_bom_details(request):
    """
    Resolves the linked BOM record for the current BOP context and returns
    navigation parameters for frmBOM (Django BOM Creation page).
    """
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    bop_creation_id = request.GET.get("bop_creation_id", "").strip()
    customer_id = request.active_customer.get("id", "") if hasattr(request, "active_customer") else ""

    if not item_creation_id:
        return JsonResponse(
            {"error": "Action Blocked: Please load a valid Item Creation ID first."},
            status=400,
        )

    item_variants = _item_creation_id_variants(item_creation_id)
    bom_creation_id, resolved_item_id = _lookup_bom_from_rfq_details(
        item_variants, customer_id, bop_creation_id
    )

    if not bom_creation_id:
        bom_creation_id, resolved_item_id = _lookup_bom_from_bomcreation(
            item_variants, customer_id
        )

    if not bom_creation_id:
        return JsonResponse(
            {"error": "Action Blocked: BOM Record not found for this Item Creation ID."},
            status=404,
        )

    customer_name = request.active_customer.get("name", "") if hasattr(request, "active_customer") else ""
    query = urlencode({
        "item_creation_id": resolved_item_id or item_creation_id,
        "bom_creation_id": bom_creation_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "from_bop": "1",
    })

    return JsonResponse({
        "status": "success",
        "bom_creation_id": bom_creation_id,
        "item_creation_id": resolved_item_id or item_creation_id,
        "redirect_url": f"/BOM/?{query}",
    })


@require_active_customer
def get_bop_autofill_data(request):
    try:
        item_creation_id = request.GET.get("item_creation_id", "").strip()
        if not item_creation_id:
            return JsonResponse({"error": "Missing item_creation_id"}, status=400)

        # Normalize ID
        item_variants = [str(item_creation_id)]
        if item_creation_id.isdigit():
            item_variants.append(str(item_creation_id.zfill(8)))

        # 1. Fetch from ItemCard
        cell = ""
        product_category_code = ""
        item_card = ItemCard.objects.filter(no__in=item_variants).first()
        if item_card:
            if item_card.cell:
                cell = getattr(item_card.cell, 'code', getattr(item_card.cell, 'cell_name', str(item_card.cell)))
            if item_card.cell_type:
                product_category_code = getattr(item_card.cell_type, 'code', str(item_card.cell_type))

        # 2. Fetch metadata from OpportunityMaster
        sop_date = customer_name = drawing_no = drawing_revision_no = ""
        part_set_no = part_name = project = remark = align_business = ""
        vol1 = vol2 = vol3 = vol4 = vol5 = ""

        opp = OpportunityMaster.objects.filter(item_no__in=item_variants).first()
        if opp:
            customer_name = opp.customer_name or ""
            part_set_no = opp.part_no or ""
            drawing_no = opp.drawing_no or ""
            drawing_revision_no = opp.drawing_revision_no or ""
            part_name = opp.part_name or ""
            project = opp.project_name or ""
            remark = opp.status or ""
            sop_date = opp.sop_date or ""
            align_business = opp.business or ""
            vol1, vol2, vol3, vol4, vol5 = (
                opp.annual_volume_1 or "",
                opp.annual_volume_2 or "",
                opp.annual_volume_3 or "",
                opp.annual_volume_4 or "",
                opp.annual_volume_5 or "",
            )

        # 3. Fetch Cell Alignment Tab Data
        align_product_category = ""
        align_process = ""
        align_mfg_location = ""
        align_cell = ""

        cell_align_obj = BOPCellAlignment.objects.filter(itemcreation_id__in=item_variants).first()
        if cell_align_obj:
            align_product_category = cell_align_obj.product_category or ""

        # FIX: define process_name safely
        process_name = align_product_category or ""
        if process_name:
            cell_type_obj = BOPCellAlignmentType.objects.filter(process=process_name).first()
            if cell_type_obj:
                align_process = cell_type_obj.process or ""
                align_mfg_location = cell_type_obj.manufacturing_location or ""
                align_cell = cell_type_obj.cell or ""

        if not align_product_category:
            align_product_category = product_category_code

        # 4. Resolve Customer Info
        matched_customer_id = ""
        customer_code = ""
        if hasattr(request, "active_customer"):
            matched_customer_id = request.active_customer.get("id", "")
        if not matched_customer_id and item_card and hasattr(item_card, "customer_id"):
            matched_customer_id = item_card.customer_id
        if matched_customer_id:
            cust_info = CustomerInfo.objects.filter(cust_id=matched_customer_id).first()
            if cust_info:
                customer_code = cust_info.cust_code or ""
                if not customer_name:
                    customer_name = cust_info.cust_name or ""

        # 5. Check existing BOP record
        bop_creation_id = last_modified_date = action_status = table_id = ""
        last_ecn_no = 0
        bop_obj = BOPCreation.objects.filter(itemcreation_id__in=item_variants).first()
        if bop_obj:
            bop_creation_id = bop_obj.bopcreation_id or ""
            action_status = bop_obj.action_status or ""
            table_id = bop_obj.id or ""
            remark = remark or bop_obj.remark or ""
            drawing_no = bop_obj.drawing_no or drawing_no
            drawing_revision_no = bop_obj.drawing_revision_no or drawing_revision_no
            part_set_no = bop_obj.part_set_no or part_set_no
            part_name = bop_obj.part_name or part_name
            project = bop_obj.project or project
            if bop_obj.last_modified_date:
                try:
                    last_modified_date = bop_obj.last_modified_date.strftime("%Y-%m-%d")
                except Exception:
                    last_modified_date = str(bop_obj.last_modified_date)
            if bop_creation_id:
                last_ecn_no = BOPCreationECN.objects.filter(bopcreation_id=bop_creation_id).count()

        return JsonResponse({
            "cell": cell,
            "product_category": product_category_code,
            "customer_name": customer_name,
            "customer_id": matched_customer_id,
            "drawing_no": drawing_no,
            "drawing_revision_no": drawing_revision_no,
            "part_set_no": part_set_no,
            "part_name": part_name,
            "project": project,
            "remark": remark,
            "customer_code": customer_code,
            "annual_volume_1": vol1,
            "annual_volume_2": vol2,
            "annual_volume_3": vol3,
            "annual_volume_4": vol4,
            "annual_volume_5": vol5,
            "bop_creation_id": bop_creation_id,
            "last_modified_date": last_modified_date,
            "action_status": action_status,
            "table_id": table_id,
            "last_ecn_no": last_ecn_no,
            "cell_align_product_category": align_product_category,
            "cell_align_business": align_business,
            "process": align_process,
            "manufacturing_location": align_mfg_location,
            "cell_align_cell": align_cell,
            "sop_date": sop_date
        })
    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


def get_location_and_cell_by_process(request):
    process_name = request.GET.get("process", "").strip()
    if not process_name:
        return JsonResponse({"error": "No process provided"}, status=400)

    records = BOPCellAlignmentType.objects.filter(process=process_name)
    if records.exists():
        data = [
            {
                "manufacturing_location": r.manufacturing_location or "",
                "cell": r.cell or "",
            }
            for r in records
        ]
        return JsonResponse({"results": data})

    return JsonResponse({"results": []})

@require_active_customer
def save_bop_form(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
        
    try:
        item_id = request.POST.get("item_creation_id", "").strip()
        if not item_id:
            return JsonResponse({"error": "Item Creation ID is required"}, status=400)
            
        table_id = request.POST.get("table_id", "").strip()
        selected_customer_id = request.active_customer.get('id') if hasattr(request, "active_customer") else ""
        
        # Safe integer cast for database compatibility
        item_creation_int = int(item_id)
        
        with transaction.atomic():
            # Attempt to locate existing record to establish if this is a CREATE or EDIT workflow
            bop_record = None
            if table_id:
                bop_record = BOPCreation.objects.filter(id=table_id).first()
            if not bop_record:
                bop_record = BOPCreation.objects.filter(itemcreation_id=item_creation_int).first()
                
            is_new = bop_record is None
            
            if is_new:
                # --- CREATE WORKFLOW (INSERT) ---
                # Check for duplicate item creation ID before inserting
                existing_dup = BOPCreation.objects.filter(itemcreation_id=item_creation_int).exists()
                if existing_dup:
                    return JsonResponse({"error": "BOP Record already exists for this Item Creation ID."}, status=400)

                bop_record = BOPCreation(itemcreation_id=item_creation_int)
                
                # 1. Generate BOP Creation ID (Example Format: BOP00001)
                latest_bop = BOPCreation.objects.all().order_by('-id').first()
                next_num = (latest_bop.id + 1) if latest_bop else 1
                bop_record.bopcreation_id = f"BOP{next_num:05d}"
                
                # 2. Generate Table ID (Defaulting to 1 for the first unique record grouping)
                bop_record.table_id = 1
                
                # 3. Set Initial Action Status
                bop_record.action_status = "Created"
            else:
                # --- EDIT WORKFLOW (UPDATE) ---
                # Access Business Rule validation: Block editing on Approved records
                if bop_record.action_status == "Approved":
                    return JsonResponse({"error": "Action Blocked: Approved BOP records cannot be edited."}, status=400)

                # Keep existing bopcreation_id and table_id intact.
                # Update status from form if explicitly provided, else flag as Updated
                form_status = request.POST.get("action_status", "").strip()
                bop_record.action_status = form_status if form_status else "Updated"

            # Fields populated/updated across both workflows
            bop_record.customer_id = selected_customer_id
            bop_record.customer_name = request.POST.get("customer_name", "")
            bop_record.product_category = request.POST.get("product_category", "")
            bop_record.drawing_no = request.POST.get("drawing_no", "")
            bop_record.drawing_revision_no = request.POST.get("drawing_revision_no", "")
            
            # Form submission strings to Date conversions safely
            rev_date_str = request.POST.get("revision_date", "").strip()
            if rev_date_str:
                try:
                    bop_record.revision_date = timezone.datetime.strptime(rev_date_str, "%Y-%m-%d").date()
                except ValueError:
                    bop_record.revision_date = timezone.now().date()
            else:
                bop_record.revision_date = timezone.now().date()

            bop_record.part_name = request.POST.get("part_name", "")
            bop_record.part_set_no = request.POST.get("part_set_no", "")
            bop_record.project = request.POST.get("project", "")
            bop_record.remark = request.POST.get("remark", "")
            
            # 4. Sets Last Modified Date matching DateField
            bop_record.last_modified_date = timezone.now().date()
            bop_record.entry_date = timezone.now().date()
            bop_record.is_download = False
            
            # 5. Save Record
            bop_record.save()
            
            # Historical ECN Logging tracking
            ecn_count = BOPCreationECN.objects.filter(bopcreation_id=bop_record.bopcreation_id).count()
            next_ecn_id = f"ECN-{ecn_count + 1:03d}"
            
            history_log = BOPCreationECN(
                bopcreation_id=bop_record.bopcreation_id,
                ecn_no=next_ecn_id,
                itemcreation_id=str(bop_record.itemcreation_id),
                customer_id=selected_customer_id,
                customer_name=bop_record.customer_name,
                drawing_no=bop_record.drawing_no,
                drawing_revision_no=bop_record.drawing_revision_no,
                revision_date=bop_record.revision_date,
                part_name=bop_record.part_name,
                product_category=bop_record.product_category,
                remark=bop_record.remark,
                annual_volume_1=request.POST.get("annual_volume_1", ""),
                annual_volume_2=request.POST.get("annual_volume_2", ""),
                annual_volume_3=request.POST.get("annual_volume_3", ""),
                annual_volume_4=request.POST.get("annual_volume_4", ""),
                annual_volume_5=request.POST.get("annual_volume_5", "")
            )
            history_log.save()
            
            # Return JSON payload mapping variables back to JavaScript
            return JsonResponse({
                "status": "success",
                "message": "BOP configuration saved successfully!" if not is_new else "BOP configuration created successfully!",
                "table_id": bop_record.id,        # Primary auto-increment tracking key
                "bop_table_id": bop_record.table_id,  # Business rule table sequence ID
                "bop_creation_id": bop_record.bopcreation_id,
                "last_ecn_no": next_ecn_id,
                "action_status": bop_record.action_status,
                "last_modified_date": bop_record.last_modified_date.strftime('%Y-%m-%d')
            })
            
    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


def get_bop_details(request):
    """
    Subform details tracker endpoint requested by the frontend script change-events loops.
    """
    bop_creation_id = request.GET.get("bop_creation_id", "").strip()
    if not bop_creation_id:
        return JsonResponse({"error": "Missing bop_creation_id"}, status=400)
        
    bop_obj = BOPCreation.objects.filter(bopcreation_id=bop_creation_id).first()
    if not bop_obj:
        return JsonResponse({"error": "Record not found"}, status=404)
        
    ecn_count = BOPCreationECN.objects.filter(bopcreation_id=bop_creation_id).count()
    last_modified_str = bop_obj.last_modified_date.strftime('%Y-%m-%d') if bop_obj.last_modified_date else ""
    rev_date_str = bop_obj.revision_date.strftime('%Y-%m-%d') if bop_obj.revision_date else ""
    
    return JsonResponse({
        "table_id": bop_obj.id,
        "bop_table_id": bop_obj.table_id or 1,
        "action_status": bop_obj.action_status or "",
        "last_ecn_no": f"ECN-{ecn_count:03d}" if ecn_count > 0 else "0",
        "last_modified_date": last_modified_str,
        "revision_date": rev_date_str
    })


@require_active_customer
def BOP_form(request):
    try:
        import traceback
        selected_customer_id = request.active_customer['id']
        items = []
        if selected_customer_id:
            items = list(ItemCard.objects.filter(customer_id=selected_customer_id).values_list("no", flat=True))
        
        cells = Cell.objects.all()
        cell_types = CellType.objects.all()
        
        # FIXED: Properly close out values() dictionary keys and add .distinct()
        processes = BOPCellAlignmentType.objects.values('process', 'manufacturing_location', 'cell').distinct()

        context = {
            'items': items,
            'cells': cells,
            'cell_types': cell_types,
            'processes': processes,  # Now contains dictionaries with all 3 columns!
            # PERF: processdesc removed from context — popup table is now loaded via AJAX
            # using the /BOP/get_bop_tab_descriptions/ endpoint
        }
        return render(request, 'BOP/BOP_form.html', context)
    except Exception as e:
        import traceback
        with open("d:/N-RFQ/debug.txt", "w") as f:
            f.write(traceback.format_exc())
        raise e

def get_bop_tab_descriptions(request):
    try:
        import traceback
        process_type = request.GET.get("type", "").strip()
        queryset = BOPTypeMaster.objects.only(
            'no', 'name', 'categorisation', 'mhr_year', 'mhr_lower', 'mhr_higher', 'costperquantity'
        )
        if process_type:
            queryset = queryset.filter(categorisation__icontains=process_type)
            
        descriptions = list(queryset.values(
            'no', 'name', 'categorisation', 'mhr_year', 'mhr_lower', 'mhr_higher', 'costperquantity'
        ))
        # Convert Decimal fields to strings for JSON serialization
        for item in descriptions:
            for key in ('mhr_year', 'mhr_lower', 'mhr_higher', 'costperquantity'):
                if item.get(key) is not None:
                    item[key] = str(item[key])
                else:
                    item[key] = ''
            item['no'] = item.get('no') or ''
            item['name'] = item.get('name') or ''
            item['categorisation'] = item.get('categorisation') or ''
        return JsonResponse({"descriptions": descriptions}, safe=False)
    except Exception as e:
        with open("d:/N-RFQ/debug.txt", "w") as f:
            f.write(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


def get_bop_tab_autofill_data(request):
    """
    Fetches 7 table columns from tbl_bop_types based on selected cost center number
    and returns them matching the script's exact field mapping keys.
    """
    try:
        cost_center_no = request.GET.get("cost_center_no", "").strip()
        selected_type = request.GET.get("type", "").strip()
        
        if not cost_center_no:
            return JsonResponse({"error": "Missing cost_center_no"}, status=400)
            
        # Lookup row profile inside master table tbl_bop_types
        bop_tab_record = BOPTypeMaster.objects.filter(no=cost_center_no).first()
        
        if not bop_tab_record:
            return JsonResponse({"error": "Data profile not located"}, status=404)
            
        # Return object mapping matching the exact keys checked in your frontend script
        return JsonResponse({
            # The 7 explicit columns requested:
            "costcenter_no": bop_tab_record.no or "",
            "description": bop_tab_record.name or "",
            "categorisation": bop_tab_record.categorisation or "",
            "mhr_year": str(bop_tab_record.mhr_year or ""),
            "mhr_lower": str(bop_tab_record.mhr_lower or ""),
            "mhr_higher": str(bop_tab_record.mhr_higher or ""),
            "costperqnty": str(bop_tab_record.costperquantity or ""),
            
            # Form field bindings called by your JavaScript formFields configuration:
            "operation_no": bop_tab_record.no or "",
            "remark": bop_tab_record.name or "",
            "type": bop_tab_record.categorisation or selected_type,
            
            # Default fallbacks for remaining calculations:
            "run_time_sec": "0",
            "run_time_min": "0",
            "boq": "1",
            "total_run_time": "0",
            "cycle_time": "0"
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_bop_tooling_options(request):
    """
    Returns data from tbl_bop_tooling for the autocomplete popup
    """
    try:
        tooling_records = BOPToolingMaster.objects.all().values('tool_description', 'unit_cost')
        data_list = []
        for record in tooling_records:
            data_list.append({
                "tool_description": record["tool_description"] or "",
                "unit_cost": str(record["unit_cost"] or "0.00")
            })
        return JsonResponse({"results": data_list}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_active_customer
def delete_bop_form(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bop_id = data.get("bop_creation_id", "").strip()
        if not bop_id:
            return JsonResponse({"error": "BOP Creation ID is required"}, status=400)
            
        with transaction.atomic():
            # Delete from BOPCreation
            BOPCreation.objects.filter(bopcreation_id=bop_id).delete()
            # Delete from BOPCreationECN
            BOPCreationECN.objects.filter(bopcreation_id=bop_id).delete()
            
        return JsonResponse({"status": "success", "message": f"BOP Record {bop_id} has been successfully deleted."})
    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


def _annual_volumes_for_item(item_creation_id):
    """Fetch annual volume fields from OpportunityMaster for ECN logging."""
    item_variants = _item_creation_id_variants(item_creation_id)
    opp = OpportunityMaster.objects.filter(item_no__in=item_variants).first()
    if not opp:
        return ("", "", "", "", "")
    return (
        opp.annual_volume_1 or "",
        opp.annual_volume_2 or "",
        opp.annual_volume_3 or "",
        opp.annual_volume_4 or "",
        opp.annual_volume_5 or "",
    )


@require_active_customer
def send_bop_approval(request):
    """
    Access Send Approval equivalent:
    validate record -> block invalid statuses -> update header -> write ECN history.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)

    try:
        data = json.loads(request.body)
        item_id = data.get("item_creation_id", "").strip()
        bop_id = data.get("bop_creation_id", "").strip()
        table_id = data.get("table_id", "").strip()

        if not item_id:
            return JsonResponse(
                {"error": "Action Blocked: Please load a valid Item Creation ID first."},
                status=400,
            )
        if not bop_id:
            return JsonResponse(
                {"error": "Action Blocked: No active BOP Record loaded to send for approval."},
                status=400,
            )

        with transaction.atomic():
            bop_record = BOPCreation.objects.filter(bopcreation_id=bop_id).first()
            if not bop_record and table_id:
                bop_record = BOPCreation.objects.filter(id=table_id).first()
            if not bop_record:
                return JsonResponse(
                    {"error": "Action Blocked: BOP Record not found."},
                    status=404,
                )

            current_status = (bop_record.action_status or "").strip()
            if current_status == "Approved":
                return JsonResponse(
                    {"error": "Action Blocked: Approved BOP records cannot be sent for approval."},
                    status=400,
                )
            if current_status == "Send for Approval":
                return JsonResponse(
                    {"error": "Action Blocked: BOP Record is already sent for approval."},
                    status=400,
                )

            bop_record.action_status = "Send for Approval"
            bop_record.last_modified_date = timezone.now().date()
            bop_record.save()

            ecn_count = BOPCreationECN.objects.filter(bopcreation_id=bop_record.bopcreation_id).count()
            next_ecn_id = f"ECN-{ecn_count + 1:03d}"
            vol1, vol2, vol3, vol4, vol5 = _annual_volumes_for_item(bop_record.itemcreation_id)

            history_log = BOPCreationECN(
                bopcreation_id=bop_record.bopcreation_id,
                ecn_no=next_ecn_id,
                itemcreation_id=str(bop_record.itemcreation_id),
                customer_id=bop_record.customer_id,
                customer_name=bop_record.customer_name,
                drawing_no=bop_record.drawing_no,
                drawing_revision_no=bop_record.drawing_revision_no,
                revision_date=bop_record.revision_date,
                part_name=bop_record.part_name,
                product_category=bop_record.product_category,
                remark=bop_record.remark,
                annual_volume_1=vol1,
                annual_volume_2=vol2,
                annual_volume_3=vol3,
                annual_volume_4=vol4,
                annual_volume_5=vol5,
            )
            history_log.save()

        return JsonResponse({
            "status": "success",
            "message": f"BOP Record {bop_record.bopcreation_id} has been sent for approval.",
            "bop_creation_id": bop_record.bopcreation_id,
            "action_status": bop_record.action_status,
            "last_modified_date": bop_record.last_modified_date.strftime("%Y-%m-%d"),
            "last_ecn_no": next_ecn_id,
        })
    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


# ============================================================
# BOP TAB — CRUD ENDPOINTS
# ============================================================

@require_active_customer
def save_bop_tab(request):
    """Save (Add/Update) a BOP Tab record (tbl_bop_tab)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bop_creation_id = data.get("bopcreation_id", "").strip()
        item_creation_id = data.get("itemcreation_id", "").strip()
        table_id = data.get("table_id", "").strip()
        record_id = data.get("id", "")  # present only for update
        customer_id = request.active_customer.get("id", "") if hasattr(request, "active_customer") else ""

        if not bop_creation_id:
            return JsonResponse({"error": "BOP Creation ID is required"}, status=400)

        with transaction.atomic():
            if record_id:
                obj = BOPTab.objects.filter(id=record_id).first()
                if not obj:
                    return JsonResponse({"error": "BOP Tab record not found"}, status=404)
            else:
                obj = BOPTab()

            obj.bopcreationid = bop_creation_id
            obj.itemcreation_id = item_creation_id
            obj.customer_id = customer_id
            obj.table_id = int(table_id) if table_id else None
            obj.type = data.get("type", "")
            obj.type_selected = data.get("type", "")
            obj.costcenter_no = data.get("costcenter_no", "")
            obj.description = data.get("description", "")
            obj.operation_no = data.get("operation_no", "")
            obj.categorisation = data.get("categorisation", "")
            obj.run_time_sec = data.get("run_time_sec") or None
            obj.run_time_min = data.get("run_time_min") or None
            obj.boq = data.get("boq") or None
            obj.total_run_time = data.get("total_run_time") or None
            obj.cycle_time = data.get("cycle_time") or None
            obj.mhr_year = data.get("mhr_year") or None
            obj.mhr_lower = data.get("mhr_lower") or None
            obj.mhr_higher = data.get("mhr_higher") or None
            obj.remark = data.get("remark", "")
            obj.costperqnty = data.get("costperqnty") or None
            obj.seq_no = data.get("seq_no") or None
            obj.last_modified_date = str(timezone.now().date())
            obj.save()

        return JsonResponse({"status": "success", "id": obj.id, "message": "BOP Tab record saved."})
    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


def load_bop_tab(request):
    """Load all BOP Tab rows for a given bopcreation_id + table_id."""
    bop_creation_id = request.GET.get("bopcreation_id", "").strip()
    table_id = request.GET.get("table_id", "").strip()
    if not bop_creation_id:
        return JsonResponse({"error": "bopcreation_id required"}, status=400)
    qs = BOPTab.objects.filter(bopcreationid=bop_creation_id)
    if table_id:
        qs = qs.filter(table_id=table_id)
    rows = []
    for obj in qs.order_by("seq_no", "id"):
        rows.append({
            "id": obj.id,
            "seq_no": obj.seq_no,
            "type": obj.type or "",
            "costcenter_no": obj.costcenter_no or "",
            "description": obj.description or "",
            "operation_no": obj.operation_no or "",
            "boq": str(obj.boq or ""),
            "run_time_sec": str(obj.run_time_sec or ""),
            "run_time_min": str(obj.run_time_min or ""),
            "total_run_time": str(obj.total_run_time or ""),
            "cycle_time": str(obj.cycle_time or ""),
            "mhr_lower": str(obj.mhr_lower or ""),
            "mhr_higher": str(obj.mhr_higher or ""),
            "remark": obj.remark or "",
        })
    return JsonResponse({"rows": rows})


@require_active_customer
def delete_bop_tab(request):
    """Delete a single BOP Tab record by id."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        record_id = data.get("id")
        if not record_id:
            return JsonResponse({"error": "id required"}, status=400)
        BOPTab.objects.filter(id=record_id).delete()
        return JsonResponse({"status": "success", "message": "BOP Tab record deleted."})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ============================================================
# BOP TOOLING — CRUD ENDPOINTS
# ============================================================

@require_active_customer
def save_bop_tolling(request):
    """Save (Add/Update) a BOP Tooling record (tbl_bop_tolling)."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bop_creation_id = data.get("bopcreation_id", "").strip()
        item_creation_id = data.get("itemcreation_id", "")
        table_id = data.get("table_id", "")
        record_id = data.get("id", "")
        customer_id = request.active_customer.get("id", "") if hasattr(request, "active_customer") else ""

        if not bop_creation_id:
            return JsonResponse({"error": "BOP Creation ID is required"}, status=400)

        with transaction.atomic():
            if record_id:
                obj = BOPTolling.objects.filter(id=record_id).first()
                if not obj:
                    return JsonResponse({"error": "Record not found"}, status=404)
            else:
                obj = BOPTolling()

            obj.bopcreationid = bop_creation_id
            obj.itemcreation_id = int(item_creation_id) if str(item_creation_id).isdigit() else None
            obj.customer_id = customer_id
            obj.table_id = int(table_id) if str(table_id).isdigit() else None
            obj.tool_description = data.get("tool_description", "")
            obj.unit_cost = data.get("unit_cost") or None
            obj.qty_required = data.get("qty_required") or None
            obj.total_estimate = data.get("total_estimate") or None
            obj.remarks = data.get("remarks", "")
            obj.entry_date = timezone.now().date()
            obj.save()

        return JsonResponse({"status": "success", "id": obj.id, "message": "BOP Tooling record saved."})
    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


def load_bop_tolling(request):
    """Load all BOP Tooling rows for a given bopcreation_id."""
    bop_creation_id = request.GET.get("bopcreation_id", "").strip()
    if not bop_creation_id:
        return JsonResponse({"error": "bopcreation_id required"}, status=400)
    qs = BOPTolling.objects.filter(bopcreationid=bop_creation_id).order_by("id")
    rows = []
    for obj in qs:
        rows.append({
            "id": obj.id,
            "tool_description": obj.tool_description or "",
            "unit_cost": str(obj.unit_cost or ""),
            "qty_required": str(obj.qty_required or ""),
            "total_estimate": str(obj.total_estimate or ""),
            "remarks": obj.remarks or "",
        })
    return JsonResponse({"rows": rows})


@require_active_customer
def delete_bop_tolling(request):
    """Delete a single BOP Tooling record by id."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        record_id = data.get("id")
        if not record_id:
            return JsonResponse({"error": "id required"}, status=400)
        BOPTolling.objects.filter(id=record_id).delete()
        return JsonResponse({"status": "success", "message": "BOP Tooling record deleted."})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ============================================================
# CELL ALIGNMENT — CRUD ENDPOINTS
# ============================================================

@require_active_customer
def save_cell_alignment(request):
    """Save (Add/Update) a Cell Alignment record."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bop_creation_id = data.get("bopcreation_id", "").strip()
        item_creation_id = data.get("itemcreation_id", "").strip()
        record_id = data.get("id", "")

        if not bop_creation_id:
            return JsonResponse({"error": "BOP Creation ID is required"}, status=400)

        with transaction.atomic():
            if record_id:
                obj = BOPCellAlignment.objects.filter(id=record_id).first()
                if not obj:
                    return JsonResponse({"error": "Record not found"}, status=404)
            else:
                obj = BOPCellAlignment()

            obj.bopcreationid = bop_creation_id
            obj.itemcreation_id = item_creation_id
            obj.table_id = data.get("table_id") or None
            obj.product_category = data.get("product_category", "")
            obj.process = data.get("process", "")
            obj.manufacturing_location = data.get("manufacturing_location", "")
            obj.cell = data.get("cell", "")
            obj.quantity = data.get("quantity") or None
            obj.remarks = data.get("remarks", "")
            obj.save()

        return JsonResponse({"status": "success", "id": obj.id, "message": "Cell Alignment record saved."})
    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


def load_cell_alignment(request):
    """Load all Cell Alignment rows for a given bopcreation_id."""
    bop_creation_id = request.GET.get("bopcreation_id", "").strip()
    if not bop_creation_id:
        return JsonResponse({"error": "bopcreation_id required"}, status=400)
    qs = BOPCellAlignment.objects.filter(bopcreationid=bop_creation_id).order_by("id")
    rows = []
    for obj in qs:
        rows.append({
            "id": obj.id,
            "product_category": obj.product_category or "",
            "process": obj.process or "",
            "manufacturing_location": obj.manufacturing_location or "",
            "cell": obj.cell or "",
            "quantity": str(obj.quantity or ""),
            "remarks": obj.remarks or "",
        })
    return JsonResponse({"rows": rows})


@require_active_customer
def delete_cell_alignment(request):
    """Delete a single Cell Alignment record by id."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        record_id = data.get("id")
        if not record_id:
            return JsonResponse({"error": "id required"}, status=400)
        BOPCellAlignment.objects.filter(id=record_id).delete()
        return JsonResponse({"status": "success", "message": "Cell Alignment record deleted."})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)