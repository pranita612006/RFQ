from django.db import connection


def active_customer(request):
    """
    Makes the currently selected customer and real-time navbar metrics/alerts
    available in all templates across the entire application.
    """
    ctx = {
        'global_customer_id': request.session.get('active_customer_id', None),
        'global_customer_name': request.session.get('active_customer_name', ''),
        'global_customer_code': request.session.get('active_customer_search_name', ''),
        'has_active_customer': bool(request.session.get('active_customer_id')),
        'navbar_notifications_count': 0,
        'navbar_messages_count': 0,
        'navbar_messages': [],
        'navbar_alerts': {
            'pending_opps': 0,
            'feasibility': 0,
            'bom': 0,
            'blanket_so': 0,
            'total': 0,
        }
    }

    try:
        with connection.cursor() as cur:
            # 1. Real System Notification Counts
            cur.execute("""
                SELECT 
                    (SELECT count(*) FROM tbl_opportunitymaster WHERE status ILIKE '%progress%' OR status = 'Not Started'),
                    (SELECT count(*) FROM tbl_feasibility),
                    (SELECT count(*) FROM tbl_bomcreation),
                    (SELECT count(*) FROM tbl_blanketso)
            """)
            row = cur.fetchone()
            if row:
                pending_opps, feas, bom, bso = [int(v or 0) for v in row]
                total_alerts = pending_opps + feas + bom + bso
                ctx['navbar_alerts'] = {
                    'pending_opps': pending_opps,
                    'feasibility': feas,
                    'bom': bom,
                    'blanket_so': bso,
                    'total': total_alerts,
                }
                ctx['navbar_notifications_count'] = total_alerts

            # 2. Real Recent RFQ Activities for Messages Dropdown
            cur.execute("""
                SELECT item_no, customername, project_name, status, creation_date, part_name
                FROM tbl_opportunitymaster
                WHERE item_no IS NOT NULL
                ORDER BY creation_date DESC NULLS LAST, id DESC
                LIMIT 4
            """)
            cols = [c[0].lower() for c in cur.description]
            messages = []
            for r in cur.fetchall():
                item = dict(zip(cols, r))
                messages.append(item)
            ctx['navbar_messages'] = messages
            ctx['navbar_messages_count'] = len(messages)
    except Exception:
        # Failsafe in case of connection limits or migration
        pass

    return ctx

