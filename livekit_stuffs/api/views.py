import json
from decouple import config
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.generics import (
    CreateAPIView,ListAPIView, UpdateAPIView
    )
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.status import (
    HTTP_200_OK,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from websocket import create_connection
from accounts.models import User
from balance.models import Contribution
from livekit_stuffs.api.serializers import LiveRoomSerializer
from profiles.models import Profile
from profiles.api.serializers import ProfileSerializer
from ..models import LiveGroupRoomConfig, LiveRoom
from .room_service_client import RoomServiceClientSingleton

from livekit import (
    AccessToken,
    VideoGrant,
)
from tracking.models import BroadcasterHistory
from me_live.utils.utils import sendDataInGlobalWebsocket
from me_live.utils.constants import liveRoomSocketBaseUrl,kRoomPrefix

LIVEKIT_HOST= config("LIVEKIT_HOST") 
LIVEKIT_API_KEY = config("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET_KEY = config("LIVEKIT_API_SECRET_KEY")

# LIVEKIT_HOST_2= config("LIVEKIT_HOST_2") 
# LIVEKIT_API_KEY_2 = config("LIVEKIT_API_KEY_2")
# LIVEKIT_API_SECRET_KEY_2 = config("LIVEKIT_API_SECRET_KEY_2")

# livekit-server --dev --bind 0.0.0.0 --config /home/than/Documents/livekit_config.yaml
# /usr/local/bin
# celery -A tip_live worker --beat --scheduler django --loglevel=info


def update_broadcasting_history(uid,is_video,seconds):
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
    
class LiveKitTokenCreateApiView(CreateAPIView):
    authentication_classes = []
    permission_classes = [HasAPIKey]

    def create(self,request, *args, **kwargs):
        data_obj = request.data
        channel_name = data_obj.get('channel_name','0')
        room_name = f"{kRoomPrefix}{channel_name}"
        identity = data_obj.get('identity','0')
        name = data_obj.get('full_name','Dummy')
        level = data_obj.get('level',0)
        is_owner = data_obj.get('is_owner',False)
        is_host = data_obj.get('is_host',False)

        token = None
        allow_broadcast = True
        message = None
        # group_room_config = None

        group_room_config = cache.get(key=f"group_room_config_{room_name}",)

        if is_owner == True:
            # Create Room
            room_service_client_obj = RoomServiceClientSingleton()
            rooms = room_service_client_obj.list_rooms()
            # If rooms is a list of dicts or objects with a "name" field
            room_exists = any(
                room.name == room_name for room in rooms
            )  # if dicts

            # Or if they're objects: room.name == room_name_to_check
            # room_exists = any(room.name == room_name_to_check for room in rooms)

            if room_exists == False:
                # print(f"Room '{room_name}' does not exist.")
                room_service_client_obj.create_room(room_name)
            # else:
            #     print(f"Room '{room_name}' is exist.")

            # if level < 2 and is_host == False:
            #     allow_broadcast = False
            #     message = "Your Level must be at least 2"
            #     data = {
            #         "token":token,
            #         "allow_broadcast": allow_broadcast,
            #         "message": message,
            #         }
                
            #     return Response(data,status=HTTP_200_OK)

        if group_room_config is None:

            group_room_config_obj = LiveGroupRoomConfig.objects.filter(user__id=int(channel_name)).first()
            if group_room_config_obj is None:
                user_obj = User.objects.filter(id=int(channel_name)).first()
                group_room_config_obj = LiveGroupRoomConfig.objects.create(user=user_obj)
                
            group_room_config = group_room_config_obj.get_group_room_config()
            cache.set(key=f"group_room_config_{room_name}",value=group_room_config,timeout=60*60*21,)

        # token = cache.get(key=f"livekit_token_{room_name}_{identity}",)
        token = None
        if token is None:
            grant = VideoGrant(room_join=True, room=room_name)
            access_token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET_KEY, grant=grant, identity=identity, name=name,ttl=timedelta(hours=24))
            token = access_token.to_jwt()
            # cache.set(key=f"livekit_token_{room_name}_{identity}",value=token,timeout=60*60*21,)
    
        server_url = 'wss://livekit-me-live.mmpvtltd.xyz'
        # server_url = 'wss://livekit-global.mmpvtltd.xyz'


        # telephone = 12000;
        # speech = 24000;
        # music = 48000;
        # musicStereo = 64000;
        # musicHighQuality = 96000;
        # musicHighQualityStereo = 128000;

        preferredCodec = 'VP9'
        audioBitrate = 48000
        hostResolution = 'LSD'
        participantResolution = 'LSD'

        # maxBitrate = 1500 * 1000 # ~1.5 Mbps
        # maxFramerate = 30



        # preferredCodec = 'H264'
        # # maxBitrate = 4 * 1000 * 1000 #~4 Mbps
        # maxBitrate = 4500 * 1000 # ~4.5 Mbps, stable for 1080x2460
        # maxFramerate = 30 
        
        data = {
            "token":token,
            "allow_broadcast": allow_broadcast,
            "message": message,
            "group_room_config": group_room_config,
            "codec": preferredCodec,
            "audio_bitrate": audioBitrate,
            "host_resolution": hostResolution,
            "participant_resolution": participantResolution,
            "websocket_base_url": liveRoomSocketBaseUrl,
            "server_url": server_url,
            }
        
        return Response(data,status=HTTP_200_OK)
    
# class LiveKitTokenV2CreateApiView(CreateAPIView):
#     authentication_classes = []
#     permission_classes = []

#     def create(self,request, *args, **kwargs):
#         data_obj = request.data
#         channel_name = data_obj.get('channel_name','0')
#         room_name = f"{kRoomPrefix}{channel_name}"
#         identity = data_obj.get('identity','0')
#         name = data_obj.get('full_name','Dummy')
#         level = data_obj.get('level',0)
#         is_owner = data_obj.get('is_owner',False)
#         is_host = data_obj.get('is_host',False)

#         token = None
#         allow_broadcast = True
#         message = None
#         # group_room_config = None

#         group_room_config = cache.get(key=f"group_room_config_{room_name}",)

#         if is_owner == True:
#             # Create Room
#             room_service_client_obj = RoomServiceClientSingleton2()
#             room_service_client_obj.create_room(room_name)
#             # if level < 2 and is_host == False:
#             #     allow_broadcast = False
#             #     message = "Your Level must be at least 2"
#             #     data = {
#             #         "token":token,
#             #         "allow_broadcast": allow_broadcast,
#             #         "message": message,
#             #         }
                
#             #     return Response(data,status=HTTP_200_OK)

#         if group_room_config is None:

#             group_room_config_obj = LiveGroupRoomConfig.objects.filter(user__id=int(channel_name)).first()
#             if group_room_config_obj is None:
#                 user_obj = User.objects.filter(id=int(channel_name)).first()
#                 group_room_config_obj = LiveGroupRoomConfig.objects.create(user=user_obj)
                
#             group_room_config = group_room_config_obj.get_group_room_config()
#             cache.set(key=f"group_room_config_{room_name}",value=group_room_config,timeout=60*60*21,)

#         # token = cache.get(key=f"livekit_token_{room_name}_{identity}",)
#         token = None
#         if token is None:
#             grant = VideoGrant(room_join=True, room=room_name)
#             access_token = AccessToken(LIVEKIT_API_KEY_2, LIVEKIT_API_SECRET_KEY_2, grant=grant, identity=identity, name=name,ttl=timedelta(hours=24))
#             token = access_token.to_jwt()
#             # cache.set(key=f"livekit_token_{room_name}_{identity}",value=token,timeout=60*60*21,)
    
#         server_url = 'wss://livekit-me-live.mmpvtltd.xyz'

#         data = {
#             "token":token,
#             "allow_broadcast": allow_broadcast,
#             "message": message,
#             "group_room_config": group_room_config,
#             # "codec": "VP9",
#             "codec": "AV1",
#             "max_bitrate": 3000 * 1000,
#             "max_framerate": 30,
#             "websocket_base_url": liveRoomSocketBaseUrl,
#             "server_url": server_url,
#             }
        
#         return Response(data,status=HTTP_200_OK)

class LiveRoomTestingListApiView(ListAPIView):
    authentication_classes = []
    permission_classes = []

    def list(self,request, *args, **kwargs):

        room_service_client_obj = RoomServiceClientSingleton()
        live_room_objs = LiveRoom.objects.only('channel_id','title').all()
        # list_rooms = room_service_client_obj.list_rooms()

        # channel_ids = []

        # for room in list_rooms:
        #     channel_ids.append(int(str(room.name).split(kRoomPrefix)[1]))

        list_rooms = []

        i = 0
        for live_room_obj in live_room_objs:
            i += 1
            channel_id = live_room_obj.channel_id

            # if channel_id in channel_ids:
            room_name = f"{kRoomPrefix}{channel_id}"

            # print(f"2 list_participants: {list_participants}........")
            try:
                participant_obj = room_service_client_obj.get_participant(room=room_name,identity=str(channel_id)).identity
                # print('Has indentity.................')
                # print(f"participant exists: {participant_obj}")
                data = {
                    'serial': i,
                    'status': 'Has indentity',
                    'title': live_room_obj.title,
                    'channel_id': channel_id
                }
                list_rooms.append(data)

            except:
                # LiveRoom.objects.filter(channel_id=channel_id).delete()
                data = {
                    'serial': i,
                    'status': 'Need to delete',
                    'title': live_room_obj.title,
                    'channel_id': channel_id
                }
                list_rooms.append(data)
                # print(f'1) Delete {channel_id}..................................')
            # else:
            #     LiveRoom.objects.filter(channel_id=channel_id).delete()
            #     # print(f'2) Delete {channel_id}..................................')


        data = {'list_rooms':list_rooms}
        return Response(data=data,status=HTTP_200_OK)

class LiveGroupRoomConfigUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def update(self,request, *args, **kwargs):
        user_obj = request.user
        data_obj = request.data
        action = data_obj.get('action',None)

        group_room_config_obj = LiveGroupRoomConfig.objects.filter(user=user_obj).first()
        if group_room_config_obj is None:
            group_room_config_obj = LiveGroupRoomConfig.objects.create(user=user_obj)

        if action == "enable_audio_lock":
            group_room_config_obj.is_audio_lock = True
            group_room_config_obj.is_audio_gp_room2_lock = data_obj.get('is_audio_gp_room2_lock',False)
            group_room_config_obj.is_audio_gp_room3_lock = data_obj.get('is_audio_gp_room3_lock',False)
            group_room_config_obj.is_audio_gp_room4_lock = data_obj.get('is_audio_gp_room4_lock',False)
            group_room_config_obj.is_audio_gp_room5_lock = data_obj.get('is_audio_gp_room5_lock',False)
            group_room_config_obj.is_audio_gp_room6_lock = data_obj.get('is_audio_gp_room6_lock',False)
            group_room_config_obj.is_audio_gp_room7_lock = data_obj.get('is_audio_gp_room7_lock',False)
            group_room_config_obj.is_audio_gp_room8_lock = data_obj.get('is_audio_gp_room8_lock',False)
            group_room_config_obj.is_audio_gp_room9_lock = data_obj.get('is_audio_gp_room9_lock',False)
            # Audio Paid
            group_room_config_obj.is_audio_gp_call_paid = False

        elif action == "enable_audio_paid":
            group_room_config_obj.is_audio_lock = False
            # Audio Paid
            group_room_config_obj.is_audio_gp_call_paid = True
            group_room_config_obj.audio_gp_call_cost_in_minute = data_obj.get('audio_gp_call_cost_in_minute',100)

        elif action == "enable_video_lock":
            group_room_config_obj.is_video_lock = True
            group_room_config_obj.is_video_gp_room2_lock = data_obj.get('is_video_gp_room2_lock',False)
            group_room_config_obj.is_video_gp_room3_lock = data_obj.get('is_video_gp_room3_lock',False)
            group_room_config_obj.is_video_gp_room4_lock = data_obj.get('is_video_gp_room4_lock',False)
            group_room_config_obj.is_video_gp_room5_lock = data_obj.get('is_video_gp_room5_lock',False)
            group_room_config_obj.is_video_gp_room6_lock = data_obj.get('is_video_gp_room6_lock',False)
            group_room_config_obj.is_video_gp_room7_lock = data_obj.get('is_video_gp_room7_lock',False)
            group_room_config_obj.is_video_gp_room8_lock = data_obj.get('is_video_gp_room8_lock',False)
            group_room_config_obj.is_video_gp_room9_lock = data_obj.get('is_video_gp_room9_lock',False)

            # Video Paid
            group_room_config_obj.is_video_gp_call_paid = False
            group_room_config_obj.is_video_request = False  

        elif action == "enable_video_paid":
            group_room_config_obj.is_video_lock = False
            group_room_config_obj.is_video_request = False  
            # Video Paid
            group_room_config_obj.is_video_gp_call_paid = True
            group_room_config_obj.video_gp_call_cost_in_minute = data_obj.get('video_gp_call_cost_in_minute',100)  

        elif action == "enable_video_request":
            group_room_config_obj.is_video_request = True  
            group_room_config_obj.is_video_lock = False
            # Video Paid
            group_room_config_obj.is_video_gp_call_paid = False

        group_room_config_obj.save(force_update=True)  
        
        return Response(status=HTTP_200_OK)
    
# class DeleteRoomDestroyApiView(DestroyAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated & HasAPIKey]
#     lookup_field = 'channel_name'

#     def destroy(self,request, *args, **kwargs):
#         channel_name = self.kwargs[self.lookup_field]
#         data_obj = request.data
#         user_obj = request.user
#         uid = int(channel_name)
#         room_name = f"{kRoomPrefix}{channel_name}"
#         creation_time = data_obj.get('creation_time',str(timezone.now()))
#         is_video = data_obj.get('is_video',False)

#         if user_obj.id == uid:
#             # Firebase
#             # remove_live_room_from_firebase(uid=uid)
#             # room_service_client_obj = RoomServiceClient(LIVEKIT_HOST,LIVE_KIT_API_KEY,LIVE_KIT_API_SECRET_KEY)
#             room_service_client_obj = RoomServiceClientSingleton()
#             try:
#                 room_service_client_obj.delete_room(room=room_name)

#                 # liveData = {
#                 #     "type": "streaming",
#                 #     "channelName": uid,
#                 #     "online": False,
#                 # }
#                 # channel_layer = get_channel_layer()
#                 # async_to_sync(channel_layer.group_send)(
#                 #     f'live_streaming_livekit_streamings',
#                 #     {'type': 'live_streaming', 'message': liveData}
#                 # )
#                 # channel_id = uid
#                 # live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
#                 # if live_room_obj:
#                 #     live_room_obj.delete()

#                 # mongoDB
#                 melive_mongo_db = MeLiveMongoDB()
#                 collection_live_room = melive_mongo_db["LiveRoom"]

#                 collection_live_room.delete_one({"channelName": f"{channel_name}",})
#                 live_data = {
#                     "type": "delete_live_room",
#                     "channelName": f"{channel_name}",
#                 } 

#                 send_to_global_websocket(data=live_data)

#                 duration = int(timezone.now().timestamp()) - datetime.fromisoformat(creation_time).timestamp()

#                 update_broadcasting_history(uid=uid,is_video=is_video,seconds=floor(duration))

#                 # # Firebase
#                 # try:
#                 #     # firestore_db.collection("LiveRoom").document(f"{channel_name}").delete()
#                 #     firebase_client = FirebaseClient()
#                 #     db_ref = firebase_client.firestore_db.collection("LiveRoom").document(f"{channel_name}")
#                 #     doc = db_ref.get()
                
#                 #     if doc.exists:
#                 #         db_ref.delete()
#                 #         firestore_json_data = doc.to_dict()
#                 #         creation_time = firestore_json_data['creation_time']
#                 #         timestamp = datetime.timestamp(creation_time)
#                 #         duration = int(timezone.now().timestamp()) - timestamp
#                 #         user_id = firestore_json_data['channelName']
#                 #         is_video = firestore_json_data['is_video']
#                 #         update_broadcasting_history(uid=user_id,is_video=is_video,seconds=floor(duration))
#                 # except:
#                 #     pass
#             except:
#                 pass

#         return Response(status=HTTP_204_NO_CONTENT)

class ParticipantListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]
    lookup_field = 'channel_name'

    def list(self,request, *args, **kwargs):
        channel_name = self.kwargs[self.lookup_field]
        room_name = f"{kRoomPrefix}{channel_name}"
        channel_id = int(channel_name)
        user_obj = request.user
        my_uid = user_obj.id

        # room_service_client_obj = RoomServiceClient(LIVEKIT_HOST,LIVE_KIT_API_KEY,LIVE_KIT_API_SECRET_KEY)
        room_service_client_obj = RoomServiceClientSingleton()
        participant_list = []
        my_contribution_diamonds = 0
        try:
            list_participants_objs = room_service_client_obj.list_participants(room=room_name)
            if list_participants_objs:
                for participant_obj in list_participants_objs:
                    # Restrict host to show self in viewer list
                    if participant_obj.identity != channel_name:
                        uid = int(participant_obj.identity)
                        profile_cache = cache.get(f'profile_{uid}')
                        if profile_cache is None:
                        
                            profile_obj = Profile.objects.filter(user__id=uid).first()
                            if profile_obj:
                                profile_cache = ProfileSerializer(instance=profile_obj,).data
                                cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*2)

                        if profile_cache["is_moderator"] == False:
                            contribution_diamonds = 0
                            contribution_obj = Contribution.objects.filter(contributor__id=uid).filter(user__id=channel_id).only('diamonds').first()
                            if contribution_obj:
                                contribution_diamonds = contribution_obj.diamonds

                            try:
                                profile_cache['vvip_or_vip_preference'] = json.loads(profile_cache['vvip_or_vip_preference'])
                            except:
                                pass
                                
                            userData = {
                                "uid": uid,
                                "full_name": profile_cache["full_name"],
                                "profile_image": profile_cache["profile_image"],
                                "contribution_diamonds": contribution_diamonds,
                                "contribution_rank": 0,
                                "is_agent": profile_cache["is_agent"],
                                "is_host": profile_cache["is_host"],
                                "is_reseller": profile_cache["is_reseller"],
                                "level": profile_cache["level"],
                                "vvip_or_vip_preference":
                                    profile_cache["vvip_or_vip_preference"],
                            }
                            if uid == my_uid:
                                my_contribution_diamonds = contribution_diamonds
                            participant_list.append(userData)
                      
        except:
            pass
            
        data = {"participant_list":participant_list,"my_contribution_diamonds":my_contribution_diamonds,}

        return Response(data=data,status=HTTP_200_OK)

# class GroupCallerListApiView(ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated & HasAPIKey]
#     lookup_field = 'channel_name'

#     def list(self,request, *args, **kwargs):
#         channel_name = self.kwargs[self.lookup_field]
#         method_dict = request.GET
#         call_type = method_dict.get("call_type","audio")

#         group_callers = get_group_callers_v2_data(channel_name=channel_name,call_type=call_type,my_uid=request.user.id)

#         return Response({"group_callers":group_callers,},status=HTTP_200_OK)

# def get_group_callers_v2_data(channel_name,call_type,my_uid):
#     group_callers = []

#     # room_service_client_obj = RoomServiceClientSingleton()
#     # room_name = f"{kRoomPrefix}{channel_name}"
#     # list_participants = room_service_client_obj.list_participants(room=room_name)

#     # participant_ids = []
#     # for participant in list_participants:
#     #     if(len(participant.tracks)):
#     #         # print(f"{participant.name}- {participant.identity}")
#     #         participant_ids.append(participant.identity)

#     # # Firebase
#     # firebase_client = FirebaseClient()
#     # db_ref = firebase_client.firestore_db.collection("LiveRoom").document(f"{channel_name}")
#     # doc = db_ref.get()

#     melive_mongo_db = MeLiveMongoDB()
#     collection_live_room = melive_mongo_db["LiveRoom"]

#     filtered_rooms = collection_live_room.find({"channelName": f"{channel_name}",}).limit(1)

#     try:
#         temp = filtered_rooms[0]
#         # print('Exists')
   
#     # if doc.exists:
#         # firestore_json_data = doc.to_dict()
#         json_data = json.dumps(temp, sort_keys=True, indent=4, default=json_util.default)

#         json_data = json.loads(json_data)

#         # caller_ids = firestore_json_data["group_caller_ids"]
#         # caller_positions = firestore_json_data["caller_positions"]
#         caller_ids = json_data["group_caller_ids"]
#         caller_positions = json_data["caller_positions"]

#         # if len(caller_ids) < len(participant_ids):
#         #     caller_ids = participant_ids

#         i = 0
#         for caller_id in caller_ids:
#             uid = int(caller_id)
#             profile_cache = cache.get(f'profile_{uid}')
#             if profile_cache is None:
#                 host_profile_obj = Profile.objects.filter(user__id=uid).first()
#                 if host_profile_obj:
#                     profile_cache = ProfileSerializer(instance=host_profile_obj).data
#                     cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*2)

#             try:
#                 profile_cache['vvip_or_vip_preference'] = json.loads(profile_cache['vvip_or_vip_preference'])
#             except:
#                 pass

#             try:
#                 index = profile_cache['followers'].index(my_uid)
#                 # Found
#                 profile_cache['followers'] = [my_uid]
#                 # print('Found')
#             except ValueError:
#                 # Not found
#                 profile_cache['followers'] = []
#                 # print('Not Found')

#             caller_data = {
#                 "uid": uid,
#                 "full_name": profile_cache["full_name"],
#                 "profile_image": profile_cache["profile_image"],
#                 "diamonds": profile_cache["diamonds"],
#                 "vvip_or_vip_preference":
#                     profile_cache["vvip_or_vip_preference"],
#                 "followers": profile_cache["followers"],
#                 # "is_agent": profile_cache["is_agent"],
#                 # "is_host": profile_cache["is_host"],
#                 # "is_reseller": profile_cache["is_reseller"],
#                 "call_type": call_type,
#                 "muted": False,
#                 "video_disabled": False,
#                 "position": caller_positions[i]
#             }

#             group_callers.append(caller_data)
#             i += 1
#             ############
#             # host_profile_obj = Profile.objects.filter(user__id=uid).first()
#             # if host_profile_obj:
#             #     profile_data = ProfileForUserInfoSerializer(instance=host_profile_obj).data
#             #     caller_data = {
#             #         "uid": uid,
#             #         "full_name": profile_data["full_name"],
#             #         "profile_image": profile_data["profile_image"],
#             #         "diamonds": profile_data["diamonds"],
#             #         "gift_coins": profile_data["gift_coins"],
#             #         "vvip_or_vip_preference":
#             #             profile_data["vvip_or_vip_preference"],
#             #         "followers": profile_data["followers"],
#             #         # "is_agent": profile_data["is_agent"],
#             #         # "is_host": profile_data["is_host"],
#             #         # "is_reseller": profile_data["is_reseller"],
#             #         "call_type": call_type,
#             #         "muted": False,
#             #         "video_disabled": False,
#             #     }

#             #     group_callers.append(caller_data)
#     except:
#         # Not Exists
#         pass

#     return group_callers

# @csrf_exempt
# @require_POST
# def livekit_webhook(request):
#     event_str = request.body.decode("utf-8")
#     event_json = json.loads(event_str)

#     # if event_json["event"] == "room_started":
#     #     room_name = event_json["room"]["name"]
#     #     if str(room_name).startswith(kRoomPrefix):
#     #         # live_room_started.delay(room_name)
#     #         live_room_started(room_name=room_name)

#     # elif event_json["event"] == "participant_joined":

#     #     room_name = event_json["room"]["name"]
#     #     # if str(room_name).startswith(kRoomPrefix):
#     #     #     participant_identity = event_json["participant"]["identity"]
#     #     #     participant_joined(room_name=room_name,participant_identity=participant_identity)
#     #     # #     full_name = event_json["participant"]["name"]
#     #     # #     created_at = ["createdAt"]

#     #     # #     # participant_joined.delay(room_name,participant_identity,full_name,created_at)
#     #     # #     participant_joined(room_name=room_name,participant_identity=participant_identity,full_name=full_name,created_at=created_at)

#     # elif event_json["event"] == "participant_left":
#     #     room_name = event_json["room"]["name"]
#     # #     if str(room_name).startswith(kRoomPrefix):
#     # #         participant_identity = event_json["participant"]["identity"]
#     # #         participant_left(room_name,participant_identity,)
#     # # #     room_service_client_obj = RoomServiceClientSingleton()

#     # # #     room_name = event_json["room"]["name"]
#     # # #     participant_identity = event_json["participant"]["identity"]
#     # # #     full_name = event_json["participant"]["name"]
#     # # #     created_at = ["createdAt"]

#     # # #     data = {
#     # # #         "message" : {
#     # # #             "action": "participant_left",
#     # # #             "identity" : int(participant_identity),
#     # # #             "full_name": full_name,
#     # # #             "created_at": created_at,
#     # # #         }
#     # # #     }

#     # # #     data = json.dumps(data)
#     # # #     data = data.encode("utf-8")

#     # # #     room_service_client_obj.send_data(room=room_name,data=data, kind=DataPacket.RELIABLE)

#     # if event_json["event"] == "room_finished":
#     #     room_name = event_json["room"]["name"]
#     #     if str(room_name).startswith(kRoomPrefix):
#     #         # delete_room.delay(room_name)
#     #         # delete_room(room_name)
#     #         remove_live_room_from_firebase(room_name)
        
#     return HttpResponse("Message received okay.", content_type="text/plain")


# def remove_live_room_from_firebase(room_name):
#     uid = int(str(room_name).split(kRoomPrefix)[1])

#     melive_mongo_db = MeLiveMongoDB()
#     collection_live_room = melive_mongo_db["LiveRoom"]
#     collection_live_room.delete_one({"channelName": f"{uid}",})

#     live_data = {
#         "type": "delete_live_room",
#         "channelName": f"{uid}",
#     } 

#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         f'live_streaming_livekit_streamings',
#         {
#             'type': 'live_streaming', 
#             'message': live_data
#         }
#     )
#     # try:
#     #     # firestore_db.collection("LiveRoom").document(f"{uid}").delete()
#     #     firebase_client = FirebaseClient()
    #     db_ref = firebase_client.firestore_db.collection("LiveRoom").document(f"{uid}")
    #     doc = db_ref.get()
    
    #     if doc.exists:
    #         firestore_json_data = doc.to_dict()
    #         pk_channel_id = None
    #         try:
    #             pk_channel_id = firestore_json_data['pkChannelName']
    #         except:
    #             pass
    #         if pk_channel_id is None or pk_channel_id == uid:
    #             room_service_client_obj = RoomServiceClientSingleton()
                
    #             try:
    #                 participant_obj = room_service_client_obj.get_participant(room=room_name,identity=str(uid))
    #                 # print("participant exist")

    #             except:
    #                 # print("participant does not exist")
    #                 try:
    #                     db_ref.delete()
    #                 except:
    #                     pass
    #             # try:
    #             #     db_ref.delete()
    #             # except:
    #             #     pass
    #             # Temporarily Commented
    #             # user_id = firestore_json_data['channelName']
    #             # creation_time = firestore_json_data['creation_time']
    #             # timestamp = datetime.timestamp(creation_time)
    #             # duration = int(timezone.now().timestamp()) - timestamp
    #             # is_video = firestore_json_data['is_video']
    #             # update_broadcasting_history(uid=user_id,is_video=is_video,seconds=floor(duration))
    # except:
    #     pass


# def delete_room(room_name):
#     channel_id = int(str(room_name).split(kRoomPrefix)[1])
#     remove_live_room_from_firebase(uid=channel_id)

# class LiveRoomListApiView(ListAPIView):
#     authentication_classes = []
#     # permission_classes = [HasAPIKey]
#     permission_classes = []


#     def list(self, request, *args, **kwargs):
#         # live_room_id_list = cache.get("live_room_id_list",[])
#         # live_room_id_temp_list = live_room_id_list
#         live_room_list = []
#         # for channel_id in live_room_id_list:
#         #     live_room_data = cache.get(f"live_room_{channel_id}")
#         #     if live_room_data is None:
#         #         live_room_id_temp_list.remove(channel_id)
#         #     else:
#         #         live_room_list.append(live_room_data)

#         # cache.set("live_room_id_list",live_room_id_temp_list,timeout=60*60*24*2)
#         melive_mongo_db = MeLiveMongoDB()
#         collection_live_room = melive_mongo_db["LiveRoom"]
#         live_rooms = collection_live_room.find()

#         try:
#             temp = live_rooms[0]
#             for live_room in live_rooms:
#                 json_encoded = json.dumps(live_room, sort_keys=True, indent=4, default=json_util.default)
#                 json_data = json.loads(json_encoded)
#                 json_data['creation_time'] = json_data['creation_time']['$date']
#                 live_room_list.append(json_data)
#         except:
#             pass

     
#         data = {"live_room_list": live_room_list}

#         return Response(data,status=HTTP_200_OK)
    
class LiveRoomV2ListApiView(ListAPIView):
    authentication_classes = []
    # permission_classes = [HasAPIKey]
    permission_classes = []


    def list(self, request, *args, **kwargs):
        live_room_objs = LiveRoom.objects.only('channel_id').all()
        live_room_list = []

        for live_room_obj in live_room_objs:
            channel_id = live_room_obj.channel_id
            live_room_data = cache.get(f"live_room_{channel_id}")
            if live_room_data is None:
                live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
                if live_room_obj:
                    live_room_data = LiveRoomSerializer(instance=live_room_obj).data
                    cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)
                    live_room_list.append(live_room_data)
            else:
                live_room_list.append(live_room_data)

        data = {"live_room_list": live_room_list}

        return Response(data,status=HTTP_200_OK)

# # TODO: Testing purpose only
# class LiveRoomTestListApiView(ListAPIView):
#     authentication_classes = []
#     permission_classes = []

#     def list(self,request, *args, **kwargs):
#         room_service_client_obj = RoomServiceClientSingleton()
#         # live_room_objs = LiveRoom.objects.only('channel_id',).all()
#         list_rooms = room_service_client_obj.list_rooms()

#         channel_ids = []

#         for room in list_rooms:
#             print(f'Room name: {room.name}')
#             channel_ids.append(int(str(room.name).split(kRoomPrefix)[1]))

#         # for live_room_obj in live_room_objs:
#         #     channel_id = live_room_obj.channel_id

#         print(f'channel_ids:  {channel_ids}')
#         print(f'channel_ids len: {len(channel_ids)}')

#         for channel_id in channel_ids:
#             room_name = f"{kRoomPrefix}{channel_id}"

#             # print(f"2 list_participants: {list_participants}........")
#             try:
#                 participant_obj = room_service_client_obj.get_participant(room=room_name,identity=str(channel_id)).identity
#                 print(f'Has indentity.....{channel_id}............')
#                 # print(f"participant exists: {participant_obj}")
#             except:
#                 # LiveRoom.objects.filter(channel_id=channel_id).delete()
#                 print(f'1) Delete {channel_id}..................................')
#         # else:
#         #     # LiveRoom.objects.filter(channel_id=channel_id).delete()
#         #     print(f'2) Delete {channel_id}..................................')



#         return Response(data={},status=HTTP_200_OK)
    
# class LiveRoomBroadcasterStatusCreateApiView(CreateAPIView):
#     authentication_classes = []
#     permission_classes = []

#     def create(self, request, *args, **kwargs):
#         data_obj = request.data
#         action = data_obj.get('action',None)
#         if action is not None:
#             melive_mongo_db = MeLiveMongoDB()
#             collection_live_room = melive_mongo_db["LiveRoom"]
#             if action == 'add_live_room':
#                 channel_id = data_obj.get('channel_id',0)
#                 # filtered_rooms = collection_live_room.find({"channelName": f"{channel_id}",}).limit(1)
#                 collection_live_room.delete_one({"channelName": f"{channel_id}",})

#                 # try:
#                 #     temp = filtered_rooms[0]
#                 #     # print('Exists')
#                 # except:
#                 #     # print('Not Exist')
#                 live_data = {
#                 "channelName": f"{channel_id}",
#                 "pk": data_obj.get('pk',False),
#                 "vvip_rank": data_obj.get('vvip_rank',0),
#                 "vvip_gif": data_obj.get('vvip_gif',None),
#                 "theme_gif": data_obj.get('theme_gif',None),
#                 'title': data_obj.get('title',None),
#                 "full_name": data_obj.get('full_name',None),
#                 "profile_image": data_obj.get('profile_image',None),

#                 "diamonds": data_obj.get('diamonds',None),
#                 "followers": data_obj.get('followers',[]),
#                 "blocks": data_obj.get('blocks',[]),
#                 "group_caller_ids": [channel_id],
#                 "caller_positions": [1],
#                 "viewers_count": 0,
#                 "is_agent": data_obj.get('is_agent',False),
#                 "is_reseller": data_obj.get('is_reseller',False),
#                 "is_host": data_obj.get('is_host',False),
#                 "is_moderator": data_obj.get('is_moderator',False),
#                 "is_video": data_obj.get('is_video',False),
#                 "is_locked": data_obj.get('is_locked',False),
#                 "allow_send": data_obj.get('allow_send',True),
#                 "creation_time": timezone.now(),
#                 }

#                 collection_live_room.insert_one(live_data)
#                 # Websocket
#                 live_data["type"] = "add_live_room"
                

#                 send_to_global_websocket(data=json.loads(DateTimeEncoder().encode(live_data)))
                

#             elif action == 'delete_live_room':
#                 channel_id = data_obj.get('channel_id',0)
#                 collection_live_room.delete_one({"channelName":f"{channel_id}",})   

#                 live_data = {
#                     "type": "delete_live_room",
#                     "channelName": f"{channel_id}",
#                 } 

#                 send_to_global_websocket(data=live_data)
            
# #             elif action == 'update_camera_filter':
# #                 channel_id = data_obj.get('channel_id',0)
# #                 cm_flt_nm = data_obj.get('cm_flt_nm','Hudson')
# #                 live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
# #                 if live_room_obj:
# #                     try:
# #                         live_room_obj.cm_flt_nm = cm_flt_nm
# #                     except:
# #                         pass
# #                     live_room_obj.save(force_update=True)

#             elif action == 'allow_comment_emoji_send':
#                 channel_id = data_obj.get('channel_id',0)
#                 allow_send = data_obj.get("allow_send",True)
                
#                 collection_live_room.update_one(filter={"channelName":f"{channel_id}",},update={'$set':{"allow_send":allow_send}})
                
#             elif action == 'update_theme_gif':
#                 channel_id = data_obj.get('channel_id',0)
#                 theme_gif = data_obj.get('theme_gif',None)

#                 collection_live_room.update_one(filter={"channelName":f"{channel_id}",},update={'$set':{"theme_gif":theme_gif,}})

#             elif action == 'update_user_in_calling_group':
#                 channel_id = data_obj.get('channel_id',0)
#                 group_caller_ids = data_obj.get('group_caller_ids',[])
#                 caller_positions = data_obj.get('caller_positions',[])

#                 collection_live_room.update_one(filter={"channelName":f"{channel_id}",},update={'$set':{"group_caller_ids":group_caller_ids,"caller_positions":caller_positions,}})

#             # elif action == 'remove_user_from_calling_group':
#             #     channel_id = data_obj.get('channel_id',0)
#             #     uid = data_obj.get('uid',0)
#             #     live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
#             #     if live_room_obj:
#             #         live_room_obj.remove_from_group_caller_id(uid=uid)

#             elif action == 'update_live_lock':
#                 channel_id = data_obj.get('channel_id',0)
#                 is_locked = data_obj.get('is_locked',False)
#                 updating_data = {"is_locked":is_locked,"locked_time":timezone.now(),}
                
#                 collection_live_room.update_one(filter={"channelName":f"{channel_id}",},update={'$set':updating_data})
#                 updating_data['type'] = 'update_live_lock'
#                 updating_data["channelName"] = f"{channel_id}",
#                 send_to_global_websocket(data=json.loads(DateTimeEncoder().encode(updating_data)))

#             elif action == 'update_viewers_count':
#                 channel_id = data_obj.get('channel_id',0)
#                 viewers_count = data_obj.get('viewers_count',0)

#                 collection_live_room.update_one(filter={"channelName":f"{channel_id}",},update={'$set':{"viewers_count":viewers_count}})
#                 # Websocket
#                 live_data = {
#                     "type": "viewers_count",
#                     "channelName": f"{channel_id}",
#                     "viewers_count": viewers_count,
#                 }
#                 send_to_global_websocket(data=live_data)
                    
# #             elif action == 'end_running_pk':
# #                 channel_id_1 = data_obj.get('channel_id_1',0)
# #                 channel_id_2 = data_obj.get('channel_id_2',0)
# #                 live_room_1_obj = LiveRoom.objects.filter(channel_id=channel_id_1).first()
# #                 live_room_2_obj = LiveRoom.objects.filter(channel_id=channel_id_2).first()

# #                 # update_list = []
# #                 if live_room_1_obj:
# #                     live_room_1_obj.is_pk = False
# #                     live_room_1_obj.pk_channel_id = channel_id_1
# #                     live_room_1_obj.anchor_pk = json.dumps([])
# #                     live_room_1_obj.pk_owner_gift_coins = 0
# #                     live_room_1_obj.pk_anchor_gift_coins = 0
# #                     live_room_1_obj.group_caller_ids = json.dumps([channel_id_1])
# #                     live_room_1_obj.pk_owner_contributors = json.dumps([])
# #                     live_room_1_obj.pk_anchor_contributors = json.dumps([])
# #                     # update_list.append(live_room_1_obj)
# #                     live_room_1_obj.save(force_update=True)

# #                 if live_room_2_obj:
# #                     live_room_2_obj.is_pk = False
# #                     live_room_2_obj.pk_channel_id = channel_id_2
# #                     live_room_2_obj.anchor_pk = json.dumps([])
# #                     live_room_2_obj.pk_owner_gift_coins = 0
# #                     live_room_2_obj.pk_anchor_gift_coins = 0
# #                     live_room_2_obj.group_caller_ids = json.dumps([channel_id_2])
# #                     live_room_2_obj.pk_owner_contributors = json.dumps([])
# #                     live_room_2_obj.pk_anchor_contributors = json.dumps([])
# #                     # update_list.append(live_room_2_obj)
# #                     live_room_2_obj.save(force_update=True)
                        
# #                 # if len(update_list) > 0:
# #                 #     LiveRoom.objects.bulk_update(update_list, ["is_pk","pk_channel_id","anchor_pk","pk_owner_gift_coins","pk_anchor_gift_coins","group_caller_ids","pk_owner_contributors","pk_anchor_contributors"],batch_size=len(update_list))
       
# #             elif action == 'remove_random_pk_request':
# #                 channel_id = data_obj.get('channel_id',0)
# #                 pk_type = data_obj.get('pk_type','random_pk')

# #                 live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()

# #                 if live_room_obj:
# #                     live_room_obj.is_pk = False
# #                     live_room_obj.save(force_update=True)

# #                     if pk_type == 'random_pk':
# #                         pk_search_obj = PkSearch.objects.first()
# #                         if pk_search_obj:
# #                             random_pk = json.loads(pk_search_obj.random_pk)
# #                             try:
# #                                 random_pk.remove(channel_id)
# #                             except:
# #                                 pass
# #                             pk_search_obj.random_pk = json.dumps(random_pk)
# #                             pk_search_obj.save(force_update=True)
                            
# #             elif action == 'add_random_pk_request':
# #                 channel_id = data_obj.get('channel_id',0)
# #                 pk_type = data_obj.get('pk_type','random_pk')
# #                 live_room_1_obj = LiveRoom.objects.filter(channel_id=channel_id).first()

# #                 if live_room_1_obj:
# #                     live_room_1_obj.is_pk = True

# #                     if pk_type == 'random_pk':
# #                         pk_search_obj = PkSearch.objects.first()
# #                         if pk_search_obj is None:
# #                             pk_search_obj = PkSearch()
# #                             pk_search_obj.random_pk = json.dumps([channel_id])
# #                             pk_search_obj.save(force_insert=True)
# #                             live_room_1_obj.save(force_update=True)
# #                         else:
# #                             random_pk = json.loads(pk_search_obj.random_pk)
# #                             if len(random_pk) == 0:
# #                                 pk_search_obj.random_pk = json.dumps([channel_id])
# #                                 pk_search_obj.save(force_update=True)
# #                                 live_room_1_obj.save(force_update=True)

# #                             elif channel_id not in random_pk:
# #                                 anchor_uid = random_pk[0]
# #                                 random_pk.remove(anchor_uid)

# #                                 pk_search_obj.random_pk = json.dumps(random_pk)
# #                                 pk_search_obj.save(force_update=True)

# #                                 pk_created_datetime = timezone.now()
# #                                 live_room_2_obj = LiveRoom.objects.filter(channel_id=anchor_uid).first()

# #                                 # update_list = []
# #                                 if live_room_1_obj:
# #                                     live_room_1_obj.is_pk = True
# #                                     live_room_1_obj.pk_winner_id = 0
# #                                     live_room_1_obj.pk_channel_id = anchor_uid
# #                                     live_room_1_obj.anchor_pk = json.dumps([anchor_uid])
# #                                     live_room_1_obj.pk_owner_gift_coins = 0
# #                                     live_room_1_obj.pk_anchor_gift_coins = 0
# #                                     live_room_1_obj.group_caller_ids = json.dumps([channel_id,anchor_uid])
# #                                     live_room_1_obj.pk_owner_contributors = json.dumps([])
# #                                     live_room_1_obj.pk_anchor_contributors = json.dumps([])
# #                                     live_room_1_obj.pk_created_datetime = pk_created_datetime
# #                                     # update_list.append(live_room_1_obj)
# #                                     live_room_1_obj.save(force_update=True)

# #                                 if live_room_2_obj:
# #                                     live_room_2_obj.is_pk = True
# #                                     live_room_2_obj.pk_winner_id = 0
# #                                     live_room_2_obj.pk_channel_id = anchor_uid
# #                                     live_room_2_obj.anchor_pk = json.dumps([channel_id])
# #                                     live_room_2_obj.pk_owner_gift_coins = 0
# #                                     live_room_2_obj.pk_anchor_gift_coins = 0
# #                                     live_room_2_obj.group_caller_ids = json.dumps([anchor_uid,channel_id])
# #                                     live_room_2_obj.pk_owner_contributors = json.dumps([])
# #                                     live_room_2_obj.pk_anchor_contributors = json.dumps([])
# #                                     live_room_2_obj.pk_created_datetime = pk_created_datetime
# #                                     # update_list.append(live_room_2_obj)
# #                                     live_room_2_obj.save(force_update=True)
                                        
# #                                 # if len(update_list) > 0:
# #                                 #     LiveRoom.objects.bulk_update(update_list, ["is_pk","pk_winner_id","pk_channel_id","anchor_pk","pk_owner_gift_coins","pk_anchor_gift_coins","group_caller_ids","pk_owner_contributors","pk_anchor_contributors","pk_created_datetime"],batch_size=len(update_list))

# #                                 first_profile_obj = Profile.objects.filter(user__id=channel_id).first()
# #                                 second_profile_obj = Profile.objects.filter(user__id=anchor_uid).first()

# #                                 first_profile_obj.pk_gift_coins = 0
# #                                 second_profile_obj.pk_gift_coins = 0

# #                                 update_profile_list = [first_profile_obj,second_profile_obj]
# #                                 Profile.objects.bulk_update(update_profile_list, ["pk_gift_coins"],batch_size=len(update_profile_list))
                                
# #             elif action == 'add_invitation_for_friends_pk':
# #                 channel_id = data_obj.get('channel_id',0)
# #                 uid = data_obj.get('uid',0)
# #                 full_name = data_obj.get('full_name','My Name')
# #                 profile_image = data_obj.get('profile_image','')
# #                 vvip_or_vip_preference = data_obj.get('vvip_or_vip_preference',{})

# #                 live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()

# #                 if live_room_obj:
# #                     uid = uid
# #                     full_name = full_name
# #                     profile_image = profile_image
# #                     vvip_or_vip_preference = vvip_or_vip_preference

# #                     friends_pk_invitation_ids = json.loads(live_room_obj.friends_pk_invitation_ids)
                
# #                     if uid not in friends_pk_invitation_ids:
# #                         friends_pk_invitation_ids.append(uid)
# #                         live_room_obj.friends_pk_invitation_ids = json.dumps(friends_pk_invitation_ids)
# #                         live_room_obj.save(force_update=True)

# #                         message = {
# #                         'action': 'invite_friends_pk',
# #                         'to_channel_name': str(channel_id),
# #                         'uid': uid,
# #                         'full_name': full_name,
# #                         'profile_image': profile_image,
# #                         'vvip_or_vip_preference': vvip_or_vip_preference,
# #                         }

# #                         channel_layer = get_channel_layer()
                    
# #                         async_to_sync(channel_layer.group_send)(
# #                             f'live_room_{channel_id}',
# #                             {
# #                                 'type': 'live_room',  
# #                                 'message': message
# #                             }
# #                         )
                        
# #             elif action == 'remove_invitation_for_friends_pk':
# #                 channel_id = data_obj.get('channel_id',0)
# #                 uid = data_obj.get('uid',0)
# #                 live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()

# #                 if live_room_obj:
# #                     friends_pk_invitation_ids = json.loads(live_room_obj.friends_pk_invitation_ids)
# #                     if uid in friends_pk_invitation_ids:
# #                         friends_pk_invitation_ids.remove(uid)
# #                         live_room_obj.friends_pk_invitation_ids = json.dumps(friends_pk_invitation_ids)
# #                         live_room_obj.save(force_update=True)
                        
# #             elif action == 'accept_friends_pk_invitation':
# #                 channel_id = data_obj.get('channel_id',0)
# #                 anchor_uid = data_obj.get('anchor_uid',0)
# #                 live_room_1_obj = LiveRoom.objects.filter(channel_id=channel_id).first()

# #                 if live_room_1_obj:
# #                     pk_created_datetime = timezone.now()
# #                     live_room_2_obj = LiveRoom.objects.filter(channel_id=anchor_uid).first()

# #                     friends_pk_invitation_ids = json.loads(live_room_1_obj.friends_pk_invitation_ids)
# #                     friends_pk_invitation_ids.remove(anchor_uid)

# #                     # update_list = []
# #                     if live_room_1_obj:
# #                         live_room_1_obj.is_pk = True
# #                         live_room_1_obj.pk_winner_id = 0
# #                         live_room_1_obj.pk_channel_id = channel_id
# #                         live_room_1_obj.anchor_pk = json.dumps([anchor_uid])
# #                         live_room_1_obj.pk_owner_gift_coins = 0
# #                         live_room_1_obj.pk_anchor_gift_coins = 0
# #                         live_room_1_obj.group_caller_ids = json.dumps([channel_id,anchor_uid])
# #                         live_room_1_obj.friends_pk_invitation_ids = json.dumps(friends_pk_invitation_ids)
# #                         live_room_1_obj.pk_owner_contributors = json.dumps([])
# #                         live_room_1_obj.pk_anchor_contributors = json.dumps([])
# #                         live_room_1_obj.pk_created_datetime = pk_created_datetime
# #                         # update_list.append(live_room_1_obj)
# #                         live_room_1_obj.save(force_update=True)

# #                     if live_room_2_obj:
# #                         live_room_2_obj.is_pk = True
# #                         live_room_2_obj.pk_winner_id = 0
# #                         live_room_2_obj.pk_channel_id = channel_id
# #                         live_room_2_obj.anchor_pk = json.dumps([channel_id])
# #                         live_room_2_obj.pk_owner_gift_coins = 0
# #                         live_room_2_obj.pk_anchor_gift_coins = 0
# #                         live_room_2_obj.group_caller_ids = json.dumps([anchor_uid,channel_id])
# #                         live_room_2_obj.pk_owner_contributors = json.dumps([])
# #                         live_room_2_obj.pk_anchor_contributors = json.dumps([])
# #                         live_room_2_obj.pk_created_datetime = pk_created_datetime
# #                         # update_list.append(live_room_2_obj)
# #                         live_room_2_obj.save(force_update=True)
                            
# #                     # if len(update_list) > 0:
# #                     #     LiveRoom.objects.bulk_update(update_list, ["is_pk","pk_winner_id","pk_channel_id","anchor_pk","pk_owner_gift_coins","pk_anchor_gift_coins","group_caller_ids","pk_owner_contributors","pk_anchor_contributors","pk_created_datetime"],batch_size=len(update_list))

# #                     first_profile_obj = Profile.objects.filter(user__id=channel_id).first()
# #                     second_profile_obj = Profile.objects.filter(user__id=anchor_uid).first()

# #                     first_profile_obj.pk_gift_coins = 0
# #                     second_profile_obj.pk_gift_coins = 0

# #                     update_profile_list = [first_profile_obj,second_profile_obj]
# #                     Profile.objects.bulk_update(update_profile_list, ["pk_gift_coins"],batch_size=len(update_profile_list))
                    
# #             elif action == 'update_pk_winner_id':
# #                 channel_id_1 = data_obj.get('channel_id_1',0)
# #                 channel_id_2 = data_obj.get('channel_id_2',0)
# #                 pk_winner_id = data_obj.get('pk_winner_id',0)
# #                 live_room_1_obj = LiveRoom.objects.filter(channel_id=channel_id_1).first()
# #                 live_room_2_obj = LiveRoom.objects.filter(channel_id=channel_id_2).first()

# #                 # update_list = []
# #                 if live_room_1_obj:
# #                     live_room_1_obj.pk_winner_id = pk_winner_id
# #                     # update_list.append(live_room_1_obj)
# #                     live_room_1_obj.save(force_update=True)

# #                 if live_room_2_obj:
# #                     live_room_2_obj.pk_winner_id = pk_winner_id
# #                     # update_list.append(live_room_2_obj)
# #                     live_room_2_obj.save(force_update=True)
                
# #             elif action == 'restart_pk':
# #                 channel_id_1 = data_obj.get('channel_id_1',0)
# #                 channel_id_2 = data_obj.get('channel_id_2',0)
# #                 pk_created_datetime = timezone.now()
# #                 live_room_1_obj = LiveRoom.objects.filter(channel_id=channel_id_1).first()
# #                 live_room_2_obj = LiveRoom.objects.filter(channel_id=channel_id_2).first()

# #                 # update_list = []
# #                 if live_room_1_obj:
# #                     live_room_1_obj.pk_owner_gift_coins = 0
# #                     live_room_1_obj.pk_anchor_gift_coins = 0
# #                     live_room_1_obj.pk_owner_contributors = json.dumps([])
# #                     live_room_1_obj.pk_anchor_contributors = json.dumps([])
# #                     live_room_1_obj.pk_created_datetime = pk_created_datetime
# #                     # update_list.append(live_room_1_obj)
# #                     live_room_1_obj.save(force_update=True)

# #                 if live_room_2_obj:
# #                     live_room_2_obj.pk_owner_gift_coins = 0
# #                     live_room_2_obj.pk_anchor_gift_coins = 0
# #                     live_room_2_obj.pk_owner_contributors = json.dumps([])
# #                     live_room_2_obj.pk_anchor_contributors = json.dumps([])
# #                     live_room_2_obj.pk_created_datetime = pk_created_datetime
# #                     # update_list.append(live_room_2_obj)
# #                     live_room_2_obj.save(force_update=True)
                        
# #                 # if len(update_list) > 0:
# #                 #     LiveRoom.objects.bulk_update(update_list, ["pk_owner_gift_coins","pk_anchor_gift_coins","pk_owner_contributors","pk_anchor_contributors","pk_created_datetime"],batch_size=len(update_list))

#         return Response(status=HTTP_201_CREATED)

class LiveRoomUpdateApiView(UpdateAPIView):
    authentication_classes = []
    # permission_classes = [HasAPIKey]
    permission_classes = []

    def update(self, request, *args, **kwargs):
        data_obj = request.data
        action = data_obj.get('action',None)
        if action is not None:
            if action == 'add_live_room':
                channel_id = data_obj.get('channel_id',0)
                is_video = data_obj.get('is_video',True)
                cm_flt_nm = data_obj.get('cm_flt_nm','Hudson')
                title = data_obj.get('title','My Title')

                if LiveRoom.objects.filter(channel_id=channel_id).exists():
                    # datetime_now = timezone.now()
                    LiveRoom.objects.filter(channel_id=channel_id).update(title=title,is_video = is_video,cm_flt_nm = cm_flt_nm)

                    live_room_data = cache.get(f"live_room_{channel_id}")
                    if live_room_data is not None:
                        live_room_data['title'] = title
                        live_room_data['is_video'] = is_video
                        live_room_data['cm_flt_nm'] = cm_flt_nm
                        # TODO: For hanging Live
                        # live_room_data['created_datetime'] = str(datetime_now)

                        cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)

                        live_room_data['type'] = 'streaming'
                        sendDataInGlobalWebsocket(data=live_room_data)
                    else:
                        live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
                        live_room_data = LiveRoomSerializer(instance=live_room_obj).data

                        if live_room_data:
                            cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)
                            live_room_data['type'] = 'streaming'
                            sendDataInGlobalWebsocket(data=live_room_data)

                    json_data={
                        'channel_id': channel_id,
                        'action':'host_already_exists'
                        }
                    # External websocket
                    ws = create_connection(f"{liveRoomSocketBaseUrl}/{channel_id}/")
                    ws.send(json.dumps({"message": json_data}))
                    ws.close()
                    
                        
                    # live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
                    # live_room_obj.is_video = is_video
                    # live_room_obj.created_datetime = timezone.now()
                    # try:
                    #     if cm_flt_nm is not None:
                    #         live_room_obj.cm_flt_nm = cm_flt_nm
                    # except:
                    #     pass
                    # live_room_obj.save(force_update=True)
                else:
                    live_room_obj = LiveRoom()
                    live_room_obj.channel_id = channel_id
                    live_room_obj.title = title
                    live_room_obj.is_video = is_video
                    live_room_obj.group_caller_ids = json.dumps([{'uid':channel_id,'position':1}])
                    try:
                        if cm_flt_nm is not None:
                            live_room_obj.cm_flt_nm = cm_flt_nm
                    except:
                        pass
                    live_room_obj.save(force_insert=True)
                    live_room_data = LiveRoomSerializer(instance=live_room_obj).data

                    if live_room_data:
                        cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)
                        live_room_data['type'] = 'streaming'
                        sendDataInGlobalWebsocket(data=live_room_data)

            elif action == 'delete_live_room':
                channel_id = data_obj.get('channel_id',0)
                room_name = f"{kRoomPrefix}{channel_id}"
               
                room_service_client_obj = RoomServiceClientSingleton()

                try:
                    room_service_client_obj.delete_room(room=room_name)                   
                except:
                    pass

                try:
                    LiveRoom.objects.filter(channel_id=channel_id).delete()  
                except:
                    pass

            elif action == 'update_camera_filter':
                channel_id = data_obj.get('channel_id',0)
                cm_flt_nm = data_obj.get('cm_flt_nm','Hudson')

                data = {
                    'type': 'update_camera_filter',
                    'channel_id': channel_id,
                    'cm_flt_nm': cm_flt_nm,
                }
                sendDataInGlobalWebsocket(data=data)

                LiveRoom.objects.filter(channel_id=channel_id).update(cm_flt_nm = cm_flt_nm)

                live_room_data = cache.get(f"live_room_{channel_id}")
                if live_room_data is not None:
                    live_room_data['cm_flt_nm'] = cm_flt_nm
                    cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)
                
                # live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
                # if live_room_obj:
                #     try:
                #         live_room_obj.cm_flt_nm = cm_flt_nm
                #     except:
                #         pass
                #     live_room_obj.save(force_update=True)

            elif action == 'allow_comment_emoji_send':
                channel_id = data_obj.get('channel_id',0)
                allow_send = data_obj.get("allow_send",True)

                data = {
                    'type': 'allow_comment_emoji_send',
                    'channel_id': channel_id,
                    'allow_send': allow_send,
                }
                sendDataInGlobalWebsocket(data=data)

                LiveRoom.objects.filter(channel_id=channel_id).update(allow_send = allow_send)

                live_room_data = cache.get(f"live_room_{channel_id}")
                if live_room_data is not None:
                    live_room_data['allow_send'] = allow_send
                    cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)

                # live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
                # if live_room_obj:
                #     try:
                #         live_room_obj.allow_send = allow_send
                #     except:
                #         pass
                #     live_room_obj.save(force_update=True)

            elif action == 'add_user_to_calling_group':
                channel_id = data_obj.get('channel_id',0)
                uid = data_obj.get('uid',0)
                position = data_obj.get('position',0)


                # data = {
                #     'type': 'add_user_to_calling_group',
                #     'channel_id': channel_id,
                #     'uid': uid,
                # }
                # sendDataInGlobalWebsocket(data=data)

                live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).only('id','group_caller_ids').first()
                if live_room_obj:
                    live_room_obj.save_group_caller_id(uid=uid,position=position)

            elif action == 'remove_user_from_calling_group':
                channel_id = data_obj.get('channel_id',0)
                uid = data_obj.get('uid',0)

                # data = {
                #     'type': 'remove_user_from_calling_group',
                #     'channel_id': channel_id,
                #     'uid': uid,
                # }
                # sendDataInGlobalWebsocket(data=data)

                live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).only('id','group_caller_ids').first()
                if live_room_obj:
                    live_room_obj.remove_from_group_caller_id(uid=uid)

            elif action == 'update_live_lock':
                channel_id = data_obj.get('channel_id',0)
                is_locked = data_obj.get('is_locked',False)

                datetime_now = timezone.now()

                data = {
                    'type': 'update_live_lock',
                    'channel_id': channel_id,
                    'is_locked': is_locked,
                    'locked_datetime': str(datetime_now),
                }
                sendDataInGlobalWebsocket(data=data)
                LiveRoom.objects.filter(channel_id=channel_id).update(is_locked = is_locked,locked_datetime = datetime_now)

                live_room_data = cache.get(f"live_room_{channel_id}")
                if live_room_data is not None:
                    live_room_data['is_locked'] = is_locked
                    live_room_data['locked_datetime'] = str(datetime_now)
                    cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)

                # live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
                # if live_room_obj:
                #     try:
                #         if is_locked:
                #             live_room_obj.is_locked = True
                #             live_room_obj.locked_datetime = timezone.now()
                #         else:
                #             live_room_obj.is_locked = False
                #     except:
                #         pass
                
                #     live_room_obj.save(force_update=True)

            elif action == 'update_viewers_count':
                
                channel_id = data_obj.get('channel_id',0)
                viewers_count = data_obj.get('viewers_count',0)

                data = {
                    'type': 'update_viewers_count',
                    'channel_id': channel_id,
                    'viewers_count': viewers_count,
                }
                sendDataInGlobalWebsocket(data=data)

                LiveRoom.objects.filter(channel_id=channel_id).update(viewers_count = viewers_count,)

                live_room_data = cache.get(f"live_room_{channel_id}")
                if live_room_data is not None:
                    live_room_data['viewers_count'] = viewers_count
                    cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)
                live_room_obj = LiveRoom.objects.filter(channel_id=channel_id).first()
                if live_room_obj:
                    try:
                        live_room_obj.viewers_count = viewers_count
                    except:
                        pass
                    live_room_obj.save(force_update=True)
                    
        return Response(status=HTTP_200_OK)
   
class GroupCallerCreateApiView(CreateAPIView):
    authentication_classes = []
    # permission_classes = [HasAPIKey]
    permission_classes = []

    lookup_field = 'channel_name'

    def create(self,request, *args, **kwargs):
        channel_name = self.kwargs[self.lookup_field]
        data_obj = request.data
        call_type = data_obj.get("call_type","audio")
        # caller_ids = data_obj.get("caller_ids",[])
        my_uid = data_obj.get('my_uid',0)


        # [3,2,4,5]
        group_callers = []

        live_room_obj = LiveRoom.objects.filter(channel_id=channel_name).first()
        if live_room_obj:
            group_caller_ids = live_room_obj.get_group_caller_ids()

            # if int(channel_name) not in caller_ids:
            #     caller_ids.insert(0,int(channel_name))
         
            # for id in caller_ids:
            #     if id not in group_caller_ids:
            #         group_caller_ids.append(id)

            # if live_room_obj.is_pk == True and len(group_caller_ids) > 2:
            #     group_caller_ids = caller_ids
            # elif live_room_obj.is_pk == False and len(group_caller_ids) > 9:
            #     group_caller_ids = caller_ids


            for caller_id in group_caller_ids:
                uid = caller_id['uid']
                position = caller_id['position']

                profile_cache = cache.get(f'profile_{uid}')
                if profile_cache is None:
                    # host_profile_obj = Profile.objects.filter(user__id=uid).first()
                    host_profile_obj = Profile.objects.filter(user__id=uid).first()
                                        
                    if host_profile_obj:
                        profile_cache = ProfileSerializer(instance=host_profile_obj).data
                        cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*30)

                try:
                    profile_cache['vvip_or_vip_preference'] = json.loads(profile_cache['vvip_or_vip_preference'])
                except:
                    pass

                try:
                    index = profile_cache['followers'].index(my_uid)
                    # Found
                    profile_cache['followers'] = [my_uid]
                    # print('Found')
                except ValueError:
                    # Not found
                    profile_cache['followers'] = []
                    # print('Not Found')

                caller_data = {
                    "uid": uid,
                    "position": position,
                    "full_name": profile_cache["full_name"],
                    "profile_image": profile_cache["profile_image"],
                    "diamonds": profile_cache["diamonds"],
                    "vvip_or_vip_preference":
                        profile_cache["vvip_or_vip_preference"],
                    "followers": profile_cache["followers"],
                    # "is_agent": profile_cache["is_agent"],
                    # "is_host": profile_cache["is_host"],
                    # "is_reseller": profile_cache["is_reseller"],
                    "call_type": call_type,
                    "muted": False,
                    "video_disabled": False,
                }

                if caller_id == channel_name:
                    group_callers.insert(0,caller_data)
                else:
                    group_callers.append(caller_data)

        return Response({"group_callers":group_callers,},status=HTTP_200_OK)
    
class FollowingLiveRoomListApiView(ListAPIView):
    authentication_classes = []
    # permission_classes = [HasAPIKey]
    permission_classes = []
    lookup_field = 'user_id'


    def list(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]

        live_room_objs = LiveRoom.objects.only('channel_id').all()
        following_live_room_id_list = []

        for live_room_obj in live_room_objs:
            channel_id = live_room_obj.channel_id

            if Profile.objects.filter(user__id=channel_id,followers__in=[user_id]).exists():
                # print(f'Exists: {channel_id}')
                following_live_room_id_list.append(channel_id)

        data = {"following_live_room_id_list": following_live_room_id_list}

        return Response(data,status=HTTP_200_OK)
   
def send_to_global_websocket(data):
    # Sending to websocket
    channel_layer = get_channel_layer()
    # Send message to room group
    async_to_sync(channel_layer.group_send)(
        f'live_streaming_livekit_streamings',
        {
            'type': 'live_streaming', 
            'message': data,
        }
    )
