import json
import csv
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from .models import BOMHeader, BOMTransaction

def BOM_form(request):
    # Retrieve all existing BOM creation IDs for the dropdown if needed
    context = {
        "headers": BOMHeader.objects.all()
    }
    return render(request, "BOM/BOM_form.html", context)

@csrf_exempt
def bom_ajax_action(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")
            
            if action == "create":
                # Create BOMHeader
                header = BOMHeader.objects.create(
                    customer_id=data.get("customer_id"),
                    item_creation_id=data.get("item_creation_id"),
                    bom_creation_id=data.get("bom_creation_id"),
                    description=data.get("description"),
                    uom_code=data.get("uom_code"),
                    action_status=data.get("action_status"),
                    last_date_modified=data.get("last_date_modified"),
                    table_id=data.get("table_id"),
                    create_date=data.get("create_date"),
                )
                return JsonResponse({"status": "success", "message": "Done", "id": header.id})
                
            elif action == "edit":
                # Edit requires a bom_creation_id or id to load
                bom_creation_id = data.get("bom_creation_id")
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    header_dict = model_to_dict(header)
                    return JsonResponse({"status": "success", "message": "Loaded", "data": header_dict})
                return JsonResponse({"status": "error", "message": "Not Found"})
                
            elif action == "save":
                # Update BOMHeader
                bom_creation_id = data.get("bom_creation_id")
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    for key, value in data.items():
                        if hasattr(header, key) and key != "action" and key != "id":
                            setattr(header, key, value)
                    header.save()
                    return JsonResponse({"status": "success", "message": "Done"})
                return JsonResponse({"status": "error", "message": "Header not found"})
                
            elif action == "delete":
                # Delete BOMHeader
                bom_creation_id = data.get("bom_creation_id")
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    header.delete()
                    # Also delete parts
                    BOMTransaction.objects.filter(bom_creation_id=bom_creation_id).delete()
                    return JsonResponse({"status": "success", "message": "Done"})
                return JsonResponse({"status": "error", "message": "Header not found"})
                
            elif action in ["send_approval", "ecn"]:
                bom_creation_id = data.get("bom_creation_id")
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    header.action_status = action.upper()
                    header.save()
                    return JsonResponse({"status": "success", "message": "Done"})
                return JsonResponse({"status": "error", "message": "Header not found"})
                
            elif action == "add_part":
                bom_creation_id = data.get("bom_creation_id")
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    trans = BOMTransaction.objects.create(
                        bom_creation_id=bom_creation_id,
                        entry_type=data.get("entry_type"),
                        part_number=data.get("part_number"),
                        quantity=data.get("quantity") if data.get("quantity") else None,
                        description=data.get("description"),
                        uom_code=data.get("uom_code"),
                        categorisation=data.get("categorisation"),
                        routing_link_code=data.get("routing_link_code"),
                        part_status=data.get("part_status"),
                        table_id=data.get("table_id")
                    )
                    return JsonResponse({"status": "success", "message": "Done", "id": trans.id})
                return JsonResponse({"status": "error", "message": "Header not found. Create BOM first."})
                
            elif action == "get_parts":
                bom_creation_id = data.get("bom_creation_id")
                parts = list(BOMTransaction.objects.filter(bom_creation_id=bom_creation_id).values())
                return JsonResponse({"status": "success", "data": parts})
                
            elif action == "delete_part":
                part_id = data.get("part_id")
                part = BOMTransaction.objects.filter(id=part_id).first()
                if part:
                    part.delete()
                    return JsonResponse({"status": "success", "message": "Done"})
                return JsonResponse({"status": "error", "message": "Part not found"})
                
            elif action in ["copy_bom_table", "copy_bom_trans", "paste_bom_trans"]:
                # Mock implementation for copying and pasting
                return JsonResponse({"status": "success", "message": "Done"})
                
            elif action == "complete":
                bom_creation_id = data.get("bom_creation_id")
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    header.action_status = "COMPLETED"
                    header.save()
                    return JsonResponse({"status": "success", "message": "Done"})
                return JsonResponse({"status": "error", "message": "Header not found"})
                
            elif action == "download":
                bom_creation_id = data.get("bom_creation_id")
                header = BOMHeader.objects.filter(bom_creation_id=bom_creation_id).first()
                if header:
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = f'attachment; filename="bom_{header.bom_creation_id}.csv"'
                    writer = csv.writer(response)
                    writer.writerow(['Entry Type', 'Part Number', 'Quantity', 'Description', 'UOM Code', 'Categorisation', 'Routing Link Code', 'Part Status'])
                    for part in BOMTransaction.objects.filter(bom_creation_id=bom_creation_id):
                        writer.writerow([part.entry_type, part.part_number, part.quantity, part.description, part.uom_code, part.categorisation, part.routing_link_code, part.part_status])
                    return response
                return JsonResponse({"status": "error", "message": "Header not found"})
                
            return JsonResponse({"status": "error", "message": "Unknown action"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
            
    return JsonResponse({"status": "error", "message": "Invalid method"})
