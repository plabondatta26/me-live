from django.db import models
from devices.models import UserDeviceInfo

class ReferBonusAmount(models.Model): 
    diamonds = models.IntegerField(default=30)

    def save(self, *args, **kwargs):
        if ReferBonusAmount.objects.first() is not None:
            return
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Diamonds of Refer Bonus (Don't add multiple rule)"

    def __str__(self):
        return f"Per bonus = {self.diamonds} diamonds"

class ReferHistory(models.Model):
	device_info = models.ForeignKey(UserDeviceInfo,on_delete=models.SET_NULL,null=True)
	refered_uid = models.IntegerField(default=0)
	referer_uid = models.IntegerField(default=0)
	device_name = models.CharField(max_length=200)
	device_id = models.CharField(max_length=200,unique=True)
	diamonds = models.IntegerField(default=0)
	datetime = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name_plural = 'Refer Histories'
		ordering = ['-datetime']

	def __str__(self):
		return f"{self.device_id} device has been refered to #User ID: {self.refered_uid} > Datetime: {str(self.datetime).split('.')[0]}"