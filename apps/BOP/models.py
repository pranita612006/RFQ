from django.db import models

class CustomerInfo(models.Model):
    cust_id = models.CharField(max_length=50, primary_key=True, db_column='customer_id') 
    cust_code = models.CharField(max_length=50, db_column='cust_code')
    cust_name = models.CharField(max_length=255, db_column='name')

    class Meta:
        db_table = 'tbl_customerinfo'
        managed = False

    def __str__(self):
        return f"{self.cust_code} - {self.cust_name}"


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class BOPCreation(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    customer_id = models.CharField(max_length=50, blank=True, null=True, db_column='customer_id')
    itemcreation_id = models.IntegerField(blank=True, null=True, db_column='itemcreation_id')
    bop_rowid = models.IntegerField(blank=True, null=True, db_column='bop_rowid')
    bopcreation_id = models.CharField(max_length=50, blank=True, null=True, db_column='bopcreation_id')
    customer_name = models.CharField(max_length=200, blank=True, null=True, db_column='customer_name')
    drawing_no = models.CharField(max_length=100, blank=True, null=True, db_column='drawing_no')
    drawing_revision_no = models.CharField(max_length=50, blank=True, null=True, db_column='drawing_revision_no')
    revision_date = models.DateField(blank=True, null=True, db_column='revision_date')
    part_set_no = models.CharField(max_length=100, blank=True, null=True, db_column='part_set_no')
    part_name = models.CharField(max_length=200, blank=True, null=True, db_column='part_name')
    product_category = models.CharField(max_length=150, blank=True, null=True, db_column='product_category')
    project = models.CharField(max_length=150, blank=True, null=True, db_column='project')
    entry_date = models.DateField(blank=True, null=True, db_column='entry_date')
    remark = models.TextField(blank=True, null=True, db_column='remark')
    table_id = models.IntegerField(blank=True, null=True, db_column='table_id')
    action_status = models.CharField(max_length=50, blank=True, null=True, db_column='action_status')
    last_modified_date = models.DateField(blank=True, null=True, db_column='last_modified_date')
    is_download = models.BooleanField(blank=True, null=True, db_column='is_download')

    class Meta:
        db_table = 'tbl_bopcreation'
        managed = False

    def __str__(self):
        return f"{self.bopcreation_id} - {self.customer_name}"


class BOPCreationECN(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    bopcreation_id = models.CharField(max_length=50, db_column='bopcreation_id')
    ecn_no = models.CharField(max_length=50, default='ECN-001', db_column='ecn_id')
    revision_date = models.DateField(db_column='revision_date')
    customer_id = models.CharField(max_length=50, blank=True, null=True, db_column='customer_id')
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_id')
    bop_rowid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, db_column='bop_rowid')
    customer_name = models.CharField(max_length=200, blank=True, null=True, db_column='customer_name')
    drawing_no = models.CharField(max_length=100, blank=True, null=True, db_column='drawing_no')
    drawing_revision_no = models.CharField(max_length=50, blank=True, null=True, db_column='drawing_revision_no')
    part_set_no = models.CharField(max_length=100, blank=True, null=True, db_column='part_set_no')
    part_name = models.CharField(max_length=200, blank=True, null=True, db_column='part_name')
    product_category = models.CharField(max_length=150, blank=True, null=True, db_column='product_category')
    project = models.CharField(max_length=150, blank=True, null=True, db_column='project')
    entry_date = models.DateField(blank=True, null=True, db_column='entry_date')
    remark = models.TextField(blank=True, null=True, db_column='remark')
    table_id = models.IntegerField(blank=True, null=True, db_column='table_id')

    class Meta:
        db_table = 'tbl_bopcreation_ecn'
        managed = False

    def __init__(self, *args, **kwargs):
        self.annual_volume_1 = kwargs.pop('annual_volume_1', None)
        self.annual_volume_2 = kwargs.pop('annual_volume_2', None)
        self.annual_volume_3 = kwargs.pop('annual_volume_3', None)
        self.annual_volume_4 = kwargs.pop('annual_volume_4', None)
        self.annual_volume_5 = kwargs.pop('annual_volume_5', None)
        super().__init__(*args, **kwargs)


class OpportunityMaster(models.Model):
    item_no = models.CharField(max_length=100, primary_key=True, db_column='item_no')
    id = models.CharField(max_length=50, blank=True, null=True, db_column='id')
    customer_name = models.CharField(max_length=255, blank=True, null=True, db_column='customer_name')
    part_no = models.CharField(max_length=100, blank=True, null=True, db_column='part_no')
    drawing_no = models.CharField(max_length=100, blank=True, null=True, db_column='drawing_no')
    drawing_revision_no = models.CharField(max_length=50, blank=True, null=True, db_column='drawing_revision_no')
    part_name = models.CharField(max_length=255, blank=True, null=True, db_column='part_name')
    project_name = models.CharField(max_length=255, blank=True, null=True, db_column='project_name')
    status = models.CharField(max_length=100, blank=True, null=True, db_column='status')
    
    annual_volume_1 = models.CharField(max_length=100, blank=True, null=True, db_column='annual_volume')
    annual_volume_2 = models.CharField(max_length=100, blank=True, null=True, db_column='annual_volume_2')
    annual_volume_3 = models.CharField(max_length=100, blank=True, null=True, db_column='annual_volume_3')
    annual_volume_4 = models.CharField(max_length=100, blank=True, null=True, db_column='annual_volume_4')
    annual_volume_5 = models.CharField(max_length=100, blank=True, null=True, db_column='annual_volume_5')
    
    business = models.CharField(max_length=150, blank=True, null=True, db_column='business')
    sop_date = models.CharField(max_length=100, blank=True, null=True, db_column='sop_date')

    class Meta:
        db_table = 'tbl_opportunitymaster'
        managed = False


class BOPCellAlignment(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_id')
    product_category = models.CharField(max_length=150, blank=True, null=True, db_column='product_category')
    process = models.CharField(max_length=150, blank=True, null=True, db_column='process')
    manufacturing_location = models.CharField(max_length=150, blank=True, null=True, db_column='manufacturing_loacation')
    cell = models.CharField(max_length=100, blank=True, null=True, db_column='cell')
    quantity = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='quantity')
    bopcreationid = models.CharField(max_length=50, blank=True, null=True, db_column='bopcreationid')
    table_id = models.IntegerField(blank=True, null=True, db_column='table_id')
    remarks = models.TextField(blank=True, null=True, db_column='remarks')
    completedon = models.DateField(blank=True, null=True, db_column='completedon')

    class Meta:
        db_table = 'tbl_bop_cellallienment'
        managed = False


class BOPCellAlignmentECN(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    product_category = models.CharField(max_length=150, blank=True, null=True, db_column='product_category')
    process = models.CharField(max_length=150, blank=True, null=True, db_column='process')
    manufacturing_location = models.CharField(max_length=150, blank=True, null=True, db_column='manufacturing_loacation')
    cell = models.CharField(max_length=100, blank=True, null=True, db_column='cell')
    quantity = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='quantity')
    bopcreationid = models.CharField(max_length=50, blank=True, null=True, db_column='bopcreationid')
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_id')
    table_id = models.IntegerField(blank=True, null=True, db_column='table_id')
    remarks = models.TextField(blank=True, null=True, db_column='remarks')
    completedon = models.DateField(blank=True, null=True, db_column='completedon')
    ecn_id = models.CharField(max_length=50, blank=True, null=True, db_column='ecn_id')
    itemcreation_ecn = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_ecn')

    class Meta:
        db_table = 'tbl_bop_cellallienment_ecn'
        managed = False


class BOPCellAlignmentType(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    process = models.CharField(max_length=150, blank=True, null=True, db_column='process')
    manufacturing_location = models.CharField(max_length=150, blank=True, null=True, db_column='manufacturing_loacation')
    cell = models.CharField(max_length=150, blank=True, null=True, db_column='cell')

    class Meta:
        db_table = 'tbl_bop_cellallienment_type'
        managed = False


class BOPTypeMaster(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    type = models.CharField(max_length=50, blank=True, null=True, db_column='type')
    no = models.CharField(max_length=50, blank=True, null=True, db_column='no')
    name = models.CharField(max_length=150, blank=True, null=True, db_column='name')
    work_center_group_code = models.CharField(max_length=50, blank=True, null=True, db_column='work_center_group_code')
    alternate_work_center = models.CharField(max_length=50, blank=True, null=True, db_column='alternate_work_center')
    unit_of_measure_code = models.CharField(max_length=50, blank=True, null=True, db_column='unit_of_measure_code')
    capacity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, db_column='capacity')
    shop_calendar_code = models.CharField(max_length=50, blank=True, null=True, db_column='shop_calendar_code')
    search_name = models.CharField(max_length=150, blank=True, null=True, db_column='search_name')
    categorisation = models.CharField(max_length=100, blank=True, null=True, db_column='categorisation')
    costperquantity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, db_column='costperquantity')
    mhr_year = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, db_column='mhr_year')
    mhr_higher = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, db_column='mhr_higher')
    mhr_lower = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, db_column='mhr_lower')
    product_line = models.CharField(db_column='Product Line', max_length=100, blank=True, null=True)
    cust_code = models.CharField(max_length=50, blank=True, null=True, db_column='cust_code')

    class Meta:
        db_table = 'tbl_bop_types'
        managed = False

    def __str__(self):
        return f"{self.no} - {self.name}"


class BOPToolingMaster(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    tool_description = models.CharField(max_length=255, blank=True, null=True, db_column='description')
    uom = models.CharField(max_length=50, blank=True, null=True, db_column='uom')
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, db_column='unit_cost')
    settled_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, db_column='settled_price')
    customer_code = models.CharField(max_length=50, blank=True, null=True, db_column='customer_code')

    class Meta:
        db_table = 'tbl_bop_tool_measure'
        managed = False

    def __str__(self):
        return f"{self.tool_description or ''}"


class BOPTab(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    seq_no = models.IntegerField(blank=True, null=True, db_column='seq_no')
    operation_no = models.CharField(max_length=50, blank=True, null=True, db_column='operation_no')
    type = models.CharField(max_length=100, blank=True, null=True, db_column='type')
    costcenter_no = models.CharField(max_length=50, blank=True, null=True, db_column='costcenter_no')
    description = models.TextField(blank=True, null=True, db_column='description')
    categorisation = models.CharField(max_length=150, blank=True, null=True, db_column='categorisation')
    run_time_sec = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='run_time_sec')
    run_time_min = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='run_time_min')
    boq = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='boq')
    total_run_time = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='total_run_time')
    cycle_time = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='cycle_time')
    mhr_year = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='mhr_year')
    mhr_lower = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='mhr_lower')
    mhr_higher = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='mhr_higher')
    costperqnty = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='costperqnty')
    total_cost = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='total_cost')
    remark = models.TextField(blank=True, null=True, db_column='remark')
    table_id = models.IntegerField(blank=True, null=True, db_column='table_id')
    bopcreationid = models.CharField(max_length=50, blank=True, null=True, db_column='bopcreationid')
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_id')
    customer_id = models.CharField(max_length=50, blank=True, null=True, db_column='customer_id')
    type_selected = models.CharField(max_length=100, blank=True, null=True, db_column='type_selected')
    completedon = models.TextField(blank=True, null=True, db_column='completedon')
    last_modified_date = models.TextField(blank=True, null=True, db_column='last_modified_date')
    is_download = models.BooleanField(blank=True, null=True, db_column='is_download')

    class Meta:
        db_table = 'tbl_bop_tab'
        managed = False


class BOPTabECN(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    seq_no = models.IntegerField(blank=True, null=True, db_column='seq_no')
    operation_no = models.CharField(max_length=50, blank=True, null=True, db_column='operation_no')
    type = models.CharField(max_length=100, blank=True, null=True, db_column='type')
    costcenter_no = models.CharField(max_length=50, blank=True, null=True, db_column='costcenter_no')
    description = models.TextField(blank=True, null=True, db_column='description')
    categorisation = models.CharField(max_length=150, blank=True, null=True, db_column='categorisation')
    run_time_sec = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='run_time_sec')
    run_time_min = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='run_time_min')
    boq = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='boq')
    total_run_time = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='total_run_time')
    cycle_time = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='cycle_time')
    mhr_year = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='mhr_year')
    mhr_lower = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='mhr_lower')
    mhr_higher = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='mhr_higher')
    costperqnty = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='costperqnty')
    total_cost = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='total_cost')
    remark = models.TextField(blank=True, null=True, db_column='remark')
    table_id = models.IntegerField(blank=True, null=True, db_column='table_id')
    bopcreationid = models.CharField(max_length=50, blank=True, null=True, db_column='bopcreationid')
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_id')
    customer_id = models.CharField(max_length=50, blank=True, null=True, db_column='customer_id')
    type_selected = models.CharField(max_length=100, blank=True, null=True, db_column='type_selected')
    completedon = models.TextField(blank=True, null=True, db_column='completedon')
    ecn_id = models.CharField(max_length=50, blank=True, null=True, db_column='ecn_id')
    itemcreation_ecn = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_ecn')

    class Meta:
        db_table = 'tbl_bop_tab_ecn'
        managed = False


class BOPTolling(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    tool_description = models.TextField(blank=True, null=True, db_column='tool_description')
    uom = models.CharField(max_length=50, blank=True, null=True, db_column='uom')
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='unit_cost')
    settled_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='settled_price')
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='qty_required')
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='total_estimate')
    total_settledprice = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='total_settledprice')
    entry_date = models.DateField(blank=True, null=True, db_column='entry_date')
    bopcreationid = models.CharField(max_length=50, blank=True, null=True, db_column='bopcreationid')
    itemcreation_id = models.IntegerField(blank=True, null=True, db_column='itemcreation_id')
    table_id = models.IntegerField(blank=True, null=True, db_column='table_id')
    customer_id = models.CharField(max_length=50, blank=True, null=True, db_column='customer_id')
    remarks = models.TextField(blank=True, null=True, db_column='remarks')
    completedon = models.DateField(blank=True, null=True, db_column='completedon')

    class Meta:
        db_table = 'tbl_bop_tolling'
        managed = False


class BOPTollingECN(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    tool_description = models.TextField(blank=True, null=True, db_column='tool_description')
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='unit_cost')
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='qty_required')
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='total_estimate')
    bopcreationid = models.CharField(max_length=50, blank=True, null=True, db_column='bopcreationid')
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_id')
    table_id = models.CharField(max_length=50, blank=True, null=True, db_column='table_id')
    customer_id = models.CharField(max_length=50, blank=True, null=True, db_column='customer_id')
    remarks = models.TextField(blank=True, null=True, db_column='remarks')
    completedon = models.DateField(blank=True, null=True, db_column='completedon')
    ecn_id = models.CharField(max_length=50, blank=True, null=True, db_column='ecn_id')
    itemcreation_ecn = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_ecn')

    class Meta:
        db_table = 'tbl_bop_tolling_ecn'
        managed = False
