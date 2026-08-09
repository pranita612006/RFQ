import json
import csv
from datetime import date, datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.db.models import Max, Count, Q
from django.db.models.functions import Cast
from django.db.models import IntegerField as DjIntegerField
from .models import (
    BOMHeader, BOMTransaction, ItemCardECN,
    BOMProdItemPartGrpMaster, BOMPartDetailsMaster,
    BomProdItemPartGrpMasterRawData, BOMProdItemPartGrpMasterDetail,
)
from config.decorators import require_active_customer


def _next_bom_trans_id():
    """Return the next available Id for tbl_bomcreation_partselection.

    Mirrors the VBA pattern:  Nz(DMax("Id", "tbl_bomcreation_partselection"), 0) + 1
    """
    max_id = BOMTransaction.objects.aggregate(m=Max('id'))['m']
    return (max_id or 0) + 1



@require_active_customer
def BOM_form(request):
    # Retrieve all existing BOM creation IDs for the dropdown if needed
    context = {
        "headers": BOMHeader.objects.all(),
        "active_customer": getattr(request, 'active_customer', None)
    }
    return render(request, "BOM/BOM_form.html", context)

@csrf_exempt
def bom_ajax_action(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")
            
            if action == "add_part":
                parent_item_code = data.get("parent_item_code") or data.get("item_creation_id")
                if not parent_item_code and data.get("bom_creation_id"):
                    header_temp = BOMHeader.objects.filter(bom_creation_id=data.get("bom_creation_id")).first()
                    if header_temp:
                        parent_item_code = header_temp.item_creation_id

                component_item_id = data.get("component_item_id") or data.get("part_number")
                quantity_raw = data.get("quantity")

                if not parent_item_code or not component_item_id or quantity_raw is None:
                    return JsonResponse({
                        "status": "error",
                        "message": "Missing required fields: parent_item_code, component_item_id, and quantity are required."
                    }, status=400)

                try:
                    quantity = float(quantity_raw or 0)
                except (ValueError, TypeError):
                    quantity = 0.0

                try:
                    from .services import check_bom_locked
                    from django.core.exceptions import ValidationError
                    
                    bom_id = data.get("bom_creation_id")
                    if bom_id:
                        check_bom_locked(bom_id)
                        
                    # Normalize parent_item_code
                    _ic = parent_item_code.strip()
                    _ip = _ic.zfill(8) if _ic.isdigit() else _ic
                    _il = _ic.lstrip('0') or _ic

                    # Retrieve or create parent BOMHeader
                    header = None
                    if bom_id:
                        header = BOMHeader.objects.filter(bom_creation_id=bom_id).first()
                    
                    if not header:
                        header = (
                            BOMHeader.objects
                            .filter(Q(item_creation_id=_ic) | Q(item_creation_id=_ip) | Q(item_creation_id=_il))
                            .first()
                        )

                    if not header:
                        today = date.today()
                        max_row = BOMHeader.objects.filter(
                            Q(item_creation_id=_ic) | Q(item_creation_id=_ip) | Q(item_creation_id=_il)
                        ).aggregate(max_row=Max("bom_row_id"))["max_row"]
                        
                        try:
                            int_bom_row_id = int(max_row or 0) + 1
                        except (ValueError, TypeError):
                            int_bom_row_id = 1
                        
                        bom_creation_id = f"BOM{today.strftime('%Y%m%d')}{int_bom_row_id}"

                        max_table = BOMHeader.objects.filter(
                            Q(item_creation_id=_ic) | Q(item_creation_id=_ip) | Q(item_creation_id=_il)
                        ).aggregate(max_table=Max("table_id"))["max_table"]
                        try:
                            table_id = str(int(max_table or 0) + 1)
                        except (TypeError, ValueError):
                            table_id = "1"

                        item_card = ItemCard.objects.filter(Q(no=_ic) | Q(no=_ip) | Q(no=_il)).first()
                        desc = item_card.description if item_card else ""
                        uom = item_card.base_unit_of_measure if item_card else ""
                        cust_id = (item_card.customer_id if item_card else "") or data.get("customer_id") or ""

                        header = BOMHeader.objects.create(
                            customer_id=cust_id,
                            item_creation_id=parent_item_code,
                            bom_row_id=int_bom_row_id,
                            bom_creation_id=bom_creation_id,
                            description=desc,
                            uom_code=uom,
                            action_status="Pending",
                            last_date_modified=today,
                            table_id=table_id,
                            create_date=today,
                        )

                    entry_type = data.get("entry_type")
                    description = data.get("description")
                    uom_code = data.get("uom_code")
                    categorisation = data.get("categorisation")
                    routing_link_code = data.get("routing_link_code")
                    part_status = data.get("part_status")

                    if entry_type == "Production BOM":
                        # Fetch all child rows for this group part
                        child_rows = list(
                            BOMProdItemPartGrpMaster.objects.filter(
                                grp_part_no__iexact=component_item_id
                            ).order_by("level", "row_id")
                        )
                        if not child_rows:
                            # Fallback to raw data table if group master has no records
                            raw_rows = list(
                                BomProdItemPartGrpMasterRawData.objects.filter(
                                    grp_partno__iexact=component_item_id
                                ).order_by("level")
                            )
                            child_rows = raw_rows

                        if child_rows:
                            grp_no = getattr(child_rows[0], "grp_part_no", None) or getattr(child_rows[0], "grp_partno", None) or component_item_id
                            grp_desc = getattr(child_rows[0], "grp_part_description", "") or description or ""

                            # Map child part details
                            part_nos = [getattr(r, "part_no", "") for r in child_rows if getattr(r, "part_no", "")]
                            details_map = {}
                            if part_nos:
                                details_qs = BOMPartDetailsMaster.objects.filter(part_no__in=part_nos)
                                for d in details_qs:
                                    if d.part_no not in details_map:
                                        details_map[d.part_no] = d

                            inserted_trans = []
                            for r in child_rows:
                                c_part_no = getattr(r, "part_no", "")
                                if not c_part_no:
                                    continue
                                d = details_map.get(c_part_no)
                                c_desc = (d.part_description if d and d.part_description else getattr(r, "part_description", "")) or ""
                                c_uom = (d.base_unit_of_measure if d and d.base_unit_of_measure else getattr(r, "unit_of_measure", "")) or ""
                                c_cat = (d.categorisation if d and d.categorisation else categorisation) or "Local BOC"
                                c_status = (d.part_status if d and d.part_status else part_status) or "Approved"
                                c_tot_qty = float(getattr(r, "total_bom_quantity", None) or getattr(r, "bom_quantity", None) or 1)
                                c_qty = c_tot_qty * quantity

                                trans = BOMTransaction.objects.create(
                                    id=_next_bom_trans_id(),
                                    bom_creation_id=header.bom_creation_id,
                                    entry_type="Production BOM",
                                    grp_part_no=grp_no,
                                    grp_part_descp=grp_desc,
                                    part_number=c_part_no,
                                    quantity=c_qty,
                                    description=c_desc,
                                    uom_code=c_uom,
                                    categorisation=c_cat,
                                    routing_link_code=routing_link_code or "0",
                                    part_status=c_status,
                                    table_id=header.table_id
                                )
                                inserted_trans.append(trans)
                        else:
                            # Single row fallback if no group details found
                            BOMTransaction.objects.create(
                                id=_next_bom_trans_id(),
                                bom_creation_id=header.bom_creation_id,
                                entry_type=entry_type,
                                part_number=component_item_id,
                                quantity=quantity,
                                description=description or "",
                                uom_code=uom_code or "",
                                categorisation=categorisation or "NA",
                                routing_link_code=routing_link_code or "0",
                                part_status=part_status or "Approved",
                                table_id=header.table_id
                            )
                    else:
                        if not entry_type or not description:
                            item_info = BOMItemList.objects.filter(part_no=component_item_id).first()
                            if item_info:
                                entry_type = entry_type or "Item"
                                description = description or item_info.description or ""
                                uom_code = uom_code or item_info.base_unit_of_measure or ""
                                categorisation = categorisation or item_info.categorisation or "NA"
                                routing_link_code = routing_link_code or "0"
                            else:
                                entry_type = entry_type or "Item"
                                description = description or ""
                                uom_code = uom_code or ""
                                categorisation = categorisation or "NA"
                                routing_link_code = routing_link_code or "0"

                        # Ensure the child BOMTransaction is created
                        trans = BOMTransaction.objects.filter(
                            bom_creation_id=header.bom_creation_id,
                            part_number=component_item_id
                        ).first()
                        
                        if not trans:
                            trans = BOMTransaction.objects.create(
                                id=_next_bom_trans_id(),
                                bom_creation_id=header.bom_creation_id,
                                entry_type=entry_type,
                                part_number=component_item_id,
                                quantity=quantity,
                                description=description,
                                uom_code=uom_code,
                                categorisation=categorisation,
                                routing_link_code=routing_link_code,
                                part_status=part_status,
                                table_id=header.table_id
                            )

                    # Update related ItemCardECN counts safely without schema errors
                    ecn = (
                        ItemCardECN.objects
                        .filter(Q(no=_ic) | Q(no=_ip) | Q(no=_il) | Q(no_2=_ic) | Q(no_2=_ip) | Q(no_2=_il))
                        .first()
                    )
                    if ecn:
                        try:
                            current_parts = int(ecn.no_of_parts or 0)
                        except (ValueError, TypeError):
                            current_parts = 0

                        try:
                            current_meft = int(ecn.no_of_meft or 0)
                        except (ValueError, TypeError):
                            current_meft = 0

                        new_parts = current_parts + 1
                        new_meft = current_meft + 1 if entry_type == "MEFT" else current_meft

                        ItemCardECN.objects.filter(ecn_id=ecn.ecn_id).update(
                            no_of_parts=new_parts,
                            no_of_meft=new_meft
                        )

                    return JsonResponse({
                        "status": "success",
                        "message": "Done",
                        "transaction_id": trans.id,
                        "bom_creation_id": header.bom_creation_id,
                        "table_id": header.table_id
                    })
                except Exception as ex:
                    return JsonResponse({
                        "status": "error",
                        "message": str(ex)
                    }, status=500)
                
            elif action == "get_parts":
                bom_creation_id = data.get("bom_creation_id")
                parts = list(BOMTransaction.objects.filter(bom_creation_id=bom_creation_id).values())
                # Dynamically compute counts
                no_of_meft = BOMTransaction.objects.filter(
                    bom_creation_id=bom_creation_id, entry_type="MEFT"
                ).count()
                no_of_parts = len(parts)
                return JsonResponse({
                    "status": "success",
                    "data": parts,
                    "no_of_meft": no_of_meft,
                    "no_of_parts": no_of_parts,
                })
                
            elif action == "delete_part":
                part_id = data.get("part_id")
                if not part_id:
                    return JsonResponse({"status": "error", "message": "Missing part_id"}, status=400)
                part = BOMTransaction.objects.filter(id=part_id).first()
                if part:
                    part.delete()
                    return JsonResponse({"status": "success", "message": "Done"})
                return JsonResponse({"status": "error", "message": "Part not found"}, status=404)
                
            elif action == "update_part":
                part_id = data.get("part_id")
                if not part_id:
                    return JsonResponse({"status": "error", "message": "Missing part_id"}, status=400)
                
                # Check record locked state before update
                bom_id = data.get("bom_creation_id")
                if bom_id:
                    from .services import check_bom_locked
                    try:
                        check_bom_locked(bom_id)
                    except ValidationError as ve:
                        return JsonResponse({"status": "error", "message": str(ve.message)}, status=400)
                
                part = BOMTransaction.objects.filter(id=part_id).first()
                if not part:
                    return JsonResponse({"status": "error", "message": "Part not found"}, status=404)
                
                part.entry_type = data.get("entry_type")
                part.part_number = data.get("part_number")
                try:
                    part.quantity = float(data.get("quantity") or 0)
                except (ValueError, TypeError):
                    part.quantity = 0.0
                part.description = data.get("description")
                part.uom_code = data.get("uom_code")
                part.categorisation = data.get("categorisation")
                part.routing_link_code = data.get("routing_link_code")
                part.part_status = data.get("part_status")
                part.save()
                
                return JsonResponse({"status": "success", "message": "Done"})
                
            elif action in ["copy_bom_table", "copy_bom_trans", "paste_bom_trans"]:
                # Mock implementation for copying and pasting
                return JsonResponse({"status": "success", "message": "Done"})
                
            elif action == "complete":
                bom_creation_id = data.get("bom_creation_id")
                if not bom_creation_id:
                    return JsonResponse({"status": "error", "message": "Missing bom_creation_id"}, status=400)
                
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    header.action_status = "COMPLETED"
                    header.save()
                    return JsonResponse({"status": "success", "message": "Done"})
                return JsonResponse({"status": "error", "message": "Header not found"}, status=404)
                
            elif action == "download":
                bom_creation_id = data.get("bom_creation_id")
                if not bom_creation_id:
                    return JsonResponse({"status": "error", "message": "Missing bom_creation_id"}, status=400)
                
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = f'attachment; filename="bom_{header.bom_creation_id}.csv"'
                    writer = csv.writer(response)
                    writer.writerow(['Entry Type', 'Part Number', 'Quantity', 'Description', 'UOM Code', 'Categorisation', 'Routing Link Code', 'Part Status'])
                    for part in BOMTransaction.objects.filter(bom_creation_id=bom_creation_id):
                        writer.writerow([part.entry_type, part.part_number, part.quantity, part.description, part.uom_code, part.categorisation, part.routing_link_code, part.part_status])
                    return response
                return JsonResponse({"status": "error", "message": "Header not found"}, status=404)
                
            return JsonResponse({"status": "error", "message": "Unknown action"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

from apps.item_creation.models import ItemCard
from .models import BOMItemList, BOMProdItemPartGrpMaster

# ---------------------------------------------------------------------------
# Module-level date formatter — shared by all BOM views
# ---------------------------------------------------------------------------
def _fmt_date(d):
    """Return d formatted as 'DD-Mon-YY', or '' if falsy."""
    if not d:
        return ""
    if isinstance(d, (date, datetime)):
        return d.strftime("%d-%b-%y")
    if isinstance(d, str):
        d_str = d.strip()
        for fmt in ("%Y-%m-%d", "%d-%b-%y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(d_str, fmt).strftime("%d-%b-%y")
            except ValueError:
                pass
        return d_str
    try:
        return d.strftime("%d-%b-%y")
    except Exception:
        return str(d)

def bom_get_autofill_data(request):
    """
    Called when a Customer ID is selected or an Item Creation ID is chosen.
    Fetches matching Item Creation IDs from tbl_itemcard.
    Also returns ECN data (No_Of_MEFT, No_Of_Parts, Fixture_No, Customer_Name, Last ECN No)
    from the latest record in tbl_itemcard_ecn for each item.
    """
    customer_id = request.GET.get("customer_id", "").strip()
    item_no = request.GET.get("item_no", "").strip()

    try:
        today_str = date.today().strftime("%d-%b-%y")

        # ------------------------------------------------------------------ #
        #  item_no branch — called when user picks an Item Creation ID
        # ------------------------------------------------------------------ #
        if item_no:
            # -------------------------------------------------------------- #
            #  Normalize item_no to handle leading-zero mismatches between
            #  the UI, tbl_itemcard, tbl_itemcard_ecn, and tbl_bomcreation.
            #  The legacy desktop tool may store "00012345", "12345", or
            #  "ITEM-XYZ" — we try all plausible variants in every query.
            # -------------------------------------------------------------- #
            item_no_clean  = item_no.strip()
            item_no_padded = item_no_clean.zfill(8) if item_no_clean.isdigit() else item_no_clean
            item_no_lstrip = item_no_clean.lstrip('0') or item_no_clean  # guard against all-zero string

            def _item_q(field):
                """Return a Q expression matching any of the three variants on `field`."""
                variants = {item_no_clean, item_no_padded, item_no_lstrip}
                q = Q(**{field: item_no_clean})
                for v in variants - {item_no_clean}:
                    q |= Q(**{field: v})
                return q

            # 1. Query ECN — match on 'No' OR 'no_2', across all variants
            ecn = (
                ItemCardECN.objects
                .filter(_item_q('no') | _item_q('no_2'))
                .first()
            )

            # Resolve last_ecn_no; fall back to the latest record that has
            # a non-blank ecn_id when the primary hit is missing it.
            last_ecn_no = ''
            if ecn and ecn.ecn_id:
                last_ecn_no = ecn.ecn_id
            else:
                fallback_ecn = (
                    ItemCardECN.objects
                    .filter(
                        (_item_q('no') | _item_q('no_2'))
                        & ~Q(ecn_id__isnull=True)
                        & ~Q(ecn_id='')
                    )
                    .first()
                )
                if fallback_ecn:
                    last_ecn_no = fallback_ecn.ecn_id or ''

            # Retrieve fallback details from ItemCard if needed
            item_card = (
                ItemCard.objects
                .filter(_item_q('no'))
                .first()
            )

            try:
                meft_val = int(ecn.no_of_meft or 0) if ecn else 0
            except (ValueError, TypeError):
                meft_val = 0
            try:
                parts_val = int(ecn.no_of_parts or 0) if ecn else 0
            except (ValueError, TypeError):
                parts_val = 0

            ecn_data = {
                "no_of_meft":    str(meft_val),
                "no_of_parts":   str(parts_val),
                "fixture_no":    (ecn.fixture_no    if ecn and ecn.fixture_no    else (getattr(item_card, 'fixture', '')                  or '')),
                "customer_id":   (ecn.customer_id   if ecn and ecn.customer_id   else (getattr(item_card, 'customer_id', '')              or '')),
                "customer_name": (ecn.customer_name if ecn and ecn.customer_name else ''),
                "last_ecn_no":   last_ecn_no,
                "status":        (ecn.status        if ecn and ecn.status        else ''),
                "description":   (ecn.description   if ecn and ecn.description   else (getattr(item_card, 'description', '')             or '')),
                "uom_code":      (ecn.base_unit_of_measure if ecn and ecn.base_unit_of_measure else (getattr(item_card, 'base_unit_of_measure', '') or '')),
            }

            # 2. Query BOM Header — try all three item_no variants
            bom_header = (
                BOMHeader.objects
                .filter(_item_q('item_creation_id'))
                .first()
            )
            if bom_header:
                bom_cid = bom_header.bom_creation_id or ''
                meft_count  = BOMTransaction.objects.filter(bom_creation_id=bom_cid, entry_type='MEFT').count() if bom_cid else 0
                parts_count = BOMTransaction.objects.filter(bom_creation_id=bom_cid).count() if bom_cid else 0
                bom_data = {
                    "bom_creation_id":    bom_cid,
                    "table_id":           bom_header.table_id or str(bom_header.id),
                    "last_date_modified": _fmt_date(bom_header.last_date_modified) or today_str,
                    "action_status":      bom_header.action_status or 'Pending',
                    "description":        bom_header.description or ecn_data["description"],
                    "uom_code":           bom_header.uom_code or ecn_data["uom_code"],
                    "no_of_meft":         str(meft_count),
                    "no_of_parts":        str(parts_count),
                }
            else:
                # No saved BOM yet — check ECN status for a better default
                ecn_status_default = ecn_data["status"] or 'Pending'
                bom_data = {
                    "bom_creation_id":    '',
                    "table_id":           '0',
                    "last_date_modified": today_str,
                    "action_status":      ecn_status_default,
                    "description":        ecn_data["description"],
                    "uom_code":           ecn_data["uom_code"],
                    "no_of_meft":         '0',
                    "no_of_parts":        '0',
                }

            return JsonResponse({"ecn_data": ecn_data, "bom_data": bom_data})

        # ------------------------------------------------------------------ #
        #  customer_id branch — populate Item Creation ID dropdown
        # ------------------------------------------------------------------ #
        if customer_id:
            # Sort by 'no'; cast to str to preserve any leading zeros stored
            # as text in the DB (VARCHAR columns are fine; INT columns won't
            # have leading zeros in storage but str() keeps them visually).
            items = list(
                ItemCard.objects
                .filter(customer_id=customer_id)
                .order_by('no')
                .values("no", "description", "base_unit_of_measure", "fixture")
            )
            # Ensure item numbers are serialised as strings
            for it in items:
                it['no'] = str(it['no']) if it['no'] is not None else ''
            return JsonResponse({"items": items})

        return JsonResponse({"items": []})

    except Exception as e:
        import traceback
        traceback.print_exc()   # full stack trace in the Django console
        return JsonResponse({"error": str(e), "ecn_data": {}, "bom_data": {}}, status=500)

def bom_get_part_statuses(request):
    """
    Returns distinct Part_Status values from tbl_bom_partdetails_master.
    Used to populate the part_status dropdown dynamically.
    """
    try:
        statuses = list(
            BOMPartDetailsMaster.objects
            .exclude(part_status__isnull=True)
            .exclude(part_status__exact='')
            .values_list('part_status', flat=True)
            .distinct()
            .order_by('part_status')
        )
        return JsonResponse({"statuses": statuses})
    except Exception as e:
        return JsonResponse({"statuses": ["Approved", "Rejected", "Pending for Approval"]})

def bom_get_part_data(request):

    """
    Fetches part lists and details based on Entry Type.
    If part_no is provided, returns that part's details.
    """
    entry_type = request.GET.get("entry_type", "").strip()
    part_no = request.GET.get("part_no", "").strip()
    
    if entry_type == "Item":
        if part_no:
            part = BOMPartDetailsMaster.objects.filter(part_no=part_no).first()
            if part:
                return JsonResponse({
                    "description": part.part_description or "",
                    "uom_code": part.base_unit_of_measure or "",
                    "categorisation": part.categorisation or "",
                    "part_status": part.part_status or ""
                })
            return JsonResponse({"error": "Not found"})
        else:
            # The table has multiple rows per part_no (one per customer).
            # Use DISTINCT ON part_no to show each part only once.
            from django.db.models import Max
            # Get unique part_nos with their first description/uom/cat/status
            parts_qs = (
                BOMPartDetailsMaster.objects
                .values("part_no", "part_description", "base_unit_of_measure", "categorisation", "part_status")
                .distinct()
                .order_by("part_no", "part_description")
            )
            # Deduplicate by part_no — keep first occurrence
            seen = set()
            parts = []
            for row in parts_qs:
                pno = row["part_no"]
                if pno not in seen:
                    seen.add(pno)
                    parts.append(row)
            return JsonResponse({"parts": parts})
            
    elif entry_type == "Production BOM":
        try:
            if part_no:
                part = BOMProdItemPartGrpMaster.objects.filter(grp_part_no=part_no).first()
                if part:
                    return JsonResponse({
                        "description": part.grp_part_description or ""
                    })
                return JsonResponse({"error": "Not found"})
            else:
                parts = list(BOMProdItemPartGrpMaster.objects.values("grp_part_no", "grp_part_description"))
                return JsonResponse({"parts": parts})
        except Exception as e:
            # Table may not exist in all deployments — return empty list
            return JsonResponse({"parts": [], "error": str(e)})

    return JsonResponse({"parts": []})
@csrf_exempt

def bom_ecn_columns(request):
    """Temporary debug view for ECN columns.
    Returns placeholder JSON data.
    """
    data = {
        "columns": [
            {"name": "No_of_MeFT", "type": "string"},
            {"name": "No_of_Parts", "type": "string"},
            {"name": "Fixture_No", "type": "string"},
            {"name": "Customer_Name", "type": "string"},
            {"name": "Last_ECN_No", "type": "string"},
        ]
    }
    return JsonResponse({"status": "success", "data": data})

# -------------------------------------------------------------------------
# BOM STEP 1 CRUD ENDPOINTS (Match BOP exactly)
# -------------------------------------------------------------------------

@csrf_exempt
@require_active_customer
def save_bom_form(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        item_id = data.get("item_creation_id", "").strip()
        if not item_id:
            return JsonResponse({"error": "Item Creation ID is required"}, status=400)

        # User-supplied BOM Creation ID (never auto-generated)
        bom_creation_id = data.get("bom_creation_id", "").strip()
        selected_customer_id = request.active_customer.get('id') if hasattr(request, "active_customer") and request.active_customer else ""

        bom_record = None
        if bom_creation_id:
            bom_record = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()

        is_new = bom_record is None
        today = date.today()

        if is_new:
            # --- Guard: only 1 BOM per Item Creation ID ---
            existing = BOMHeader.objects.filter(item_creation_id=item_id).first()
            if existing:
                return JsonResponse({
                    "error": (
                        f"Action Blocked: Item Creation ID '{item_id}' already has an active BOM "
                        f"({existing.bom_creation_id}). Only 1 BOM per Item ID is allowed."
                    )
                }, status=400)

            # --- Require a user-supplied BOM Creation ID ---
            if not bom_creation_id:
                return JsonResponse(
                    {"error": "BOM Creation ID is required. Please enter a BOM ID before creating."},
                    status=400
                )

            # CREATE
            bom_record = BOMHeader(item_creation_id=item_id)
            bom_record.bom_creation_id = bom_creation_id

            # Fix NULL PK on unmanaged legacy table: compute next_id explicitly
            # (no PostgreSQL sequence is attached to tbl_bomcreation)
            from django.db.models import Max as _Max
            max_id = BOMHeader.objects.aggregate(max_id=_Max('id'))['max_id']
            bom_record.id = (max_id or 0) + 1

            # bom_row_id — incremental per (item_id, customer)
            max_row = BOMHeader.objects.filter(
                item_creation_id=item_id,
                customer_id=selected_customer_id
            ).aggregate(max_row=_Max("bom_row_id"))["max_row"]
            try:
                int_bom_row_id = int(max_row or 0) + 1
            except (ValueError, TypeError):
                int_bom_row_id = 1
            bom_record.bom_row_id = int_bom_row_id

            # table_id — incremental per item_id
            max_table = BOMHeader.objects.filter(
                item_creation_id=item_id
            ).aggregate(max_table=_Max("table_id"))["max_table"]
            try:
                bom_record.table_id = str(int(max_table or 0) + 1)
            except (TypeError, ValueError):
                bom_record.table_id = "1"

            bom_record.action_status = "Created"
            bom_record.create_date = today
        else:
            # EDIT
            if bom_record.action_status == "Approved":
                return JsonResponse({"error": "Action Blocked: Approved BOM records cannot be edited."}, status=400)

            form_status = data.get("action_status", "").strip()
            bom_record.action_status = form_status if form_status else "Updated"

        bom_record.customer_id = selected_customer_id
        bom_record.description = data.get("description", "")
        bom_record.uom_code = data.get("uom_code", "")
        bom_record.last_date_modified = today

        bom_record.save()

        return JsonResponse({
            "status": "success",
            "message": "BOM configuration created successfully!" if is_new else "BOM configuration saved successfully!",
            "table_id": bom_record.table_id,
            "bom_creation_id": bom_record.bom_creation_id,
            "action_status": bom_record.action_status,
            "last_date_modified": bom_record.last_date_modified.strftime('%d-%b-%y') if bom_record.last_date_modified else today.strftime('%d-%b-%y')
        })

    except Exception as e:
        import traceback
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


@csrf_exempt
@require_active_customer
def delete_bom_form(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bom_id = data.get("bom_creation_id", "").strip()
        if not bom_id:
            return JsonResponse({"error": "BOM Creation ID is required"}, status=400)
            
        header = BOMHeader.objects.filter(bom_creation_id=bom_id).first()
        if header:
            header.delete()
            BOMTransaction.objects.filter(bom_creation_id=bom_id).delete()
            
        return JsonResponse({"status": "success", "message": f"BOM Record {bom_id} has been successfully deleted."})
    except Exception as e:
        import traceback
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


@csrf_exempt
@require_active_customer
def send_bom_approval(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        from .services import process_send_approval
        from django.core.exceptions import ValidationError
        from django.contrib import messages
        
        is_json = request.content_type == 'application/json' or 'json' in request.META.get('HTTP_ACCEPT', '')
        
        if request.content_type == 'application/json':
            data = json.loads(request.body or '{}')
            bom_id = data.get("bom_creation_id", "").strip()
        else:
            bom_id = request.POST.get("bom_creation_id", "").strip()
            
        if not bom_id:
            msg = "BOM Creation ID is required."
            if is_json:
                return JsonResponse({"error": msg}, status=400)
            messages.error(request, msg)
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        header = BOMHeader.objects.filter(bom_creation_id=bom_id).first()
        if not header:
            msg = "Action Blocked: BOM Record not found."
            if is_json:
                return JsonResponse({"error": msg}, status=404)
            messages.error(request, msg)
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        # Process approval using the dedicated service with user tracking and ECN integration checks
        try:
            header = process_send_approval(
                instance=header, 
                user=request.user if hasattr(request, 'user') else None,
                transaction_model=BOMTransaction, 
                transaction_fk_kwargs={'bom_creation_id': bom_id}
            )
        except ValidationError as ve:
            error_msg = ve.message if hasattr(ve, 'message') else str(ve)
            if is_json:
                return JsonResponse({"error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        success_msg = f"BOM Record '{bom_id}' sent for approval successfully."
        messages.success(request, success_msg)
        
        return JsonResponse({
            "status": "success", 
            "message": success_msg,
            "action_status": header.action_status,
            "is_locked": True,
            "last_date_modified": header.last_date_modified.strftime('%d-%b-%y') if header.last_date_modified else ''
        })
    except Exception as e:
        import traceback
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)



@csrf_exempt
@require_active_customer
def ecn_bom(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
    try:
        data = json.loads(request.body)
        bom_id = data.get("bom_creation_id", "").strip()
        if not bom_id:
            return JsonResponse({"error": "BOM Creation ID is required"}, status=400)
            
        header = BOMHeader.objects.filter(bom_creation_id=bom_id).first()
        if not header:
            return JsonResponse({"error": "Action Blocked: BOM Record not found."}, status=404)
            
        header.action_status = "ECN"
        header.last_date_modified = date.today()
        header.save()
        
        return JsonResponse({
            "status": "success", 
            "message": "BOM Record transitioned to ECN successfully.",
            "action_status": header.action_status,
            "last_date_modified": header.last_date_modified.strftime('%d-%b-%y')
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_bom_details(request):
    bom_creation_id = request.GET.get("bom_creation_id", "").strip()
    if not bom_creation_id:
        return JsonResponse({"error": "Missing bom_creation_id"}, status=400)
        
    header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
    if not header:
        return JsonResponse({"error": "Record not found"}, status=404)
        
    def fmt_date(d):
        if not d:
            return ""
        if isinstance(d, (date, datetime)):
            return d.strftime("%d-%b-%y")
        if isinstance(d, str):
            d_str = d.strip()
            for fmt in ("%Y-%m-%d", "%d-%b-%y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                try:
                    return datetime.strptime(d_str, fmt).strftime("%d-%b-%y")
                except ValueError:
                    pass
            return d_str
        return str(d)
        
    # Fetch ECN fields
    item_no = header.item_creation_id or ""
    ecn_fixture_no = ""
    ecn_customer_name = ""
    ecn_last_ecn_no = ""
    if item_no:
        _ic = item_no.strip()
        _ip = _ic.zfill(8) if _ic.isdigit() else _ic
        _il = _ic.lstrip('0') or _ic
        ecn_edit = (
            ItemCardECN.objects
            .filter(Q(no=_ic) | Q(no=_ip) | Q(no=_il) | Q(no_2=_ic) | Q(no_2=_ip) | Q(no_2=_il))
            .first()
        )
        if ecn_edit:
            ecn_fixture_no    = ecn_edit.fixture_no    or ""
            ecn_customer_name = ecn_edit.customer_name or ""
            ecn_last_ecn_no   = ecn_edit.ecn_id        or ""

    live_meft  = BOMTransaction.objects.filter(bom_creation_id=bom_creation_id, entry_type='MEFT').count()
    live_parts = BOMTransaction.objects.filter(bom_creation_id=bom_creation_id).count()
    
    raw_status = header.action_status or ""
    status_map = {
        "SEND_APPROVAL": "Sent for Approval",
        "SENT_APPROVAL": "Sent for Approval",
        "COMPLETED":     "Completed",
        "ECN":           "ECN",
        "APPROVED":      "Approved",
        "REJECTED":      "Rejected",
    }
    clean_status = status_map.get(raw_status.upper(), raw_status)

    return JsonResponse({
        "item_creation_id":   header.item_creation_id or "",
        "bom_creation_id":    header.bom_creation_id or "",
        "description":        header.description or "",
        "uom_code":           header.uom_code or "",
        "fixture_no":         ecn_fixture_no,
        "no_of_meft":         str(live_meft),
        "no_of_parts":        str(live_parts),
        "last_ecn_no":        ecn_last_ecn_no,
        "action_status":      clean_status,
        "last_date_modified": fmt_date(header.last_date_modified),
        "table_id":           header.table_id or str(header.id),
        "create_date":        fmt_date(header.create_date),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint 1: validate_production_bom_part
# ─────────────────────────────────────────────────────────────────────────────
@csrf_exempt
def validate_production_bom_part(request):
    """
    GET: ?entry_type=<>&part_number=<>
    Checks BOMProdItemPartGrpMaster and BomProdItemPartGrpMasterRawData.
    Returns {show_modal: true, grp_part_no, grp_part_description, items: [...]}
    with details for each child item in the group.
    """
    entry_type = request.GET.get("entry_type", "").strip()
    part_number = request.GET.get("part_number", "").strip()

    if entry_type != "Production BOM" or not part_number:
        return JsonResponse({"show_modal": False})

    child_rows = list(
        BOMProdItemPartGrpMaster.objects.filter(
            grp_part_no__iexact=part_number
        ).order_by("level", "row_id")
    )

    if not child_rows:
        raw_rows = list(
            BomProdItemPartGrpMasterRawData.objects.filter(
                grp_partno__iexact=part_number
            ).order_by("level")
        )
        if not raw_rows:
            return JsonResponse({"show_modal": False})

        grp_no = raw_rows[0].grp_partno or part_number
        grp_desc = raw_rows[0].grp_part_description or ""

        part_nos = [r.part_no for r in raw_rows if r.part_no]
        details_map = {}
        if part_nos:
            details_qs = BOMPartDetailsMaster.objects.filter(part_no__in=part_nos)
            for d in details_qs:
                if d.part_no not in details_map:
                    details_map[d.part_no] = d

        items = []
        for r in raw_rows:
            d = details_map.get(r.part_no)
            items.append({
                "level": r.level or 1,
                "part_no": r.part_no or "",
                "description": (d.part_description if d and d.part_description else r.part_description) or "",
                "uom": (d.base_unit_of_measure if d and d.base_unit_of_measure else r.unit_of_measure) or "",
                "categorisation": (d.categorisation if d and d.categorisation else "Local BOC"),
                "part_status": (d.part_status if d and d.part_status else "Approved"),
                "total_bom_quantity": float(r.total_bom_quantity or r.bom_quantity or 1),
            })

        return JsonResponse({
            "show_modal": True,
            "modal_id": "frm_BOM_ProdItem_GrpPart_Selected",
            "grp_part_no": grp_no,
            "grp_part_description": grp_desc,
            "items": items,
        })

    grp_no = child_rows[0].grp_part_no or part_number
    grp_desc = child_rows[0].grp_part_description or ""

    part_nos = [r.part_no for r in child_rows if r.part_no]
    details_map = {}
    if part_nos:
        details_qs = BOMPartDetailsMaster.objects.filter(part_no__in=part_nos)
        for d in details_qs:
            if d.part_no not in details_map:
                details_map[d.part_no] = d

    items = []
    for r in child_rows:
        d = details_map.get(r.part_no)
        items.append({
            "level": r.level or 1,
            "part_no": r.part_no or "",
            "description": (d.part_description if d and d.part_description else r.part_description) or "",
            "uom": (d.base_unit_of_measure if d and d.base_unit_of_measure else r.unit_of_measure) or "",
            "categorisation": (d.categorisation if d and d.categorisation else "Local BOC"),
            "part_status": (d.part_status if d and d.part_status else "Approved"),
            "total_bom_quantity": float(r.total_bom_quantity or r.bom_quantity or 1),
        })

    return JsonResponse({
        "show_modal": True,
        "modal_id": "frm_BOM_ProdItem_GrpPart_Selected",
        "grp_part_no": grp_no,
        "grp_part_description": grp_desc,
        "items": items,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint 2: save_bom_line_item
# ─────────────────────────────────────────────────────────────────────────────
@csrf_exempt
def save_bom_line_item(request):
    """
    POST JSON body with line-item fields.
    If `part_id` is provided, update that BOMTransaction row.
    Otherwise create a new row, assigning the next table_id safely.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)

    bom_creation_id = data.get("bom_creation_id", "").strip()
    if not bom_creation_id:
        return JsonResponse({"status": "error", "message": "bom_creation_id is required"}, status=400)

    part_id = data.get("part_id")  # None → create, int → update

    # Safely compute the next integer table_id across ALL transactions
    agg = BOMTransaction.objects.annotate(
        tid_int=Cast("table_id", output_field=DjIntegerField())
    ).aggregate(max_tid=Max("tid_int"))
    next_tid = str((agg["max_tid"] or 0) + 1)

    qty_raw = data.get("quantity", 0)
    try:
        quantity = float(qty_raw) if qty_raw not in (None, "") else 0.0
    except (ValueError, TypeError):
        quantity = 0.0

    fields = dict(
        bom_creation_id=bom_creation_id,
        entry_type=data.get("entry_type", ""),
        part_number=data.get("part_number", ""),
        quantity=quantity,
        description=data.get("description", ""),
        uom_code=data.get("uom_code", ""),
        categorisation=data.get("categorisation", ""),
        routing_link_code=data.get("routing_link_code", ""),
        part_status=data.get("part_status", ""),
        grp_part_no=data.get("grp_part_no", ""),
        grp_part_descp=data.get("grp_part_descp", ""),
        start_date=data.get("start_date", ""),
    )

    if part_id:
        updated = BOMTransaction.objects.filter(pk=part_id).update(**fields)
        if not updated:
            return JsonResponse({"status": "error", "message": "Part not found"}, status=404)
        return JsonResponse({"status": "success", "message": "Line item updated", "part_id": part_id})
    else:
        fields["table_id"] = next_tid
        fields["id"] = _next_bom_trans_id()
        obj = BOMTransaction.objects.create(**fields)
        return JsonResponse({"status": "success", "message": "Line item saved", "part_id": obj.pk, "table_id": next_tid})


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint 3: create_copy
# ─────────────────────────────────────────────────────────────────────────────
@csrf_exempt
def create_copy(request):
    """
    POST JSON: {"source_bom_id": "...", "target_bom_id": "..."}
    Duplicates all BOMTransaction rows from source to target using bulk_create.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError) as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)

    source_bom_id = data.get("source_bom_id", "").strip()
    target_bom_id = data.get("target_bom_id", "").strip()

    if not source_bom_id or not target_bom_id:
        return JsonResponse({"status": "error", "message": "source_bom_id and target_bom_id are required"}, status=400)

    if source_bom_id == target_bom_id:
        return JsonResponse({"status": "error", "message": "source and target BOM IDs must be different"}, status=400)

    source_rows = BOMTransaction.objects.filter(bom_creation_id=source_bom_id)
    if not source_rows.exists():
        return JsonResponse({"status": "error", "message": f"No transactions found for source BOM: {source_bom_id}"}, status=404)

    # Compute starting table_id for new copies
    agg = BOMTransaction.objects.annotate(
        tid_int=Cast("table_id", output_field=DjIntegerField())
    ).aggregate(max_tid=Max("tid_int"))
    base_tid = (agg["max_tid"] or 0) + 1

    new_rows = []
    for i, row in enumerate(source_rows):
        new_rows.append(BOMTransaction.objects.create(
            id=_next_bom_trans_id(),
            bom_creation_id=target_bom_id,
            entry_type=row.entry_type,
            part_number=row.part_number,
            quantity=row.quantity,
            description=row.description,
            uom_code=row.uom_code,
            categorisation=row.categorisation,
            routing_link_code=row.routing_link_code,
            part_status=row.part_status,
            grp_part_no=row.grp_part_no,
            grp_part_descp=row.grp_part_descp,
            start_date=row.start_date,
            table_id=str(base_tid + i),
        ))

    return JsonResponse({
        "status": "success",
        "message": f"{len(new_rows)} transaction(s) copied from {source_bom_id} to {target_bom_id}",
        "copied_count": len(new_rows),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Part Details Master — dropdown options & create (mirrors Access frm_BOM_PartDetails_Master)
# ─────────────────────────────────────────────────────────────────────────────

def get_part_master_dropdowns(request):
    """
    Returns distinct values for the Part Details Master form dropdowns:
    base_unit_of_measure, customer, classification, categorisation.
    """
    def distinct_values(field):
        return sorted(
            BOMPartDetailsMaster.objects
            .exclude(**{f'{field}__isnull': True})
            .exclude(**{f'{field}__exact': ''})
            .values_list(field, flat=True)
            .distinct()
        )

    return JsonResponse({
        "base_units": distinct_values("base_unit_of_measure"),
        "customers": distinct_values("customer"),
        "classifications": distinct_values("classification"),
        "categorisations": distinct_values("categorisation"),
    })


@csrf_exempt
def create_part_master(request):
    """
    Creates a new record in tbl_bom_partdetails_master.
    Mirrors the VBA btn_Create_Click logic from frm_BOM_PartDetails_Master.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    part_no = (data.get("part_no") or "").strip()
    part_description = (data.get("part_description") or "").strip()
    base_unit_of_measure = (data.get("base_unit_of_measure") or "").strip()
    customer = (data.get("customer") or "").strip() or "NA"
    classification = (data.get("classification") or "").strip()
    cost_price = data.get("cost_price", 0)
    settle_price = data.get("settle_price", 0)
    categorisation = (data.get("categorisation") or "").strip()
    part_status = (data.get("part_status") or "").strip() or "Sent for approval"

    # Required field validations (same as VBA logic)
    if not part_no:
        return JsonResponse({"status": "error", "message": "Please add Part No and try again."}, status=400)
    if not part_description:
        return JsonResponse({"status": "error", "message": "Please add Part Description and try again."}, status=400)
    if not base_unit_of_measure:
        return JsonResponse({"status": "error", "message": "Please add Base Unit of Measure and try again."}, status=400)
    if not classification:
        return JsonResponse({"status": "error", "message": "Please add Classification and try again."}, status=400)
    if not categorisation:
        return JsonResponse({"status": "error", "message": "Please add Categorisation and try again."}, status=400)

    # Duplicate check (same as VBA DLookup)
    if BOMPartDetailsMaster.objects.filter(part_no=part_no).exists():
        return JsonResponse({
            "status": "error",
            "message": "Mentioned part number already exists in the database!"
        }, status=409)

    # Convert prices safely
    try:
        cost_price = float(cost_price) if cost_price else 0
    except (ValueError, TypeError):
        cost_price = 0
    try:
        settle_price = float(settle_price) if settle_price else 0
    except (ValueError, TypeError):
        settle_price = 0

    # Insert via raw SQL since model is managed=False with a composite-like PK
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO tbl_bom_partdetails_master
                ("Part No", "Part Description", "Base Unit of Measure",
                 "Customer", "Classification", "Cost_Price", "Settle Price",
                 "Categorisation", "Part_Status", "Part_Type")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            part_no, part_description, base_unit_of_measure,
            customer, classification, cost_price, settle_price,
            categorisation, part_status, "New"
        ])

    return JsonResponse({
        "status": "success",
        "message": "Part record saved!",
        "part": {
            "part_no": part_no,
            "part_description": part_description,
            "base_unit_of_measure": base_unit_of_measure,
            "categorisation": categorisation,
            "part_status": part_status,
        }
    })

# ─────────────────────────────────────────────────────────────────────────────
# Copy/Paste Transactions Session Data
# ─────────────────────────────────────────────────────────────────────────────

from django.views.decorators.http import require_POST

@require_POST
def copy_bom_trans(request):
    """
    Saves the BOM's transactions to the user's session so they can be pasted elsewhere.
    """
    try:
        data = json.loads(request.body)
        bom_id = data.get('bom_id')
        if not bom_id:
            return JsonResponse({'status': 'error', 'message': 'bom_id is required'})
            
        items = BOMTransaction.objects.filter(bom_creation_id=bom_id)
        
        copied_items = []
        for item in items:
            copied_items.append({
                'entry_type': item.entry_type,
                'part_number': item.part_number,
                'quantity': float(item.quantity) if item.quantity is not None else 0,
                'description': item.description,
                'uom_code': item.uom_code,
                'categorisation': item.categorisation,
                'routing_link_code': item.routing_link_code,
                'part_status': item.part_status,
            })
            
        request.session['copied_bom_trans'] = copied_items
        return JsonResponse({'status': 'success', 'message': f'{len(copied_items)} transactions copied!'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
def paste_bom_trans(request):
    """
    Pastes the copied BOM transactions from the session to a target BOM.
    """
    try:
        data = json.loads(request.body)
        target_bom_id = data.get('target_bom_id')
        if not target_bom_id:
            return JsonResponse({'status': 'error', 'message': 'target_bom_id is required'}, status=400)
            
        copied_items = request.session.get('copied_bom_trans')
        if not copied_items:
            return JsonResponse({'status': 'error', 'message': 'No copied transactions found in session. Please copy first.'}, status=400)
            
        # Compute starting table_id for new copies
        agg = BOMTransaction.objects.annotate(
            tid_int=Cast("table_id", output_field=DjIntegerField())
        ).aggregate(max_tid=Max("tid_int"))
        base_tid = (agg["max_tid"] or 0) + 1
        
        new_rows = []
        for i, item in enumerate(copied_items):
            new_rows.append(BOMTransaction.objects.create(
                id=_next_bom_trans_id(),
                bom_creation_id=target_bom_id,
                entry_type=item.get('entry_type'),
                part_number=item.get('part_number'),
                quantity=item.get('quantity', 0),
                description=item.get('description'),
                uom_code=item.get('uom_code'),
                categorisation=item.get('categorisation'),
                routing_link_code=item.get('routing_link_code'),
                part_status=item.get('part_status'),
                table_id=str(base_tid + i),
            ))
            
        return JsonResponse({'status': 'success', 'message': f'{len(new_rows)} transactions pasted successfully!'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
