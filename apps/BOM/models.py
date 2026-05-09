from django.db import models

class BOMHeader(models.Model):
    id = models.AutoField(primary_key=True)
    customer_id = models.CharField(max_length=100, db_column='Customer_ID', null=True, blank=True)
    item_creation_id = models.CharField(max_length=100, db_column='ItemCreation_Id', null=True, blank=True)
    bom_creation_id = models.CharField(max_length=100, db_column='BOMCreation_Id', null=True, blank=True)
    description = models.CharField(max_length=255, db_column='Description', null=True, blank=True)
    uom_code = models.CharField(max_length=50, db_column='Unit_of_Measure_Code', null=True, blank=True)
    action_status = models.CharField(max_length=50, db_column='Status', null=True, blank=True)
    last_date_modified = models.CharField(max_length=50, db_column='Last_Date_Modified', null=True, blank=True)
    table_id = models.CharField(max_length=100, db_column='Table_Id', null=True, blank=True)
    create_date = models.CharField(max_length=50, db_column='Creation_Date', null=True, blank=True)

    class Meta:
        db_table = "tbl_bomcreation"
        managed = False

    def __str__(self):
        return f"{self.bom_creation_id}"

class BOMTransaction(models.Model):
    id = models.AutoField(primary_key=True, db_column='Id')
    bom_creation_id = models.CharField(max_length=100, db_column='BOMCreation_ID', null=True, blank=True)
    entry_type = models.CharField(max_length=50, db_column='Entry_Type', null=True, blank=True)
    part_number = models.CharField(max_length=100, db_column='Part_Number', null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, db_column='Quantity', null=True, blank=True)
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