
# models_sbc_patch.py
# Adição do modelo SbcPhonecall (alocar/mesclar em models.py)
from django.db import models

class SbcPhonecall(models.Model):
    id = models.BigIntegerField(primary_key=True)
    hostid = models.SmallIntegerField(blank=True, null=True)
    startdate = models.DateField(blank=True, null=True)
    starttime = models.TimeField(blank=True, null=True)
    stopdate = models.DateField(blank=True, null=True)
    stoptime = models.TimeField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    dialednumber = models.CharField(max_length=40, blank=True, null=True)
    connectednumber = models.CharField(max_length=40, blank=True, null=True)
    conditioncode = models.SmallIntegerField(blank=True, null=True)
    callcasedata = models.IntegerField(blank=True, null=True)
    chargednumber = models.CharField(max_length=40, blank=True, null=True)
    seqnumber = models.IntegerField(blank=True, null=True)
    seqlim = models.SmallIntegerField(blank=True, null=True)
    callid = models.CharField(max_length=24, blank=True, null=True)
    callidass1 = models.CharField(max_length=24, blank=True, null=True)
    callidass2 = models.CharField(max_length=24, blank=True, null=True)
    event_type = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "sbc_phonecall"
