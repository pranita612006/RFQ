class ActiveCustomerMiddleware:
    """
    Middleware to attach the active customer directly to the request object.
    This allows easy access to request.active_customer in any view.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Determine if this is a main app page request
        path = request.path
        is_page_request = not (
            path.startswith('/static/') or 
            path.startswith('/media/') or 
            path.startswith('/admin/') or
            'javascript' in request.META.get('HTTP_ACCEPT', '') or
            'json' in request.META.get('HTTP_ACCEPT', '')
        )

        if is_page_request:
            customer_id = request.GET.get('customer_id') or request.POST.get('customer_id') or request.POST.get('custId')
            if customer_id:
                request.session['active_customer_id'] = customer_id

            sess_cust_id = request.session.get('active_customer_id')
            if sess_cust_id and (customer_id or not request.session.get('active_customer_name') or not request.session.get('active_customer_search_name')):
                try:
                    from apps.opportunities.models import CustomerInfo
                    cust = CustomerInfo.objects.filter(customer_id=sess_cust_id).first()
                    if cust:
                        request.session['active_customer_name'] = getattr(cust, 'name', '') or ''
                        request.session['active_customer_search_name'] = getattr(cust, 'search_name', '') or ''
                    else:
                        if customer_id:
                            request.session['active_customer_name'] = request.GET.get('name') or request.POST.get('name') or ''
                            request.session['active_customer_search_name'] = request.GET.get('search_name') or request.POST.get('search_name') or ''
                except Exception:
                    if customer_id:
                        request.session['active_customer_name'] = request.GET.get('name') or request.POST.get('name') or ''
                        request.session['active_customer_search_name'] = request.GET.get('search_name') or request.POST.get('search_name') or ''
                request.session.modified = True


        # Attach the customer dictionary directly to the request object
        request.active_customer = {
            'id': request.session.get('active_customer_id'),
            'name': request.session.get('active_customer_name'),
            'search_name': request.session.get('active_customer_search_name'),
        }
        
        # Helper boolean
        request.has_active_customer = bool(request.active_customer['id'])

        response = self.get_response(request)
        return response
