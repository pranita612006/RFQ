from django.db import models
from django.contrib.auth import get_user_model


class NormsDetails(models.Model):
    """Maps to the existing PostgreSQL table: tbl_normsdetails.

    managed = False — table already exists with production data.
    All db_column values are lowercase to match the actual Postgres schema.
    """
    Sr_No               = models.AutoField(primary_key=True,  db_column='sr_no')
    Norms_Code          = models.CharField(max_length=255,    db_column='norms_code',          blank=True, null=True)
    Sheet_Name          = models.CharField(max_length=255,    db_column='sheet_name',          blank=True, null=True)
    Customer_Name       = models.CharField(max_length=255,    db_column='customer_name',       blank=True, null=True)
    Cell_Location       = models.CharField(max_length=500,    db_column='cell_location',       blank=True, null=True)
    Cell_Value          = models.TextField(                   db_column='cell_value',          blank=True, null=True)
    Location            = models.CharField(max_length=500,    db_column='location',            blank=True, null=True)
    Export_Path         = models.TextField(                   db_column='export_path',         blank=True, null=True)
    # Extra columns present in the real table
    local_bo_flag       = models.BooleanField(default=False,  db_column='local_bo_flag',       blank=True, null=True)
    total_local_bo_flag = models.BooleanField(default=False,  db_column='total_local_bo_flag', blank=True, null=True)
    packaging_series    = models.BooleanField(default=False,  db_column='packaging_series',    blank=True, null=True)
    packaging_proto     = models.BooleanField(default=False,  db_column='packaging_proto',     blank=True, null=True)
    os_template         = models.CharField(max_length=255,    db_column='os_template',         blank=True, null=True)

    class Meta:
        db_table = 'tbl_normsdetails'
        managed  = False

    def __str__(self):
        return f"{self.Norms_Code} | {self.Sheet_Name}"


class CostingInternalConversion(models.Model):
    """Maps to PostgreSQL table tbl_costing_internalconversion."""
    id                     = models.AutoField(primary_key=True, db_column='id')
    description            = models.CharField(max_length=255, db_column='description', blank=True, null=True)
    mhr                    = models.DecimalField(max_digits=12, decimal_places=4, db_column='mhr', blank=True, null=True)
    run_time_sec           = models.DecimalField(max_digits=12, decimal_places=4, db_column='run_time_sec', blank=True, null=True)
    perhouroutput          = models.DecimalField(max_digits=12, decimal_places=4, db_column='perhouroutput', blank=True, null=True)
    rateperunit            = models.DecimalField(max_digits=12, decimal_places=4, db_column='rateperunit', blank=True, null=True)
    boq                    = models.DecimalField(max_digits=12, decimal_places=4, db_column='boq', blank=True, null=True)
    total                  = models.DecimalField(max_digits=15, decimal_places=4, db_column='total', blank=True, null=True)
    contributionpercentage = models.DecimalField(max_digits=8, decimal_places=4, db_column='contributionpercentage', blank=True, null=True)
    mhr_category           = models.CharField(max_length=50, db_column='mhr_category', blank=True, null=True)
    customer_id            = models.CharField(max_length=50, db_column='customer_id', blank=True, null=True)
    itemcreation_id        = models.CharField(max_length=50, db_column='itemcreation_id', blank=True, null=True)

    class Meta:
        db_table = 'tbl_costing_internalconversion'
        managed = False

    def __str__(self):
        return f"{self.itemcreation_id} | {self.description} ({self.mhr_category})"


class DTCategoryList(models.Model):
    """Maps to tbl_dtcategorylist.

    category_name is the natural primary key stored in the 'category' column.
    Using it as primary_key=True means Django uses it directly for FK lookups
    without needing a separate numeric id column that may not exist.
    """
    category_name = models.CharField(
        max_length=100,
        primary_key=True,      # the DB's natural PK — no separate id column
        unique=True,
        db_index=True,
        db_column='category',
    )
    description   = models.TextField(blank=True, null=True, db_column='currency')
    is_active     = models.BooleanField(default=True)

    class Meta:
        db_table = 'tbl_dtcategorylist'
        managed = False

    def __str__(self):
        return self.category_name or ""


class DTAssignmentYearData(models.Model):
    """Maps to tbl_dtassigmentyeardata."""
    id              = models.AutoField(primary_key=True, db_column='id')
    item_creation   = models.CharField(max_length=50, db_column='itemcreation_id', blank=True, null=True, db_index=True)
    customer_id     = models.CharField(max_length=50, db_column='customer_id', blank=True, null=True)
    category        = models.CharField(max_length=100, db_column='category', blank=True, null=True)
    assignment_year = models.IntegerField(db_column='year', blank=True, null=True)
    assigned_value  = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, db_column='cost', blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'tbl_dtassigmentyeardata'
        managed = False

    def __str__(self):
        return f"{self.item_creation} | {self.category} ({self.assignment_year})"


# ---------------------------------------------------------------------------
# Offer Sheet RM Conversion
# ---------------------------------------------------------------------------

class OfferSheetRMConversion(models.Model):
    """Maps to the existing PostgreSQL table: tbl_offersheetrmconversion.

    This table is the write-target for the BOC sync service.
    managed = False — the table already exists in production.
    """
    id                   = models.AutoField(primary_key=True)
    part_number          = models.CharField(max_length=100,  blank=True, null=True)
    raw_material_desc    = models.TextField(blank=True,       null=True,  db_column='raw_material_description')
    tube_size            = models.CharField(max_length=50,   blank=True, null=True)
    unit                 = models.CharField(max_length=20,   blank=True, null=True)
    internal_cost        = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    rate_per_unit        = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, db_column='rateperunit')
    qnty                 = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_cost           = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    rm_flag              = models.CharField(max_length=20,   blank=True, null=True)
    customer_id          = models.CharField(max_length=50,   blank=True, null=True)
    item_creation_id     = models.CharField(max_length=50,   blank=True, null=True, db_column='itemcreation_id')
    process_date         = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'tbl_offersheetrmconversion'
        managed  = False

    def __str__(self) -> str:
        return f"{self.customer_id} | {self.item_creation_id} | {self.rm_flag} | {self.part_number}"


# ---------------------------------------------------------------------------
# BOP Creation (approval gate)
# ---------------------------------------------------------------------------

class BopCreation(models.Model):
    """Thin read-only proxy onto tbl_bopcreation for prerequisite checking.

    managed = False — do not alter the live BOP table.
    """
    id              = models.AutoField(primary_key=True, db_column='id')
    customer_id     = models.CharField(max_length=50,  blank=True, null=True, db_column='customer_id')
    itemcreation_id = models.CharField(max_length=50,  blank=True, null=True, db_column='itemcreation_id')
    table_id        = models.IntegerField(blank=True, null=True, db_column='table_id')
    action_status   = models.CharField(max_length=50,  blank=True, null=True, db_column='action_status')

    class Meta:
        db_table = 'tbl_bopcreation'
        managed  = False

    def __str__(self) -> str:
        return f"{self.customer_id} | {self.itemcreation_id} | {self.action_status}"


class BopTab(models.Model):
    """Maps to tbl_bop_tab for fetching Conversion Cost operation details."""
    id              = models.AutoField(primary_key=True)
    table_id        = models.IntegerField(blank=True, null=True, db_column='table_id')
    customer_id     = models.CharField(max_length=50, blank=True, null=True, db_column='customer_id')
    itemcreation_id = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_id')
    categorisation  = models.CharField(max_length=150, blank=True, null=True, db_column='categorisation')
    costperqnty     = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='costperqnty')
    boq             = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='boq')
    total_cost      = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True, db_column='total_cost')
    description     = models.TextField(blank=True, null=True, db_column='description')

    class Meta:
        db_table = 'tbl_bop_tab'
        managed  = False

    def __str__(self) -> str:
        return f"{self.customer_id} | {self.itemcreation_id} | {self.categorisation}"


class BopTolling(models.Model):
    """Maps to tbl_bop_tolling for Data Tooling : Internal & Recovery Tooling Cost."""
    id                  = models.AutoField(primary_key=True)
    tool_description    = models.TextField(blank=True, null=True, db_column='tool_description')
    uom                 = models.CharField(max_length=50, blank=True, null=True, db_column='uom')
    unit_cost           = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='unit_cost')
    settled_price       = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='settled_price')
    qty_required        = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='qty_required')
    total_estimate      = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='total_estimate')
    total_settledprice  = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_column='total_settledprice')
    entry_date          = models.DateField(blank=True, null=True, db_column='entry_date')
    bopcreationid       = models.CharField(max_length=50, blank=True, null=True, db_column='bopcreationid')
    itemcreation_id     = models.CharField(max_length=50, blank=True, null=True, db_column='itemcreation_id')
    table_id            = models.IntegerField(blank=True, null=True, db_column='table_id')
    customer_id         = models.CharField(max_length=50, blank=True, null=True, db_column='customer_id')
    remarks             = models.TextField(blank=True, null=True, db_column='remarks')
    completedon         = models.DateField(blank=True, null=True, db_column='completedon')

    class Meta:
        db_table = 'tbl_bop_tolling'
        managed  = False

    def __str__(self) -> str:
        return f"{self.customer_id} | {self.itemcreation_id} | {self.tool_description}"


from django.db.models.fields.related import ForeignObject


# ---------------------------------------------------------------------------
# BOM Creation (approval gate & related model)
# ---------------------------------------------------------------------------

class BomCreation(models.Model):
    """Maps to tbl_BomCreation (PostgreSQL table: tbl_bomcreation)."""
    bomcreation_id   = models.CharField(max_length=50, primary_key=True, db_column='BOMCreation_Id')
    table_id         = models.CharField(max_length=50, null=True, blank=True, db_column='Table_Id')
    customer_id      = models.CharField(max_length=50,  blank=True, null=True, db_column='Customer_ID')
    item_creation_id = models.CharField(max_length=50,  blank=True, null=True, db_column='ItemCreation_Id')
    remark           = models.TextField(blank=True, null=True, db_column='Remark')

    class Meta:
        db_table = 'tbl_bomcreation'
        managed  = False

    @property
    def id(self):
        return self.bomcreation_id

    @id.setter
    def id(self, val):
        self.bomcreation_id = val

    def __str__(self) -> str:
        return f"BOM {self.bomcreation_id} (table {self.table_id}) | {self.customer_id}"


# ---------------------------------------------------------------------------
# Offer Sheet Part Details (Costing Calculator Local/Imported BOC)
# ---------------------------------------------------------------------------

class OfferSheetPartDetails(models.Model):
    """Primary Django Model mapped to PostgreSQL view/table tbl_OfferSheetPartDetails."""
    id                   = models.AutoField(primary_key=True)
    part_number          = models.CharField(max_length=100, db_column='Part_Number', null=True, blank=True)
    description          = models.TextField(db_column='Description', null=True, blank=True)
    unit_of_measure_code = models.CharField(max_length=20, db_column='Unit_of_Measure_Code', null=True, blank=True)
    quantity             = models.FloatField(db_column='Quantity', default=0.0)
    internal_cost        = models.FloatField(db_column='Internal_Cost', default=0.0)
    settle_price         = models.FloatField(db_column='Settle Price', null=True, blank=True)
    categorisation       = models.CharField(max_length=50, db_column='Categorisation', null=True, blank=True)
    customer_id          = models.CharField(max_length=50, db_column='Customer_ID')
    itemcreation_id      = models.CharField(max_length=50, db_column='ItemCreation_Id')
    bomcreation_id       = models.CharField(max_length=50, db_column='BOMCreation_ID', null=True, blank=True)
    table_id             = models.CharField(max_length=50, db_column='Table_id', null=True, blank=True)

    # Multi-column relationship to BomCreation matching MS Access join:
    # LEFT JOIN tbl_BomCreation ON (t1.BOMCreation_ID = t2.BOMCreation_ID AND t1.Table_id = t2.table_id)
    bom = ForeignObject(
        BomCreation,
        on_delete=models.DO_NOTHING,
        from_fields=['bomcreation_id', 'table_id'],
        to_fields=['bomcreation_id', 'table_id'],
        null=True,
        blank=True,
        related_name='part_details',
    )

    class Meta:
        db_table = 'tbl_OfferSheetPartDetails'
        managed  = False

    def __str__(self) -> str:
        return f"{self.part_number} | {self.categorisation} (Cust: {self.customer_id}, Item: {self.itemcreation_id})"


# ---------------------------------------------------------------------------
# RFQ Details (completion gate)
# ---------------------------------------------------------------------------

class RFQDetails(models.Model):
    """Thin read-only proxy onto tbl_rfq_details for prerequisite checking.

    managed = False — the table is shared across multiple apps.
    """
    id               = models.AutoField(primary_key=True)
    customer_id      = models.CharField(max_length=50,  blank=True, null=True, db_column='customer_id')
    itemcreation_id  = models.CharField(max_length=50,  blank=True, null=True, db_column='itemcreation_id')
    customername     = models.CharField(max_length=255, blank=True, null=True, db_column='customername')
    bomcreation_id   = models.CharField(max_length=50,  blank=True, null=True, db_column='bomcreation_id')
    bopcreation_id   = models.CharField(max_length=50,  blank=True, null=True, db_column='bopcreation_id')
    boc_creation_id  = models.CharField(max_length=50,  blank=True, null=True, db_column='boc_creation_id')
    is_completed     = models.CharField(max_length=20,  blank=True, null=True, db_column='is_completed')
    action_date      = models.DateTimeField(blank=True, null=True, db_column='action_date')
    updated_by       = models.CharField(max_length=100, blank=True, null=True, db_column='updated_by')

    class Meta:
        db_table = 'tbl_rfq_details'
        managed  = False

    def __str__(self) -> str:
        return f"{self.customer_id} | {self.itemcreation_id} | is_completed={self.is_completed}"


# ---------------------------------------------------------------------------
# Offer Sheet BOC  (Costing Calculator — Local / Imported BOC)
# ---------------------------------------------------------------------------

class OfferSheetBOC(models.Model):
    """Primary Django Model for the Costing Calculator BOC entries.

    Mapped to the PostgreSQL table: ztbl_offersheet_boc.

    Each row represents a single Bill-of-Components line saved by the user
    through the Costing Calculator UI.  The table is fully managed by Django
    (managed = True), so migrations will create / alter it automatically.

    Key discriminator columns:
        boc_type   — 'Local' | 'Imported'
        update_by  — 'USER' (rows submitted by the web UI)
    """
    part_number          = models.CharField(max_length=100,  db_column='part_number',          null=True,  blank=True)
    description          = models.TextField(                  db_column='description',          null=True,  blank=True)
    unit_of_measure_code = models.CharField(max_length=20,   db_column='unit_of_measure_code', null=True,  blank=True)
    quantity             = models.FloatField(                 db_column='quantity',             default=0.0)
    internal_cost        = models.FloatField(                 db_column='internal_cost',        default=0.0)
    settle_price         = models.FloatField(                 db_column='settle_price',         default=0.0)
    cost                 = models.FloatField(                 db_column='cost',                 default=0.0)
    categorisation       = models.CharField(max_length=50,   db_column='categorisation',       null=True,  blank=True)
    customer_id          = models.CharField(max_length=50,   db_column='customer_id')
    itemcreation_id      = models.BigIntegerField(            db_column='itemcreation_id')
    boc_type             = models.CharField(max_length=50,   db_column='boc_type',             default='Local')
    update_by            = models.CharField(max_length=100,  db_column='update_by',            null=True, blank=True)

    class Meta:
        db_table = 'ztbl_offersheet_boc'
        managed  = False  # Table pre-exists in PostgreSQL; Django manages ORM only

    def __str__(self) -> str:
        return (
            f"{self.part_number} | {self.boc_type} | "
            f"Cust: {self.customer_id} | Item: {self.itemcreation_id}"
        )


class OfferSheetTransCost(models.Model):
    """Maps to PostgreSQL table tbl_offersheet_transcost."""
    id              = models.AutoField(primary_key=True)
    particular      = models.CharField(max_length=255, db_column='particular')
    total_cost      = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, db_column='total_cost')
    cust_code       = models.CharField(max_length=100, blank=True, null=True, db_column='cust_code')
    customer_id     = models.CharField(max_length=100, blank=True, null=True, db_column='customer_id')
    itemcreation_id = models.CharField(max_length=100, blank=True, null=True, db_column='itemcreation_id')

    class Meta:
        db_table = 'tbl_offersheet_transcost'
        managed  = False

    def __str__(self) -> str:
        return f"{self.customer_id} | {self.itemcreation_id} | {self.particular}: {self.total_cost}"

