from django.db import models


class ApplyTemplate(models.Model):
    id = models.AutoField(primary_key=True)
    template_name = models.CharField(max_length=100, db_column="type")
    item_category_code = models.CharField(max_length=50, null=True, db_column="item_category_code")
    costing_method = models.CharField(max_length=50, null=True, db_column="costing_method")
    inventory_posting_group = models.CharField(max_length=50, null=True, db_column="inventory_posting_group")
    price_profit_calculation = models.CharField(max_length=50, null=True, db_column="price_profit_calculation")
    gen_prod_posting_group = models.CharField(max_length=50, null=True, db_column="gen_prod_posting_group")
    replenishment_system = models.CharField(max_length=50, null=True, db_column="replenishment_system")
    qc_applicable = models.CharField(max_length=50, null=True, db_column="qc_applicable")
    manufacturing_policy = models.CharField(max_length=50, null=True, db_column="manufacturing_policy")
    assembly_policy = models.CharField(max_length=50, null=True, db_column="assembly_policy")
    reordering_policy = models.CharField(max_length=50, null=True, db_column="reordering_policy")
    include_inventory = models.CharField(max_length=50, null=True, db_column="include_inventory")
    gst_credit = models.CharField(max_length=50, null=True, db_column="gst_credit")
    flushing_method = models.CharField(max_length=50, null=True, db_column="flushing_method")
    template_applied = models.CharField(max_length=100, null=True, db_column="template_applied")
    rounding_precision = models.CharField(max_length=50, null=True, db_column="rounding_precision")
    gst_group_code = models.CharField(max_length=50, null=True, db_column="gst_group_code")

    class Meta:
        db_table = "tbl_applytemplate"
        managed = False


class ItemCard(models.Model):
    """Read/write model for tbl_itemcard. No PK constraint in DB — 'no' is logical PK."""
    no = models.CharField(max_length=50, primary_key=True, db_column="no")
    customer_id = models.CharField(max_length=50, db_column="customerid", null=True)
    customer_name_org = models.CharField(max_length=255, db_column="customername", null=True)
    description = models.CharField(max_length=255, db_column="description", null=True)
    template_name = models.CharField(max_length=100, db_column="template_name", null=True)
    base_unit_of_measure = models.CharField(max_length=50, db_column="base_unit_of_measure", null=True)
    shelf_no = models.CharField(max_length=50, db_column="shelf_no", null=True)
    cell = models.CharField(max_length=50, db_column="cell", null=True)
    cell_type = models.CharField(max_length=50, db_column="cell_type", null=True)
    item_category_code = models.CharField(max_length=50, db_column="item_category_code", null=True)
    product_group_code = models.CharField(max_length=50, db_column="product_group_code", null=True)
    status = models.CharField(max_length=50, db_column="status", null=True)
    last_date_modified = models.TextField(db_column="last_date_modified", null=True)
    fixture_no = models.CharField(max_length=50, db_column="fixture_no", null=True)
    no_of_parts = models.CharField(max_length=50, db_column="no_of_parts", null=True)
    no_of_meft = models.CharField(max_length=50, db_column="no_of_meft", null=True)
    customer_name = models.CharField(max_length=255, db_column="customer_name", null=True)
    revision_no = models.CharField(max_length=50, db_column="revision_no", null=True)
    customer_vendor_code = models.CharField(max_length=100, db_column="customer_vendor_code", null=True)
    hsn_sac_code = models.CharField(max_length=50, db_column="hsn_sac_code", null=True)
    costing_method = models.CharField(max_length=100, db_column="costing_method", null=True)
    inventory_posting_group = models.CharField(max_length=100, db_column="inventory_posting_group", null=True)
    price_profit_calculation = models.CharField(max_length=100, db_column="price_profit_calculation", null=True)
    gen_prod_posting_group = models.CharField(max_length=100, db_column="gen_prod_posting_group", null=True)
    replenishment_system = models.CharField(max_length=100, db_column="replenishment_system", null=True)
    qc_applicable = models.CharField(max_length=100, db_column="qc_applicable", null=True)
    manufacturing_policy = models.CharField(max_length=100, db_column="manufacturing_policy", null=True)
    assembly_policy = models.CharField(max_length=100, db_column="assembly_policy", null=True)
    reordering_policy = models.CharField(max_length=100, db_column="reordering_policy", null=True)
    include_inventory = models.CharField(max_length=100, db_column="include_inventory", null=True)
    gst_credit = models.CharField(max_length=100, db_column="gst_credit", null=True)
    flushing_method = models.CharField(max_length=100, db_column="flushing_method", null=True)
    template_applied = models.CharField(max_length=255, db_column="template_applied", null=True)
    rounding_precision = models.CharField(max_length=50, db_column="rounding_precision", null=True)
    gst_group_code = models.CharField(max_length=50, db_column="gst_group_code", null=True)
    monthyear = models.CharField(max_length=20, db_column="monthyear", null=True)
    fy = models.CharField(max_length=20, db_column="fy", null=True)
    quarter = models.CharField(max_length=10, db_column="quarter", null=True)
    is_download = models.TextField(db_column="is_download", null=True)
    unit_price = models.TextField(db_column="unit_price", null=True)

    class Meta:
        db_table = "tbl_itemcard"
        managed = False


class UnitOfMeasure(models.Model):
    code = models.CharField(max_length=50, primary_key=True, db_column="code")
    description = models.CharField(max_length=255, db_column="description")

    class Meta:
        db_table = "tbl_unitsofmeasure"
        managed = False


class ItemCategory(models.Model):
    code = models.CharField(max_length=50, primary_key=True, db_column="code")
    description = models.CharField(max_length=255, db_column="description")
    def_gen_prod_posting_group = models.CharField(max_length=50, db_column="def_gen_prod_posting_group", null=True)

    class Meta:
        db_table = "tbl_itemcategories"
        managed = False


class ProductGroup(models.Model):
    code = models.CharField(max_length=50, primary_key=True, db_column="code")

    class Meta:
        db_table = "tbl_productgroups"
        managed = False


class Cell(models.Model):
    code = models.CharField(max_length=50, primary_key=True, db_column="code")

    class Meta:
        db_table = "tbl_cell"
        managed = False


class CellType(models.Model):
    code = models.CharField(max_length=50, primary_key=True, db_column="code")

    class Meta:
        db_table = "tbl_celltype"
        managed = False


class HSNCode(models.Model):
    code = models.CharField(max_length=50, primary_key=True, db_column="code")
    description = models.TextField(db_column="description", null=True)
    gst_group_code = models.CharField(max_length=50, db_column="gst_group_code", null=True)

    class Meta:
        db_table = "tbl_itemcard_invoice"
        managed = False


class CustomerInfo(models.Model):
    """Read-only view of tbl_customerinfo for lookup purposes."""
    customer_id = models.CharField(max_length=50, primary_key=True, db_column="customer_id")
    name = models.TextField(db_column="name", null=True)
    shortname = models.TextField(db_column="shortname", null=True)
    primary_contact_no = models.TextField(db_column="primary_contact_no", null=True)

    class Meta:
        db_table = "tbl_customerinfo"
        managed = False


class RFQDetails(models.Model):
    """Read-only view of tbl_rfq_details for completion/lock checks."""
    id = models.CharField(max_length=50, primary_key=True, db_column="id")
    customer_id = models.CharField(max_length=50, db_column="customer_id", null=True)
    itemcreation_id = models.CharField(max_length=50, db_column="itemcreation_id", null=True)
    is_completed = models.BooleanField(db_column="is_completed", null=True)

    class Meta:
        db_table = "tbl_rfq_details"
        managed = False