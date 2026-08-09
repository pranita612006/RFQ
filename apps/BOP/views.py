from django.utils import datastructures
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import transaction, connection
from django.utils import timezone
from urllib.parse import urlencode
from config.decorators import require_active_customer
from apps.item_creation.models import ItemCard, Cell, CellType
from apps.BOM.models import BOMHeader
from .models import BOPToolingMaster
import csv
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
    BOPTabECN,
    BOPTollingECN,
    BOPCellAlignmentECN,
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
def get_bom_details_for_modal(request):
    """
    Returns BOM header + parts data as JSON for the in-page BOM Details modal.
    Called by the BOM Details button instead of navigating away.
    """
    item_creation_id = request.GET.get("item_creation_id", "").strip()
    bop_creation_id = request.GET.get("bop_creation_id", "").strip()
    customer_id = request.active_customer.get("id", "") if hasattr(request, "active_customer") else ""

    if not item_creation_id:
        return JsonResponse({"error": "Please load a valid Item Creation ID first."}, status=400)

    item_variants = _item_creation_id_variants(item_creation_id)

    # Resolve linked BOM ID
    bom_creation_id, resolved_item_id = _lookup_bom_from_rfq_details(
        item_variants, customer_id, bop_creation_id
    )
    if not bom_creation_id:
        bom_creation_id, resolved_item_id = _lookup_bom_from_bomcreation(
            item_variants, customer_id
        )
    if not bom_creation_id:
        return JsonResponse({"error": "BOM Record not found for this Item Creation ID."}, status=404)

    # Fetch BOM Header
    from apps.BOM.models import BOMHeader, BOMTransaction
    header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
    header_data = {}
    if header:
        header_data = {
            "bom_creation_id": header.bom_creation_id or "",
            "item_creation_id": header.item_creation_id or "",
            "customer_id": header.customer_id or "",
            "description": header.description or "",
            "uom_code": header.uom_code or "",
            "action_status": header.action_status or "",
            "table_id": header.table_id or "",
            "create_date": header.create_date or "",
            "last_date_modified": header.last_date_modified or "",
        }

    # Fetch BOM Parts / Transactions
    parts = list(
        BOMTransaction.objects.filter(bom_creation_id=bom_creation_id).values(
            "id", "entry_type", "part_number", "quantity", "description",
            "uom_code", "categorisation", "routing_link_code", "part_status",
            "grp_part_no", "grp_part_descp", "start_date", "table_id"
        )
    )
    # Convert Decimal fields for JSON
    for p in parts:
        if p.get("quantity") is not None:
            p["quantity"] = str(p["quantity"])

    return JsonResponse({
        "status": "success",
        "bom_creation_id": bom_creation_id,
        "header": header_data,
        "parts": parts,
        "bom_url": f"/BOM/?item_creation_id={resolved_item_id or item_creation_id}&bom_creation_id={bom_creation_id}&customer_id={customer_id}&from_bop=1",
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

        # 5. Check existing BOP record — scoped to active customer first, then any match
        bop_creation_id = last_modified_date = action_status = table_id = ""
        last_ecn_no = 0

        # Primary lookup: active customer scope — determines form mode (Create vs View)
        bop_obj = BOPCreation.objects.filter(
            itemcreation_id__in=item_variants,
            customer_id=matched_customer_id,
        ).first() if matched_customer_id else None

        # Fallback: any BOP for this item (across customers) — won't override form mode
        if not bop_obj:
            bop_obj = BOPCreation.objects.filter(itemcreation_id__in=item_variants).first()
            # Only populate the BOP ID field if it belongs to this customer
            if bop_obj and str(bop_obj.customer_id) != str(matched_customer_id):
                bop_obj = None  # Don't auto-load a different customer's BOP

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

        # Collect all BOP IDs for this item (all customers) to populate the dropdown datalist
        all_bop_ids = list(
            BOPCreation.objects.filter(itemcreation_id__in=item_variants)
            .exclude(bopcreation_id="")
            .values_list("bopcreation_id", flat=True)
            .distinct()
        )

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
            "all_bop_ids": all_bop_ids,
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
            # Scope lookups to the active customer so approved records from other customers
            # do not interfere with the current customer's workflow.
            bop_record = None
            if table_id:
                bop_record = BOPCreation.objects.filter(id=table_id).first()
            if not bop_record:
                bop_record = BOPCreation.objects.filter(
                    itemcreation_id=item_creation_int,
                    customer_id=selected_customer_id,
                ).first()
                
            is_new = bop_record is None
            
            if is_new:
                # --- CREATE WORKFLOW (INSERT) ---
                # Check for duplicate item creation ID scoped to this customer before inserting
                existing_dup = BOPCreation.objects.filter(
                    itemcreation_id=item_creation_int,
                    customer_id=selected_customer_id,
                ).exists()
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
            
            # Historical ECN Logging tracking — use raw SQL because tbl_bopcreation_ecn
            # is managed=False and has no 'id' column (imported from Access DB).
            # Django ORM's save() fails with RETURNING "id" on such tables.
            ecn_count = BOPCreationECN.objects.filter(bopcreation_id=bop_record.bopcreation_id).count()
            next_ecn_id = f"ECN-{ecn_count + 1:03d}"

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO tbl_bopcreation_ecn (
                            bopcreation_id, ecn_id, itemcreation_id, customer_id,
                            customer_name, drawing_no, drawing_revision_no, revision_date,
                            part_name, product_category, remark
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            bop_record.bopcreation_id,
                            next_ecn_id,
                            str(bop_record.itemcreation_id),
                            selected_customer_id,
                            bop_record.customer_name,
                            bop_record.drawing_no,
                            bop_record.drawing_revision_no,
                            bop_record.revision_date,
                            bop_record.part_name,
                            bop_record.product_category,
                            bop_record.remark,
                        ]
                    )
            except Exception as ecn_err:
                # ECN logging is non-critical — log but don't fail the main save
                import traceback as _tb
                print(f"[WARN] ECN log insert failed: {ecn_err}\n{_tb.format_exc()}")
            
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
    """Fetch annual volume fields from OpportunityMaster for ECN logging"""
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

            # Use raw SQL to insert into tbl_bopcreation_ecn because it has no auto-incrementing primary key 'id' column,
            # which causes Django's default .save() ORM method to fail with a RETURNING "id" error on access tables.
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tbl_bopcreation_ecn (
                        bopcreation_id, ecn_id, itemcreation_id, customer_id,
                        customer_name, drawing_no, drawing_revision_no, revision_date,
                        part_name, product_category, remark, project, part_set_no, table_id, entry_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        bop_record.bopcreation_id,
                        next_ecn_id,
                        str(bop_record.itemcreation_id),
                        bop_record.customer_id,
                        bop_record.customer_name,
                        bop_record.drawing_no,
                        bop_record.drawing_revision_no,
                        bop_record.revision_date,
                        bop_record.part_name,
                        bop_record.product_category,
                        bop_record.remark,
                        bop_record.project,
                        bop_record.part_set_no,
                        bop_record.table_id,
                        timezone.now().date(),
                    ]
                )


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


@require_active_customer
def ecn_bop(request):
    """
    Handle ECN button click: transition BOP record status to 'ECN'.
    This allows an approved record to be edited again.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        item_id = data.get("item_creation_id", "").strip()
        bop_id = data.get("bop_creation_id", "").strip()
        table_id = data.get("table_id", "")

        if not item_id:
            return JsonResponse(
                {"error": "Action Blocked: Please load a valid Item Creation ID first."},
                status=400,
            )
        if not bop_id:
            return JsonResponse(
                {"error": "Action Blocked: No active BOP Record loaded."},
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
            if current_status == "ECN":
                return JsonResponse(
                    {"error": "Action Blocked: BOP Record is already in ECN status."},
                    status=400,
                )

            bop_record.action_status = "ECN"
            bop_record.last_modified_date = timezone.now().date()
            bop_record.save()

            ecn_count = BOPCreationECN.objects.filter(bopcreation_id=bop_record.bopcreation_id).count()
            next_ecn_id = f"ECN-{ecn_count:03d}" if ecn_count > 0 else "0"

        return JsonResponse({
            "status": "success",
            "message": f"BOP Record {bop_record.bopcreation_id} transitioned to ECN status. You can now edit and save changes.",
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


# ============================================================
# COPY BOP TABLE — Access VBA btn_CreateTable_Click equivalent
# ============================================================

@require_active_customer
def copy_bop_table(request):
    """
    Copy all BOP sub-table rows (Cell Alignment, BOP Tab, BOP Tooling) from the
    currently selected table_id into a new incremented table_id for the same BOP record.

    Access VBA equivalent: btn_CreateTable_Click + btn_CreateCopy_Click
    - Determines current max table_id across all three sub-tables for the BOP record.
    - Inserts copies of every row under new_table_id = max_table_id + 1.

    Uses raw SQL INSERT...SELECT (omitting id) and calls setval() before each insert
    to advance the PostgreSQL sequence past the table's actual max id.  This is
    required for managed=False tables imported from Access whose sequences are
    out-of-sync with the real data, causing "duplicate key" errors on normal inserts.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)

    try:
        data = json.loads(request.body)
        bop_creation_id = data.get("bop_creation_id", "").strip()
        source_table_id = data.get("table_id", "")

        if not bop_creation_id:
            return JsonResponse({"error": "Action Blocked: BOP Creation ID is required."}, status=400)

        try:
            source_table_id = int(source_table_id)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Action Blocked: A valid Table ID must be selected to copy."}, status=400)

        with transaction.atomic():
            from django.db.models import Max

            # Compute new_table_id = max existing table_id across all three sub-tables + 1
            max_cell    = BOPCellAlignment.objects.filter(bopcreationid=bop_creation_id).aggregate(m=Max("table_id"))["m"] or 0
            max_tab     = BOPTab.objects.filter(bopcreationid=bop_creation_id).aggregate(m=Max("table_id"))["m"] or 0
            max_tolling = BOPTolling.objects.filter(bopcreationid=bop_creation_id).aggregate(m=Max("table_id"))["m"] or 0
            new_table_id = max(max_cell, max_tab, max_tolling) + 1

            with connection.cursor() as cur:

                # Advance a sequence past the table's actual max id before inserting.
                # Prevents duplicate-key errors on Access-imported tables where the
                # PostgreSQL sequence lags behind the real data.
                def fix_seq(table, seq):
                    cur.execute(
                        f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"
                    )

                # ── Cell Alignment ──────────────────────────────────────────
                fix_seq("tbl_bop_cellallienment", "tbl_bop_cellallienment_id_seq")
                cur.execute(
                    """
                    INSERT INTO tbl_bop_cellallienment
                        (product_category, process, manufacturing_loacation, cell,
                         quantity, bopcreationid, itemcreation_id, table_id,
                         remarks, completedon)
                    SELECT
                        product_category, process, manufacturing_loacation, cell,
                        quantity, bopcreationid, itemcreation_id, %s,
                        remarks, completedon
                    FROM tbl_bop_cellallienment
                    WHERE bopcreationid = %s AND table_id = %s
                    """,
                    [new_table_id, bop_creation_id, source_table_id]
                )
                cell_count = cur.rowcount

                # ── BOP Tab ─────────────────────────────────────────────────
                fix_seq("tbl_bop_tab", "tbl_bop_tab_id_seq")
                cur.execute(
                    """
                    INSERT INTO tbl_bop_tab
                        (seq_no, operation_no, type, costcenter_no, description,
                         categorisation, run_time_sec, run_time_min, boq,
                         total_run_time, cycle_time, mhr_year, mhr_lower, mhr_higher,
                         costperqnty, total_cost, remark, table_id, bopcreationid,
                         itemcreation_id, customer_id, type_selected, completedon,
                         last_modified_date, is_download)
                    SELECT
                        seq_no, operation_no, type, costcenter_no, description,
                        categorisation, run_time_sec, run_time_min, boq,
                        total_run_time, cycle_time, mhr_year, mhr_lower, mhr_higher,
                        costperqnty, total_cost, remark, %s, bopcreationid,
                        itemcreation_id, customer_id, type_selected, completedon,
                        %s, NULL
                    FROM tbl_bop_tab
                    WHERE bopcreationid = %s AND table_id = %s
                    """,
                    [new_table_id, str(timezone.now().date()), bop_creation_id, source_table_id]
                )
                tab_count = cur.rowcount

                # ── BOP Tooling ─────────────────────────────────────────────
                fix_seq("tbl_bop_tolling", "tbl_bop_tolling_id_seq")
                cur.execute(
                    """
                    INSERT INTO tbl_bop_tolling
                        (tool_description, uom, unit_cost, settled_price, qty_required,
                         total_estimate, total_settledprice, entry_date, bopcreationid,
                         itemcreation_id, table_id, customer_id, remarks, completedon)
                    SELECT
                        tool_description, uom, unit_cost, settled_price, qty_required,
                        total_estimate, total_settledprice, %s, bopcreationid,
                        itemcreation_id, %s, customer_id, remarks, completedon
                    FROM tbl_bop_tolling
                    WHERE bopcreationid = %s AND table_id = %s
                    """,
                    [timezone.now().date(), new_table_id, bop_creation_id, source_table_id]
                )
                tolling_count = cur.rowcount

        total_copied = cell_count + tab_count + tolling_count
        return JsonResponse({
            "status": "success",
            "new_table_id": new_table_id,
            "copied": {
                "cell_alignment": cell_count,
                "bop_tab": tab_count,
                "bop_tolling": tolling_count,
                "total": total_copied,
            },
            "message": (
                f"BOP Table copied successfully! New Table ID: {new_table_id}. "
                f"Copied {tab_count} BOP Tab row(s), {cell_count} Cell Alignment row(s), "
                f"and {tolling_count} Tooling row(s)."
            ),
        })

    except Exception as e:
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


@require_active_customer
def download_cell_alignment(request):
    """Download Cell Alignment records as CSV, filtered by bopcreationid and table_id."""
    bopcreation_id = request.GET.get("bopcreation_id", "").strip()
    table_id = request.GET.get("table_id", "").strip()
    
    if not bopcreation_id:
        return HttpResponse("BOP Creation ID is required", status=400)
        
    queryset = BOPCellAlignment.objects.filter(bopcreationid=bopcreation_id)
    if table_id:
        try:
            queryset = queryset.filter(table_id=int(table_id))
        except ValueError:
            pass
            
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cell_alignment_{bopcreation_id}_{table_id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Item Creation ID', 'Product Category', 'Process', 
        'Manufacturing Location', 'Cell', 'Quantity', 'BOP Creation ID', 
        'Table ID', 'Remarks', 'Completed On'
    ])
    
    for row in queryset:
        writer.writerow([
            row.id,
            row.itemcreation_id or '',
            row.product_category or '',
            row.process or '',
            row.manufacturing_location or '',
            row.cell or '',
            row.quantity or '',
            row.bopcreationid or '',
            row.table_id or '',
            row.remarks or '',
            row.completedon or ''
        ])
    return response


@require_active_customer
def complete_cell_alignment(request):
    """Mark Cell Alignment section as completed with validation and ECN logging."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bopcreation_id = data.get("bopcreation_id", "").strip()
        table_id = data.get("table_id", "").strip()
        
        if not bopcreation_id:
            return JsonResponse({"status": "error", "message": "BOP Creation ID is required"}, status=400)
            
        with transaction.atomic():
            parent_bop = BOPCreation.objects.filter(bopcreation_id=bopcreation_id).first()
            if not parent_bop:
                return JsonResponse({"status": "error", "message": f"BOP Record not found for {bopcreation_id}."}, status=404)
                
            queryset = BOPCellAlignment.objects.filter(bopcreationid=bopcreation_id)
            if table_id:
                try:
                    queryset = queryset.filter(table_id=int(table_id))
                except ValueError:
                    return JsonResponse({"status": "error", "message": "Invalid Table ID"}, status=400)
            
            records = list(queryset)
            if not records:
                return JsonResponse({"status": "error", "message": "No Cell Alignment records exist for the given BOP Creation ID and Table ID."}, status=400)
                
            # Prevent duplicate completion
            if any(record.completedon for record in records):
                return JsonResponse({"status": "error", "message": "This section has already been completed."}, status=400)
                
            # Validate mandatory fields
            errors = []
            for idx, record in enumerate(records, 1):
                missing = []
                if not record.product_category or not record.product_category.strip():
                    missing.append("Product Category")
                if not record.process or not record.process.strip():
                    missing.append("Process")
                if not record.manufacturing_location or not record.manufacturing_location.strip():
                    missing.append("Manufacturing Location")
                if not record.cell or not record.cell.strip():
                    missing.append("Cell")
                if record.quantity is None:
                    missing.append("Quantity")
                if missing:
                    errors.append(f"Row {idx} is missing: {', '.join(missing)}")
                    
            if errors:
                return JsonResponse({
                    "status": "error",
                    "message": f"Mandatory fields are missing: {'; '.join(errors)}"
                }, status=400)
                
            today = timezone.now().date()
            
            # Update all matching records
            queryset.update(completedon=today)
            
            # Update parent BOP record
            parent_bop.last_modified_date = today
            if parent_bop.action_status not in ["Approved", "ECN", "Send for Approval", "Created", "Updated"]:
                parent_bop.action_status = "Updated"
            parent_bop.save()
            
            # Historical ECN Logging
            ecn_count = BOPCreationECN.objects.filter(bopcreation_id=parent_bop.bopcreation_id).count()
            next_ecn_id = f"ECN-{ecn_count + 1:03d}"
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO tbl_bopcreation_ecn (
                            bopcreation_id, ecn_id, itemcreation_id, customer_id,
                            customer_name, drawing_no, drawing_revision_no, revision_date,
                            part_name, product_category, remark, project, part_set_no, table_id, entry_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            parent_bop.bopcreation_id,
                            next_ecn_id,
                            str(parent_bop.itemcreation_id),
                            parent_bop.customer_id,
                            parent_bop.customer_name,
                            parent_bop.drawing_no,
                            parent_bop.drawing_revision_no,
                            parent_bop.revision_date,
                            parent_bop.part_name,
                            parent_bop.product_category,
                            parent_bop.remark,
                            parent_bop.project,
                            parent_bop.part_set_no,
                            parent_bop.table_id,
                            today,
                        ]
                    )
            except Exception as ecn_err:
                import traceback as _tb
                print(f"[WARN] ECN log insert failed: {ecn_err}\n{_tb.format_exc()}")
                
        return JsonResponse({
            "status": "success",
            "message": "Section completed successfully.",
            "completed_on": today.strftime("%Y-%m-%d")
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_active_customer
def download_bop_tab(request):
    """Download BOP Tab records as CSV, filtered by bopcreationid and table_id, and flag is_download = True."""
    bopcreation_id = request.GET.get("bopcreation_id", "").strip()
    table_id = request.GET.get("table_id", "").strip()
    
    if not bopcreation_id:
        return HttpResponse("BOP Creation ID is required", status=400)
        
    queryset = BOPTab.objects.filter(bopcreationid=bopcreation_id)
    if table_id:
        try:
            queryset = queryset.filter(table_id=int(table_id))
        except ValueError:
            pass
            
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bop_tab_{bopcreation_id}_{table_id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Seq No', 'Operation No', 'Type', 'Cost Center No', 'Description',
        'Categorisation', 'Run Time Sec', 'Run Time Min', 'BOQ', 'Total Run Time',
        'Cycle Time', 'MHR Year', 'MHR Lower', 'MHR Higher', 'Cost Per Qty',
        'Total Cost', 'Remark', 'Table ID', 'BOP Creation ID', 'Item Creation ID',
        'Customer ID', 'Type Selected', 'Completed On', 'Last Modified Date', 'Is Download'
    ])
    
    rows = list(queryset)
    if rows:
        queryset.update(is_download=True)
        
    for row in rows:
        writer.writerow([
            row.id,
            row.seq_no or '',
            row.operation_no or '',
            row.type or '',
            row.costcenter_no or '',
            row.description or '',
            row.categorisation or '',
            row.run_time_sec or '',
            row.run_time_min or '',
            row.boq or '',
            row.total_run_time or '',
            row.cycle_time or '',
            row.mhr_year or '',
            row.mhr_lower or '',
            row.mhr_higher or '',
            row.costperqnty or '',
            row.total_cost or '',
            row.remark or '',
            row.table_id or '',
            row.bopcreationid or '',
            row.itemcreation_id or '',
            row.customer_id or '',
            row.type_selected or '',
            row.completedon or '',
            row.last_modified_date or '',
            True
        ])
    return response


@require_active_customer
def complete_bop_tab(request):
    """Mark BOP Tab section as completed with validation and ECN logging."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bopcreation_id = data.get("bopcreation_id", "").strip()
        table_id = data.get("table_id", "").strip()
        
        if not bopcreation_id:
            return JsonResponse({"status": "error", "message": "BOP Creation ID is required"}, status=400)
            
        with transaction.atomic():
            parent_bop = BOPCreation.objects.filter(bopcreation_id=bopcreation_id).first()
            if not parent_bop:
                return JsonResponse({"status": "error", "message": f"BOP Record not found for {bopcreation_id}."}, status=404)
                
            queryset = BOPTab.objects.filter(bopcreationid=bopcreation_id)
            if table_id:
                try:
                    queryset = queryset.filter(table_id=int(table_id))
                except ValueError:
                    return JsonResponse({"status": "error", "message": "Invalid Table ID"}, status=400)
            
            records = list(queryset)
            if not records:
                return JsonResponse({"status": "error", "message": "No BOP Tab records exist for the given BOP Creation ID and Table ID."}, status=400)
                
            # Prevent duplicate completion
            if any(record.completedon for record in records):
                return JsonResponse({"status": "error", "message": "This section has already been completed."}, status=400)
                
            # Validate mandatory fields
            errors = []
            for idx, record in enumerate(records, 1):
                missing = []
                if record.seq_no is None:
                    missing.append("Seq No")
                if not record.operation_no or not record.operation_no.strip():
                    missing.append("Operation No")
                if not record.type or not record.type.strip():
                    missing.append("Type")
                if not record.costcenter_no or not record.costcenter_no.strip():
                    missing.append("Cost Center No")
                if not record.description or not record.description.strip():
                    missing.append("Description")
                if record.run_time_sec is None:
                    missing.append("Run Time Sec")
                if record.run_time_min is None:
                    missing.append("Run Time Min")
                if record.boq is None:
                    missing.append("BOQ")
                if record.total_run_time is None:
                    missing.append("Total Run Time")
                if record.cycle_time is None:
                    missing.append("Cycle Time")
                if missing:
                    errors.append(f"Row {idx} (Seq {record.seq_no or 'N/A'}) is missing: {', '.join(missing)}")
                    
            if errors:
                return JsonResponse({
                    "status": "error",
                    "message": f"Mandatory fields are missing: {'; '.join(errors)}"
                }, status=400)
                
            today = timezone.now().date()
            today_str = str(today)
            
            # Update all matching records
            queryset.update(completedon=today_str, last_modified_date=today_str)
            
            # Update parent BOP record
            parent_bop.last_modified_date = today
            if parent_bop.action_status not in ["Approved", "ECN", "Send for Approval", "Created", "Updated"]:
                parent_bop.action_status = "Updated"
            parent_bop.save()
            
            # Historical ECN Logging
            ecn_count = BOPCreationECN.objects.filter(bopcreation_id=parent_bop.bopcreation_id).count()
            next_ecn_id = f"ECN-{ecn_count + 1:03d}"
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO tbl_bopcreation_ecn (
                            bopcreation_id, ecn_id, itemcreation_id, customer_id,
                            customer_name, drawing_no, drawing_revision_no, revision_date,
                            part_name, product_category, remark, project, part_set_no, table_id, entry_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            parent_bop.bopcreation_id,
                            next_ecn_id,
                            str(parent_bop.itemcreation_id),
                            parent_bop.customer_id,
                            parent_bop.customer_name,
                            parent_bop.drawing_no,
                            parent_bop.drawing_revision_no,
                            parent_bop.revision_date,
                            parent_bop.part_name,
                            parent_bop.product_category,
                            parent_bop.remark,
                            parent_bop.project,
                            parent_bop.part_set_no,
                            parent_bop.table_id,
                            today,
                        ]
                    )
            except Exception as ecn_err:
                import traceback as _tb
                print(f"[WARN] ECN log insert failed: {ecn_err}\n{_tb.format_exc()}")
                
        return JsonResponse({
            "status": "success",
            "message": "Section completed successfully.",
            "completed_on": today.strftime("%Y-%m-%d")
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_active_customer
def download_bop_tolling(request):
    """Download BOP Tooling records as CSV, filtered by bopcreationid and table_id."""
    bopcreation_id = request.GET.get("bopcreation_id", "").strip()
    table_id = request.GET.get("table_id", "").strip()
    
    if not bopcreation_id:
        return HttpResponse("BOP Creation ID is required", status=400)
        
    queryset = BOPTolling.objects.filter(bopcreationid=bopcreation_id)
    if table_id:
        try:
            queryset = queryset.filter(table_id=int(table_id))
        except ValueError:
            pass
            
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bop_tolling_{bopcreation_id}_{table_id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Tool Description', 'UOM', 'Unit Cost', 'Settled Price',
        'Qty Required', 'Total Estimate', 'Total Settled Price', 'Entry Date',
        'BOP Creation ID', 'Item Creation ID', 'Table ID', 'Customer ID',
        'Remarks', 'Completed On'
    ])
    
    for row in queryset:
        writer.writerow([
            row.id,
            row.tool_description or '',
            row.uom or '',
            row.unit_cost or '',
            row.settled_price or '',
            row.qty_required or '',
            row.total_estimate or '',
            row.total_settledprice or '',
            row.entry_date or '',
            row.bopcreationid or '',
            row.itemcreation_id or '',
            row.table_id or '',
            row.customer_id or '',
            row.remarks or '',
            row.completedon or ''
        ])
    return response


@require_active_customer
def complete_bop_tolling(request):
    """Mark BOP Tooling section as completed with validation and ECN logging."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bopcreation_id = data.get("bopcreation_id", "").strip()
        table_id = data.get("table_id", "").strip()
        
        if not bopcreation_id:
            return JsonResponse({"status": "error", "message": "BOP Creation ID is required"}, status=400)
            
        with transaction.atomic():
            parent_bop = BOPCreation.objects.filter(bopcreation_id=bopcreation_id).first()
            if not parent_bop:
                return JsonResponse({"status": "error", "message": f"BOP Record not found for {bopcreation_id}."}, status=404)
                
            queryset = BOPTolling.objects.filter(bopcreationid=bopcreation_id)
            if table_id:
                try:
                    queryset = queryset.filter(table_id=int(table_id))
                except ValueError:
                    return JsonResponse({"status": "error", "message": "Invalid Table ID"}, status=400)
            
            records = list(queryset)
            if not records:
                return JsonResponse({"status": "error", "message": "No BOP Tooling records exist for the given BOP Creation ID and Table ID."}, status=400)
                
            # Prevent duplicate completion
            if any(record.completedon for record in records):
                return JsonResponse({"status": "error", "message": "This section has already been completed."}, status=400)
                
            # Validate mandatory fields
            errors = []
            for idx, record in enumerate(records, 1):
                missing = []
                if not record.tool_description or not record.tool_description.strip():
                    missing.append("Tool Description")
                if record.unit_cost is None:
                    missing.append("Unit Cost")
                if record.qty_required is None:
                    missing.append("Qty Required")
                if record.total_estimate is None:
                    missing.append("Total Estimate")
                if missing:
                    errors.append(f"Row {idx} is missing: {', '.join(missing)}")
                    
            if errors:
                return JsonResponse({
                    "status": "error",
                    "message": f"Mandatory fields are missing: {'; '.join(errors)}"
                }, status=400)
                
            today = timezone.now().date()
            
            # Update all matching records
            queryset.update(completedon=today)
            
            # Update parent BOP record
            parent_bop.last_modified_date = today
            if parent_bop.action_status not in ["Approved", "ECN", "Send for Approval", "Created", "Updated"]:
                parent_bop.action_status = "Updated"
            parent_bop.save()
            
            # Historical ECN Logging
            ecn_count = BOPCreationECN.objects.filter(bopcreation_id=parent_bop.bopcreation_id).count()
            next_ecn_id = f"ECN-{ecn_count + 1:03d}"
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO tbl_bopcreation_ecn (
                            bopcreation_id, ecn_id, itemcreation_id, customer_id,
                            customer_name, drawing_no, drawing_revision_no, revision_date,
                            part_name, product_category, remark, project, part_set_no, table_id, entry_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            parent_bop.bopcreation_id,
                            next_ecn_id,
                            str(parent_bop.itemcreation_id),
                            parent_bop.customer_id,
                            parent_bop.customer_name,
                            parent_bop.drawing_no,
                            parent_bop.drawing_revision_no,
                            parent_bop.revision_date,
                            parent_bop.part_name,
                            parent_bop.product_category,
                            parent_bop.remark,
                            parent_bop.project,
                            parent_bop.part_set_no,
                            parent_bop.table_id,
                            today,
                        ]
                    )
            except Exception as ecn_err:
                import traceback as _tb
                print(f"[WARN] ECN log insert failed: {ecn_err}\n{_tb.format_exc()}")
                
        return JsonResponse({
            "status": "success",
            "message": "Section completed successfully.",
            "completed_on": today.strftime("%Y-%m-%d")
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_active_customer
def copy_bop(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bopcreation_id = data.get("bopcreation_id", "").strip()
        table_id = data.get("table_id", "").strip()

        if not bopcreation_id:
            return JsonResponse({"status": "error", "message": "BOP Creation ID is required"}, status=400)

        queryset = BOPTab.objects.filter(bopcreationid=bopcreation_id)
        if table_id:
            try:
                queryset = queryset.filter(table_id=int(table_id))
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid Table ID"}, status=400)
        
        records = list(queryset)
        if not records:
            return JsonResponse({"status": "error", "message": "No records found to copy."}, status=404)
        
        copied_data = []
        exclude_fields = ['id', 'pk', 'completedon', 'last_modified_date', 'is_download', 'bopcreationid', 'itemcreation_id', 'table_id', 'customer_id']
        for record in records:
            record_dict = {}
            for field in record._meta.fields:
                if field.name not in exclude_fields:
                    val = getattr(record, field.name)
                    if isinstance(val, (int, float, str, bool, type(None))):
                        record_dict[field.name] = val
                    else:
                        record_dict[field.name] = str(val) if val is not None else None
            copied_data.append(record_dict)

        request.session["copied_bop"] = copied_data
        request.session.modified = True

        return JsonResponse({"status": "success", "message": "BOP copied successfully."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_active_customer
def paste_bop(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST requests allowed"}, status=405)
    try:
        copied_data = request.session.get("copied_bop")
        if not copied_data:
            return JsonResponse({"status": "error", "message": "No copied BOP available."}, status=404)

        data = json.loads(request.body)
        bopcreation_id = data.get("bopcreation_id", "").strip()
        itemcreation_id = data.get("itemcreation_id", "").strip()
        table_id = data.get("table_id", "").strip()
        customer_id = data.get("customer_id", "").strip()

        if not bopcreation_id:
            return JsonResponse({"status": "error", "message": "Target BOP Creation ID is required"}, status=400)

        with transaction.atomic():
            for record_data in copied_data:
                new_record = BOPTab(**record_data)
                new_record.bopcreationid = bopcreation_id
                if itemcreation_id:
                    new_record.itemcreation_id = itemcreation_id
                if table_id:
                    try:
                        new_record.table_id = int(table_id)
                    except ValueError:
                        pass
                if customer_id:
                    new_record.customer_id = customer_id
                new_record.save()

        return JsonResponse({"status": "success", "message": "BOP pasted successfully."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
