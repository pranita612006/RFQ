from django.db import models
# Reload trigger: tbl_bom_proditem_partgrpmaster

class BOMHeader(models.Model):
    id = models.AutoField(primary_key=True)
    customer_id = models.CharField(max_length=50, db_column='Customer_ID', null=True, blank=True)
    item_creation_id = models.CharField(max_length=50, db_column='ItemCreation_Id', null=True, blank=True)
    bom_row_id = models.IntegerField(db_column='BOM_RowID', null=True, blank=True)
    bom_creation_id = models.CharField(max_length=50, db_column='BOMCreation_Id', null=True, blank=True)
    description = models.TextField(db_column='Description', null=True, blank=True)
    description_2 = models.TextField(db_column='Description_2', null=True, blank=True)
    search_name = models.CharField(max_length=100, db_column='Search_Name', null=True, blank=True)
    uom_code = models.CharField(max_length=50, db_column='Unit_of_Measure_Code', null=True, blank=True)
    low_level_code = models.CharField(max_length=50, db_column='Low-Level Code', null=True, blank=True)
    create_date = models.DateField(db_column='Creation_Date', null=True, blank=True)
    last_date_modified = models.DateField(db_column='Last_Date_Modified', null=True, blank=True)
    action_status = models.CharField(max_length=100, db_column='Status', null=True, blank=True)
    version_number = models.CharField(max_length=50, db_column='Version_Number', null=True, blank=True)
    series = models.CharField(max_length=50, db_column='Series', null=True, blank=True)
    table_id = models.CharField(max_length=50, db_column='Table_Id', null=True, blank=True)
    remark = models.TextField(db_column='Remark', null=True, blank=True)
    is_download = models.IntegerField(db_column='Is_Download', null=True, blank=True)

    class Meta:
        db_table = "tbl_bomcreation"
        managed = False

    def __str__(self):
        return f"{self.bom_creation_id}"

class BOMTransaction(models.Model):
    id = models.IntegerField(primary_key=True, db_column='Id')
    # NOTE: bom_creation_id is kept as a plain CharField (denormalized key) rather
    # than a ForeignKey because both models use managed=False (legacy unmanaged
    # tables). A Django ForeignKey would require the DB to have a matching PK
    # constraint, which may not exist in the legacy schema. Use
    # BOMHeader.objects.filter(bom_creation_id=...) for cross-model lookups.
    bom_creation_id = models.CharField(max_length=100, db_column='BOMCreation_ID', null=True, blank=True)
    entry_type = models.CharField(max_length=50, db_column='Entry_Type', null=True, blank=True)
    part_number = models.CharField(max_length=100, db_column='Part_Number', null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, db_column='Quantity', null=True, blank=True, default=0)
    description = models.CharField(max_length=255, db_column='Description', null=True, blank=True)
    uom_code = models.CharField(max_length=50, db_column='Unit_of_Measure_Code', null=True, blank=True)
    categorisation = models.CharField(max_length=100, db_column='Categorisation', null=True, blank=True)
    routing_link_code = models.CharField(max_length=100, db_column='Routing_Link_Code', null=True, blank=True)
    part_status = models.CharField(max_length=50, db_column='Part_Status', null=True, blank=True)
    
    grp_part_no = models.CharField(max_length=100, db_column='grp_part_number', null=True, blank=True)
    grp_part_descp = models.CharField(max_length=255, db_column='grp_part_description', null=True, blank=True)
    start_date = models.CharField(max_length=50, db_column='start_date', null=True, blank=True)
    
    table_id = models.CharField(max_length=100, db_column='Table_Id', null=True, blank=True)

    class Meta:
        db_table = "tbl_bomcreation_partselection"
        managed = False

    def __str__(self):
        return f"{self.part_number}"

class BOMItemList(models.Model):
    part_no = models.CharField(max_length=100, primary_key=True, db_column='part_no')
    description = models.CharField(max_length=255, db_column='description', null=True, blank=True)
    base_unit_of_measure = models.CharField(max_length=50, db_column='base_unit_of_measure', null=True, blank=True)
    categorisation = models.CharField(max_length=100, db_column='categorisation', null=True, blank=True)

    class Meta:
        db_table = "tbl_bom_itemlist"
        managed = False

class BOMProdItemPartGrpMaster(models.Model):
    row_id = models.AutoField(primary_key=True, db_column='row_id')
    grp_part_no = models.CharField(max_length=100, db_column='grp_partno', blank=True, null=True)
    grp_part_description = models.CharField(max_length=255, db_column='grp_part_description', null=True, blank=True)
    level = models.IntegerField(db_column='level', blank=True, null=True)
    part_no = models.CharField(max_length=100, db_column='part_no', blank=True, null=True)
    part_description = models.TextField(db_column='part_description', blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50, db_column='unit_of_measure', blank=True, null=True)
    bom_quantity = models.DecimalField(max_digits=18, decimal_places=4, db_column='bom_quantity', blank=True, null=True)
    total_bom_quantity = models.DecimalField(max_digits=18, decimal_places=4, db_column='total_bom_quantity', blank=True, null=True)

    class Meta:
        db_table = "tbl_bom_proditem_partgrpmaster"
        managed = False

class BOMPartDetailsMaster(models.Model):
    part_no = models.CharField(db_column='Part No', max_length=100, primary_key=True) 
    part_description = models.TextField(db_column='Part Description', blank=True, null=True) 
    base_unit_of_measure = models.CharField(db_column='Base Unit of Measure', max_length=50, blank=True, null=True) 
    customer = models.CharField(db_column='Customer', max_length=150, blank=True, null=True) 
    classification = models.CharField(db_column='Classification', max_length=100, blank=True, null=True) 
    cost_price = models.DecimalField(db_column='Cost_Price', max_digits=18, decimal_places=2, blank=True, null=True) 
    settle_price = models.DecimalField(db_column='Settle Price', max_digits=18, decimal_places=2, blank=True, null=True) 
    categorisation = models.CharField(db_column='Categorisation', max_length=100, blank=True, null=True) 
    part_status = models.CharField(db_column='Part_Status', max_length=50, blank=True, null=True) 
    part_type = models.CharField(db_column='Part_Type', max_length=50, blank=True, null=True) 
    latest_inward = models.DateField(db_column='Latest Inward', blank=True, null=True) 
    rate = models.DecimalField(db_column='Rate', max_digits=18, decimal_places=2, blank=True, null=True) 
    conversion_factor = models.DecimalField(db_column='Conversion Factor', max_digits=18, decimal_places=4, blank=True, null=True) 

    class Meta:
        db_table = 'tbl_bom_partdetails_master'
        managed = False

class ItemCardECN(models.Model):
    """Maps to tbl_itemcard_ecn — source for No_Of_MEFT, No_Of_Parts, Fixture_No, Customer_Name autofill."""
    # ecn_id is used as the primary key. The table is managed=False (legacy);
    # an explicit PK must be declared to avoid Django trying to SELECT an 'id'
    # column that doesn't exist in the legacy schema.
    ecn_id = models.TextField(primary_key=True, db_column='ecn_id')
    ecn_type = models.TextField(db_column='ecn_type', null=True, blank=True)
    customer_id = models.TextField(db_column='customerid', null=True, blank=True)
    customer_name = models.TextField(db_column='customername', null=True, blank=True)
    no = models.TextField(db_column='No', null=True, blank=True)
    no_2 = models.TextField(db_column='no_2', null=True, blank=True)
    description = models.TextField(db_column='description', null=True, blank=True)
    base_unit_of_measure = models.TextField(db_column='base_unit_of_measure', null=True, blank=True)
    fixture_no = models.TextField(db_column='fixture_no', null=True, blank=True)
    # Stored as INTEGER in the DB; IntegerField allows direct arithmetic in
    # views (e.g. annotation, aggregation) without casting from a string.
    # null=True covers legacy rows where the column was left empty.
    no_of_meft  = models.IntegerField(db_column='no_of_meft',  null=True, blank=True, default=0)
    no_of_parts = models.IntegerField(db_column='no_of_parts', null=True, blank=True, default=0)
    revision_no = models.TextField(db_column='revision_no', null=True, blank=True)
    status = models.TextField(db_column='status', null=True, blank=True)

    class Meta:
        db_table = "tbl_itemcard_ecn"
        managed = False

class BOMProdItemPartGrpMasterDetail(models.Model):
    row_id = models.AutoField(primary_key=True, db_column='row_id')
    grp_partno = models.CharField(max_length=100, db_column='grp_partno', blank=True, null=True)
    grp_part_description = models.TextField(db_column='grp_part_description', blank=True, null=True)
    level = models.IntegerField(db_column='level', blank=True, null=True)
    part_no = models.CharField(max_length=100, db_column='part_no', blank=True, null=True)
    part_description = models.TextField(db_column='part_description', blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50, db_column='unit_of_measure', blank=True, null=True)
    bom_quantity = models.DecimalField(max_digits=18, decimal_places=4, db_column='bom_quantity', blank=True, null=True)
    total_bom_quantity = models.DecimalField(max_digits=18, decimal_places=4, db_column='total_bom_quantity', blank=True, null=True)

    class Meta:
        db_table = 'tbl_bom_proditem_partgrpmaster'
        managed = False

class BomProdItemPartGrpMasterRawData(models.Model):
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
