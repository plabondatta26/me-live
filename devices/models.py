import json
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from websocket import create_connection 
from accounts.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from livekit_stuffs.api.room_service_client import RoomServiceClientSingleton
from me_live.utils.constants import liveRoomSocketBaseUrl,kRoomPrefix

class UserDeviceInfo(models.Model):
    blocked_moderator = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True,null=True)
    user_id = models.IntegerField(default=0)
    device_name = models.CharField(max_length=200)
    device_id = models.CharField(max_length=200,unique=True)
    blocked = models.BooleanField(default=False)
    entry_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,null=True)

    class Meta:
        verbose_name_plural = 'User Devices Information'
        ordering = ['-entry_datetime']

    def save(self, *args, **kwargs):
        if self.blocked:
            user_device_blocked_obj = UserDeviceBlocked.objects.filter(device_id=self.device_id).first()
            if user_device_blocked_obj is None:
                user_device_blocked_obj = UserDeviceBlocked() 
                user_device_blocked_obj.device_info = self
                user_device_blocked_obj.user_id = self.user_id
                user_device_blocked_obj.device_name = self.device_name
                user_device_blocked_obj.device_id = self.device_id
                user_device_blocked_obj.save()

                data = {
                    'type': 'device_block',
                    'device_blocked': True,
                    'device_id': self.device_id,
                    'user_id': self.user_id,
                }

                channel_layer = get_channel_layer() 
                
                async_to_sync(channel_layer.group_send)(
                    f'live_streaming_livekit_streamings', 
                    {
                        'type': 'live_streaming', 
                        'message': data
                    }
                )
                # async_to_sync(channel_layer.group_send)(
                #     f'live_room_{self.user_id}',
                #     {
                #         'type': 'live_room',  
                #         'message': {
                #             'action': 'close_everything',
                #         }
                #     } 
                # )
                # External websocket
                ws = create_connection(f"{liveRoomSocketBaseUrl}/{self.user_id}/")
                ws.send(json.dumps({"message": {'action': 'close_everything'}}))
                ws.close()

                # Delete Live
                room_name = f"{kRoomPrefix}{self.user_id}"
                room_service_client_obj = RoomServiceClientSingleton()

                try:
                    room_service_client_obj.delete_room(room=room_name)                    
                except:
                    pass
              
            
        elif self.blocked is False:
            user_device_blocked_obj = UserDeviceBlocked.objects.filter(device_id=self.device_id).first()
            if user_device_blocked_obj:
                user_device_blocked_obj.delete()
        super().save(*args, **kwargs)

    def __str__(self):
        blocked_message = ''
        if self.blocked:
            blocked_message = ' (Device Blocked)'
        return f"User ID: {self.user_id} > Device Name: {self.device_name} > Entry Datetime: {str(self.entry_datetime).split('.')[0]}{blocked_message}" 

class UserDeviceBlocked(models.Model):
    device_info = models.ForeignKey(UserDeviceInfo,on_delete=models.SET_NULL,null=True)
    user_id = models.IntegerField(default=0)
    device_name = models.CharField(max_length=200)
    device_id = models.CharField(max_length=200,unique=True)
    blocked_datetime = models.DateTimeField(auto_now_add=True,)

    class Meta:
        verbose_name_plural = 'User Devices Blocked List'
        ordering = ['-blocked_datetime']

    def __str__(self):
        return f"User ID: {self.user_id} > Device Name: {self.device_name} > Blocked Datetime: {str(self.blocked_datetime).split('.')[0]}"

@receiver(post_delete,sender=UserDeviceBlocked)
def user_device_blocked_submission_delete(sender,instance,**kwargs):
    if instance.device_info:
        instance.device_info.blocked = False
        instance.device_info.save()

