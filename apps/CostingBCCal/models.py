from django.db import models


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
    category        = models.ForeignKey(
        DTCategoryList,
        on_delete=models.CASCADE,
        related_name="assignments",
        db_column='category',
        to_field='category_name',
    )
    assignment_year = models.IntegerField(db_column='year', blank=True, null=True)
    assigned_value  = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, db_column='cost', blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'tbl_dtassigmentyeardata'
        managed = False

    def __str__(self):
        return f"{self.item_creation} | {self.category_id} ({self.assignment_year})"

