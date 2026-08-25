from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class BocItemCard(models.Model):
    no = models.CharField(max_length=50, primary_key=True, db_column="no")
    customerid = models.CharField(max_length=50, db_column="customerid", null=True, blank=True)
    drg_revno = models.CharField(max_length=50, db_column="revision_no", null=True, blank=True)
    drg_revdate = models.DateField(db_column="last_date_modified", null=True, blank=True)
    customer_partsetno = models.CharField(max_length=50, db_column="customer_vendor_code", null=True, blank=True)
    part_name = models.CharField(max_length=255, db_column="description", null=True, blank=True)

    class Meta:
        db_table = "tbl_itemcard"
        managed = False

class BocCreation(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=150, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_rowid = models.CharField(max_length=50, blank=True, null=True)
    boc_creation_id = models.CharField(max_length=50, primary_key=True)
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

class BocCreationEcn(models.Model):
    boc_creation_id = models.CharField(max_length=50, blank=True, null=True)
    table_id        = models.CharField(max_length=50, blank=True, null=True)
    ecn_id          = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_boc_creation_ecn'

class BocTolling(models.Model):
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

class BocTollingEcn(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True)
    boc_creation_id = models.CharField(db_column='boc_creationid', max_length=50, blank=True, null=True)

    tool_descriptionforboc = models.TextField(db_column='tool_description_boc', blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    qty_required = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    total_estimate = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    table_id = models.CharField(max_length=50, blank=True, null=True)
    ecn_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_boc_tolling_ecn'

class BocStatus(models.Model):
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

class SupplierList(models.Model):
    no = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=150, blank=True, null=True)
    location_code = models.CharField(max_length=50, blank=True, null=True)
    phone_no = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_supplier_list'
