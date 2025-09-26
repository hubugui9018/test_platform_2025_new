from django.db import models


# Create your models here.

class Devices(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    device_type = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default='unknown')
    unique_id = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    port_num = models.IntegerField()
    device_width = models.CharField(max_length=255)
    device_high = models.CharField(max_length=255)
    last_connected = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'devices'