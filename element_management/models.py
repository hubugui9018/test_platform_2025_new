from django.db import models


# Create your models here.

class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    function = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'product'


class ElementManage(models.Model):
    id = models.BigAutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    model = models.CharField(max_length=255, null=True, blank=True)
    function = models.CharField(max_length=255, null=True, blank=True)
    text = models.CharField(max_length=255, null=True, blank=True)
    content_desc = models.CharField(max_length=255, null=True, blank=True)
    original_x_proportion = models.CharField(max_length=255, null=True, blank=True)
    original_y_proportion = models.CharField(max_length=255, null=True, blank=True)
    operate_type = models.CharField(max_length=255, null=True, blank=True)
    start_x_start_y_end_x_end_y = models.CharField(max_length=255, null=True, blank=True)
    duration = models.CharField(max_length=255, null=True, blank=True)
    enter_text = models.CharField(max_length=255, null=True, blank=True)
    remark = models.CharField(max_length=255, null=True, blank=True)
    assertion = models.CharField(max_length=255, null=True, blank=True)

    # create_time = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'element_manage'


class AppPackage(models.Model):
    id = models.BigAutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    app_package = models.CharField(max_length=255)
    app_activity = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'app_package'


class TestCase(models.Model):
    id = models.BigAutoField(primary_key=True)
    case_name = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    function = models.CharField(max_length=255)
    elements_list = models.JSONField()

    class Meta:
        managed = True
        db_table = 'test_case'


class TestCaseExecution(models.Model):
    id = models.BigAutoField(primary_key=True)
    unique_id = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    test_case_id = models.CharField(max_length=255)
    start_time = models.CharField(max_length=255)
    end_time = models.CharField(max_length=255)
    execution_time = models.CharField(max_length=255)
    result = models.CharField(max_length=255)
    log = models.CharField(max_length=2550)
    screenshot_path = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'test_case_execution'
