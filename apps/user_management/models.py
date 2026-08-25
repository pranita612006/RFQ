from django.db import models

class EmpDetails(models.Model):
    emp_username       = models.CharField(max_length=100, primary_key=True, db_column='emp_username')
    emp_name           = models.CharField(max_length=200, db_column='emp_name', null=True, blank=True)
    emp_designation    = models.CharField(max_length=100, db_column='emp_designations', null=True, blank=True)
    emp_password       = models.CharField(max_length=255, db_column='emp_password', default='voss@123')
    password_reset_status = models.CharField(max_length=50, db_column='password_reset_status', null=True, blank=True, default='0')
    is_admin           = models.CharField(max_length=50, db_column='isadmin', default='No')
    user_type          = models.CharField(max_length=100, db_column='user_type', default='Standard User')
    email_id           = models.EmailField(db_column='email_id', null=True, blank=True)

    class Meta:
        db_table = 'tbl_empdetails'
        managed  = False

    def __str__(self):
        return self.emp_username
