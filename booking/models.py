from django.db import models

# Create your models here.
class screen(models.Model):
    screenId = models.AutoField(primary_key=True)
    screenName = models.CharField(max_length=100, null=False) ## ex - 'inox'

class seat(models.Model):
    screenId = models.ForeignKey(screen, on_delete=models.CASCADE) ## foreign key and pointing to screen table
    rowName = models.CharField(max_length=1, null=False) ## row name - ex A,B,C..
    seatNo = models.IntegerField(null=False) ## seat No - ex 0,1,2...
    status = models.SmallIntegerField(default=0) ## status = 1 if reserved else 0
    isAisle = models.SmallIntegerField(default=0) ## isAisle = 1 if it is an Aisle seat

