from celery import shared_task
from django.utils import timezone
from accounts.models import User

from tracking.models import BroadcasterHistory

@shared_task
def update_broadcasting_history_task(uid,is_video,seconds):
    broadcaster_history_obj = BroadcasterHistory.objects.filter(user__id=uid,broadcasting_date=timezone.now().date()).first()
    if broadcaster_history_obj:
        if is_video == False:
            broadcaster_history_obj.audio_broadcast_in_second += seconds
        else:
            broadcaster_history_obj.video_broadcast_in_second += seconds
        broadcaster_history_obj.save(force_update=True)
    else:
        user_obj = User.objects.filter(id=uid).first()
        if user_obj:
            broadcaster_history_obj = BroadcasterHistory()
            broadcaster_history_obj.user = user_obj
            if is_video == False:
                broadcaster_history_obj.audio_broadcast_in_second = seconds
            else:
                broadcaster_history_obj.video_broadcast_in_second = seconds
            broadcaster_history_obj.save(force_insert=True)  
