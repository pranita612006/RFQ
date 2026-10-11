import datetime
from django.db import connection

def safe_float(val, default=0.0):
    try:
        if val is None:
            return default
        return float(str(val).replace(',', '').strip())
    except Exception:
        return default

def safe_int(val, default=0):
    try:
        if val is None:
            return default
        return int(float(str(val).replace(',', '').strip()))
    except Exception:
        return default

def get_dashboard_v1_data(active_customer_id=None):
    """
    Dashboard v1 (Red Theme): Executive Business & RFQ Opportunity Pipeline Intelligence
    """
    data = {
        'total_opps': 0,
        'total_volume': 0,
        'total_value': 0.0,
        'total_customers': 0,
        'total_items': 0,
        'total_blanket_so': 0,
        'total_feasibility': 0,
        'total_bom': 0,
        'total_bop': 0,
        'total_boc': 0,
        'segment_labels': [],
        'segment_counts': [],
        'sales_labels': [],
        'sales_counts': [],
        'recent_opportunities': [],
        'active_customer_stats': None,
        'lifecycle_counts': {
            'opportunity': 0,
            'feasibility': 0,
            'bom': 0,
            'bop': 0,
            'boc': 0,
            'blanket_so': 0,
        }
    }

    try:
        with connection.cursor() as cur:
            # High-level counts
            try:
                cur.execute("SELECT count(*) FROM tbl_opportunitymaster WHERE item_no IS NOT NULL")
                data['total_opps'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_customerinfo")
                data['total_customers'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_itemcard WHERE no IS NOT NULL")
                data['total_items'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_feasibility WHERE \"Item_No\" IS NOT NULL")
                data['total_feasibility'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_bomcreation WHERE \"BOMCreation_Id\" IS NOT NULL OR \"ItemCreation_Id\" IS NOT NULL")
                data['total_bom'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_bopcreation")
                data['total_bop'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_boc_creation")
                data['total_boc'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_blanketso")
                data['total_blanket_so'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            data['lifecycle_counts'] = {
                'opportunity': data['total_opps'],
                'feasibility': data['total_feasibility'],
                'bom': data['total_bom'],
                'bop': data['total_bop'],
                'boc': data['total_boc'],
                'blanket_so': data['total_blanket_so'],
            }

            # Opportunities details
            try:
                cur.execute("""
                    SELECT item_no, customerid, customername, project_name, status,
                           annual_volume, part_price_1, salesperson_code, segment_description,
                           creation_date, part_name
                    FROM tbl_opportunitymaster
                    WHERE item_no IS NOT NULL
                    ORDER BY creation_date DESC NULLS LAST, id DESC
                """)
                cols = [c[0].lower() for c in cur.description]
                opps = []
                total_val = 0.0
                total_vol = 0

                for r in cur.fetchall():
                    row = dict(zip(cols, r))
                    vol = safe_int(row.get('annual_volume'))
                    price = safe_float(row.get('part_price_1'))
                    project_val = vol * price
                    total_vol += vol
                    total_val += project_val

                    row['calc_volume'] = vol
                    row['calc_price'] = price
                    row['calc_value'] = project_val
                    opps.append(row)

                data['total_volume'] = total_vol
                data['total_value'] = total_val
                data['recent_opportunities'] = opps
            except Exception as e:
                print("Dashboard v1 opps query error:", e)

            # Recent Item Cards (Item Creation)
            try:
                cur.execute("""
                    SELECT no, description, template_name, customername, last_date_modified, status
                    FROM tbl_itemcard
                    WHERE no IS NOT NULL
                    ORDER BY last_date_modified DESC NULLS LAST, no DESC
                    LIMIT 20
                """)
                cols = [c[0].lower() for c in cur.description]
                data['recent_items'] = [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception as e:
                print("Dashboard v1 items query error:", e)

            # Segments breakdown
            try:
                cur.execute("""
                    SELECT COALESCE(NULLIF(segment_description, ''), 'General Automotive') as seg, count(*)
                    FROM tbl_opportunitymaster
                    WHERE item_no IS NOT NULL
                    GROUP BY COALESCE(NULLIF(segment_description, ''), 'General Automotive')
                    ORDER BY count(*) DESC
                """)
                rows = cur.fetchall()
                data['segment_labels'] = [r[0] for r in rows] or ['Passenger Car', 'Commercial Vehicle', 'Two/Three Wheeler']
                data['segment_counts'] = [r[1] for r in rows] or [4, 2, 1]
            except Exception:
                data['segment_labels'] = ['Passenger Car', 'Commercial Vehicle', 'Two/Three Wheeler']
                data['segment_counts'] = [4, 2, 1]

            # Sales reps breakdown
            try:
                cur.execute("""
                    SELECT COALESCE(NULLIF(salesperson_code, ''), 'Standard Team') as sp, count(*)
                    FROM tbl_opportunitymaster
                    WHERE item_no IS NOT NULL
                    GROUP BY COALESCE(NULLIF(salesperson_code, ''), 'Standard Team')
                    ORDER BY count(*) DESC
                """)
                rows = cur.fetchall()
                data['sales_labels'] = [r[0] for r in rows] or ['SGK', 'PRANJIT', 'PNS', 'SGS']
                data['sales_counts'] = [r[1] for r in rows] or [3, 2, 1, 1]
            except Exception:
                data['sales_labels'] = ['SGK', 'PRANJIT', 'PNS', 'SGS']
                data['sales_counts'] = [3, 2, 1, 1]

            # Active customer specific stats
            if active_customer_id:
                try:
                    cur.execute("""
                        SELECT count(*), COALESCE(sum(CAST(NULLIF(regexp_replace(annual_volume, '[^0-9.]', '', 'g'), '') AS numeric)), 0)
                        FROM tbl_opportunitymaster
                        WHERE customerid = %s AND item_no IS NOT NULL
                    """, [active_customer_id])
                    c_row = cur.fetchone()
                    c_opps = c_row[0] if c_row else 0
                    c_vol = safe_int(c_row[1]) if c_row else 0

                    cur.execute("SELECT count(*) FROM tbl_blanketso WHERE selltocustomerno = %s OR customer_id = %s", [active_customer_id, active_customer_id])
                    bso_row = cur.fetchone()
                    c_bso = bso_row[0] if bso_row else 0

                    data['active_customer_stats'] = {
                        'opp_count': c_opps,
                        'total_volume': c_vol,
                        'bso_count': c_bso,
                    }
                except Exception as e:
                    print("Active customer query error:", e)

    except Exception as e:
        print("General error in dashboard v1 data:", e)

    return data


def get_dashboard_v2_data():
    """
    Dashboard v2 (Purple Theme): Engineering, Costing & Manufacturing Progress
    """
    data = {
        'total_feasibility': 0,
        'total_bom': 0,
        'total_bom_items': 0,
        'total_bom_parts': 0,
        'total_bop': 0,
        'total_boc': 0,
        'total_costing_conversions': 0,
        'total_cell_types': 0,
        'feasibility_list': [],
        'bom_list': [],
        'boc_list': [],
        'feasibility_type_labels': [],
        'feasibility_type_counts': [],
        'boc_projects_labels': [],
        'boc_projects_counts': [],
    }

    try:
        with connection.cursor() as cur:
            try:
                cur.execute("SELECT count(*) FROM tbl_feasibility WHERE \"Item_No\" IS NOT NULL")
                data['total_feasibility'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_bomcreation")
                data['total_bom'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_bom_itemlist")
                data['total_bom_items'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_bom_partdetails_master")
                data['total_bom_parts'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_bopcreation")
                data['total_bop'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_boc_creation")
                data['total_boc'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_costing_internalconversion")
                data['total_costing_conversions'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            try:
                cur.execute("SELECT count(*) FROM tbl_bop_cellallienment_type")
                data['total_cell_types'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            # Feasibility breakdown
            try:
                cur.execute("""
                    SELECT COALESCE(NULLIF("FeasibilityType", ''), 'Standard Review') as ftype, count(*)
                    FROM tbl_feasibility
                    WHERE "Item_No" IS NOT NULL
                    GROUP BY COALESCE(NULLIF("FeasibilityType", ''), 'Standard Review')
                """)
                rows = cur.fetchall()
                data['feasibility_type_labels'] = [r[0] for r in rows] or ['Simple Projects', 'Standard Review', 'Complex Engineering']
                data['feasibility_type_counts'] = [r[1] for r in rows] or [5, 2, 1]
            except Exception:
                data['feasibility_type_labels'] = ['Simple Projects', 'Standard Review', 'Complex Engineering']
                data['feasibility_type_counts'] = [5, 2, 1]

            # Feasibility recent list
            try:
                cur.execute("""
                    SELECT "Item_No", "CustomerName", "PartName", "FeasibilityType", "ProjectedVolume", "InitialDate"
                    FROM tbl_feasibility
                    WHERE "Item_No" IS NOT NULL
                    ORDER BY "InitialDate" DESC NULLS LAST
                    LIMIT 8
                """)
                cols = [c[0] for c in cur.description]
                data['feasibility_list'] = [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception as e:
                print("Feasibility list error:", e)

            # BOM list
            try:
                cur.execute("""
                    SELECT "BOMCreation_Id", "Customer_ID", "ItemCreation_Id", "Description", "Creation_Date", "Status"
                    FROM tbl_bomcreation
                    WHERE "BOMCreation_Id" IS NOT NULL OR "ItemCreation_Id" IS NOT NULL
                    ORDER BY "Creation_Date" DESC NULLS LAST, id DESC
                    LIMIT 8
                """)
                cols = [c[0] for c in cur.description]
                data['bom_list'] = [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception as e:
                print("BOM list error:", e)

            # BOC list
            try:
                cur.execute("""
                    SELECT boc_creation_id, customer_name, part_name, project, annual_volume
                    FROM tbl_boc_creation
                    LIMIT 8
                """)
                cols = [c[0] for c in cur.description]
                data['boc_list'] = [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception as e:
                print("BOC list error:", e)

    except Exception as e:
        print("General error in dashboard v2 data:", e)

    return data


def get_dashboard_v3_data(selected_customer_id=None):
    """
    Dashboard v3 (Light Blue Theme): Customer-Centric Account & Commercial Progress
    """
    data = {
        'customers_list': [],
        'selected_customer': None,
        'customer_opps': [],
        'customer_items': [],
        'customer_blanket_so': [],
        'customer_feasibility': [],
        'top_accounts': [],
        'stats': {
            'total_opps': 0,
            'total_volume': 0,
            'total_value': 0.0,
            'total_blanket_orders': 0,
            'items_developed': 0,
            'overall_org_customers': 0,
            'overall_org_opps': 0,
        }
    }

    try:
        with connection.cursor() as cur:
            # 1. Fetch dropdown list of customers in ascending order of customer_id
            try:
                cur.execute("""
                    SELECT customer_id, name, city, search_name
                    FROM tbl_customerinfo
                    WHERE customer_id IS NOT NULL AND customer_id != ''
                    ORDER BY customer_id ASC
                """)
                cols = [c[0] for c in cur.description]
                data['customers_list'] = [dict(zip(cols, r)) for r in cur.fetchall()]
                data['stats']['overall_org_customers'] = len(data['customers_list'])
            except Exception:
                pass

            # Overall org opps
            try:
                cur.execute("SELECT count(*) FROM tbl_opportunitymaster WHERE item_no IS NOT NULL")
                data['stats']['overall_org_opps'] = cur.fetchone()[0] or 0
            except Exception:
                pass

            # Select customer: fallback to CUST-005 (Cooper) or first customer if not specified
            cust_id = selected_customer_id
            if not cust_id and data['customers_list']:
                # Find Cooper Corporation CUST-005 or first
                found = next((c for c in data['customers_list'] if c['customer_id'] == 'CUST-005'), None)
                cust_id = found['customer_id'] if found else data['customers_list'][0]['customer_id']

            # Find selected customer record
            if cust_id:
                try:
                    cur.execute("""
                        SELECT customer_id, name, city, search_name
                        FROM tbl_customerinfo
                        WHERE customer_id = %s
                        LIMIT 1
                    """, [cust_id])
                    cols = [c[0] for c in cur.description]
                    row = cur.fetchone()
                    if row:
                        data['selected_customer'] = dict(zip(cols, row))
                except Exception as e:
                    print("Selected customer query error in dashboard v3:", e)

            if cust_id:
                # Customer Opportunities
                try:
                    cur.execute("""
                        SELECT item_no, project_name, status, annual_volume, part_price_1,
                               salesperson_code, segment_description, creation_date, part_name
                        FROM tbl_opportunitymaster
                        WHERE customerid = %s AND item_no IS NOT NULL
                        ORDER BY creation_date DESC NULLS LAST
                    """, [cust_id])
                    cols = [c[0].lower() for c in cur.description]
                    opps = []
                    c_vol = 0
                    c_val = 0.0

                    for r in cur.fetchall():
                        row = dict(zip(cols, r))
                        vol = safe_int(row.get('annual_volume'))
                        price = safe_float(row.get('part_price_1'))
                        val = vol * price
                        c_vol += vol
                        c_val += val
                        row['calc_volume'] = vol
                        row['calc_price'] = price
                        row['calc_value'] = val
                        # Stage Progress calculation for this project
                        st = (row.get('status') or '').lower()
                        if 'complete' in st or 'won' in st:
                            row['stage_pct'] = 100
                            row['stage_name'] = 'Commercial Ready / Won'
                        elif 'progress' in st:
                            row['stage_pct'] = 65
                            row['stage_name'] = 'Technical & Costing Active'
                        else:
                            row['stage_pct'] = 25
                            row['stage_name'] = 'RFQ Initial Review'
                        opps.append(row)

                    data['customer_opps'] = opps
                    data['stats']['total_opps'] = len(opps)
                    data['stats']['total_volume'] = c_vol
                    data['stats']['total_value'] = c_val
                except Exception as e:
                    print("Customer opps error:", e)

                # Customer Items
                try:
                    cur.execute("""
                        SELECT no, description, template_name, customername, last_date_modified, status
                        FROM tbl_itemcard
                        WHERE (customerid = %s OR customer_id = %s) AND no IS NOT NULL
                        ORDER BY last_date_modified DESC NULLS LAST, no ASC
                    """, [cust_id, cust_id])
                    cols = [c[0] for c in cur.description]
                    items = []
                    for r in cur.fetchall():
                        item_row = dict(zip(cols, r))
                        item_row['type'] = item_row.get('template_name', '')
                        items.append(item_row)
                    data['customer_items'] = items
                    data['stats']['items_developed'] = len(items)
                except Exception as e:
                    # Fallback if only customerid column exists
                    try:
                        cur.execute("""
                            SELECT no, description, template_name, customername, last_date_modified, status
                            FROM tbl_itemcard
                            WHERE customerid = %s AND no IS NOT NULL
                            ORDER BY last_date_modified DESC NULLS LAST, no ASC
                        """, [cust_id])
                        cols = [c[0] for c in cur.description]
                        items = [dict(zip(cols, r)) for r in cur.fetchall()]
                        data['customer_items'] = items
                        data['stats']['items_developed'] = len(items)
                    except Exception as e2:
                        print("Customer items error:", e2)

                # Customer Blanket SOs
                try:
                    cur.execute("""
                        SELECT id, no, bsocreationid, orderdate, status, locationcode
                        FROM tbl_blanketso
                        WHERE selltocustomerno = %s OR customer_id = %s
                    """, [cust_id, cust_id])
                    cols = [c[0] for c in cur.description]
                    bsos = [dict(zip(cols, r)) for r in cur.fetchall()]
                    data['customer_blanket_so'] = bsos
                    data['stats']['total_blanket_orders'] = len(bsos)
                except Exception as e:
                    try:
                        cur.execute("""
                            SELECT id, no, bsocreationid, orderdate, status, locationcode
                            FROM tbl_blanketso
                            WHERE selltocustomerno = %s
                        """, [cust_id])
                        cols = [c[0] for c in cur.description]
                        bsos = [dict(zip(cols, r)) for r in cur.fetchall()]
                        data['customer_blanket_so'] = bsos
                        data['stats']['total_blanket_orders'] = len(bsos)
                    except Exception as e2:
                        print("Blanket SO error:", e2)

            # Top active accounts across all customers
            try:
                cur.execute("""
                    SELECT customerid, customername, count(*) as count_opps,
                           sum(CAST(NULLIF(regexp_replace(annual_volume::text, '[^0-9.]', '', 'g'), '') AS numeric)) as total_vol
                    FROM tbl_opportunitymaster
                    WHERE customerid IS NOT NULL AND item_no IS NOT NULL
                    GROUP BY customerid, customername
                    ORDER BY count_opps DESC, total_vol DESC NULLS LAST
                    LIMIT 8
                """)
                cols = [c[0].lower() for c in cur.description]
                data['top_accounts'] = [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception as e:
                print("Top accounts error:", e)

    except Exception as e:
        print("General error in dashboard v3 data:", e)

    return data

