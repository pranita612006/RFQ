from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmpDetails',
            fields=[
                ('emp_username', models.CharField(db_column='Emp_UserName', max_length=100, primary_key=True, serialize=False)),
                ('emp_name', models.CharField(blank=True, db_column='Emp_Name', max_length=200, null=True)),
                ('emp_designation', models.CharField(blank=True, db_column='Emp_Designations', max_length=100, null=True)),
                ('emp_password', models.CharField(db_column='Emp_Password', default='voss@123', max_length=255)),
                ('password_reset_status', models.IntegerField(blank=True, db_column='Password_Reset_Status', default=0, null=True)),
                ('is_admin', models.BooleanField(db_column='IsAdmin', default=False)),
                ('user_type', models.CharField(db_column='User_Type', default='Standard User', max_length=100)),
                ('email_id', models.EmailField(blank=True, db_column='Email_Id', max_length=254, null=True)),
                ('user_status', models.CharField(default='Active', max_length=50)),
                ('last_modified_date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'tbl_empdetails',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='EmpUserAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_type', models.CharField(blank=True, db_column='User_Type', max_length=100, null=True)),
                ('access_to', models.CharField(db_column='AccessTo', max_length=100)),
                ('access_type', models.CharField(db_column='Access_Type', max_length=50)),
                ('last_modified_date', models.DateTimeField(auto_now=True, db_column='LastModifiedDate')),
                ('emp', models.ForeignKey(db_column='Emp_UserName', on_delete=django.db.models.deletion.CASCADE, to='user_management.empdetails')),
            ],
            options={
                'db_table': 'tbl_empdetails_useraccess',
                'managed': False,
            },
        ),
    ]
