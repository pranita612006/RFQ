from django.db import models


class BlanketSO(models.Model):
    # DB has auto 'id' as PK, bsocreationid is a regular unique field
    id = models.AutoField(primary_key=True, db_column='id')
    bso_creation_id = models.CharField(max_length=50, db_column='bsocreationid', unique=True, blank=True, null=True)
    no = models.CharField(max_length=50, db_column='no', blank=True, null=True)
    document_date = models.DateField(db_column='documentdate', blank=True, null=True)
    sellto_customer_no = models.CharField(max_length=50, db_column='selltocustomerno', blank=True, null=True)
    billto_customer_no = models.CharField(max_length=50, db_column='billtocustomerno', blank=True, null=True)
    sellto_customer_name = models.CharField(max_length=255, db_column='selltocustomername', blank=True, null=True)
    order_date = models.DateField(db_column='orderdate', blank=True, null=True)
    external_document_no = models.CharField(max_length=50, db_column='externaldocumentno', blank=True, null=True)
    location_code = models.CharField(max_length=50, db_column='locationcode', blank=True, null=True)
    status = models.CharField(max_length=50, db_column='status', blank=True, null=True)
    billto_contact = models.CharField(max_length=255, db_column='billtocontact', blank=True, null=True)
    billto_country_region_code = models.CharField(max_length=50, db_column='billtocountryregioncode', blank=True, null=True)
    billto_name = models.CharField(max_length=255, db_column='billtoname', blank=True, null=True)
    billto_post_code = models.CharField(max_length=20, db_column='billtopostcode', blank=True, null=True)
    currency_code = models.CharField(max_length=10, db_column='currencycode', blank=True, null=True)
    plant_code = models.CharField(max_length=50, db_column='plantcode', blank=True, null=True)
    posting_date = models.DateField(db_column='postingdate', blank=True, null=True)
    product_group_code = models.CharField(max_length=50, db_column='productgroupcode', blank=True, null=True)
    salesperson_code = models.CharField(max_length=50, db_column='salespersoncode', blank=True, null=True)
    sellto_contact = models.CharField(max_length=255, db_column='selltocontact', blank=True, null=True)
    sellto_country_region_code = models.CharField(max_length=50, db_column='selltocountryregioncode', blank=True, null=True)
    sellto_post_code = models.CharField(max_length=20, db_column='selltopostcode', blank=True, null=True)
    shipto_code = models.CharField(max_length=50, db_column='shiptocode', blank=True, null=True)
    shipto_contact = models.CharField(max_length=255, db_column='shiptocontact', blank=True, null=True)
    shipto_country_region_code = models.CharField(max_length=50, db_column='shiptocountryregioncode', blank=True, null=True)
    shipto_name = models.CharField(max_length=255, db_column='shiptoname', blank=True, null=True)
    shipto_post_code = models.CharField(max_length=20, db_column='shiptopostcode', blank=True, null=True)
    bso_row_id = models.IntegerField(db_column='bso_rowid', blank=True, null=True)
    item_creation_id = models.CharField(max_length=50, db_column='itemcreation_id', blank=True, null=True)
    customer_id = models.CharField(max_length=50, db_column='customer_id', blank=True, null=True)
    customer_name = models.CharField(max_length=255, db_column='customer_name', blank=True, null=True)
    table_id = models.CharField(max_length=50, db_column='table_id', blank=True, null=True)

    class Meta:
        db_table = 'tbl_blanketso'
        managed = False

    def __str__(self):
        return f"BlanketSO {self.bso_creation_id or self.no or ''}"


class BSOSalesLine(models.Model):
    id_field = models.AutoField(primary_key=True, db_column='id')
    # FK references bsocreationid column (matching the parent table's column name)
    blanket_so = models.ForeignKey(BlanketSO, to_field='bso_creation_id', on_delete=models.CASCADE, db_column='bsocreationid', related_name='sales_lines')
    item_creation_id = models.CharField(max_length=50, db_column='itemcreation_id', blank=True, null=True)
    customer_id = models.CharField(max_length=50, db_column='customer_id', blank=True, null=True)
    customer_name = models.CharField(max_length=255, db_column='customer_name', blank=True, null=True)
    table_id = models.CharField(max_length=50, db_column='table_id', blank=True, null=True)
    document_type = models.CharField(max_length=50, db_column='documenttype', blank=True, null=True)
    document_no = models.CharField(max_length=50, db_column='documentno', blank=True, null=True)
    sellto_customer_no = models.CharField(max_length=50, db_column='selltocustomerno', blank=True, null=True)
    line_type = models.CharField(max_length=50, db_column='type', blank=True, null=True)
    line_no = models.DecimalField(max_digits=10, decimal_places=2, db_column='lineno', blank=True, null=True)
    line_no_field = models.CharField(max_length=50, db_column='no', blank=True, null=True)
    description = models.CharField(max_length=255, db_column='description', blank=True, null=True)
    location_code = models.CharField(max_length=50, db_column='locationcode', blank=True, null=True)
    reserve = models.CharField(max_length=50, db_column='reserve', blank=True, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, db_column='quantity', blank=True, null=True)
    unit_of_measure_code = models.CharField(max_length=20, db_column='unitofmeasurecode', blank=True, null=True)
    unit_price_excl_tax = models.DecimalField(max_digits=12, decimal_places=2, db_column='unitpriceexcltax', blank=True, null=True)
    line_amount_excl_tax = models.DecimalField(max_digits=12, decimal_places=2, db_column='lineamountexcltax', blank=True, null=True)
    line_discount = models.DecimalField(max_digits=5, decimal_places=2, db_column='linediscount', blank=True, null=True)
    shipment_date = models.CharField(max_length=50, db_column='shipmentdate', blank=True, null=True)
    outstanding_quantity = models.DecimalField(max_digits=12, decimal_places=2, db_column='outstandingquantity', blank=True, null=True)
    price_from_date = models.CharField(max_length=50, db_column='pricefromdate', blank=True, null=True)
    price_to_date = models.CharField(max_length=50, db_column='pricetodate', blank=True, null=True)
    remarks = models.TextField(db_column='remarks', blank=True, null=True)
    plant_code = models.CharField(max_length=50, db_column='plantcode', blank=True, null=True)
    rm_base = models.DecimalField(max_digits=12, decimal_places=2, db_column='rmbase', blank=True, null=True)
    boc_base = models.DecimalField(max_digits=12, decimal_places=2, db_column='bocbase', blank=True, null=True)

    class Meta:
        db_table = 'tbl_bso_saleslines'
        managed = False

    def __str__(self):
        return f"Line {self.line_no} for {self.blanket_so}"
