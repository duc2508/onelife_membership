from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class MembershipUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=200)
    points = models.IntegerField(default=0)
    total_spend = models.FloatField(default=0)
    membership_level = models.CharField(max_length=20, default="Member")
    registration_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.username

class Voucher(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.FloatField()
    expiry_date = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.value} VND"