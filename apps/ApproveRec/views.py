import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import connection
from config.decorators import require_active_customer


@require_active_customer
def ApproveRec_form(request):
    return render(request, "ApproveRec/ApproveRec_form.html")


# Helper function to query with fallback for joins / case matching
def _execute_query(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        cols = [d[0] for d in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
    return cols, rows


# ------------------------------------------------------------------
# API: GET distinct Customer IDs from qry_BomSendForApproval
# SELECT DISTINCT Customer_ID FROM qry_BomSendForApproval;
# ------------------------------------------------------------------
@require_active_customer
def get_approve_customers(request):
    # Only show customers who still have BOM records pending approval.
    cols, rows = _execute_query("""
        SELECT DISTINCT "Customer_ID"
        FROM tbl_bomcreation
        WHERE "Customer_ID" IS NOT NULL
          AND LOWER(TRIM(COALESCE("Remark", "Status", ''))) = 'sent for approval'
        ORDER BY "Customer_ID"
    """)
    customers = [r[0] for r in rows if r[0]]
    return JsonResponse({'customers': customers})


# ------------------------------------------------------------------
# API: GET distinct ItemCreation_Id for a given Customer_ID
# ------------------------------------------------------------------
@require_active_customer
def get_approve_items(request):
    customer_id = request.GET.get('customer_id', '').strip()
    if not customer_id:
        return JsonResponse({'items': []})

    # Return ALL distinct items for this customer (remark filtering is shown per-row in the grid)
    cols, rows = _execute_query("""
        SELECT DISTINCT "ItemCreation_Id"
        FROM tbl_bomcreation
        WHERE "Customer_ID" = %s AND "ItemCreation_Id" IS NOT NULL
        ORDER BY "ItemCreation_Id"
    """, [customer_id])
    items = [r[0] for r in rows if r[0] is not None]

    return JsonResponse({'items': items})


# ------------------------------------------------------------------
# API: GET distinct BOMCreation_Id for a given Customer_ID + ItemCreation_Id
# ------------------------------------------------------------------
@require_active_customer
def get_approve_bom_ids(request):
    customer_id = request.GET.get('customer_id', '').strip()
    item_id = request.GET.get('item_id', '').strip()
    if not customer_id:
        return JsonResponse({'bom_ids': []})

    sql = """
        SELECT DISTINCT c."BOMCreation_Id"
        FROM tbl_bomcreation c
        WHERE c."Customer_ID" = %s
    """
    params = [customer_id]
    if item_id:
        sql += ' AND (c."ItemCreation_Id" = %s OR c."ItemCreation_Id" IS NULL)'
        params.append(item_id)

    sql += ' ORDER BY c."BOMCreation_Id"'
    cols, rows = _execute_query(sql, params)
    bom_ids = [r[0] for r in rows if r[0] is not None]

    return JsonResponse({'bom_ids': bom_ids})


# ------------------------------------------------------------------
# API: GET BOM part lines for selected Customer + Item + BOM Creation ID
# ------------------------------------------------------------------
@require_active_customer
def get_approve_bom_lines(request):
    customer_id = request.GET.get('customer_id', '').strip()
    item_id = request.GET.get('item_id', '').strip()
    bom_id = request.GET.get('bom_id', '').strip()

    if not customer_id:
        return JsonResponse({'records': []})

    try:
        # SELECT DISTINCT fields matching qry_BomSendForApproval (header + part selection details)
        sql = """
            SELECT DISTINCT
                c."Customer_ID",
                COALESCE(c."ItemCreation_Id", '') AS "ItemCreation_Id",
                COALESCE(c."BOMCreation_Id", '')  AS "BOMCreation_Id",
                c."Table_Id",
                p."Entry_Type",
                p."Part_Number",
                p."Quantity",
                COALESCE(p."Description", c."Description") AS part_description,
                COALESCE(p."Unit_of_Measure_Code", c."Unit_of_Measure_Code") AS part_uom,
                p."Categorisation",
                p."Routing_Link_Code",
                p."start_date",
                p."Part_Status",
                c."Description" AS header_description,
                c."Description_2",
                c."Search_Name",
                c."Low-Level Code",
                c."Creation_Date",
                c."Last_Date_Modified",
                c."Status",
                c."Series",
                c."Version_Number",
                c."Remark"
            FROM tbl_bomcreation c
            LEFT JOIN tbl_bomcreation_partselection p
                ON p."BOMCreation_ID" = c."BOMCreation_Id"
            WHERE c."Customer_ID" = %s
              AND LOWER(TRIM(COALESCE(c."Remark", c."Status", ''))) = 'sent for approval'
        """
        params = [customer_id]

        if item_id:
            sql += ' AND c."ItemCreation_Id" = %s'
            params.append(item_id)

        if bom_id:
            sql += ' AND c."BOMCreation_Id" = %s'
            params.append(bom_id)

        cols, rows = _execute_query(sql, params)

        records = []
        for row in rows:
            rec = dict(zip(cols, row))
            for k, v in rec.items():
                if hasattr(v, 'isoformat'):
                    rec[k] = v.isoformat()
            records.append(rec)

        return JsonResponse({'records': records})
    except Exception as e:
        print("[get_approve_bom_lines Error]:", e)
        return JsonResponse({'records': [], 'error': str(e)})


# ------------------------------------------------------------------
# API: POST — save action status (Approved / Rejected / Sent for approval)
# Updates BOTH "Status" (read by BOM form as action_status) AND "Remark"
# so the BOM Creation page correctly reflects the approval decision.
# ------------------------------------------------------------------
@csrf_exempt
@require_POST
@require_active_customer
def save_approve_action(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    bom_id = body.get('bom_id', '').strip()
    customer_id = body.get('customer_id', '').strip()
    action_status = body.get('action_status', '').strip()

    valid_statuses = ['Sent for approval', 'Sent for Approval', 'Approved', 'Rejected']
    if not bom_id or not customer_id:
        return JsonResponse({'error': 'bom_id and customer_id are required'}, status=400)
    if action_status not in valid_statuses:
        return JsonResponse({'error': f'Invalid action_status: {action_status!r}'}, status=400)

    try:
        with connection.cursor() as cursor:
            # Update BOTH "Status" (what BOM form reads as action_status) AND "Remark"
            cursor.execute("""
                UPDATE tbl_bomcreation
                SET "Status" = %s,
                    "Remark" = %s
                WHERE "BOMCreation_Id" = %s AND "Customer_ID" = %s
            """, [action_status, action_status, bom_id, customer_id])
            updated = cursor.rowcount
        return JsonResponse({'success': True, 'updated': updated, 'action_status': action_status})
    except Exception as e:
        print("[save_approve_action Error]:", e)
        return JsonResponse({'error': str(e)}, status=500)


# ------------------------------------------------------------------
# API: POST — per-row save action for a single BOM record
# ------------------------------------------------------------------
@csrf_exempt
@require_POST
@require_active_customer
def save_approve_row_action(request):
    """Approve / Reject a single BOM row identified by bom_id + customer_id."""
    return save_approve_action(request)



# ------------------------------------------------------------------
# API: GET BOM New Part records from tbl_BOM_PartDetails_Master
# WHERE Cost_Price <> 0 AND Part_Status = 'Sent for approval' AND Part_Type = 'New'
# ------------------------------------------------------------------
@require_active_customer
def get_approve_bom_new_parts(request):
    customer = request.GET.get('customer', '').strip()
    status_filter = request.GET.get('status', 'Sent for approval').strip()

    try:
        from apps.BOM.models import BOMPartDetailsMaster
        records = []

        # 1. Primary query using BOMPartDetailsMaster ORM
        try:
            qs = BOMPartDetailsMaster.objects.all()
            if status_filter:
                qs = qs.filter(part_status__iexact=status_filter)
            qs = qs.filter(part_type__iexact='New').exclude(cost_price=0).exclude(cost_price__isnull=True)
            if customer:
                qs = qs.filter(customer__iexact=customer)

            for item in qs:
                records.append({
                    'part_no': item.part_no or '',
                    'part_description': item.part_description or '',
                    'base_uom': item.base_unit_of_measure or '',
                    'customer': item.customer or '',
                    'classification': item.classification or '',
                    'cost_price': float(item.cost_price) if item.cost_price else 0.0,
                    'settle_price': float(item.settle_price) if item.settle_price else 0.0,
                    'categorisation': item.categorisation or '',
                    'part_status': item.part_status or '',
                    'part_type': item.part_type or ''
                })
        except Exception as err_orm:
            print("[get_approve_bom_new_parts ORM warning]:", err_orm)

        # 2. Fallback: query raw SQL with dynamic column resolution if ORM yielded no rows
        if not records:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'tbl_bom_partdetails_master'
                """)
                existing_cols = {r[0].lower(): r[0] for r in cursor.fetchall()}

            if existing_cols:
                c_part_no     = existing_cols.get('part no') or existing_cols.get('part_no') or 'part_no'
                c_part_desc   = existing_cols.get('part description') or existing_cols.get('part_description') or 'part_description'
                c_base_uom    = existing_cols.get('base unit of measure') or existing_cols.get('base  of measure') or existing_cols.get('base_unit_of_measure') or 'base_unit_of_measure'
                c_customer    = existing_cols.get('customer') or 'customer'
                c_class       = existing_cols.get('classification') or 'classification'
                c_cost_price  = existing_cols.get('cost_price') or 'cost_price'
                c_settle_price= existing_cols.get('settle price') or existing_cols.get('settle_price') or 'settle_price'
                c_cat         = existing_cols.get('categorisation') or 'categorisation'
                c_status      = existing_cols.get('part_status') or existing_cols.get('part status') or 'part_status'
                c_type        = existing_cols.get('part_type') or existing_cols.get('part type') or 'part_type'

                sql = f"""
                    SELECT 
                        "{c_part_no}" AS part_no,
                        "{c_part_desc}" AS part_description,
                        "{c_base_uom}" AS base_uom,
                        "{c_customer}" AS customer,
                        "{c_class}" AS classification,
                        "{c_cost_price}" AS cost_price,
                        "{c_settle_price}" AS settle_price,
                        "{c_cat}" AS categorisation,
                        "{c_status}" AS part_status,
                        "{c_type}" AS part_type
                    FROM tbl_bom_partdetails_master
                    WHERE COALESCE("{c_cost_price}", 0) <> 0
                      AND LOWER(TRIM(COALESCE("{c_type}", ''))) = 'new'
                """
                params = []
                if status_filter:
                    sql += f' AND LOWER(TRIM(COALESCE("{c_status}", \'\'))) = %s'
                    params.append(status_filter.lower())
                if customer:
                    sql += f' AND LOWER(TRIM(COALESCE("{c_customer}", \'\'))) = %s'
                    params.append(customer.lower())

                sql += f' ORDER BY "{c_part_no}"'

                cols, rows = _execute_query(sql, params)
                for row in rows:
                    rec = dict(zip(cols, row))
                    for k, v in rec.items():
                        if hasattr(v, 'isoformat'):
                            rec[k] = v.isoformat()
                        elif isinstance(v, (float, int)) or hasattr(v, '__float__'):
                            rec[k] = float(v)
                    records.append(rec)

        return JsonResponse({'records': records})
    except Exception as e:
        print("[get_approve_bom_new_parts Error]:", e)
        return JsonResponse({'records': [], 'error': str(e)})


# ------------------------------------------------------------------
# API: POST — Save action status for BOM New Parts
# ------------------------------------------------------------------
@csrf_exempt
@require_POST
@require_active_customer
def save_approve_new_part_action(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    part_nos = body.get('part_nos', [])
    action_status = body.get('action_status', '').strip()

    valid_statuses = ['Sent for approval', 'Sent for Approval', 'Approved', 'Rejected']
    if not part_nos:
        return JsonResponse({'error': 'No parts selected'}, status=400)
    if action_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid action_status'}, status=400)

    try:
        from apps.BOM.models import BOMPartDetailsMaster
        updated = BOMPartDetailsMaster.objects.filter(part_no__in=part_nos).update(part_status=action_status)
        if updated == 0:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE tbl_bom_partdetails_master
                    SET "Part_Status" = %s
                    WHERE "Part No" IN %s OR "part_no" IN %s
                """, [action_status, tuple(part_nos), tuple(part_nos)])
                updated = cursor.rowcount

        return JsonResponse({'success': True, 'updated': updated, 'action_status': action_status})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ------------------------------------------------------------------
# API: GET distinct Customer IDs for BOP Approval (qry_BOPSendForApproval)
# SELECT DISTINCT Customer_ID FROM qry_BOPSendForApproval;
# ------------------------------------------------------------------
@require_active_customer
def get_approve_bop_customers(request):
    # BOP writes action_status = "Send for Approval" (imperative form).
    # Match both "send for approval" and "sent for approval" to be safe.
    cols, rows = _execute_query("""
        SELECT DISTINCT customer_id
        FROM tbl_bopcreation
        WHERE customer_id IS NOT NULL
          AND LOWER(TRIM(COALESCE(action_status, remark, '')))
              IN ('send for approval', 'sent for approval', 'pending_approval')
        ORDER BY customer_id
    """)
    customers = [r[0] for r in rows if r[0]]
    return JsonResponse({'customers': customers})


# ------------------------------------------------------------------
# API: GET distinct ItemCreation_Id for BOP given Customer_ID
# SELECT DISTINCT qry_BOPSendForApproval.ItemCreation_Id, qry_BOPSendForApproval.Customer_ID 
# FROM qry_BOPSendForApproval WHERE Customer_ID = %s;
# ------------------------------------------------------------------
@require_active_customer
def get_approve_bop_items(request):
    customer_id = request.GET.get('customer_id', '').strip()
    if not customer_id:
        return JsonResponse({'items': []})

    cols, rows = _execute_query("""
        SELECT DISTINCT itemcreation_id::text AS item_id
        FROM tbl_bopcreation
        WHERE customer_id = %s
          AND itemcreation_id IS NOT NULL
        ORDER BY item_id
    """, [customer_id])
    items = [str(r[0]) for r in rows if r[0] is not None]

    return JsonResponse({'items': items})


# ------------------------------------------------------------------
# API: GET distinct BOPCreation_ID for given Customer_ID + ItemCreation_Id
# SELECT DISTINCT bop_send.Customer_ID, bop_send.ItemCreation_Id, bop_send.BOPCreation_ID 
# FROM qry_BOPSendForApproval AS bop_send;
# ------------------------------------------------------------------
@require_active_customer
def get_approve_bop_ids(request):
    customer_id = request.GET.get('customer_id', '').strip()
    item_id = request.GET.get('item_id', '').strip()

    if not customer_id:
        return JsonResponse({'bop_ids': []})

    sql = """
        SELECT DISTINCT bopcreation_id
        FROM tbl_bopcreation
        WHERE customer_id = %s
    """
    params = [customer_id]

    if item_id:
        sql += ' AND itemcreation_id::text = %s'
        params.append(item_id)

    sql += ' ORDER BY bopcreation_id'
    cols, rows = _execute_query(sql, params)
    bop_ids = [str(r[0]) for r in rows if r[0] is not None]

    return JsonResponse({'bop_ids': bop_ids})


# ------------------------------------------------------------------
# API: GET BOP lines and header details for approval grid
# ------------------------------------------------------------------
@require_active_customer
def get_approve_bop_lines(request):
    customer_id = request.GET.get('customer_id', '').strip()
    item_id = request.GET.get('item_id', '').strip()
    bop_id = request.GET.get('bop_id', '').strip()

    if not customer_id:
        return JsonResponse({'records': []})

    try:
        sql = """
            SELECT
                c.customer_id                                AS "Customer_ID",
                c.itemcreation_id::text                      AS "ItemCreation_Id",
                c.bopcreation_id                             AS "BOPCreation_Id",
                COALESCE(c.customer_name, '')                AS "Customer_Name",
                COALESCE(c.part_name, '')                    AS "Part_Name",
                COALESCE(c.drawing_no, '')                   AS "Drawing_No",
                COALESCE(c.drawing_revision_no, '')          AS "Drawing_Revision_No",
                COALESCE(c.product_category, '')             AS "Product_Category",
                COALESCE(c.project, '')                      AS "Project",
                COALESCE(c.action_status, c.remark, '')      AS "Action_Status",
                COALESCE(t.seq_no, 0)                        AS "Seq_No",
                COALESCE(t.operation_no, '')                 AS "Operation_No",
                COALESCE(t.type, '')                         AS "Type",
                COALESCE(t.costcenter_no, '')                AS "Costcenter_No",
                COALESCE(t.description, '')                  AS "Description",
                COALESCE(t.categorisation, '')               AS "Categorisation",
                COALESCE(t.run_time_sec, 0)                  AS "Run_Time_Sec",
                COALESCE(t.run_time_min, 0)                  AS "Run_Time_Min",
                COALESCE(t.boq, 0)                           AS "BOQ",
                COALESCE(t.total_run_time, 0)                AS "Total_Run_Time",
                COALESCE(t.cycle_time, 0)                    AS "Cycle_Time",
                COALESCE(t.total_cost, 0)                    AS "Total_Cost",
                COALESCE(t.remark, c.remark, '')             AS "Remark"
            FROM tbl_bopcreation c
            LEFT JOIN tbl_bop_tab t ON t.bopcreationid = c.bopcreation_id
            WHERE c.customer_id = %s
              AND LOWER(TRIM(COALESCE(c.action_status, c.remark, '')))
                  IN ('send for approval', 'sent for approval', 'pending_approval')
        """
        params = [customer_id]

        if item_id:
            sql += ' AND c.itemcreation_id::text = %s'
            params.append(item_id)

        if bop_id:
            sql += ' AND c.bopcreation_id = %s'
            params.append(bop_id)

        sql += ' ORDER BY "Seq_No", "BOPCreation_Id"'

        cols, rows = _execute_query(sql, params)

        records = []
        for row in rows:
            rec = dict(zip(cols, row))
            for k, v in rec.items():
                if hasattr(v, 'isoformat'):
                    rec[k] = v.isoformat()
                elif isinstance(v, (float, int)) or hasattr(v, '__float__'):
                    rec[k] = float(v)
            records.append(rec)

        # Fallback to ORM if raw SQL query returned 0 rows
        if not records:
            from apps.BOP.models import BOPCreation, BOPTab
            qs_c = BOPCreation.objects.filter(customer_id=customer_id)
            # Only show records still pending approval — BOP writes "Send for Approval"
            qs_c = BOPCreation.objects.filter(
                customer_id=customer_id,
                action_status__in=['Send for Approval', 'Sent for Approval', 'sent for approval', 'send for approval', 'pending_approval']
            )
            if item_id:
                qs_c = qs_c.filter(itemcreation_id=item_id)
            if bop_id:
                qs_c = qs_c.filter(bopcreation_id=bop_id)

            for bop_rec in qs_c:
                tab_lines = BOPTab.objects.filter(bopcreationid=bop_rec.bopcreation_id)
                if tab_lines.exists():
                    for t in tab_lines:
                        records.append({
                            "Customer_ID": bop_rec.customer_id or customer_id,
                            "ItemCreation_Id": str(bop_rec.itemcreation_id or item_id or ''),
                            "BOPCreation_Id": bop_rec.bopcreation_id or '',
                            "Customer_Name": bop_rec.customer_name or '',
                            "Part_Name": bop_rec.part_name or '',
                            "Drawing_No": bop_rec.drawing_no or '',
                            "Drawing_Revision_No": bop_rec.drawing_revision_no or '',
                            "Product_Category": bop_rec.product_category or '',
                            "Project": bop_rec.project or '',
                            "Action_Status": bop_rec.action_status or bop_rec.remark or '',
                            "Seq_No": t.seq_no or 0,
                            "Operation_No": t.operation_no or '',
                            "Type": t.type or '',
                            "Costcenter_No": t.costcenter_no or '',
                            "Description": t.description or '',
                            "Categorisation": t.categorisation or '',
                            "Run_Time_Sec": float(t.run_time_sec) if t.run_time_sec else 0,
                            "Run_Time_Min": float(t.run_time_min) if t.run_time_min else 0,
                            "BOQ": float(t.boq) if t.boq else 0,
                            "Total_Run_Time": float(t.total_run_time) if t.total_run_time else 0,
                            "Cycle_Time": float(t.cycle_time) if t.cycle_time else 0,
                            "Total_Cost": float(t.total_cost) if t.total_cost else 0,
                            "Remark": t.remark or bop_rec.remark or '',
                        })
                else:
                    records.append({
                        "Customer_ID": bop_rec.customer_id or customer_id,
                        "ItemCreation_Id": str(bop_rec.itemcreation_id or item_id or ''),
                        "BOPCreation_Id": bop_rec.bopcreation_id or '',
                        "Customer_Name": bop_rec.customer_name or '',
                        "Part_Name": bop_rec.part_name or '',
                        "Drawing_No": bop_rec.drawing_no or '',
                        "Drawing_Revision_No": bop_rec.drawing_revision_no or '',
                        "Product_Category": bop_rec.product_category or '',
                        "Project": bop_rec.project or '',
                        "Action_Status": bop_rec.action_status or bop_rec.remark or '',
                        "Seq_No": 1,
                        "Operation_No": "",
                        "Type": "",
                        "Costcenter_No": "",
                        "Description": "",
                        "Categorisation": "",
                        "Run_Time_Sec": 0,
                        "Run_Time_Min": 0,
                        "BOQ": 0,
                        "Total_Run_Time": 0,
                        "Cycle_Time": 0,
                        "Total_Cost": 0,
                        "Remark": bop_rec.remark or '',
                    })

        return JsonResponse({'records': records})
    except Exception as e:
        print("[get_approve_bop_lines Error]:", e)
        return JsonResponse({'records': [], 'error': str(e)})


# ------------------------------------------------------------------
# API: POST — save BOP action status ("Sent for approval", "Approved", "Rejected")
# Mirrors VBA btn_SaveRecord_Click for BOP:
#   - Updates tbl_BopCreation.Action_Status
#   - On Approved: stamps CompletedOn on tbl_BOP_CellAllienment, tbl_BOP_Tab, tbl_BOP_Tolling
# ------------------------------------------------------------------
@csrf_exempt
@require_POST
@require_active_customer
def save_approve_bop_action(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    bop_id = body.get('bop_id', '').strip()
    customer_id = body.get('customer_id', '').strip()
    action_status = body.get('action_status', '').strip()
    item_id = body.get('item_id', '').strip()

    valid_statuses = ['Sent for approval', 'Sent for Approval', 'Approved', 'Rejected']
    if not customer_id or not bop_id:
        return JsonResponse({'error': 'customer_id and bop_id are required'}, status=400)
    if action_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid action_status'}, status=400)

    updated = 0
    try:
        from apps.BOP.models import BOPCreation
        qs = BOPCreation.objects.filter(bopcreation_id=bop_id, customer_id=customer_id)
        if not qs.exists():
            qs = BOPCreation.objects.filter(bopcreation_id=bop_id)
        updated = qs.update(action_status=action_status, remark=action_status)
    except Exception as e:
        print("[save_approve_bop_action ORM warning]:", e)

    try:
        with connection.cursor() as cursor:
            if updated == 0:
                cursor.execute("""
                    UPDATE tbl_bopcreation
                    SET action_status = %s, remark = %s
                    WHERE (LOWER(TRIM(bopcreation_id)) = LOWER(TRIM(%s)) AND LOWER(TRIM(customer_id)) = LOWER(TRIM(%s)))
                       OR LOWER(TRIM(bopcreation_id)) = LOWER(TRIM(%s))
                """, [action_status, action_status, bop_id, customer_id, bop_id])
                updated = cursor.rowcount

            # Step 2: On Approved, stamp CompletedOn on child tables (mirrors VBA logic)
            if action_status == 'Approved':
                # Fetch Table_Id from tbl_bopcreation
                cursor.execute("""
                    SELECT table_id FROM tbl_bopcreation
                    WHERE bopcreation_id = %s AND customer_id = %s
                    LIMIT 1
                """, [bop_id, customer_id])
                row = cursor.fetchone()
                table_id = row[0] if row else None

                if table_id is not None:
                    item_filter = ' AND itemcreation_id = %s' if item_id else ''
                    for tbl in ['tbl_bop_cellallienment', 'tbl_bop_tab', 'tbl_bop_tolling']:
                        params = [bop_id, table_id]
                        if item_id:
                            params.insert(1, item_id)
                        bop_col = 'bopcreationid' if tbl in ('tbl_bop_tab', 'tbl_bop_cellallienment', 'tbl_bop_tolling') else 'bopcreation_id'
                        sql = f"""
                            UPDATE {tbl}
                            SET completedon = CURRENT_DATE::text
                            WHERE {bop_col} = %s{item_filter}
                              AND table_id = %s
                        """
                        try:
                            cursor.execute(sql, params)
                        except Exception as ex:
                            print(f"[save_approve_bop_action] CompletedOn update failed for {tbl}: {ex}")
    except Exception as e:
        print("[save_approve_bop_action Error]:", e)
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'success': True, 'updated': updated, 'action_status': action_status})



# ------------------------------------------------------------------
# API: POST — per-row save action for a single BOP record
# ------------------------------------------------------------------
@csrf_exempt
@require_POST
@require_active_customer
def save_approve_bop_row_action(request):
    """Approve / Reject a single BOP row. Delegates to save_approve_bop_action."""
    return save_approve_bop_action(request)


# ------------------------------------------------------------------
# API: GET distinct Updated_By values for RFQ dropdown
# Mirrors: SELECT 'ALL' AS Updated_By FROM qry_RFQ_Details
#          UNION SELECT DISTINCT Updated_By FROM qry_RFQ_Details
# ------------------------------------------------------------------
@require_active_customer
def get_rfq_updated_by(request):
    try:
        cols, rows = _execute_query("""
            SELECT DISTINCT updated_by
            FROM tbl_rfq_details
            WHERE updated_by IS NOT NULL AND TRIM(updated_by) <> ''
            ORDER BY updated_by
        """)
        values = [r[0] for r in rows if r[0]]
        return JsonResponse({'updated_by': values})
    except Exception as e:
        print("[get_rfq_updated_by Error]:", e)
        return JsonResponse({'updated_by': [], 'error': str(e)}, status=500)


# ------------------------------------------------------------------
# API: GET RFQ records from qry_RFQ_Details with optional filter
# qry_RFQ_Details: SELECT *, IIF(tbl_RFQ_Details.Is_Completed='Yes','Closed','Open') AS RFQ_Status
#                  FROM tbl_RFQ_Details
# ------------------------------------------------------------------
@require_active_customer
def get_rfq_records(request):
    updated_by = request.GET.get('updated_by', '').strip()
    try:
        sql = """
            SELECT
                id AS "ID",
                customer_id AS "Customer_ID",
                customername AS "CustomerName",
                itemcreation_id AS "ItemCreation_ID",
                bopcreation_id AS "BOPCreation_ID",
                boc_creation_id AS "BOC_Creation_ID",
                CASE WHEN is_completed IS TRUE THEN 'Yes' ELSE 'No' END AS "Is_Completed",
                action_date AS "Action_Date",
                updated_by AS "Updated_By",
                CASE WHEN is_completed IS TRUE THEN 'Closed' ELSE 'Open' END AS "RFQ_Status"
            FROM tbl_rfq_details
        """
        params = []
        if updated_by and updated_by.upper() != 'ALL':
            sql += ' WHERE updated_by = %s'
            params.append(updated_by)
        sql += ' ORDER BY id'

        cols, rows = _execute_query(sql, params)
        records = []
        for row in rows:
            rec = dict(zip(cols, row))
            for k, v in rec.items():
                if hasattr(v, 'strftime'):
                    rec[k] = v.strftime('%d-%m-%Y')
                elif hasattr(v, 'isoformat'):
                    rec[k] = v.isoformat()
            records.append(rec)
        return JsonResponse({'records': records})
    except Exception as e:
        print("[get_rfq_records Error]:", e)
        return JsonResponse({'records': [], 'error': str(e)})


# ------------------------------------------------------------------
# API: POST — Reopen RFQ (set Is_Completed = FALSE)
# Mirrors: btnEdit_RfqStatus_Click → UPDATE tbl_RFQ_Details
#          SET Is_Completed='No' WHERE ID = <row_id>
# ------------------------------------------------------------------
@csrf_exempt
@require_POST
@require_active_customer
def save_rfq_reopen(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    row_id = body.get('row_id')
    if not row_id:
        return JsonResponse({'error': 'row_id is required'}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tbl_rfq_details
                SET is_completed = FALSE
                WHERE id = %s
            """, [row_id])
            updated = cursor.rowcount
        return JsonResponse({'success': True, 'updated': updated})
    except Exception as e:
        print("[save_rfq_reopen Error]:", e)
        return JsonResponse({'error': str(e)}, status=500)




