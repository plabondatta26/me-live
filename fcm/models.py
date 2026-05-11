from django.db import models
from accounts.models import User

class FCMDeviceToken(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='device_token')
    token = models.CharField(max_length=200)
    peer_user = models.OneToOneField(User,related_name='peer_user',on_delete=models.SET_NULL,blank=True,null=True)

    class Meta:
        verbose_name_plural = 'FCM Device Tokens'

    def __str__(self):
        return f'{self.user.phone} > {self.token}'