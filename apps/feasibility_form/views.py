from django.shortcuts import render
from django.http import JsonResponse
from .models import ItemCard, Feasibility
from datetime import datetime
from django.views.decorators.csrf import csrf_protect
from config.decorators import require_active_customer

@csrf_protect
@require_active_customer
def feasibility(request):
    # GET Request Logic
    customer_id = request.active_customer['id']
    customer_name = request.active_customer['name']
    items = []

    # Fetch unique customers for the dropdown
    customers = ItemCard.objects.values('customer_id', 'customer_name').distinct().order_by('customer_name')

    if customer_id:
        items = ItemCard.objects.filter(customer_id=customer_id).values_list('no', flat=True)
        customer_record = ItemCard.objects.filter(customer_id=customer_id).first()
        if customer_record:
            customer_name = customer_record.customer_name
            
    # Fetch existing records to display in the table
    if customer_id:
        # Get items for this customer
        cust_items = ItemCard.objects.filter(customer_id=customer_id).values_list('no', flat=True)
        all_records = Feasibility.objects.filter(item_no__in=cust_items).order_by('-item_no')[:50]
    else:
        all_records = Feasibility.objects.all().order_by('-item_no')[:50]

    return render(request, "feasibility_form/feasibility.html", {
        "itemNo": items,
        "selected_customer_id": customer_id,
        "selected_name": customer_name,
        "records": all_records,
        "customers": customers,
    })

@csrf_protect
def feasibility_create(request):
    if request.method == "POST":
        item_no = request.POST.get('itemNo')
        if not item_no:
            return JsonResponse({"status": "error", "message": "Item No is required to save."})
        
        record = Feasibility.objects.filter(item_no=item_no).first()
        if not record:
            record = Feasibility.objects.filter(item_no=item_no.zfill(8)).first()

        # If still not found, create a new record
        if not record:
            record = Feasibility(item_no=item_no)

        if record:
            # --- HELPER FUNCTION FOR DATES ---
            def safe_parse_date(date_str):
                if not date_str or date_str.lower() == "none":
                    return None
                for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y'):
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except (ValueError, TypeError):
                        continue
                return None

           # 1. INITIAL DATA
            record.customer_name = request.POST.get('customer_name')
            record.enq_no = request.POST.get('enqNo')
            record.part_name = request.POST.get('part_name')
            record.application = request.POST.get('application')
            record.feasibility_type = request.POST.get('feasibility_type')
            record.projected_volume = request.POST.get('projected_volume')
            record.part_no = request.POST.get('part_no')
            record.feasibility_no = request.POST.get('feasibility_no')
            record.vehicle_model = request.POST.get('vehicle_model')
            record.daily_peak_volumes = request.POST.get('daily_peak')

            # 2. DATE FIELDS
            record.initial_date = safe_parse_date(request.POST.get('initial_date'))
            record.updated_on = safe_parse_date(request.POST.get('updated_on'))
            record.date_of_sop = safe_parse_date(request.POST.get('sop_date'))
            record.AttDate = safe_parse_date(request.POST.get('marketing_date')) # Common date used for Attendance

            # 3. QUESTIONNAIRE & PROJECTS
            record.availability_customer_inter_f = request.POST.get('questionnaire_status')
            record.availability_customer_inter_r = request.POST.get('questionnaire_responsible')
            record.availability_customer_inter_c = request.POST.get('questionnaire_comments')

            record.project_status_f = request.POST.get('project_status')
            record.project_responsible_r = request.POST.get('project_responsible')
            record.project_comments_c = request.POST.get('project_comments')

            # 4. VOSS, PARTS, STDS
            record.voss_status_f = request.POST.get('Voss_status')
            record.voss_responsible_r = request.POST.get('Voss_responsible')
            record.voss_comments_c = request.POST.get('Voss_comments')

            record.a2parts_status_f = request.POST.get('parts_status')
            record.a2parts_responsible_r = request.POST.get('parts_responsible')
            record.a2parts_comments_c = request.POST.get('parts_comments')

            record.a3stds_status_f = request.POST.get('stds_status')
            record.a3stds_responsible_r = request.POST.get('stds_responsible')
            record.a3stds_comments_c = request.POST.get('stds_comments')

            # 5. LOGISTICS & SAFETY (Section II)
            record.source_status_f = request.POST.get('source_status')
            record.source_responsible_r = request.POST.get('source_responsible')
            record.source_comments_c = request.POST.get('source_comments')

            record.safety_status_f = request.POST.get('safety_status')
            record.safety_responsible_r = request.POST.get('safety_responsible')
            record.safety_comments_c = request.POST.get('safety_comments')

            record.export_status_f = request.POST.get('export_status')
            record.export_responsible_r = request.POST.get('export_responsible')
            record.export_comments_c = request.POST.get('export_comments')

            record.receipt_status_f = request.POST.get('receipt_status')
            record.receipt_responsible_r = request.POST.get('receipt_responsible')
            record.receipt_comments_c = request.POST.get('receipt_comments')

            record.shipment_status_f = request.POST.get('shipment_status')
            record.shipment_responsible_r = request.POST.get('shipment_responsible')
            record.shipment_comments_c = request.POST.get('shipment_comments')

            record.dest_status_f = request.POST.get('dest_status')
            record.dest_responsible_r = request.POST.get('dest_responsible')
            record.dest_comments_c = request.POST.get('dest_comments')

            # 6. LEGAL, TEST, BSC
            record.legal_status_f = request.POST.get('legal_status')
            record.legal_responsible_r = request.POST.get('legal_responsible')
            record.legal_comments_c = request.POST.get('legal_comments')

            record.test_status_f = request.POST.get('test_status')
            record.test_responsible_r = request.POST.get('test_responsible')
            record.test_comments_c = request.POST.get('test_comments')

            record.b_status_f = request.POST.get('b_status')
            record.b_responsible_r = request.POST.get('b_responsible')
            record.b_comments_c = request.POST.get('b_comments')

            record.bsc_status_f = request.POST.get('bsc_status')
            record.bsc_responsible_r = request.POST.get('bsc_responsible')
            record.bsc_comments_c = request.POST.get('bsc_comments')

            # 7. DATA, SURFACE, METHOD
            record.data_status_f = request.POST.get('data_status')
            record.data_responsible_r = request.POST.get('data_responsible')
            record.data_comments_c = request.POST.get('data_comments')

            record.surface_status_f = request.POST.get('surface_status')
            record.surface_responsible_r = request.POST.get('surface_responsible')
            record.surface_comments_c = request.POST.get('surface_comments')

            record.method_status_f = request.POST.get('method_status')
            record.method_responsible_r = request.POST.get('method_responsible')
            record.method_comments_c = request.POST.get('method_comments')

            # 8. SECTION C (Manufacturing)
            record.c1_status_f = request.POST.get('c1_status')
            record.c1_responsible_r = request.POST.get('c1_responsible')
            record.c1_comments_c = request.POST.get('c1_comments')

            record.c2_status_f = request.POST.get('c2_status')
            record.c2_responsible_r = request.POST.get('c2_responsible')
            record.c2_comments_c = request.POST.get('c2_comments')

            record.c3_status_f = request.POST.get('c3_status')
            record.c3_responsible_r = request.POST.get('c3_responsible')
            record.c3_comments_c = request.POST.get('c3_comments')

            record.c4_status_f = request.POST.get('c4_status')
            record.c4_responsible_r = request.POST.get('c4_responsible')
            record.c4_comments_c = request.POST.get('c4_comments')

            record.c5_status_f = request.POST.get('c5_status')
            record.c5_responsible_r = request.POST.get('c5_responsible')
            record.c5_comments_c = request.POST.get('c5_comments')

            # 9. SECTION D & E
            record.d1_status_f = request.POST.get('d1_status')
            record.d1_responsible_r = request.POST.get('d1_responsible')
            record.d1_comments_c = request.POST.get('d1_comments')

            record.d2_status_f = request.POST.get('d2_status')
            record.d2_responsible_r = request.POST.get('d2_responsible')
            record.d2_comments_c = request.POST.get('d2_comments')

            record.d3_status_f = request.POST.get('d3_status')
            record.d3_responsible_r = request.POST.get('d3_responsible')
            record.d3_comments_c = request.POST.get('d3_comments')

            record.d4_status_f = request.POST.get('d4_status')
            record.d4_responsible_r = request.POST.get('d4_responsible')
            record.d4_comments_c = request.POST.get('d4_comments')

            record.d5_status_f = request.POST.get('d5_status')
            record.d5_responsible_r = request.POST.get('d5_responsible')
            record.d5_comments_c = request.POST.get('d5_comments')

            record.e1_status_f = request.POST.get('e1_status')
            record.e1_responsible_r = request.POST.get('e1_responsible')
            record.e1_comments_c = request.POST.get('e1_comments')

            record.e2_status_f = request.POST.get('e2_status')
            record.e2_responsible_r = request.POST.get('e2_responsible')
            record.e2_comments_c = request.POST.get('e2_comments')

            record.e3_status_f = request.POST.get('e3_status')
            record.e3_responsible_r = request.POST.get('e3_responsible')
            record.e3_comments_c = request.POST.get('e3_comments')

            # 10. SECTIONS F, G, H, I
            record.f1_status_f = request.POST.get('f1_status')
            record.f1_responsible_r = request.POST.get('f1_responsible')
            record.f1_comments_c = request.POST.get('f1_comments')

            record.f2_status_f = request.POST.get('f2_status')
            record.f2_responsible_r = request.POST.get('f2_responsible')
            record.f2_comments_c = request.POST.get('f2_comments')

            record.f3_status_f = request.POST.get('f3_status')
            record.f3_responsible_r = request.POST.get('f3_responsible')
            record.f3_comments_c = request.POST.get('f3_comments')

            record.g1_status_f = request.POST.get('g1_status')
            record.g1_responsible_r = request.POST.get('g1_responsible')
            record.g1_comments_c = request.POST.get('g1_comments')

            record.g2_status_f = request.POST.get('g2_status')
            record.g2_responsible_r = request.POST.get('g2_responsible')
            record.g2_comments_c = request.POST.get('g2_comments')

            record.g3_status_f = request.POST.get('g3_status')
            record.g3_responsible_r = request.POST.get('g3_responsible')
            record.g3_comments_c = request.POST.get('g3_comments')

            record.h1_status_f = request.POST.get('h1_status')
            record.h1_responsible_r = request.POST.get('h1_responsible')
            record.h1_comments_c = request.POST.get('h1_comments')

            record.h2_status_f = request.POST.get('h2_status')
            record.h2_responsible_r = request.POST.get('h2_responsible')
            record.h2_comments_c = request.POST.get('h2_comments')

            record.h3_status_f = request.POST.get('h3_status')
            record.h3_responsible_r = request.POST.get('h3_responsible')
            record.h3_comments_c = request.POST.get('h3_comments')

            # Section I (1-7)
            for i in range(1, 8):
                setattr(record, f'i{i}_status_f', request.POST.get(f'i{i}_status'))
                setattr(record, f'i{i}_responsible_r', request.POST.get(f'i{i}_responsible'))
                setattr(record, f'i{i}_comments_c', request.POST.get(f'i{i}_comments'))

            # 11. FINAL DECISIONS
            record.final1_status_f = request.POST.get('final1_status')
            record.final1_responsible_r = request.POST.get('final1_responsible')
            record.final1_comments_c = request.POST.get('final1_comments')

            record.final2_status_f = request.POST.get('final2_status')
            record.final2_responsible_r = request.POST.get('final2_responsible')
            record.final2_comments_c = request.POST.get('final2_comments')

            record.final3_status_f = request.POST.get('final3_status')
            record.final3_responsible_r = request.POST.get('final3_responsible')
            record.final3_comments_c = request.POST.get('final3_comments')

            # 12. ATTENDANCE
            record.marketing_attendance = request.POST.get('marketing_attendance')
            record.materials_attendance = request.POST.get('materials_attendance')
            record.quality_attendance = request.POST.get('quality_attendance')
            record.pe_attendance = request.POST.get('pe_attendance')
            record.me_attendance = request.POST.get('me_attendance')
            record.pm_attendance = request.POST.get('pm_attendance')

            try:
                record.save()
                
                # Prepare data to return for dynamically adding to the frontend table
                new_record_data = {
                    "item_no": record.item_no or "",
                    "customer_name": record.customer_name or "",
                    "part_name": record.part_name or "",
                    "feasibility_type": record.feasibility_type or "",
                    "feasibility_no": record.feasibility_no or "",
                    "updated_on": str(record.updated_on) if record.updated_on else ""
                }
                
                return JsonResponse({
                    "status": "success", 
                    "message": "Data saved successfully!",
                    "record": new_record_data
                })
            except Exception as e:
                return JsonResponse({"status": "error", "message": f"Database Error: {str(e)}"})
        
        return JsonResponse({"status": "error", "message": "Failed to process record."})
    return JsonResponse({"status": "error", "message": "Invalid request method."})

def feasibility_list(request):
    customer_id = getattr(request, 'active_customer', {}).get('id', '')
    
    # Base query for records
    if customer_id:
        cust_items = ItemCard.objects.filter(customer_id=customer_id).values_list('no', flat=True)
        records = Feasibility.objects.filter(item_no__in=cust_items).order_by('-item_no')[:50]
        # Also return the item numbers for this customer
        items = list(cust_items)
        # Try to get customer name
        customer_name = ""
        first_cust = ItemCard.objects.filter(customer_id=customer_id).first()
        if first_cust:
            customer_name = first_cust.customer_name
    else:
        records = Feasibility.objects.all().order_by('-item_no')[:50]
        items = []
        customer_name = ""

    data = []
    for rec in records:
        data.append({
            "item_no": rec.item_no or "",
            "customer_name": rec.customer_name or "",
            "part_name": rec.part_name or "",
            "feasibility_type": rec.feasibility_type or "",
            "feasibility_no": rec.feasibility_no or "",
            "updated_on": str(rec.updated_on) if rec.updated_on else ""
        })
        
    return JsonResponse({
        "status": "success", 
        "records": data,
        "items": items,
        "customer_name": customer_name
    })

def get_opportunity_data(request):
    item_no = request.GET.get("item_no", "")
    if not item_no:
        return JsonResponse({"status": "error", "message": "Item number is required"})
    
    normalized_item_no = item_no.zfill(8) if item_no else ""
    record = Feasibility.objects.filter(item_no=item_no).first()
    if not record:
        record = Feasibility.objects.filter(item_no=normalized_item_no).first()
    
    print("Searching for Item_No:", normalized_item_no)  # Debug log

    if not record:
        return JsonResponse({"status": "error", "message": "No feasibility data found"})


    data = {
        "customer_name": record.customer_name,
        "enqNo": record.enq_no,
        "part_name": record.part_name,
        "application": record.application,
        "feasibility_type": record.feasibility_type,
        "projected_volume": record.projected_volume,
        "initial_date": str(record.initial_date) if record.initial_date else "",
        "updated_on": str(record.updated_on) if record.updated_on else "",
        "part_no": record.part_no,
        "feasibility_no": record.feasibility_no,
        "vehicle_model": record.vehicle_model,
        "daily_peak": record.daily_peak_volumes,
        "sop_date": str(record.date_of_sop) if record.date_of_sop else "",
        "att_date": str(record.AttDate) if record.AttDate else "",
           
        # Question I
    "questionnaire_status": record.availability_customer_inter_f,
    "questionnaire_responsible": record.availability_customer_inter_r,
    "questionnaire_comments": record.availability_customer_inter_c,

    # Question II
    "project_status": record.project_status_f,
    "project_responsible": record.project_responsible_r,
    "project_comments": record.project_comments_c,

    "Voss_status": record.voss_status_f,
    "Voss_responsible": record.voss_responsible_r,
    "Voss_comments": record.voss_comments_c,

    "parts_status": record.a2parts_status_f,
    "parts_responsible": record.a2parts_responsible_r,
    "parts_comments": record.a2parts_comments_c,

    "stds_status": record.a3stds_status_f,
    "stds_responsible": record.a3stds_responsible_r,
    "stds_comments": record.a3stds_comments_c,

    # Question II
    "source_status": record.source_status_f,
    "source_responsible": record.source_responsible_r,
    "source_comments": record.source_comments_c,

    "safety_status": record.safety_status_f,
    "safety_responsible": record.safety_responsible_r,
    "safety_comments": record.safety_comments_c,

    "export_status": record.export_status_f,
    "export_responsible": record.export_responsible_r,
    "export_comments": record.export_comments_c,

    "receipt_status": record.receipt_status_f,
    "receipt_responsible": record.receipt_responsible_r,
    "receipt_comments": record.receipt_comments_c,

    "shipment_status": record.shipment_status_f,
    "shipment_responsible": record.shipment_responsible_r,
    "shipment_comments": record.shipment_comments_c,


     # Question II
    "dest_status": record.dest_status_f,
    "dest_responsible": record.dest_responsible_r,
    "dest_comments": record.dest_comments_c,

    "legal_status": record.legal_status_f,
    "legal_responsible": record.legal_responsible_r,
    "legal_comments": record.legal_comments_c,

    "test_status": record.test_status_f,
    "test_responsible": record.test_responsible_r,
    "test_comments": record.test_comments_c,

    "b_status": record.b_status_f,
    "b_responsible": record.b_responsible_r,
    "b_comments": record.b_comments_c,

    "bsc_status": record.bsc_status_f,
    "bsc_responsible": record.bsc_responsible_r,
    "bsc_comments": record.bsc_comments_c,
 # Question II
    "data_status": record.data_status_f,
    "data_responsible": record.data_responsible_r,
    "data_comments": record.data_comments_c,

    "surface_status": record.surface_status_f,
    "surface_responsible": record.surface_responsible_r,
    "surface_comments": record.surface_comments_c,

    "method_status": record.method_status_f,
    "method_responsible": record.method_responsible_r,
    "method_comments": record.method_comments_c,
    
    
    
    "c1_status": record.c1_status_f,
    "c1_responsible": record.c1_responsible_r,
    "c1_comments": record.c1_comments_c,

    "c2_status": record.c2_status_f,
    "c2_responsible": record.c2_responsible_r,
    "c2_comments": record.c2_comments_c,

    "c3_status": record.c3_status_f,
    "c3_responsible": record.c3_responsible_r,
    "c3_comments": record.c3_comments_c,

    "c4_status": record.c4_status_f,
    "c4_responsible": record.c4_responsible_r,
    "c4_comments": record.c4_comments_c,

    "c5_status": record.c5_status_f,
    "c5_responsible": record.c5_responsible_r,
    "c5_comments": record.c5_comments_c,


    
    "d1_status": record.d1_status_f,
    "d1_responsible": record.d1_responsible_r,
    "d1_comments": record.d1_comments_c,

    "d2_status": record.d2_status_f,
    "d2_responsible": record.d2_responsible_r,
    "d2_comments": record.d2_comments_c,

    "d3_status": record.d3_status_f,
    "d3_responsible": record.d3_responsible_r,
    "d3_comments": record.d3_comments_c,

    "d4_status": record.d4_status_f,
    "d4_responsible": record.d4_responsible_r,
    "d4_comments": record.d4_comments_c,

    "d5_status": record.d5_status_f,
    "d5_responsible": record.d5_responsible_r,
    "d5_comments": record.d5_comments_c,


    "e1_status": record.e1_status_f,
    "e1_responsible": record.e1_responsible_r,
    "e1_comments": record.e1_comments_c,

    "e2_status": record.e2_status_f,
    "e2_responsible": record.e2_responsible_r,
    "e2_comments": record.e2_comments_c,

    "e3_status": record.e3_status_f,
    "e3_responsible": record.e3_responsible_r,
    "e3_comments": record.e3_comments_c,

    "f1_status": record.f1_status_f,
    "f1_responsible": record.f1_responsible_r,
    "f1_comments": record.f1_comments_c,

    "f2_status": record.f2_status_f,
    "f2_responsible": record.f2_responsible_r,
    "f2_comments": record.f2_comments_c,

    "f3_status": record.f3_status_f,
    "f3_responsible": record.f3_responsible_r,
    "f3_comments": record.f3_comments_c,

    "g1_status": record.g1_status_f,
    "g1_responsible": record.g1_responsible_r,
    "g1_comments": record.g1_comments_c,

    "g2_status": record.g2_status_f,
    "g2_responsible": record.g2_responsible_r,
    "d2_comments": record.g2_comments_c,

    "g3_status": record.g3_status_f,
    "g3_responsible": record.g3_responsible_r,
    "g3_comments": record.g3_comments_c,

    "h1_status": record.h1_status_f,
    "h1_responsible": record.h1_responsible_r,
    "h1_comments": record.h1_comments_c,

    "h2_status": record.h2_status_f,
    "h2_responsible": record.h2_responsible_r,
    "h2_comments": record.h2_comments_c,

    "h3_status": record.h3_status_f,
    "h3_responsible": record.h3_responsible_r,
    "h3_comments": record.h3_comments_c,

    "i1_status": record.i1_status_f,
    "i1_responsible": record.i1_responsible_r,
    "i1_comments": record.i1_comments_c,

    "i2_status": record.i2_status_f,
    "i2_responsible": record.i2_responsible_r,
    "i2_comments": record.i2_comments_c,

    "i3_status": record.i3_status_f,
    "i3_responsible": record.i3_responsible_r,
    "i3_comments": record.i3_comments_c,

    "i4_status": record.i4_status_f,
    "i4_responsible": record.i4_responsible_r,
    "i4_comments": record.i4_comments_c,

    "i5_status": record.i5_status_f,
    "i5_responsible": record.i5_responsible_r,
    "i5_comments": record.i5_comments_c,

    "i6_status": record.i6_status_f,
    "i6_responsible": record.i6_responsible_r,
    "i6_comments": record.i6_comments_c,

    "i7_status": record.i7_status_f,
    "i7_responsible": record.i7_responsible_r,
    "i7_comments": record.i7_comments_c,

    "final1_status": record.final1_status_f,
    "final1_responsible": record.final1_responsible_r,
    "final1_comments": record.final1_comments_c,

    "final2_status": record.final2_status_f,
    "final2_responsible": record.final2_responsible_r,
    "final2_comments": record.final2_comments_c,

    "final3_status": record.final3_status_f,
    "final3_responsible": record.final3_responsible_r,
    "final3_comments": record.final3_comments_c,

    
    "marketing_attendance": record.marketing_attendance,
    "materials_attendance": record.materials_attendance,
    "quality_attendance": record.quality_attendance,

    "pe_attendance": record.pe_attendance,
    "me_attendance": record.me_attendance,
    "pm_attendance": record.pm_attendance,

    }

    return JsonResponse({"status": "success", "data": data})


