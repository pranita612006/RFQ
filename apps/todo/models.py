from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class TblOpportunitymaster(models.Model):
    item_no = models.CharField(max_length=50, blank=True, null=True)
    sales_cycle_code = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'tbl_opportunitymaster'

class TblOppsalescycles(models.Model):
    code = models.CharField(max_length=50, db_column='CODE', blank=True, null=True)
    description = models.CharField(max_length=255, db_column='Description', blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'tbl_oppsalescycles'

class TblCustomerinfo(models.Model):
    customer_id = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    emailid = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'tbl_customerinfo'

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