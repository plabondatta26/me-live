from django.db import models
from accounts.models import User

class CallHistory(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    is_outgoing_call = models.BooleanField(default=False)
    is_incoming_call = models.BooleanField(default=False)
    is_missed_call = models.BooleanField(default=False)
    call_type = models.CharField(max_length=10)
    peer_user = models.ForeignKey(User,related_name='call_peer_user',on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Call Histories'
        ordering = ['-id']

    def __str__(self):
        return f'{self.user.phone} > {self.datetime}'