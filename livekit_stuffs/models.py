import json
from math import floor
from django.utils import timezone
from datetime import datetime
from django.core.cache import cache
from rest_framework import serializers
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from websocket import create_connection 
from accounts.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from me_live.utils.constants import liveRoomSocketBaseUrl,kRoomPrefix
from tracking.tasks import update_broadcasting_history_task

class LiveRoom(models.Model):
    channel_id = models.IntegerField(default=0,db_index=True)
    title = models.CharField(max_length=100)
    is_pk = models.BooleanField(default=False)
    is_video = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    allow_send = models.BooleanField(default=True)
    cm_flt_nm = models.CharField(max_length=50,default="Hudson")
    group_caller_ids = models.TextField(default=json.dumps([]),)   
    reacts = models.BigIntegerField(default=0)
    viewers_count = models.IntegerField(default=0)

    locked_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,null=True,blank=True)
    created_datetime = models.DateTimeField(auto_now_add=True)

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     # Perform after save method called
    #     channel_id = self.channel_id
    #     live_room_data = cache.get(f"live_room_{channel_id}")
    #     if live_room_data is not None:
    #         live_room_data['viewers_count'] = self.viewers_count
    #         cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)

    def get_group_caller_ids(self):
         group_caller_ids = json.loads(self.group_caller_ids)
         if len(group_caller_ids) == 0:
              group_caller_ids.append({'uid':self.channel_id,'position':1,})
         return group_caller_ids

    def save_group_caller_id(self,uid,position):
        group_caller_ids = json.loads(self.group_caller_ids)
        uids = []
        positions = []
        for caller in group_caller_ids:
            uids.append(caller['uid'])
            positions.append(caller['position'])
        if position in positions:
            for p in [2,3,4,5,6,7,8]:
                if p not in positions:
                    position = p
                    break
        if uid not in uids:
            group_caller_ids.append({'uid':uid,'position':position,})
            self.group_caller_ids = json.dumps(group_caller_ids)
            self.save(force_update=True)

        live_room_data = cache.get(f"live_room_{self.channel_id}")
        if live_room_data is not None:
            live_room_data['group_caller_ids'] = group_caller_ids
            cache.set(f"live_room_{self.channel_id}",live_room_data,timeout=60*60*24)

    def remove_from_group_caller_id(self,uid):
        group_caller_ids = json.loads(self.group_caller_ids)
        for caller in group_caller_ids:
            if uid == caller['uid']:
                group_caller_ids.remove(caller)
                self.group_caller_ids = json.dumps(group_caller_ids)
                self.save(force_update=True)       
                break     

        live_room_data = cache.get(f"live_room_{self.channel_id}")
        if live_room_data is not None:
            live_room_data['group_caller_ids'] = group_caller_ids
            cache.set(f"live_room_{self.channel_id}",live_room_data,timeout=60*60*24)
  
    def __str__(self):
	    return f"Channel ID: {self.channel_id}"

class LiveGroupRoomConfig(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Audio Lock 
    is_audio_lock = models.BooleanField(default=True)
    is_audio_gp_room2_lock = models.BooleanField(default=True)
    is_audio_gp_room3_lock = models.BooleanField(default=True)
    is_audio_gp_room4_lock = models.BooleanField(default=True)
    is_audio_gp_room5_lock = models.BooleanField(default=True)
    is_audio_gp_room6_lock = models.BooleanField(default=True)
    is_audio_gp_room7_lock = models.BooleanField(default=True)
    is_audio_gp_room8_lock = models.BooleanField(default=True)
    is_audio_gp_room9_lock = models.BooleanField(default=True)
    # Audio Paid
    is_audio_gp_call_paid = models.BooleanField(default=False)
    audio_gp_call_cost_in_minute = models.IntegerField(default=100)
    # Video group call request system
    is_video_request = models.BooleanField(default=True)
     # Video Lock 
    is_video_lock = models.BooleanField(default=False)
    is_video_gp_room2_lock = models.BooleanField(default=True)
    is_video_gp_room3_lock = models.BooleanField(default=True)
    is_video_gp_room4_lock = models.BooleanField(default=True)
    is_video_gp_room5_lock = models.BooleanField(default=True)
    is_video_gp_room6_lock = models.BooleanField(default=True)
    is_video_gp_room7_lock = models.BooleanField(default=True)
    is_video_gp_room8_lock = models.BooleanField(default=True)
    is_video_gp_room9_lock = models.BooleanField(default=True)

    # Video Paid
    is_video_gp_call_paid = models.BooleanField(default=False)
    video_gp_call_cost_in_minute = models.IntegerField(default=100)

    class Meta:
        verbose_name_plural = 'Live Group Room Configuration'

    def save(self, *args, **kwargs):  
        group_room_config = LiveGroupRoomConfigSerializer(instance=self).data
        data = {
            'action': 'live_group_room_config',
            'config': group_room_config,
        }

        # channel_layer = get_channel_layer() 
        # async_to_sync(channel_layer.group_send)(
        #     f'live_room_{self.user_id}',
        #     {
        #         'type': 'live_room',  
        #         'message': data,
        #     }
        # )    
        # External websocket
        ws = create_connection(f"{liveRoomSocketBaseUrl}/{self.user_id}/")
        ws.send(json.dumps({"message": data}))
        ws.close()

        room_name = f"{kRoomPrefix}{self.user_id}"
        cache.set(key=f"group_room_config_{room_name}",value=group_room_config,timeout=60*60*21,)

        super().save(*args, **kwargs)

        

    def get_group_room_config(self):
        return LiveGroupRoomConfigSerializer(instance=self).data

    def __str__(self):
        return f"Live Room User ID: {self.user_id}" 
    
class LiveGroupRoomConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveGroupRoomConfig
        fields = '__all__'

@receiver(post_delete,sender=LiveRoom)
def live_room_submission_delete(sender,instance,**kwargs):
    channel_id = instance.channel_id
    cache.delete(f"live_room_{channel_id}")

    data = {"type":"delete_live","channel_id":channel_id,}
    # Sending to websocket
    channel_layer = get_channel_layer()
    # Send message to room group
    async_to_sync(channel_layer.group_send)(
        f'live_streaming_livekit_streamings',
        {
            'type': 'live_streaming', 
            'message': data
        }
    )

    # room_name = f"{kRoomPrefix}{channel_id}"
    # room_service_client_obj = RoomServiceClientSingleton()

    # try:
    #     room_service_client_obj.delete_room(room=room_name)
    # except:
    #     pass

    timestamp = datetime.timestamp(instance.created_datetime)
    duration = int(timezone.now().timestamp()) - timestamp
    update_broadcasting_history_task.delay(uid=channel_id,is_video=instance.is_video,seconds=floor(duration))

# def update_broadcasting_history(uid,is_video,seconds):
#         broadcaster_history_obj = BroadcasterHistory.objects.filter(user__id=uid,broadcasting_date=timezone.now().date()).first()
#         if broadcaster_history_obj:
#             if is_video == False:
#                 broadcaster_history_obj.audio_broadcast_in_second += seconds
#             else:
#                 broadcaster_history_obj.video_broadcast_in_second += seconds
#             broadcaster_history_obj.save(force_update=True)
#         else:
#             user_obj = User.objects.filter(id=uid).first()
#             if user_obj:
#                 broadcaster_history_obj = BroadcasterHistory()
#                 broadcaster_history_obj.user = user_obj
#                 if is_video == False:
#                     broadcaster_history_obj.audio_broadcast_in_second = seconds
#                 else:
#                     broadcaster_history_obj.video_broadcast_in_second = seconds
#                 broadcaster_history_obj.save(force_insert=True)  
