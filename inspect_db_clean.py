# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ApproverecTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'ApproveRec_task'


class BocTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'BOC_task'


class BomTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'BOM_task'


class BopTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'BOP_task'


class BlanketsalesTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'BlanketSales_task'


class CostingbccalTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'CostingBCCal_task'


class ReportTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'Report_task'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class AuthtokenToken(models.Model):
    key = models.CharField(primary_key=True, max_length=40)
    created = models.DateTimeField()
    user = models.OneToOneField(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'authtoken_token'


class CustomerCreationCustomer(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer_id = models.CharField(unique=True, max_length=20)
    name = models.CharField(max_length=100)
    search_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'customer_creation_customer'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DynDtHideshowfilter(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent = models.CharField(max_length=255, blank=True, null=True)
    key = models.CharField(max_length=255)
    value = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'dyn_dt_hideshowfilter'


class DynDtModelfilter(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent = models.CharField(max_length=255, blank=True, null=True)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'dyn_dt_modelfilter'


class DynDtPageitems(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent = models.CharField(max_length=255, blank=True, null=True)
    items_per_page = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dyn_dt_pageitems'


class FeasibilityFormFeasibility(models.Model):
    id = models.BigAutoField(primary_key=True)
    item_no = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=255)
    enq_no = models.CharField(max_length=100)
    part_name = models.CharField(max_length=255)
    application = models.CharField(max_length=255)
    projected_volume = models.CharField(max_length=100)
    initial_date = models.CharField(max_length=100)
    part_no = models.CharField(max_length=100)
    feasibility_no = models.CharField(max_length=100)
    vehicle_model = models.CharField(max_length=255)
    daily_peak = models.CharField(max_length=100)
    sop_date = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'feasibility_form_feasibility'


class ItemCreationItemcard(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer_id = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=200)
    no = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    base_unit_of_measure = models.CharField(max_length=50, blank=True, null=True)
    shelf_no = models.CharField(max_length=50, blank=True, null=True)
    item_category_code = models.CharField(max_length=50, blank=True, null=True)
    product_group_code = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    hsn_sac_code = models.CharField(max_length=50, blank=True, null=True)
    gst_group_code = models.CharField(max_length=50, blank=True, null=True)
    revision_no = models.CharField(max_length=50, blank=True, null=True)
    template_name = models.CharField(max_length=50, blank=True, null=True)
    monthyear = models.CharField(max_length=20, blank=True, null=True)
    fy = models.CharField(max_length=20, blank=True, null=True)
    quarter = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'item_creation_itemcard'


class OpportunitiesOpportunity(models.Model):
    id = models.BigAutoField(primary_key=True)
    projectname = models.CharField(db_column='projectName', max_length=255, blank=True, null=True)  # Field name made lowercase.
    customername = models.CharField(db_column='customerName', max_length=255, blank=True, null=True)  # Field name made lowercase.
    contactname = models.CharField(db_column='contactName', max_length=255, blank=True, null=True)  # Field name made lowercase.
    contactno = models.CharField(db_column='contactNo', max_length=20, blank=True, null=True)  # Field name made lowercase.
    itemno = models.CharField(db_column='itemNo', max_length=100, blank=True, null=True)  # Field name made lowercase.
    custid = models.CharField(db_column='custId', max_length=100, blank=True, null=True)  # Field name made lowercase.
    estimatedsalesprice = models.FloatField(db_column='estimatedSalesPrice')  # Field name made lowercase.
    nominatedprice = models.FloatField(db_column='nominatedPrice')  # Field name made lowercase.
    creationdate = models.DateField(db_column='creationDate', blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'opportunities_opportunity'


class PagesProduct(models.Model):
    name = models.CharField(max_length=100)
    info = models.CharField(max_length=100)
    price = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pages_product'


class TblAccessmanagement(models.Model):
    user_group = models.CharField(max_length=100)
    form_name = models.CharField(max_length=100)
    has_access = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'tbl_accessmanagement'


class TblApplytemplate(models.Model):
    id = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    item_category_code = models.TextField(blank=True, null=True)
    costing_method = models.TextField(blank=True, null=True)
    inventory_posting_group = models.TextField(blank=True, null=True)
    price_profit_calculation = models.TextField(blank=True, null=True)
    gen_prod_posting_group = models.TextField(blank=True, null=True)
    replenishment_system = models.TextField(blank=True, null=True)
    qc_applicable = models.TextField(blank=True, null=True)
    manufacturing_policy = models.TextField(blank=True, null=True)
    assembly_policy = models.TextField(blank=True, null=True)
    reordering_policy = models.TextField(blank=True, null=True)
    include_inventory = models.TextField(blank=True, null=True)
    gst_credit = models.TextField(blank=True, null=True)
    flushing_method = models.TextField(blank=True, null=True)
    template_applied = models.TextField(blank=True, null=True)
    rounding_precision = models.TextField(blank=True, null=True)
    gst_group_code = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_applytemplate'


class TblBlanketso(models.Model):
    id = models.IntegerField(blank=True, null=True)
    no = models.CharField(max_length=50, blank=True, null=True)
    documentdate = models.CharField(max_length=20, blank=True, null=True)
    selltocustomerno = models.CharField(max_length=50, blank=True, null=True)
    billtocustomerno = models.CharField(max_length=50, blank=True, null=True)
    selltocustomername = models.CharField(max_length=150, blank=True, null=True)
    orderdate = models.CharField(max_length=20, blank=True, null=True)
    externaldocumentno = models.CharField(max_length=100, blank=True, null=True)
    locationcode = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    billtocontact = models.CharField(max_length=100, blank=True, null=True)
    billtocountryregioncode = models.CharField(max_length=50, blank=True, null=True)
    billtoname = models.CharField(max_length=150, blank=True, null=True)
    billtopostcode = models.CharField(max_length=20, blank=True, null=True)
    currencycode = models.CharField(max_length=20, blank=True, null=True)
    plantcode = models.CharField(max_length=50, blank=True, null=True)
    postingdate = models.CharField(max_length=20, blank=True, null=True)
    productgroupcode = models.CharField(max_length=50, blank=True, null=True)
    salespersoncode = models.CharField(max_length=50, blank=True, null=True)
    selltocontact = models.CharField(max_length=100, blank=True, null=True)
    selltocountryregioncode = models.CharField(max_length=50, blank=True, null=True)
    selltopostcode = models.CharField(max_length=20, blank=True, null=True)
    shiptocode = models.CharField(max_length=50, blank=True, null=True)
    shiptocontact = models.CharField(max_length=100, blank=True, null=True)
    shiptocountryregioncode = models.CharField(max_length=50, blank=True, null=True)
    shiptoname = models.CharField(max_length=150, blank=True, null=True)
    shiptopostcode = models.CharField(max_length=20, blank=True, null=True)
    bsocreationid = models.CharField(max_length=50, blank=True, null=True)
    bso_rowid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=150, blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_blanketso'


class TblBocCreation(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=150, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_rowid = models.CharField(max_length=50, blank=True, null=True)
    boc_creation_id = models.CharField(max_length=50, blank=True, null=True)
    customer_drgno = models.CharField(max_length=100, blank=True, null=True)
    drg_revno = models.CharField(max_length=50, blank=True, null=True)
    drg_revdate = models.TextField(blank=True, null=True)
    customer_partsetno = models.CharField(max_length=100, blank=True, null=True)
    part_name = models.CharField(max_length=150, blank=True, null=True)
    project = models.CharField(max_length=150, blank=True, null=True)
    project_sopdate = models.TextField(blank=True, null=True)
    rfq_no = models.CharField(max_length=100, blank=True, null=True)
    annual_volume = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    tool_descriptionforboc = models.TextField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_boc_creation'


class TblBocCreationEcn(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=150, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_rowid = models.CharField(max_length=50, blank=True, null=True)
    boc_creation_id = models.CharField(max_length=50, blank=True, null=True)
    customer_drgno = models.CharField(max_length=100, blank=True, null=True)
    drg_revno = models.CharField(max_length=50, blank=True, null=True)
    drg_revdate = models.TextField(blank=True, null=True)
    customer_partsetno = models.CharField(max_length=100, blank=True, null=True)
    part_name = models.CharField(max_length=150, blank=True, null=True)
    project = models.CharField(max_length=150, blank=True, null=True)
    project_sopdate = models.TextField(blank=True, null=True)
    rfq_no = models.CharField(max_length=100, blank=True, null=True)
    annual_volume = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    tool_descriptionforboc = models.TextField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)
    ecn_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_boc_creation_ecn'


class TblBocStatus(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_creationid = models.CharField(max_length=50, blank=True, null=True)
    boc = models.CharField(max_length=100, blank=True, null=True)
    supplier = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    date_sent = models.DateField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    basic_price_quoted_by_supplier_in_rs = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    final_price_submission_date = models.TextField(blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_boc_status'


class TblBocStatusEcn(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_creationid = models.CharField(max_length=50, blank=True, null=True)
    boc = models.CharField(max_length=100, blank=True, null=True)
    supplier = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    date_sent = models.DateField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    basic_price_quoted_by_supplier_in_rs = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    final_price_submission_date = models.DateField(blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)
    completedon = models.DateField(blank=True, null=True)
    ecn_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_boc_status_ecn'


class TblBocTolling(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_creationid = models.CharField(max_length=50, blank=True, null=True)
    tool_description_boc = models.TextField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_boc_tolling'


class TblBocTollingEcn(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_creationid = models.CharField(max_length=50, blank=True, null=True)
    tool_description_boc = models.TextField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    completedon = models.TextField(blank=True, null=True)
    ecn_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_boc_tolling_ecn'


class TblBomHeader(models.Model):
    no = models.CharField(max_length=50, blank=True, null=True)
    production_bom_no = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    description_2 = models.TextField(blank=True, null=True)
    search_name = models.CharField(max_length=100, blank=True, null=True)
    unit_of_measure_code = models.CharField(max_length=20, blank=True, null=True)
    low_level_code = models.IntegerField(blank=True, null=True)
    creation_date = models.DateField(blank=True, null=True)
    last_date_modified = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=30, blank=True, null=True)
    version_nos = models.CharField(max_length=30, blank=True, null=True)
    no_series = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bom_header'


class TblBomItemlist(models.Model):
    part_no = models.CharField(max_length=100)
    part_description = models.TextField(blank=True, null=True)
    base_unit_measure = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bom_itemlist'


class TblBomLine(models.Model):
    production_bom_no = models.CharField(max_length=100, blank=True, null=True)
    routing_link_code = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    no = models.IntegerField(blank=True, null=True)
    description = models.IntegerField(blank=True, null=True)
    quantity_per = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    unit_of_measure_code = models.CharField(max_length=100, blank=True, null=True)
    scrap = models.CharField(max_length=100, blank=True, null=True)
    principal_input = models.CharField(max_length=100, blank=True, null=True)
    calculation_formula = models.CharField(max_length=100, blank=True, null=True)
    depth = models.IntegerField(blank=True, null=True)
    ending_date = models.DateField(blank=True, null=True)
    leadtime_offset = models.CharField(max_length=100, blank=True, null=True)
    length = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    position_2 = models.CharField(max_length=100, blank=True, null=True)
    position_3 = models.CharField(max_length=100, blank=True, null=True)
    starting_date = models.DateField(blank=True, null=True)
    variant_code = models.CharField(max_length=100, blank=True, null=True)
    weight = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    width = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    version_code = models.CharField(max_length=100, blank=True, null=True)
    line_no = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bom_line'


class TblBomPartdetailsMaster(models.Model):
    part_no = models.CharField(db_column='Part No', max_length=100, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    part_description = models.TextField(db_column='Part Description', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    base_unit_of_measure = models.CharField(db_column='Base Unit of Measure', max_length=50, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    customer = models.CharField(db_column='Customer', max_length=150, blank=True, null=True)  # Field name made lowercase.
    classification = models.CharField(db_column='Classification', max_length=100, blank=True, null=True)  # Field name made lowercase.
    cost_price = models.DecimalField(db_column='Cost_Price', max_digits=18, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    settle_price = models.DecimalField(db_column='Settle Price', max_digits=18, decimal_places=2, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    categorisation = models.CharField(db_column='Categorisation', max_length=100, blank=True, null=True)  # Field name made lowercase.
    part_status = models.CharField(db_column='Part_Status', max_length=50, blank=True, null=True)  # Field name made lowercase.
    part_type = models.CharField(db_column='Part_Type', max_length=50, blank=True, null=True)  # Field name made lowercase.
    latest_inward = models.DateField(db_column='Latest Inward', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    rate = models.DecimalField(db_column='Rate', max_digits=18, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    conversion_factor = models.DecimalField(db_column='Conversion Factor', max_digits=18, decimal_places=4, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'tbl_bom_partdetails_master'


class TblBomProditemPartgrpmaster(models.Model):
    row_id = models.AutoField(primary_key=True)
    grp_partno = models.CharField(max_length=100, blank=True, null=True)
    grp_part_description = models.TextField(blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    part_no = models.CharField(max_length=100, blank=True, null=True)
    part_description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50, blank=True, null=True)
    bom_quantity = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    total_bom_quantity = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    inserted_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bom_proditem_partgrpmaster'


class TblBomProditemPartgrpmasterRawdata(models.Model):
    grp_partno = models.CharField(max_length=50, blank=True, null=True)
    grp_part_description = models.CharField(max_length=200, blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    part_no = models.CharField(max_length=50, blank=True, null=True)
    part_description = models.CharField(max_length=200, blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50, blank=True, null=True)
    bom_quantity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_bom_quantity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bom_proditem_partgrpmaster_rawdata'


class TblBomcrationPartselectionEcn(models.Model):
    entry_type = models.CharField(max_length=50, blank=True, null=True)
    grp_part_number = models.CharField(max_length=100, blank=True, null=True)
    grp_part_description = models.TextField(blank=True, null=True)
    part_number = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    quantity_packet = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit_of_measure_code = models.CharField(max_length=50, blank=True, null=True)
    categorisation = models.CharField(max_length=100, blank=True, null=True)
    routing_link_code = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.TextField(blank=True, null=True)
    end_date = models.TextField(blank=True, null=True)
    part_status = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=100, blank=True, null=True)
    bomcreation_id = models.CharField(max_length=100, blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    ecn_id = models.CharField(max_length=100, blank=True, null=True)
    itemcreation_ecn = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bomcration_partselection_ecn'


class TblBomcreation(models.Model):
    id = models.IntegerField(primary_key=True)
    customer_id = models.CharField(db_column='Customer_ID', max_length=50, blank=True, null=True)  # Field name made lowercase.
    itemcreation_id = models.CharField(db_column='ItemCreation_Id', max_length=50, blank=True, null=True)  # Field name made lowercase.
    bom_rowid = models.IntegerField(db_column='BOM_RowID', blank=True, null=True)  # Field name made lowercase.
    bomcreation_id = models.CharField(db_column='BOMCreation_Id', max_length=50, blank=True, null=True)  # Field name made lowercase.
    description = models.TextField(db_column='Description', blank=True, null=True)  # Field name made lowercase.
    description_2 = models.TextField(db_column='Description_2', blank=True, null=True)  # Field name made lowercase.
    search_name = models.CharField(db_column='Search_Name', max_length=100, blank=True, null=True)  # Field name made lowercase.
    unit_of_measure_code = models.CharField(db_column='Unit_of_Measure_Code', max_length=50, blank=True, null=True)  # Field name made lowercase.
    low_level_code = models.CharField(db_column='Low-Level Code', max_length=50, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    creation_date = models.DateField(db_column='Creation_Date', blank=True, null=True)  # Field name made lowercase.
    last_date_modified = models.DateField(db_column='Last_Date_Modified', blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='Status', max_length=100, blank=True, null=True)  # Field name made lowercase.
    version_number = models.CharField(db_column='Version_Number', max_length=50, blank=True, null=True)  # Field name made lowercase.
    series = models.CharField(db_column='Series', max_length=50, blank=True, null=True)  # Field name made lowercase.
    table_id = models.CharField(db_column='Table_Id', max_length=50, blank=True, null=True)  # Field name made lowercase.
    remark = models.TextField(db_column='Remark', blank=True, null=True)  # Field name made lowercase.
    is_download = models.IntegerField(db_column='Is_Download', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_bomcreation'


class TblBomcreationEcn(models.Model):
    customer_id = models.IntegerField(blank=True, null=True)
    itemcreation_id = models.IntegerField(blank=True, null=True)
    bom_rowid = models.IntegerField(blank=True, null=True)
    bomcreation_id = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    description_2 = models.TextField(blank=True, null=True)
    search_name = models.TextField(blank=True, null=True)
    unit_of_measure_code = models.CharField(max_length=50, blank=True, null=True)
    low_level_code = models.IntegerField(db_column='Low-Level Code', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    creation_date = models.DateField(blank=True, null=True)
    last_date_modified = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    version_number = models.IntegerField(blank=True, null=True)
    series = models.CharField(max_length=50, blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    ecn_id = models.IntegerField(blank=True, null=True)
    itemcreation_ecn = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bomcreation_ecn'


class TblBomcreationPartselection(models.Model):
    id = models.IntegerField(db_column='Id', primary_key=True)  # Field name made lowercase.
    entry_type = models.CharField(db_column='Entry_Type', max_length=50, blank=True, null=True)  # Field name made lowercase.
    grp_part_number = models.CharField(max_length=100, blank=True, null=True)
    grp_part_description = models.TextField(blank=True, null=True)
    part_number = models.CharField(db_column='Part_Number', max_length=100, blank=True, null=True)  # Field name made lowercase.
    quantity = models.DecimalField(db_column='Quantity', max_digits=65535, decimal_places=65535, blank=True, null=True)  # Field name made lowercase.
    quantity_packet = models.DecimalField(db_column='Quantity_Packet', max_digits=65535, decimal_places=65535, blank=True, null=True)  # Field name made lowercase.
    description = models.TextField(db_column='Description', blank=True, null=True)  # Field name made lowercase.
    unit_of_measure_code = models.CharField(db_column='Unit_of_Measure_Code', max_length=50, blank=True, null=True)  # Field name made lowercase.
    categorisation = models.CharField(db_column='Categorisation', max_length=100, blank=True, null=True)  # Field name made lowercase.
    routing_link_code = models.CharField(db_column='Routing_Link_Code', max_length=100, blank=True, null=True)  # Field name made lowercase.
    start_date = models.TextField(blank=True, null=True)
    end_date = models.TextField(blank=True, null=True)
    part_status = models.CharField(db_column='Part_Status', max_length=100, blank=True, null=True)  # Field name made lowercase.
    itemcreation_id = models.CharField(db_column='ItemCreation_Id', max_length=50, blank=True, null=True)  # Field name made lowercase.
    bomcreation_id = models.CharField(db_column='BOMCreation_ID', max_length=50, blank=True, null=True)  # Field name made lowercase.
    customer_id = models.CharField(db_column='Customer_ID', max_length=50, blank=True, null=True)  # Field name made lowercase.
    table_id = models.CharField(db_column='Table_Id', max_length=50, blank=True, null=True)  # Field name made lowercase.
    table_status = models.CharField(db_column='Table_Status', max_length=100, blank=True, null=True)  # Field name made lowercase.
    completedon = models.DateField(db_column='CompletedOn', blank=True, null=True)  # Field name made lowercase.
    last_modified_date = models.DateField(db_column='Last_Modified_Date', blank=True, null=True)  # Field name made lowercase.
    is_download = models.IntegerField(db_column='Is_Download', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_bomcreation_partselection'


class TblBopCellallienment(models.Model):
    product_category = models.CharField(max_length=150, blank=True, null=True)
    process = models.CharField(max_length=150, blank=True, null=True)
    manufacturing_loacation = models.CharField(max_length=150, blank=True, null=True)
    cell = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    bopcreationid = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    completedon = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_cellallienment'


class TblBopCellallienmentEcn(models.Model):
    product_category = models.CharField(max_length=150, blank=True, null=True)
    process = models.CharField(max_length=150, blank=True, null=True)
    manufacturing_loacation = models.CharField(max_length=150, blank=True, null=True)
    cell = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    bopcreationid = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    completedon = models.DateField(blank=True, null=True)
    ecn_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_ecn = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_cellallienment_ecn'


class TblBopCellallienmentType(models.Model):
    process = models.CharField(max_length=100)
    manufacturing_loacation = models.CharField(max_length=150, blank=True, null=True)
    cell = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_cellallienment_type'


class TblBopCycletime(models.Model):
    process = models.CharField(max_length=100)
    station = models.CharField(max_length=100, blank=True, null=True)
    production_shift = models.CharField(max_length=50, blank=True, null=True)
    run_time_sec = models.IntegerField(blank=True, null=True)
    run_time_mins = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    setup_time_mins = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_cycletime'


class TblBopMachinecenter(models.Model):
    no = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    work_center_no = models.CharField(max_length=50, blank=True, null=True)
    capacity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    efficiency = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    search_name = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_machinecenter'


class TblBopTab(models.Model):
    seq_no = models.IntegerField(blank=True, null=True)
    operation_no = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    costcenter_no = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    categorisation = models.CharField(max_length=150, blank=True, null=True)
    run_time_sec = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    run_time_min = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    boq = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    total_run_time = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    cycle_time = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    mhr_year = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    mhr_lower = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    mhr_higher = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    costperqnty = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    bopcreationid = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    type_selected = models.CharField(max_length=100, blank=True, null=True)
    completedon = models.TextField(blank=True, null=True)
    last_modified_date = models.TextField(blank=True, null=True)
    is_download = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_tab'


class TblBopTabEcn(models.Model):
    seq_no = models.IntegerField(blank=True, null=True)
    operation_no = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    costcenter_no = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    categorisation = models.CharField(max_length=150, blank=True, null=True)
    run_time_sec = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    run_time_min = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    boq = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    total_run_time = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    cycle_time = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    mhr_year = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    mhr_lower = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    mhr_higher = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    costperqnty = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    bopcreationid = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    type_selected = models.CharField(max_length=100, blank=True, null=True)
    completedon = models.TextField(blank=True, null=True)
    ecn_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_ecn = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_tab_ecn'


class TblBopTolling(models.Model):
    tool_description = models.TextField(blank=True, null=True)
    uom = models.CharField(max_length=50, blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    settled_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total_settledprice = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    entry_date = models.DateField(blank=True, null=True)
    bopcreationid = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.IntegerField(blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    completedon = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_tolling'


class TblBopTollingEcn(models.Model):
    tool_description = models.TextField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    bopcreationid = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    completedon = models.DateField(blank=True, null=True)
    ecn_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_ecn = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_tolling_ecn'


class TblBopTollingN(models.Model):
    tool_description = models.TextField(blank=True, null=True)
    uom = models.CharField(max_length=50, blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    settled_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    total_settledprice = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    entry_date = models.DateField(blank=True, null=True)
    bopcreationid = models.IntegerField(blank=True, null=True)
    itemcreation_id = models.IntegerField(blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    customer_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_tolling_n'


class TblBopTollingTodolist(models.Model):
    tool_description = models.TextField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    bopcreationid = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.IntegerField(blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    completedon = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_tolling_todolist'


class TblBopToolMeasure(models.Model):
    id = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    uom = models.CharField(max_length=50, blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    settled_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    customer_code = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_tool_measure'


class TblBopTypes(models.Model):
    id = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    no = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    work_center_group_code = models.CharField(max_length=50, blank=True, null=True)
    alternate_work_center = models.CharField(max_length=50, blank=True, null=True)
    unit_of_measure_code = models.CharField(max_length=50, blank=True, null=True)
    capacity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    shop_calendar_code = models.CharField(max_length=50, blank=True, null=True)
    search_name = models.CharField(max_length=150, blank=True, null=True)
    categorisation = models.CharField(max_length=100, blank=True, null=True)
    costperquantity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    mhr_year = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    mhr_higher = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    mhr_lower = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    product_line = models.CharField(db_column='Product Line', max_length=100, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_code = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_types'


class TblBopWorkcenter(models.Model):
    no = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    alternate_work_center = models.CharField(max_length=50, blank=True, null=True)
    work_center_group_code = models.CharField(max_length=50, blank=True, null=True)
    unit_of_measure_code = models.CharField(max_length=30, blank=True, null=True)
    capacity = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    shop_calendar_code = models.CharField(max_length=50, blank=True, null=True)
    search_name = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bop_workcenter'


class TblBopcreation(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.IntegerField(blank=True, null=True)
    bop_rowid = models.IntegerField(blank=True, null=True)
    bopcreation_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    drawing_no = models.CharField(max_length=100, blank=True, null=True)
    drawing_revision_no = models.CharField(max_length=50, blank=True, null=True)
    revision_date = models.DateField(blank=True, null=True)
    part_set_no = models.CharField(max_length=100, blank=True, null=True)
    part_name = models.CharField(max_length=200, blank=True, null=True)
    product_category = models.CharField(max_length=150, blank=True, null=True)
    project = models.CharField(max_length=150, blank=True, null=True)
    entry_date = models.DateField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    action_status = models.CharField(max_length=50, blank=True, null=True)
    last_modified_date = models.DateField(blank=True, null=True)
    is_download = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bopcreation'


class TblBopcreationEcn(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    bop_rowid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bopcreation_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    drawing_no = models.CharField(max_length=100, blank=True, null=True)
    drawing_revision_no = models.CharField(max_length=50, blank=True, null=True)
    revision_date = models.DateField(blank=True, null=True)
    part_set_no = models.CharField(max_length=100, blank=True, null=True)
    part_name = models.CharField(max_length=200, blank=True, null=True)
    product_category = models.CharField(max_length=150, blank=True, null=True)
    project = models.CharField(max_length=150, blank=True, null=True)
    entry_date = models.DateField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    ecn_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bopcreation_ecn'


class TblBsoLocationcode(models.Model):
    location_code = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'tbl_bso_locationcode'


class TblBsoSaleslines(models.Model):
    id = models.IntegerField(blank=True, null=True)
    documenttype = models.CharField(max_length=50, blank=True, null=True)
    documentno = models.CharField(max_length=50, blank=True, null=True)
    selltocustomerno = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    lineno = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    no = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    locationcode = models.CharField(max_length=50, blank=True, null=True)
    reserve = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    unitofmeasurecode = models.CharField(max_length=50, blank=True, null=True)
    lineamountexcltax = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    shipmentdate = models.CharField(max_length=20, blank=True, null=True)
    outstandingquantity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    pricefromdate = models.CharField(max_length=20, blank=True, null=True)
    pricetodate = models.CharField(max_length=20, blank=True, null=True)
    remarks = models.CharField(max_length=250, blank=True, null=True)
    unitpriceexcltax = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    linediscount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    plantcode = models.CharField(max_length=50, blank=True, null=True)
    rmbase = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    bocbase = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    bsocreationid = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=150, blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_bso_saleslines'


class TblCell(models.Model):
    id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_cell'


class TblCelltype(models.Model):
    id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=150, blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_celltype'


class TblCostingInternalconversion(models.Model):
    description = models.CharField(max_length=150, blank=True, null=True)
    mhr = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    run_time_sec = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    perhouroutput = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rateperunit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    boq = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    contributionpercentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    mhr_category = models.CharField(max_length=50, blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_costing_internalconversion'


class TblCustomerinfo(models.Model):
    customer_id = models.TextField(blank=True, null=True)
    cust_code = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    search_name = models.TextField(blank=True, null=True)
    shortname = models.TextField(blank=True, null=True)
    name2 = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    address2 = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    contact = models.TextField(blank=True, null=True)
    payment_terms_code = models.TextField(blank=True, null=True)
    primary_contact_no = models.TextField(blank=True, null=True)
    country_region_code = models.TextField(db_column='Country/Region Code', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    post_code = models.TextField(db_column='Post Code', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    os_template = models.TextField(blank=True, null=True)
    group_oem_tier_1 = models.TextField(db_column='GROUP-OEM/Tier-1', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'tbl_customerinfo'


class TblCustomerinfo1(models.Model):
    customer_id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=200, blank=True, null=True)
    search_name = models.CharField(max_length=200, blank=True, null=True)
    shortname = models.CharField(max_length=100, blank=True, null=True)
    group_oem_tier_1 = models.CharField(db_column='GROUP-OEM/Tier-1', max_length=100, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    name2 = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    address2 = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    payment_terms_code = models.CharField(max_length=50, blank=True, null=True)
    primary_contact_no = models.CharField(max_length=50, blank=True, null=True)
    country_region_code = models.CharField(db_column='Country/Region Code', max_length=50, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    post_code = models.CharField(db_column='Post Code', max_length=20, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    vendor_codes = models.CharField(max_length=100, blank=True, null=True)
    structure = models.CharField(max_length=100, blank=True, null=True)
    currency_code = models.CharField(db_column='Currency Code', max_length=10, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'tbl_customerinfo1'


class TblDtassigmentyeardata(models.Model):
    category = models.CharField(max_length=100, blank=True, null=True)
    cost = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_dtassigmentyeardata'


class TblDtcategorylist(models.Model):
    rowid = models.IntegerField(primary_key=True)
    category = models.CharField(max_length=300, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_dtcategorylist'


class TblEmpdetails(models.Model):
    emp_username = models.TextField(blank=True, null=True)
    emp_name = models.TextField(blank=True, null=True)
    emp_designations = models.TextField(blank=True, null=True)
    emp_password = models.TextField(blank=True, null=True)
    password_reset_status = models.TextField(blank=True, null=True)
    isadmin = models.TextField(blank=True, null=True)
    user_type = models.TextField(blank=True, null=True)
    email_id = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_empdetails'


class TblEmpdetailsOrg(models.Model):
    emp_username = models.CharField(primary_key=True, max_length=100)
    emp_name = models.CharField(max_length=150, blank=True, null=True)
    emp_designations = models.CharField(max_length=150, blank=True, null=True)
    emp_password = models.CharField(max_length=255, blank=True, null=True)
    password_reset_status = models.BooleanField(blank=True, null=True)
    isadmin = models.BooleanField(blank=True, null=True)
    user_type = models.CharField(db_column='User Type', max_length=50, blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    email_id = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_empdetails_org'


class TblEmpdetailsUseraccess(models.Model):
    emp_username = models.TextField(blank=True, null=True)
    user_type = models.TextField(blank=True, null=True)
    accessto = models.TextField(blank=True, null=True)
    access_type = models.TextField(blank=True, null=True)
    lastmodifieddate = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_empdetails_useraccess'


class TblFeasibility(models.Model):
    feasibilityno = models.TextField(db_column='FeasibilityNo', blank=True, null=True)  # Field name made lowercase.
    item_no = models.TextField(db_column='Item_No', blank=True, null=True)  # Field name made lowercase.
    customername = models.TextField(db_column='CustomerName', blank=True, null=True)  # Field name made lowercase.
    enqno = models.TextField(db_column='EnqNo', blank=True, null=True)  # Field name made lowercase.
    partname = models.TextField(db_column='PartName', blank=True, null=True)  # Field name made lowercase.
    application = models.TextField(db_column='Application', blank=True, null=True)  # Field name made lowercase.
    feasibilitytype = models.TextField(db_column='FeasibilityType', blank=True, null=True)  # Field name made lowercase.
    projectedvolume = models.TextField(db_column='ProjectedVolume', blank=True, null=True)  # Field name made lowercase.
    projectclassification = models.TextField(db_column='ProjectClassification', blank=True, null=True)  # Field name made lowercase.
    initialdate = models.DateField(db_column='InitialDate', blank=True, null=True)  # Field name made lowercase.
    updatedon = models.DateField(db_column='UpdatedOn', blank=True, null=True)  # Field name made lowercase.
    partno = models.TextField(db_column='PartNo', blank=True, null=True)  # Field name made lowercase.
    vehicle_model = models.TextField(db_column='Vehicle/Model', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dailypeakvolumes = models.TextField(db_column='DailyPeakVolumes', blank=True, null=True)  # Field name made lowercase.
    dateofsop = models.DateField(db_column='DateofSOP', blank=True, null=True)  # Field name made lowercase.
    availability_of_customer_inter_f = models.TextField(db_column='Availability of Customer Inter_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    availability_of_customer_inter_r = models.TextField(db_column='Availability of Customer Inter_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    availability_of_customer_inter_c = models.TextField(db_column='Availability of Customer Inter_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    does_vaipl_possess_the_technology_and_engineering_f = models.TextField(db_column='Does VAIPL possess the technology and engineering_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    does_vaipl_possess_the_technology_and_engineering_r = models.TextField(db_column='Does VAIPL possess the technology and engineering_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    does_vaipl_possess_the_technology_and_engineering_c = models.TextField(db_column='Does VAIPL possess the technology and engineering_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_availability_of_tubing_raw_mat_f = models.TextField(db_column='RAW_Availability of tubing raw mat_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_availability_of_tubing_raw_mat_r = models.TextField(db_column='RAW_Availability of tubing raw mat_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_availability_of_tubing_raw_mat_c = models.TextField(db_column='RAW_Availability of tubing raw mat_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_sourcing_of_raw_material_for_b_f = models.TextField(db_column='RAW_Sourcing of raw material for B_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_sourcing_of_raw_material_for_b_r = models.TextField(db_column='RAW_Sourcing of raw material for B_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_sourcing_of_raw_material_for_b_c = models.TextField(db_column='RAW_Sourcing of raw material for B_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_is_there_any_customer_designated_source_f = models.TextField(db_column='RAW_Is there any customer designated source_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_is_there_any_customer_designated_source_r = models.TextField(db_column='RAW_Is there any customer designated source_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_is_there_any_customer_designated_source_c = models.TextField(db_column='RAW_Is there any customer designated source_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_are_product_safety_related_characteristics_f = models.TextField(db_column='RAW_Are product safety related characteristics_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_are_product_safety_related_characteristics_r = models.TextField(db_column='RAW_Are product safety related characteristics_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_are_product_safety_related_characteristics_c = models.TextField(db_column='RAW_Are product safety related characteristics_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_statutory_regulatory_requirments_f = models.TextField(db_column='RAW_Statutory & regulatory requirments_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_statutory_regulatory_requirments_r = models.TextField(db_column='RAW_Statutory & regulatory requirments_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_statutory_regulatory_requirments_c = models.TextField(db_column='RAW_Statutory & regulatory requirments_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_country_of_receipt_f = models.TextField(db_column='RAW_Country of receipt_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_country_of_receipt_r = models.TextField(db_column='RAW_Country of receipt_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_country_of_receipt_c = models.TextField(db_column='RAW_Country of receipt_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_country_of_shipment_f = models.TextField(db_column='RAW_Country of shipment_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_country_of_shipment_r = models.TextField(db_column='RAW_Country of shipment_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_country_of_shipment_c = models.TextField(db_column='RAW_Country of shipment_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_customer_identified_country_of_destination_f = models.TextField(db_column='RAW_Customer identified country of destination_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_customer_identified_country_of_destination_r = models.TextField(db_column='RAW_Customer identified country of destination_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_customer_identified_country_of_destination_c = models.TextField(db_column='RAW_Customer identified country of destination_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_is_applicable_communication_to_hr_f = models.TextField(db_column='RAW_is applicable - Communication to HR_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_is_applicable_communication_to_hr_r = models.TextField(db_column='RAW_is applicable - Communication to HR_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_is_applicable_communication_to_hr_c = models.TextField(db_column='RAW_is applicable - Communication to HR_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_raw_material_specification_or_stds_f = models.TextField(db_column='RAW_raw material specification or Stds_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_raw_material_specification_or_stds_r = models.TextField(db_column='RAW_raw material specification or Stds_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_raw_material_specification_or_stds_c = models.TextField(db_column='RAW_raw material specification or Stds_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_feasibility_of_conducting_test_f = models.TextField(db_column='RAW_Feasibility of conducting test_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_feasibility_of_conducting_test_r = models.TextField(db_column='RAW_Feasibility of conducting test_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    raw_feasibility_of_conducting_test_c = models.TextField(db_column='RAW_Feasibility of conducting test_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_developing_the_product_in_the_drawing_rfq_specs_f = models.TextField(db_column='DRAW_Developing the product in the drawing/RFQ/Specs_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_developing_the_product_in_the_drawing_rfq_specs_r = models.TextField(db_column='DRAW_Developing the product in the drawing/RFQ/Specs_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_developing_the_product_in_the_drawing_rfq_specs_c = models.TextField(db_column='DRAW_Developing the product in the drawing/RFQ/Specs_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_availablity_of_sc_cc_on_the_drawing_f = models.TextField(db_column='DRAW_Availablity of SC/CC on the drawing_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_availablity_of_sc_cc_on_the_drawing_r = models.TextField(db_column='DRAW_Availablity of SC/CC on the drawing_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_availablity_of_sc_cc_on_the_drawing_c = models.TextField(db_column='DRAW_Availablity of SC/CC on the drawing_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_information_data_for_sourcing_b_o_f = models.TextField(db_column='DRAW_information/data for sourcing B/O_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_information_data_for_sourcing_b_o_r = models.TextField(db_column='DRAW_information/data for sourcing B/O_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_information_data_for_sourcing_b_o_c = models.TextField(db_column='DRAW_information/data for sourcing B/O_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_surface_finish_painting_coatings_for_b_o_components_f = models.TextField(db_column='DRAW_Surface finish/painting/coatings for B/O components_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_surface_finish_painting_coatings_for_b_o_components_r = models.TextField(db_column='DRAW_Surface finish/painting/coatings for B/O components_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_surface_finish_painting_coatings_for_b_o_components_c = models.TextField(db_column='DRAW_Surface finish/painting/coatings for B/O components_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_feasibility_of_conducting_functional_tests_specified_f = models.TextField(db_column='DRAW_Feasibility of conducting functional tests specified_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_feasibility_of_conducting_functional_tests_specified_r = models.TextField(db_column='DRAW_Feasibility of conducting functional tests specified_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    draw_feasibility_of_conducting_functional_tests_specified_c = models.TextField(db_column='DRAW_Feasibility of conducting functional tests specified_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_feasibility_of_achieving_the_product_tolerances_f = models.TextField(db_column='MAN_Feasibility of achieving the product tolerances_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_feasibility_of_achieving_the_product_tolerances_r = models.TextField(db_column='MAN_Feasibility of achieving the product tolerances_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_feasibility_of_achieving_the_product_tolerances_c = models.TextField(db_column='MAN_Feasibility of achieving the product tolerances_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_achievability_of_cp_cpk_167_wherever_sc_cc_f = models.TextField(db_column='MAN_Achievability of CP/CPk >167 wherever SC/CC_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_achievability_of_cp_cpk_167_wherever_sc_cc_r = models.TextField(db_column='MAN_Achievability of CP/CPk >167 wherever SC/CC_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_achievability_of_cp_cpk_167_wherever_sc_cc_c = models.TextField(db_column='MAN_Achievability of CP/CPk >167 wherever SC/CC_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_any_new_processing_facility_required_f = models.TextField(db_column='MAN_Any new processing facility required_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_any_new_processing_facility_required_r = models.TextField(db_column='MAN_Any new processing facility required_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_any_new_processing_facility_required_c = models.TextField(db_column='MAN_Any new processing facility required_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_requirement_of_any_special_jigs_f = models.TextField(db_column='MAN_Requirement of any special Jigs_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_requirement_of_any_special_jigs_r = models.TextField(db_column='MAN_Requirement of any special Jigs_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_requirement_of_any_special_jigs_c = models.TextField(db_column='MAN_Requirement of any special Jigs_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_manufacturing_feasibility_of_jigs_fixtures_f = models.TextField(db_column='MAN_Manufacturing feasibility of Jigs/Fixtures_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_manufacturing_feasibility_of_jigs_fixtures_r = models.TextField(db_column='MAN_Manufacturing feasibility of Jigs/Fixtures_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    man_manufacturing_feasibility_of_jigs_fixtures_c = models.TextField(db_column='MAN_Manufacturing feasibility of Jigs/Fixtures_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_former_mfg_capacity_f = models.TextField(db_column='CAP_Former Mfg Capacity_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_former_mfg_capacity_r = models.TextField(db_column='CAP_Former Mfg Capacity_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_former_mfg_capacity_c = models.TextField(db_column='CAP_Former Mfg Capacity_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_chk_bundle_fix_mfg_capacity_f = models.TextField(db_column='CAP_Chk/Bundle Fix Mfg Capacity_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_chk_bundle_fix_mfg_capacity_r = models.TextField(db_column='CAP_Chk/Bundle Fix Mfg Capacity_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_chk_bundle_fix_mfg_capacity_c = models.TextField(db_column='CAP_Chk/Bundle Fix Mfg Capacity_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_forming_capacity_f = models.TextField(db_column='CAP_Forming Capacity_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_forming_capacity_r = models.TextField(db_column='CAP_Forming Capacity_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_forming_capacity_c = models.TextField(db_column='CAP_Forming Capacity_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_production_capacity_cell_manpower_f = models.TextField(db_column='CAP_Production Capacity Cell Manpower_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_production_capacity_cell_manpower_r = models.TextField(db_column='CAP_Production Capacity Cell Manpower_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_production_capacity_cell_manpower_c = models.TextField(db_column='CAP_Production Capacity Cell Manpower_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_b_o_part_sourcing_supplier_capacity_f = models.TextField(db_column='CAP_B/O Part sourcing-Supplier Capacity_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_b_o_part_sourcing_supplier_capacity_r = models.TextField(db_column='CAP_B/O Part sourcing-Supplier Capacity_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cap_b_o_part_sourcing_supplier_capacity_c = models.TextField(db_column='CAP_B/O Part sourcing-Supplier Capacity_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_feasibility_of_checking_sc_cc_f = models.TextField(db_column='INSP_Feasibility of checking SC/CC_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_feasibility_of_checking_sc_cc_r = models.TextField(db_column='INSP_Feasibility of checking SC/CC_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_feasibility_of_checking_sc_cc_c = models.TextField(db_column='INSP_Feasibility of checking SC/CC_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_any_special_inspection_equipment_f = models.TextField(db_column='INSP_Any Special Inspection equipment_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_any_special_inspection_equipment_r = models.TextField(db_column='INSP_Any Special Inspection equipment_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_any_special_inspection_equipment_c = models.TextField(db_column='INSP_Any Special Inspection equipment_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_list_the_dimensions_associated_with_sc_cc_f = models.TextField(db_column='INSP_List the dimensions associated with SC/CC_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_list_the_dimensions_associated_with_sc_cc_r = models.TextField(db_column='INSP_List the dimensions associated with SC/CC_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    insp_list_the_dimensions_associated_with_sc_cc_c = models.TextField(db_column='INSP_List the dimensions associated with SC/CC_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_requirement_of_functional_endurance_f = models.TextField(db_column='TEST_Requirement of Functional /Endurance_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_requirement_of_functional_endurance_r = models.TextField(db_column='TEST_Requirement of Functional /Endurance_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_requirement_of_functional_endurance_c = models.TextField(db_column='TEST_Requirement of Functional /Endurance_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_are_dvp_tests_required_f = models.TextField(db_column='TEST_Are DVP tests required_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_are_dvp_tests_required_r = models.TextField(db_column='TEST_Are DVP tests required_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_are_dvp_tests_required_c = models.TextField(db_column='TEST_Are DVP tests required_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_identify_sources_for_conducting_tests_f = models.TextField(db_column='TEST_Identify sources for conducting tests_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_identify_sources_for_conducting_tests_r = models.TextField(db_column='TEST_Identify sources for conducting tests_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    test_identify_sources_for_conducting_tests_c = models.TextField(db_column='TEST_Identify sources for conducting tests_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_feasibility_of_achieving_any_customer_f = models.TextField(db_column='CUST_Feasibility of achieving any customer_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_feasibility_of_achieving_any_customer_r = models.TextField(db_column='CUST_Feasibility of achieving any customer_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_feasibility_of_achieving_any_customer_c = models.TextField(db_column='CUST_Feasibility of achieving any customer_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_requirement_of_customer_regarding_f = models.TextField(db_column='CUST_Requirement of customer regarding_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_requirement_of_customer_regarding_r = models.TextField(db_column='CUST_Requirement of customer regarding_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_requirement_of_customer_regarding_c = models.TextField(db_column='CUST_Requirement of customer regarding_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_need_identification_updating_skill_matrix_f = models.TextField(db_column='CUST_Need identification/updating skill matrix_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_need_identification_updating_skill_matrix_r = models.TextField(db_column='CUST_Need identification/updating skill matrix_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cust_need_identification_updating_skill_matrix_c = models.TextField(db_column='CUST_Need identification/updating skill matrix_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_availability_of_existing_projects_very_similar_f = models.TextField(db_column='EXP_Availability of existing projects very similar_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_availability_of_existing_projects_very_similar_r = models.TextField(db_column='EXP_Availability of existing projects very similar_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_availability_of_existing_projects_very_similar_c = models.TextField(db_column='EXP_Availability of existing projects very similar_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_reference_of_tgr_tgw_g8d_complaint_f = models.TextField(db_column='EXP_Reference of TGR/TGW/G8D/Complaint_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_reference_of_tgr_tgw_g8d_complaint_r = models.TextField(db_column='EXP_Reference of TGR/TGW/G8D/Complaint_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_reference_of_tgr_tgw_g8d_complaint_c = models.TextField(db_column='EXP_Reference of TGR/TGW/G8D/Complaint_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_refer_project_guidelines_mgidcsrv01_quality_f = models.TextField(db_column='EXP_Refer PROJECT GUIDELINES\\Mgidcsrv01\\quality_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_refer_project_guidelines_mgidcsrv01_quality_r = models.TextField(db_column='EXP_Refer PROJECT GUIDELINES\\Mgidcsrv01\\quality_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    exp_refer_project_guidelines_mgidcsrv01_quality_c = models.TextField(db_column='EXP_Refer PROJECT GUIDELINES\\Mgidcsrv01\\quality_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_is_aspect_impact_study_required_f = models.TextField(db_column='ENV_Is Aspect & Impact Study required_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_is_aspect_impact_study_required_r = models.TextField(db_column='ENV_Is Aspect & Impact Study required_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_is_aspect_impact_study_required_c = models.TextField(db_column='ENV_Is Aspect & Impact Study required_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_if_yes_are_there_significant_aspect_f = models.TextField(db_column='ENV_If Yes, Are there Significant Aspect_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_if_yes_are_there_significant_aspect_r = models.TextField(db_column='ENV_If Yes, Are there Significant Aspect_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_if_yes_are_there_significant_aspect_c = models.TextField(db_column='ENV_If Yes, Are there Significant Aspect_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_if_yes_what_is_the_control_of_significant_aspects_f = models.TextField(db_column='ENV_If Yes, What is the control of Significant Aspects_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_if_yes_what_is_the_control_of_significant_aspects_r = models.TextField(db_column='ENV_If Yes, What is the control of Significant Aspects_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_if_yes_what_is_the_control_of_significant_aspects_c = models.TextField(db_column='ENV_If Yes, What is the control of Significant Aspects_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_is_there_any_additioal_legal_requirements_f = models.TextField(db_column='ENV_Is there any additioal Legal requirements_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_is_there_any_additioal_legal_requirements_r = models.TextField(db_column='ENV_Is there any additioal Legal requirements_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_is_there_any_additioal_legal_requirements_c = models.TextField(db_column='ENV_Is there any additioal Legal requirements_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_compliance_to_legal_requirements_f = models.TextField(db_column='ENV_Compliance to Legal requirements_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_compliance_to_legal_requirements_r = models.TextField(db_column='ENV_Compliance to Legal requirements_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_compliance_to_legal_requirements_c = models.TextField(db_column='ENV_Compliance to Legal requirements_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_availability_of_msds_f = models.TextField(db_column='ENV_Availability of MSDS_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_availability_of_msds_r = models.TextField(db_column='ENV_Availability of MSDS_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_availability_of_msds_c = models.TextField(db_column='ENV_Availability of MSDS_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_requirmentrelatedtoems_f = models.TextField(db_column='ENV_RequirmentRelatedToEMS_F', blank=True, null=True)  # Field name made lowercase.
    env_requirmentrelatedtoems_r = models.TextField(db_column='ENV_RequirmentRelatedToEMS_R', blank=True, null=True)  # Field name made lowercase.
    env_requirmentrelatedtoems_c = models.TextField(db_column='ENV_RequirmentRelatedToEMS_C', blank=True, null=True)  # Field name made lowercase.
    env_product_can_be_produced_as_specified_f = models.TextField(db_column='ENV_Product can be produced as specified_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_product_can_be_produced_as_specified_r = models.TextField(db_column='ENV_Product can be produced as specified_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_product_can_be_produced_as_specified_c = models.TextField(db_column='ENV_Product can be produced as specified_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_changes_recommended_f = models.TextField(db_column='ENV_Changes recommended_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_changes_recommended_r = models.TextField(db_column='ENV_Changes recommended_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    env_changes_recommended_c = models.TextField(db_column='ENV_Changes recommended_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    evn_design_revision_required_to_produce_f = models.TextField(db_column='EVN_Design revision required to produce_F', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    evn_design_revision_required_to_produce_r = models.TextField(db_column='EVN_Design revision required to produce_R', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    evn_design_revision_required_to_produce_c = models.TextField(db_column='EVN_Design revision required to produce_C', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    marketing = models.TextField(db_column='Marketing', blank=True, null=True)  # Field name made lowercase.
    materials = models.TextField(db_column='Materials', blank=True, null=True)  # Field name made lowercase.
    quality = models.TextField(db_column='Quality', blank=True, null=True)  # Field name made lowercase.
    pe = models.TextField(db_column='PE', blank=True, null=True)  # Field name made lowercase.
    me = models.TextField(db_column='ME', blank=True, null=True)  # Field name made lowercase.
    pdpm = models.TextField(db_column='PDPM', blank=True, null=True)  # Field name made lowercase.
    attdate = models.DateField(db_column='AttDate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_feasibility'


class TblGenproductpostinggroups(models.Model):
    id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True, null=True)
    def_vat_prod_posting_group = models.CharField(max_length=100, blank=True, null=True)
    auto_insert_default = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_genproductpostinggroups'


class TblGstgroup(models.Model):
    code = models.CharField(max_length=50)
    gst_group_type = models.CharField(max_length=50)
    gst_placeof_supply = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    reverse_charge = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_gstgroup'


class TblInventorypostinggroups(models.Model):
    code = models.CharField(unique=True, max_length=50)
    description = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_inventorypostinggroups'


class TblItemcard(models.Model):
    id = models.IntegerField(blank=True, null=True)
    customerid = models.TextField(blank=True, null=True)
    customername = models.TextField(blank=True, null=True)
    no = models.TextField(blank=True, null=True)
    no_2 = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    search_description = models.TextField(blank=True, null=True)
    description_2 = models.TextField(blank=True, null=True)
    base_unit_of_measure = models.TextField(blank=True, null=True)
    price_unit_conversion = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    inventory_posting_group = models.TextField(blank=True, null=True)
    shelf_no = models.TextField(blank=True, null=True)
    item_disc_group = models.TextField(blank=True, null=True)
    allow_invoice_disc = models.TextField(blank=True, null=True)
    statistics_group = models.TextField(blank=True, null=True)
    commission_group = models.TextField(blank=True, null=True)
    unit_price = models.TextField(blank=True, null=True)
    price_profit_calculation = models.TextField(blank=True, null=True)
    profit = models.TextField(blank=True, null=True)
    costing_method = models.TextField(blank=True, null=True)
    unit_cost = models.TextField(blank=True, null=True)
    standard_cost = models.TextField(blank=True, null=True)
    last_direct_cost = models.TextField(blank=True, null=True)
    indirect_cost = models.TextField(blank=True, null=True)
    cost_is_adjusted = models.TextField(blank=True, null=True)
    allow_online_adjustment = models.TextField(blank=True, null=True)
    vendor_no = models.TextField(blank=True, null=True)
    vendor_item_no = models.TextField(blank=True, null=True)
    lead_time_calculation = models.TextField(blank=True, null=True)
    reorder_point = models.TextField(blank=True, null=True)
    maximum_inventory = models.TextField(blank=True, null=True)
    reorder_quantity = models.TextField(blank=True, null=True)
    alternative_item_no = models.TextField(blank=True, null=True)
    unit_list_price = models.TextField(blank=True, null=True)
    duty_due = models.TextField(blank=True, null=True)
    duty_code = models.TextField(blank=True, null=True)
    gross_weight = models.TextField(blank=True, null=True)
    net_weight = models.TextField(blank=True, null=True)
    units_per_parcel = models.TextField(blank=True, null=True)
    unit_volume = models.TextField(blank=True, null=True)
    durability = models.TextField(blank=True, null=True)
    freight_type = models.TextField(blank=True, null=True)
    tariff_no = models.TextField(blank=True, null=True)
    duty_unit_conversion = models.TextField(blank=True, null=True)
    country_region_purchased_code = models.TextField(blank=True, null=True)
    budget_quantity = models.TextField(blank=True, null=True)
    budgeted_amount = models.TextField(blank=True, null=True)
    budget_profit = models.TextField(blank=True, null=True)
    blocked = models.TextField(blank=True, null=True)
    last_date_modified = models.TextField(blank=True, null=True)
    price_includes_vat = models.TextField(blank=True, null=True)
    vat_bus_posting_gr_price = models.TextField(blank=True, null=True)
    gen_prod_posting_group = models.TextField(blank=True, null=True)
    country_region_of_origin_code = models.TextField(blank=True, null=True)
    automatic_ext_texts = models.TextField(blank=True, null=True)
    no_series = models.TextField(blank=True, null=True)
    tax_group_code = models.TextField(blank=True, null=True)
    vat_prod_posting_group = models.TextField(blank=True, null=True)
    reserve = models.TextField(blank=True, null=True)
    global_dimension_1_code = models.TextField(blank=True, null=True)
    global_dimension_2_code = models.TextField(blank=True, null=True)
    stockout_warning = models.TextField(blank=True, null=True)
    prevent_negative_inventory = models.TextField(blank=True, null=True)
    application_wksh_user_id = models.TextField(blank=True, null=True)
    assembly_policy = models.TextField(blank=True, null=True)
    gtin = models.TextField(blank=True, null=True)
    default_deferral_template_code = models.TextField(blank=True, null=True)
    lowlevel_code = models.TextField(blank=True, null=True)
    lot_size = models.TextField(blank=True, null=True)
    serial_nos = models.TextField(blank=True, null=True)
    last_unit_cost_calc_date = models.TextField(blank=True, null=True)
    rolledup_material_cost = models.TextField(blank=True, null=True)
    rolledup_capacity_cost = models.TextField(blank=True, null=True)
    scrap = models.TextField(blank=True, null=True)
    inventory_value_zero = models.TextField(blank=True, null=True)
    discrete_order_quantity = models.TextField(blank=True, null=True)
    minimum_order_quantity = models.TextField(blank=True, null=True)
    maximum_order_quantity = models.TextField(blank=True, null=True)
    safety_stock_quantity = models.TextField(blank=True, null=True)
    order_multiple = models.TextField(blank=True, null=True)
    safety_lead_time = models.TextField(blank=True, null=True)
    flushing_method = models.TextField(blank=True, null=True)
    replenishment_system = models.TextField(blank=True, null=True)
    rounding_precision = models.TextField(blank=True, null=True)
    sales_unit_of_measure = models.TextField(blank=True, null=True)
    purch_unit_of_measure = models.TextField(blank=True, null=True)
    time_bucket = models.TextField(blank=True, null=True)
    reordering_policy = models.TextField(blank=True, null=True)
    include_inventory = models.TextField(blank=True, null=True)
    manufacturing_policy = models.TextField(blank=True, null=True)
    rescheduling_period = models.TextField(blank=True, null=True)
    lot_accumulation_period = models.TextField(blank=True, null=True)
    dampener_period = models.TextField(blank=True, null=True)
    dampener_quantity = models.TextField(blank=True, null=True)
    overflow_level = models.TextField(blank=True, null=True)
    manufacturer_code = models.TextField(blank=True, null=True)
    item_category_code = models.TextField(blank=True, null=True)
    created_from_nonstock_item = models.TextField(blank=True, null=True)
    product_group_code = models.TextField(blank=True, null=True)
    service_item_group = models.TextField(blank=True, null=True)
    item_tracking_code = models.TextField(blank=True, null=True)
    lot_nos = models.TextField(blank=True, null=True)
    expiration_calculation = models.TextField(blank=True, null=True)
    special_equipment_code = models.TextField(blank=True, null=True)
    putaway_template_code = models.TextField(blank=True, null=True)
    putaway_unit_of_measure_code = models.TextField(blank=True, null=True)
    phys_invt_counting_period_code = models.TextField(blank=True, null=True)
    last_counting_period_update = models.TextField(blank=True, null=True)
    use_crossdocking = models.TextField(blank=True, null=True)
    next_counting_start_date = models.TextField(blank=True, null=True)
    next_counting_end_date = models.TextField(blank=True, null=True)
    excise_prod_posting_group = models.TextField(blank=True, null=True)
    excise_accounting_type = models.TextField(blank=True, null=True)
    assessable_value = models.TextField(blank=True, null=True)
    declared_goods = models.TextField(blank=True, null=True)
    capital_item = models.TextField(blank=True, null=True)
    subcontracting = models.TextField(blank=True, null=True)
    sub_comp_location = models.TextField(blank=True, null=True)
    fixed_asset = models.TextField(blank=True, null=True)
    scrap_item = models.TextField(blank=True, null=True)
    mrp_price = models.TextField(blank=True, null=True)
    mrp_value = models.TextField(blank=True, null=True)
    abatement = models.TextField(blank=True, null=True)
    pit_structure = models.TextField(blank=True, null=True)
    price_inclusive_of_tax = models.TextField(blank=True, null=True)
    gst_group_code = models.TextField(blank=True, null=True)
    hsn_sac_code = models.TextField(blank=True, null=True)
    gst_credit = models.TextField(blank=True, null=True)
    exempted = models.TextField(blank=True, null=True)
    rounding_set_to_1 = models.TextField(blank=True, null=True)
    need_barcode = models.TextField(blank=True, null=True)
    fixture_no = models.TextField(blank=True, null=True)
    no_of_meft = models.TextField(blank=True, null=True)
    sales_quote_bom_no = models.TextField(blank=True, null=True)
    template_applied = models.TextField(blank=True, null=True)
    qc_applicable = models.TextField(blank=True, null=True)
    qc_type = models.TextField(blank=True, null=True)
    blanket_order_mandatory = models.TextField(blank=True, null=True)
    breakeven_quantity = models.TextField(blank=True, null=True)
    ppap_applicable = models.TextField(blank=True, null=True)
    no_of_parts = models.TextField(blank=True, null=True)
    cell = models.TextField(blank=True, null=True)
    cell_type = models.TextField(blank=True, null=True)
    qc_after_grn = models.TextField(blank=True, null=True)
    no_of_single_formings = models.TextField(blank=True, null=True)
    cycle_time = models.TextField(blank=True, null=True)
    customer_name = models.TextField(blank=True, null=True)
    vendor_name = models.TextField(blank=True, null=True)
    revision_no = models.TextField(blank=True, null=True)
    item_expiration_mandatory = models.TextField(blank=True, null=True)
    customer_vendor_code = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    fixture_mandatory = models.TextField(blank=True, null=True)
    routing_no = models.TextField(blank=True, null=True)
    production_bom_no = models.TextField(blank=True, null=True)
    singlelevel_material_cost = models.TextField(blank=True, null=True)
    singlelevel_capacity_cost = models.TextField(blank=True, null=True)
    singlelevel_subcontrd_cost = models.TextField(blank=True, null=True)
    singlelevel_cap_ovhd_cost = models.TextField(blank=True, null=True)
    singlelevel_mfg_ovhd_cost = models.TextField(blank=True, null=True)
    overhead_rate = models.TextField(blank=True, null=True)
    rolledup_subcontracted_cost = models.TextField(blank=True, null=True)
    rolledup_mfg_ovhd_cost = models.TextField(blank=True, null=True)
    rolledup_cap_overhead_cost = models.TextField(blank=True, null=True)
    order_tracking_policy = models.TextField(blank=True, null=True)
    critical = models.TextField(blank=True, null=True)
    common_item_no = models.TextField(blank=True, null=True)
    template_name = models.TextField(blank=True, null=True)
    upload_status = models.TextField(blank=True, null=True)
    monthyear = models.TextField(blank=True, null=True)
    fy = models.TextField(blank=True, null=True)
    quarter = models.TextField(blank=True, null=True)
    completedon = models.TextField(blank=True, null=True)
    is_download = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_itemcard'


class TblItemcardEcn(models.Model):
    ecn_id = models.TextField(blank=True, null=True)
    ecn_type = models.TextField(blank=True, null=True)
    customerid = models.TextField(blank=True, null=True)
    customername = models.TextField(blank=True, null=True)
    no = models.TextField(db_column='No', blank=True, null=True)  # Field name made lowercase.
    no_2 = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    search_description = models.TextField(blank=True, null=True)
    description_2 = models.TextField(blank=True, null=True)
    base_unit_of_measure = models.TextField(blank=True, null=True)
    price_unit_conversion = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    inventory_posting_group = models.TextField(blank=True, null=True)
    shelf_no = models.TextField(blank=True, null=True)
    item_disc_group = models.TextField(blank=True, null=True)
    allow_invoice_disc = models.TextField(blank=True, null=True)
    statistics_group = models.TextField(blank=True, null=True)
    commission_group = models.TextField(blank=True, null=True)
    unit_price = models.TextField(blank=True, null=True)
    price_profit_calculation = models.TextField(blank=True, null=True)
    profit = models.TextField(blank=True, null=True)
    costing_method = models.TextField(blank=True, null=True)
    unit_cost = models.TextField(blank=True, null=True)
    standard_cost = models.TextField(blank=True, null=True)
    last_direct_cost = models.TextField(blank=True, null=True)
    indirect_cost = models.TextField(blank=True, null=True)
    cost_is_adjusted = models.TextField(blank=True, null=True)
    allow_online_adjustment = models.TextField(blank=True, null=True)
    vendor_no = models.TextField(blank=True, null=True)
    vendor_item_no = models.TextField(blank=True, null=True)
    lead_time_calculation = models.TextField(blank=True, null=True)
    reorder_point = models.TextField(blank=True, null=True)
    maximum_inventory = models.TextField(blank=True, null=True)
    reorder_quantity = models.TextField(blank=True, null=True)
    alternative_item_no = models.TextField(blank=True, null=True)
    unit_list_price = models.TextField(blank=True, null=True)
    duty_due = models.TextField(blank=True, null=True)
    duty_code = models.TextField(blank=True, null=True)
    gross_weight = models.TextField(blank=True, null=True)
    net_weight = models.TextField(blank=True, null=True)
    units_per_parcel = models.TextField(blank=True, null=True)
    unit_volume = models.TextField(blank=True, null=True)
    durability = models.TextField(blank=True, null=True)
    freight_type = models.TextField(blank=True, null=True)
    tariff_no = models.TextField(blank=True, null=True)
    duty_unit_conversion = models.TextField(blank=True, null=True)
    country_region_purchased_code = models.TextField(blank=True, null=True)
    budget_quantity = models.TextField(blank=True, null=True)
    budgeted_amount = models.TextField(blank=True, null=True)
    budget_profit = models.TextField(blank=True, null=True)
    blocked = models.TextField(blank=True, null=True)
    last_date_modified = models.TextField(blank=True, null=True)
    price_includes_vat = models.TextField(blank=True, null=True)
    vat_bus_posting_gr_price_field = models.TextField(db_column='VAT_Bus_Posting_Gr_(Price)', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    gen_prod_posting_group = models.TextField(blank=True, null=True)
    country_region_of_origin_code = models.TextField(blank=True, null=True)
    automatic_ext_texts = models.TextField(blank=True, null=True)
    no_series = models.TextField(blank=True, null=True)
    tax_group_code = models.TextField(blank=True, null=True)
    vat_prod_posting_group = models.TextField(blank=True, null=True)
    reserve = models.TextField(blank=True, null=True)
    global_dimension_1_code = models.TextField(blank=True, null=True)
    global_dimension_2_code = models.TextField(blank=True, null=True)
    stockout_warning = models.TextField(blank=True, null=True)
    prevent_negative_inventory = models.TextField(blank=True, null=True)
    application_wksh_user_id = models.TextField(blank=True, null=True)
    assembly_policy = models.TextField(blank=True, null=True)
    gtin = models.TextField(blank=True, null=True)
    default_deferral_template_code = models.TextField(blank=True, null=True)
    lowlevel_code = models.TextField(blank=True, null=True)
    lot_size = models.TextField(blank=True, null=True)
    serial_nos = models.TextField(blank=True, null=True)
    last_unit_cost_calc_date = models.TextField(blank=True, null=True)
    rolledup_material_cost = models.TextField(blank=True, null=True)
    rolledup_capacity_cost = models.TextField(blank=True, null=True)
    scrap = models.TextField(blank=True, null=True)
    inventory_value_zero = models.TextField(blank=True, null=True)
    discrete_order_quantity = models.TextField(blank=True, null=True)
    minimum_order_quantity = models.TextField(blank=True, null=True)
    maximum_order_quantity = models.TextField(blank=True, null=True)
    safety_stock_quantity = models.TextField(blank=True, null=True)
    order_multiple = models.TextField(blank=True, null=True)
    safety_lead_time = models.TextField(blank=True, null=True)
    flushing_method = models.TextField(blank=True, null=True)
    replenishment_system = models.TextField(blank=True, null=True)
    rounding_precision = models.TextField(blank=True, null=True)
    sales_unit_of_measure = models.TextField(blank=True, null=True)
    purch_unit_of_measure = models.TextField(blank=True, null=True)
    time_bucket = models.TextField(blank=True, null=True)
    reordering_policy = models.TextField(blank=True, null=True)
    include_inventory = models.TextField(blank=True, null=True)
    manufacturing_policy = models.TextField(blank=True, null=True)
    rescheduling_period = models.TextField(blank=True, null=True)
    lot_accumulation_period = models.TextField(blank=True, null=True)
    dampener_period = models.TextField(blank=True, null=True)
    dampener_quantity = models.TextField(blank=True, null=True)
    overflow_level = models.TextField(blank=True, null=True)
    manufacturer_code = models.TextField(blank=True, null=True)
    item_category_code = models.TextField(blank=True, null=True)
    created_from_nonstock_item = models.TextField(blank=True, null=True)
    product_group_code = models.TextField(blank=True, null=True)
    service_item_group = models.TextField(blank=True, null=True)
    item_tracking_code = models.TextField(blank=True, null=True)
    lot_nos = models.TextField(blank=True, null=True)
    expiration_calculation = models.TextField(blank=True, null=True)
    special_equipment_code = models.TextField(blank=True, null=True)
    putaway_template_code = models.TextField(blank=True, null=True)
    putaway_unit_of_measure_code = models.TextField(blank=True, null=True)
    phys_invt_counting_period_code = models.TextField(blank=True, null=True)
    last_counting_period_update = models.TextField(blank=True, null=True)
    use_crossdocking = models.TextField(blank=True, null=True)
    next_counting_start_date = models.TextField(blank=True, null=True)
    next_counting_end_date = models.TextField(blank=True, null=True)
    excise_prod_posting_group = models.TextField(blank=True, null=True)
    excise_accounting_type = models.TextField(blank=True, null=True)
    assessable_value = models.TextField(blank=True, null=True)
    declared_goods = models.TextField(blank=True, null=True)
    capital_item = models.TextField(blank=True, null=True)
    subcontracting = models.TextField(blank=True, null=True)
    sub_comp_location = models.TextField(blank=True, null=True)
    fixed_asset = models.TextField(blank=True, null=True)
    scrap_item = models.TextField(blank=True, null=True)
    mrp_price = models.TextField(blank=True, null=True)
    mrp_value = models.TextField(blank=True, null=True)
    abatement = models.TextField(blank=True, null=True)
    pit_structure = models.TextField(blank=True, null=True)
    price_inclusive_of_tax = models.TextField(blank=True, null=True)
    gst_group_code = models.TextField(blank=True, null=True)
    hsn_sac_code = models.TextField(blank=True, null=True)
    gst_credit = models.TextField(blank=True, null=True)
    exempted = models.TextField(blank=True, null=True)
    rounding_set_to_1 = models.TextField(blank=True, null=True)
    need_barcode = models.TextField(blank=True, null=True)
    fixture_no = models.TextField(blank=True, null=True)
    no_of_meft = models.TextField(blank=True, null=True)
    sales_quote_bom_no = models.TextField(blank=True, null=True)
    template_applied = models.TextField(blank=True, null=True)
    qc_applicable = models.TextField(blank=True, null=True)
    qc_type = models.TextField(blank=True, null=True)
    blanket_order_mandatory = models.TextField(blank=True, null=True)
    breakeven_quantity = models.TextField(blank=True, null=True)
    ppap_applicable = models.TextField(blank=True, null=True)
    no_of_parts = models.TextField(blank=True, null=True)
    cell = models.TextField(blank=True, null=True)
    cell_type = models.TextField(blank=True, null=True)
    qc_after_grn = models.TextField(blank=True, null=True)
    no_of_single_formings = models.TextField(blank=True, null=True)
    cycle_time = models.TextField(blank=True, null=True)
    customer_name = models.TextField(blank=True, null=True)
    vendor_name = models.TextField(blank=True, null=True)
    revision_no = models.TextField(blank=True, null=True)
    item_expiration_mandatory = models.TextField(blank=True, null=True)
    customer_vendor_code = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    fixture_mandatory = models.TextField(blank=True, null=True)
    routing_no = models.TextField(blank=True, null=True)
    production_bom_no = models.TextField(blank=True, null=True)
    singlelevel_material_cost = models.TextField(blank=True, null=True)
    singlelevel_capacity_cost = models.TextField(blank=True, null=True)
    singlelevel_subcontrd_cost = models.TextField(blank=True, null=True)
    singlelevel_cap_ovhd_cost = models.TextField(blank=True, null=True)
    singlelevel_mfg_ovhd_cost = models.TextField(blank=True, null=True)
    overhead_rate = models.TextField(blank=True, null=True)
    rolledup_subcontracted_cost = models.TextField(blank=True, null=True)
    rolledup_mfg_ovhd_cost = models.TextField(blank=True, null=True)
    rolledup_cap_overhead_cost = models.TextField(blank=True, null=True)
    order_tracking_policy = models.TextField(blank=True, null=True)
    critical = models.TextField(blank=True, null=True)
    common_item_no = models.TextField(blank=True, null=True)
    template_name = models.TextField(blank=True, null=True)
    upload_status = models.TextField(blank=True, null=True)
    monthyear = models.TextField(blank=True, null=True)
    fy = models.TextField(blank=True, null=True)
    quarter = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_itemcard_ecn'


class TblItemcardInvoice(models.Model):
    id = models.TextField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    gst_group_code = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_itemcard_invoice'


class TblItemcategories(models.Model):
    id = models.TextField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    def_gen_prod_posting_group = models.TextField(blank=True, null=True)
    def_inventory_posting_group = models.TextField(blank=True, null=True)
    def_vat_prod_posting_group = models.TextField(blank=True, null=True)
    def_costing_method = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_itemcategories'


class TblNormsdetails(models.Model):
    sr_no = models.AutoField(primary_key=True)
    norms_code = models.CharField(max_length=50, blank=True, null=True)
    sheet_name = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=150, blank=True, null=True)
    cell_location = models.CharField(max_length=50, blank=True, null=True)
    cell_value = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    export_path = models.TextField(blank=True, null=True)
    local_bo_flag = models.BooleanField(blank=True, null=True)
    total_local_bo_flag = models.BooleanField(blank=True, null=True)
    packaging_series = models.BooleanField(blank=True, null=True)
    packaging_proto = models.BooleanField(blank=True, null=True)
    os_template = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_normsdetails'


class TblOffersheetOthercharges(models.Model):
    customer_id = models.CharField(max_length=20)
    os_description = models.CharField(max_length=255)
    rateinpercentage = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_offersheet_othercharges'


class TblOffersheetTranscost(models.Model):
    particular = models.CharField(max_length=255)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cust_code = models.CharField(max_length=20)
    customer_id = models.CharField(max_length=20, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_offersheet_transcost'


class TblOffersheetrmconversion(models.Model):
    part_number = models.CharField(max_length=100, blank=True, null=True)
    raw_material_description = models.TextField(blank=True, null=True)
    tube_size = models.CharField(max_length=50, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    internal_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    rateperunit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    qnty = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    rm_flag = models.CharField(max_length=20, blank=True, null=True)
    customer_id = models.CharField(max_length=20, blank=True, null=True)
    process_date = models.DateField(blank=True, null=True)
    itemcreation_id = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_offersheetrmconversion'


class TblOpportunitymaster(models.Model):
    id = models.TextField(blank=True, null=True)
    item_no = models.TextField(blank=True, null=True)
    no_2 = models.TextField(blank=True, null=True)
    customerid = models.TextField(blank=True, null=True)
    customername = models.TextField(blank=True, null=True)
    contactname = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    salesperson_code = models.TextField(blank=True, null=True)
    campaign_no = models.TextField(blank=True, null=True)
    contact_no = models.TextField(blank=True, null=True)
    contact_company_no = models.TextField(blank=True, null=True)
    sales_cycle_code = models.TextField(blank=True, null=True)
    sales_document_no = models.TextField(blank=True, null=True)
    creation_date = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    priority = models.TextField(blank=True, null=True)
    closed = models.TextField(blank=True, null=True)
    date_closed = models.TextField(blank=True, null=True)
    no_series = models.TextField(blank=True, null=True)
    segment_no = models.TextField(blank=True, null=True)
    estimated_closing_date = models.TextField(blank=True, null=True)
    sales_document_type = models.TextField(blank=True, null=True)
    wizard_step = models.TextField(blank=True, null=True)
    activate_first_stage = models.TextField(blank=True, null=True)
    segment_description = models.TextField(blank=True, null=True)
    wizard_estimated_value = models.TextField(blank=True, null=True)
    wizard_chances_of_success = models.TextField(blank=True, null=True)
    wizard_estimated_closing_date = models.TextField(blank=True, null=True)
    wizard_contact_name = models.TextField(blank=True, null=True)
    wizard_campaign_description = models.TextField(blank=True, null=True)
    sales_cycle_stage = models.TextField(blank=True, null=True)
    estimated_value = models.TextField(blank=True, null=True)
    probability_per = models.TextField(blank=True, null=True)
    chances_of_success_per = models.TextField(blank=True, null=True)
    completed_per = models.TextField(blank=True, null=True)
    part_no = models.TextField(blank=True, null=True)
    part_name = models.TextField(blank=True, null=True)
    opportunity_received_date = models.TextField(blank=True, null=True)
    sop_date = models.TextField(blank=True, null=True)
    annual_volume = models.TextField(blank=True, null=True)
    drawing_revision_no = models.TextField(blank=True, null=True)
    application = models.TextField(blank=True, null=True)
    business = models.TextField(blank=True, null=True)
    voss_plant_location = models.TextField(blank=True, null=True)
    life_cycle_in_years = models.TextField(blank=True, null=True)
    competitor_name = models.TextField(blank=True, null=True)
    annual_volume_2 = models.TextField(blank=True, null=True)
    annual_volume_3 = models.TextField(blank=True, null=True)
    annual_volume_4 = models.TextField(blank=True, null=True)
    annual_volume_5 = models.TextField(blank=True, null=True)
    annual_volume_year = models.TextField(blank=True, null=True)
    annual_volume_year_2 = models.TextField(blank=True, null=True)
    annual_volume_year_3 = models.TextField(blank=True, null=True)
    annual_volume_year_4 = models.TextField(blank=True, null=True)
    annual_volume_year_5 = models.TextField(blank=True, null=True)
    supply_location = models.TextField(blank=True, null=True)
    part_price_1 = models.TextField(blank=True, null=True)
    tooling_cost = models.TextField(blank=True, null=True)
    category_of_project = models.TextField(blank=True, null=True)
    division = models.TextField(blank=True, null=True)
    cogs = models.TextField(blank=True, null=True)
    tooling_payback_date = models.TextField(blank=True, null=True)
    part_price_2 = models.TextField(blank=True, null=True)
    part_price_3 = models.TextField(blank=True, null=True)
    status_date = models.TextField(blank=True, null=True)
    sales_goahead_date_for_tool = models.TextField(blank=True, null=True)
    project_name = models.TextField(blank=True, null=True)
    drawing_no = models.TextField(blank=True, null=True)
    customer_name = models.TextField(blank=True, null=True)
    upload_status = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    estimated_euro_conv = models.TextField(blank=True, null=True)
    attachmentofreferencedocs = models.TextField(blank=True, null=True)
    quotestatus = models.TextField(blank=True, null=True)
    categorytype = models.TextField(blank=True, null=True)
    completedon = models.TextField(blank=True, null=True)
    last_modified_date = models.TextField(blank=True, null=True)
    is_download = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_opportunitymaster'


class TblOpportunitymasterEcn(models.Model):
    ecn_id = models.CharField(max_length=20, blank=True, null=True)
    ecn_type = models.CharField(max_length=20, blank=True, null=True)
    customerid = models.CharField(max_length=50, blank=True, null=True)
    customername = models.CharField(max_length=200, blank=True, null=True)
    contactname = models.CharField(max_length=100, blank=True, null=True)
    item_no = models.CharField(max_length=50, blank=True, null=True)
    no_2 = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    salesperson_code = models.CharField(max_length=50, blank=True, null=True)
    campaign_no = models.CharField(max_length=50, blank=True, null=True)
    contact_no = models.CharField(max_length=50, blank=True, null=True)
    contact_company_no = models.CharField(max_length=50, blank=True, null=True)
    sales_cycle_code = models.CharField(max_length=50, blank=True, null=True)
    sales_document_no = models.CharField(max_length=50, blank=True, null=True)
    creation_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    reason = models.CharField(max_length=100, blank=True, null=True)
    priority = models.CharField(max_length=50, blank=True, null=True)
    closed = models.BooleanField(blank=True, null=True)
    date_closed = models.DateField(blank=True, null=True)
    no_series = models.CharField(max_length=50, blank=True, null=True)
    segment_no = models.CharField(max_length=50, blank=True, null=True)
    estimated_closing_date = models.DateField(blank=True, null=True)
    sales_document_type = models.CharField(max_length=50, blank=True, null=True)
    wizard_step = models.CharField(max_length=50, blank=True, null=True)
    activate_first_stage = models.BooleanField(blank=True, null=True)
    segment_description = models.CharField(max_length=100, blank=True, null=True)
    wizard_estimated_value = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    wizard_chances_of_success = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    wizard_estimated_closing_date = models.DateField(blank=True, null=True)
    wizard_contact_name = models.CharField(max_length=100, blank=True, null=True)
    wizard_campaign_description = models.CharField(max_length=200, blank=True, null=True)
    sales_cycle_stage = models.CharField(max_length=50, blank=True, null=True)
    estimated_value = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    probability_per = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    chances_of_success_per = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    completed_per = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    part_no = models.CharField(max_length=50, blank=True, null=True)
    part_name = models.CharField(max_length=100, blank=True, null=True)
    opportunity_received_date = models.DateField(blank=True, null=True)
    sop_date = models.DateField(blank=True, null=True)
    annual_volume = models.IntegerField(blank=True, null=True)
    drawing_revision_no = models.CharField(max_length=50, blank=True, null=True)
    application = models.CharField(max_length=100, blank=True, null=True)
    business = models.CharField(max_length=100, blank=True, null=True)
    voss_plant_location = models.CharField(max_length=100, blank=True, null=True)
    life_cycle_in_years = models.IntegerField(blank=True, null=True)
    competitor_name = models.CharField(max_length=100, blank=True, null=True)
    annual_volume_2 = models.IntegerField(blank=True, null=True)
    annual_volume_3 = models.IntegerField(blank=True, null=True)
    annual_volume_4 = models.IntegerField(blank=True, null=True)
    annual_volume_5 = models.IntegerField(blank=True, null=True)
    annual_volume_year = models.IntegerField(blank=True, null=True)
    annual_volume_year_2 = models.IntegerField(blank=True, null=True)
    annual_volume_year_3 = models.IntegerField(blank=True, null=True)
    annual_volume_year_4 = models.IntegerField(blank=True, null=True)
    annual_volume_year_5 = models.IntegerField(blank=True, null=True)
    supply_location = models.CharField(max_length=100, blank=True, null=True)
    part_price_1 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    tooling_cost = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    category_of_project = models.CharField(max_length=100, blank=True, null=True)
    division = models.CharField(max_length=100, blank=True, null=True)
    cogs = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    tooling_payback_date = models.DateField(blank=True, null=True)
    part_price_2 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    part_price_3 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    status_date = models.DateField(blank=True, null=True)
    sales_goahead_date_for_tool = models.DateField(blank=True, null=True)
    project_name = models.CharField(max_length=150, blank=True, null=True)
    drawing_no = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    upload_status = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    quotestatus = models.CharField(max_length=50, blank=True, null=True)
    categorytype = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_opportunitymaster_ecn'


class TblOppsalescycles(models.Model):
    id = models.IntegerField(db_column='ID', primary_key=True)  # Field name made lowercase.
    code = models.CharField(db_column='Code', max_length=50, blank=True, null=True)  # Field name made lowercase.
    description = models.CharField(db_column='Description', max_length=100, blank=True, null=True)  # Field name made lowercase.
    probability_calculation = models.CharField(db_column='Probability_Calculation', max_length=100, blank=True, null=True)  # Field name made lowercase.
    blocked = models.IntegerField(db_column='Blocked', blank=True, null=True)  # Field name made lowercase.
    comment = models.IntegerField(db_column='Comment', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_oppsalescycles'


class TblOppsalescyclestages(models.Model):
    stage = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    completed = models.BooleanField(blank=True, null=True)
    activity_code = models.CharField(max_length=50, blank=True, null=True)
    quote_required = models.BooleanField(blank=True, null=True)
    allow_skip = models.BooleanField(blank=True, null=True)
    date_formula = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_oppsalescyclestages'


class TblOppsalescyclestages1(models.Model):
    stage = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    completed = models.BooleanField(blank=True, null=True)
    activity_code = models.CharField(max_length=50, blank=True, null=True)
    quote_required = models.BooleanField(blank=True, null=True)
    allow_skip = models.BooleanField(blank=True, null=True)
    date_formula = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_oppsalescyclestages1'


class TblOppsalespeople(models.Model):
    code = models.CharField(unique=True, max_length=20)
    name = models.CharField(max_length=100)
    commission = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_oppsalespeople'


class TblOppsegment(models.Model):
    id = models.IntegerField(primary_key=True)
    no = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    campaign_no = models.CharField(max_length=50, blank=True, null=True)
    salesperson_code = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_oppsegment'


class TblProductgroups(models.Model):
    code = models.CharField(unique=True, max_length=20)
    description = models.TextField(blank=True, null=True)
    item_category_code = models.CharField(max_length=20, blank=True, null=True)
    warehouse_class_code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_productgroups'


class TblRfqDetails(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customername = models.CharField(max_length=100, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    bomcreation_id = models.CharField(max_length=50, blank=True, null=True)
    bopcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_creation_id = models.CharField(max_length=50, blank=True, null=True)
    is_completed = models.BooleanField(blank=True, null=True)
    action_date = models.DateField(blank=True, null=True)
    updated_by = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_rfq_details'


class TblRmconversionHeaderposition(models.Model):
    norms_code = models.CharField(primary_key=True, max_length=50)  # The composite primary key (norms_code, headername) found, that is not supported. The first column is selected.
    headername = models.CharField(max_length=100)
    cell_position = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_rmconversion_headerposition'
        unique_together = (('norms_code', 'headername'),)


class TblSalesorder(models.Model):
    documenttype = models.CharField(max_length=20)
    documentno = models.CharField(primary_key=True, max_length=50)
    sell_tocustomerno = models.CharField(max_length=50, blank=True, null=True)
    customername = models.CharField(max_length=150, blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    no = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    locationcode = models.CharField(max_length=50, blank=True, null=True)
    reserve = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    reservedqty_base = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    unitofmeasurecode = models.CharField(max_length=20, blank=True, null=True)
    lineamountexcltax = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    shipmentdate = models.DateField(blank=True, null=True)
    outstandingquantity = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    price_from_date = models.DateField(blank=True, null=True)
    price_to_date = models.DateField(blank=True, null=True)
    unitcost_lcy = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    unitpriceexcltax = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    linediscountperc = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    externaldocumentno = models.CharField(max_length=50, blank=True, null=True)
    documentdate = models.DateField(blank=True, null=True)
    rmbase = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    bocbase = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    plantcode = models.CharField(max_length=20, blank=True, null=True)
    productgroupcode = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_salesorder'


class TblSupplierList(models.Model):
    no = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=150, blank=True, null=True)
    location_code = models.CharField(max_length=50, blank=True, null=True)
    phone_no = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_supplier_list'


class TblUnitsofmeasure(models.Model):
    id = models.IntegerField(blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    international_standard_code = models.CharField(max_length=50, blank=True, null=True)
    gst_reporting_uqc = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_unitsofmeasure'


class TblUserdetails(models.Model):
    user_id = models.CharField(primary_key=True, max_length=20)
    user_name = models.CharField(max_length=100, blank=True, null=True)
    user_password = models.CharField(max_length=100)
    email_address = models.CharField(unique=True, max_length=150)
    access_role = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tbl_userdetails'


class TblUsermanagement(models.Model):
    user_name = models.CharField(max_length=100)
    email_address = models.CharField(max_length=150, blank=True, null=True)
    user_password = models.CharField(max_length=100)
    user_group = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tbl_usermanagement'


class TblUsertaskdetails(models.Model):
    task_name = models.CharField(max_length=150)
    form_name = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_usertaskdetails'


class TodoTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'todo_task'
