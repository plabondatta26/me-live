# import hmac
# import hashlib
# import os
import json

from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from livekit_stuffs.tasks import db_live_room_delete_task, participant_count_update_task
# from me_live.utils import sendDataInGlobalWebsocket
# from ..models import LiveRoom
# from .models import LiveKitEvent, LiveKitRoom

# WEBHOOK_SECRET = os.getenv("LIVEKIT_WEBHOOK_SECRET", "your_webhook_secret")
# WEBHOOK_SECRET = os.getenv("LIVEKIT_WEBHOOK_SECRET", "LIVEKIT_API_SECRET_KEY")



@csrf_exempt
@require_POST
def livekit_webhook(request):
    body_bytes = request.body
    # signature = request.headers.get("Authorization")

    # # ✅ Verify HMAC signature
    # if WEBHOOK_SECRET and signature:
    #     expected_signature = hmac.new(
    #         WEBHOOK_SECRET.encode(),
    #         body_bytes,
    #         hashlib.sha256
    #     ).hexdigest()
    #     if signature != f"Bearer {expected_signature}":
    #         print('Invalid signature')
    #         return HttpResponseForbidden("Invalid signature")

    try:
        data = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        # print('Invalid JSON')
        return HttpResponseForbidden("Invalid JSON")

    event = data.get("event", "")
    room_name = data.get("room", {}).get("name")
    participant_identity = data.get("participant", {}).get("identity")
    # track_sid = data.get("track", {}).get("sid")

    # print(f"📩 LiveKit webhook: {event}")

    # # 🔹 Save event in DB
    # LiveKitEvent.objects.create(
    #     event=event,
    #     room_name=room_name,
    #     participant_identity=participant_identity,
    #     track_sid=track_sid,
    #     payload=data,
    # )

    # 🔹 Update or create room status
    if room_name:
        # room, _ = LiveKitRoom.objects.get_or_create(name=room_name)

        # if event == "room_started":
        #     # print(f"✅ Room started: {room_name}")
        #     # room.is_active = True
        #     # room.participant_count = 0


        # elif event == "room_reconnected":
        #     # print(f"🔄 Room reconnected: {room_name}")
        #     # room.is_active = True

        # if event == "room_deleted":
        #     # print(f"❌ Room deleted: {room_name}")
        #     deleteLiveRoom(room_name=room_name)
        #     # LiveRoom.objects.filter(channel_id=channel_id).delete()
        #     # room.is_active = False
        #     # room.participant_count = 0

        # elif event == "room_finished":
        #     # print(f"❌ Room finished: {room_name}")
        #     deleteLiveRoom(room_name=room_name)
        #     # LiveRoom.objects.filter(channel_id=channel_id).delete()
        #     # room.is_active = False
        #     # room.participant_count = 0

        if event == "participant_joined":
            participant_identity = data["participant"]["identity"]
            # print(f"👤 Participant joined: {participant_identity}")
            participant_count_update(room_name=room_name,participant_identity=participant_identity,status='joined')
            # room.participant_count += 1

        elif event == "participant_left":
            participant_identity = data["participant"]["identity"]
            # print(f"👋 Participant left: {participant_identity}")
            participant_count_update(room_name=room_name,participant_identity=participant_identity,status='left')
            # room.participant_count = max(0, room.participant_count - 1)

        # elif event == "track_published":
        #     track_sid = data["track"]["sid"]
        #     # print(f"🎥 Track published: {track_sid}")

        # elif event == "egress_started":
        #     # print("▶️ Egress started (recording/streaming)")

        # elif event == "egress_ended":
        #     # print("⏹️ Egress ended")

        # room.last_event = event
        # room.save()

    return JsonResponse({"status": "ok"})

# Viewers update
def participant_count_update(room_name,participant_identity,status):
    participant_count_update_task.delay(room_name,participant_identity,status)
    # if str(room_name).startswith(kRoomPrefix):
    #     channel_id = str(room_name).split(kRoomPrefix)[1]
    #     # print(f"channel_id: {channel_id}")

    #     if channel_id != participant_identity:
    #         # print(f'Updating viewers count for indentity: {participant_identity}')

    #         channel_id = int(channel_id)
    #         live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).only('id','viewers_count').first()
    #         if live_room_obj:
    #             if status == 'joined':
    #                 viewers_count = live_room_obj.viewers_count + 1
    #             else:
    #                 # status == 'left'
    #                 viewers_count = live_room_obj.viewers_count - 1

    #             live_room_obj.viewers_count = viewers_count

    #             data = {
    #                 'type': 'update_viewers_count',
    #                 'channel_id': channel_id,
    #                 'viewers_count': viewers_count,
    #             }
    #             sendDataInGlobalWebsocket(data=data)
    #             live_room_obj.save(force_update=True)

def deleteLiveRoom(room_name):
    # No action for now
    return
    # db_live_room_delete_task.delay(room_name)
    # if str(room_name).startswith(kRoomPrefix):
    #     channel_id = str(room_name).split(kRoomPrefix)[1]
    #     # print(f"channel_id: {channel_id}")
    #     LiveRoom.objects.filter(channel_id=int(channel_id)).delete()
