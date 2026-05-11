from celery import shared_task

from .models import LiveRoom
from me_live.utils.utils import sendDataInGlobalWebsocket
from me_live.utils.constants import kRoomPrefix
from .api.room_service_client import RoomServiceClientSingleton

# Viewers update
@shared_task
def participant_count_update_task(room_name,participant_identity,status):
    if str(room_name).startswith(kRoomPrefix):
        channel_id = str(room_name).split(kRoomPrefix)[1]
        # print(f"channel_id: {channel_id}")

        if channel_id != participant_identity:
            # print(f'Updating viewers count for indentity: {participant_identity}')

            channel_id = int(channel_id)
            live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).only('id','viewers_count').first()
            if live_room_obj:
                if status == 'joined':
                    viewers_count = live_room_obj.viewers_count + 1
                else:
                    # status == 'left'
                    viewers_count = live_room_obj.viewers_count - 1
                    if viewers_count < 0:
                        viewers_count = 0

                live_room_obj.viewers_count = viewers_count

                data = {
                    'type': 'update_viewers_count',
                    'channel_id': channel_id,
                    'viewers_count': viewers_count,
                }
                sendDataInGlobalWebsocket(data=data)
                live_room_obj.save(force_update=True)

    return 'participant_count_update_task is processing'

@shared_task
def db_live_room_delete_task(room_name):
    if str(room_name).startswith(kRoomPrefix):
        room_service_client_obj = RoomServiceClientSingleton()

        channel_id = str(room_name).split(kRoomPrefix)[1]
        try:
            participant_obj = room_service_client_obj.get_participant(room=room_name,identity=str(channel_id)).identity
        except:
            try:
                LiveRoom.objects.filter(channel_id=channel_id).delete() 
            except:
                pass

    return 'db_live_room_delete_task is processing'

@shared_task
def db_live_room_list_refine():
    room_service_client_obj = RoomServiceClientSingleton()
    live_room_objs = LiveRoom.objects.only('channel_id',).all()
    # list_rooms = room_service_client_obj.list_rooms()

    # channel_ids = []

    # for room in list_rooms:
    #     channel_ids.append(int(str(room.name).split(kRoomPrefix)[1]))

    for live_room_obj in live_room_objs:
        channel_id = live_room_obj.channel_id

        # if channel_id in channel_ids:
        room_name = f"{kRoomPrefix}{channel_id}"

        # print(f"2 list_participants: {list_participants}........")
        try:
            participant_obj = room_service_client_obj.get_participant(room=room_name,identity=str(channel_id)).identity
            # print('Has indentity.................')
            # print(f"participant exists: {participant_obj}")
        except:
            LiveRoom.objects.filter(channel_id=channel_id).delete()
            # print(f'1) Delete {channel_id}..................................')
        # else:
        #     LiveRoom.objects.filter(channel_id=channel_id).delete()
        #     # print(f'2) Delete {channel_id}..................................')


    return 'db_live_room_list_refine is processing'
