import json
from websocket import create_connection
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.generics import (
    CreateAPIView
    )
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.status import (
    HTTP_201_CREATED,HTTP_203_NON_AUTHORITATIVE_INFORMATION,
    HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from live_streamings.tasks import gifting_execution
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from livekit_stuffs.api.firebase_client import FirebaseClient
from ..tasks import paying_live_lock_diamonds,paying_call_lock_diamonds
from me_live.utils.constants import liveRoomSocketBaseUrl
# from livekit_stuffs.api.constants import firestore_db

# class AgoraRtcTokenRetrieveApiView(RetrieveAPIView):
#     authentication_classes = []
#     permission_classes = []

#     def retrieve(self, request, *args, **kwargs):

#         agora_token_obj = AgoraToken.objects.first()
#         rtc_token = ''
#         if agora_token_obj:
#             APP_ID = agora_token_obj.app_id
#             APP_CERTIFICATE = agora_token_obj.app_certificate

#             method_dict = request.GET
#             channel_name = method_dict.get('channel_name',None)
#             uid = method_dict.get('uid',0)
#             role = method_dict.get('role',2)
#             # role
#             # Role_Publisher = 1: A broadcaster (host) in a live-broadcast profile. 
#             # Role_Subscriber = 2: (Default) A audience in a live-broadcast profile.

#             # Expire time in second
#             today = timezone.now()
#             privilegeExpireTs = today.timestamp() + 60*60*12 
#             #Build token with uid
#             rtc_token = RtcTokenBuilder.buildTokenWithUid(APP_ID, APP_CERTIFICATE, channel_name, uid, role, privilegeExpireTs)
#         return Response({'rtcToken':rtc_token},status=HTTP_200_OK)

# class LiveStreamingStateUpdateApiView(UpdateAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def update(self, request, *args, **kwargs):
#         data_obj = request.data
#         user = request.user
#         profile_obj = user.profile
#         timestamp = data_obj.get('timestamp',str(timezone.now()))
#         active_calls = data_obj.get('active_calls',[])

#         present_datetime = timezone.now()
#         allow_streaming = True
#         allow_audio_call = True
#         allow_video_call = True
#         # plan_purchased_objs = PlanPurchased.objects.filter(user=request.user,expired_datetime__gte=present_datetime)
#         # if plan_purchased_objs:
#         #     allow_streaming = True
#         #     for plan_purchased_obj in plan_purchased_objs:
#         #         if plan_purchased_obj.plan.receive_call_type == 'audio':
#         #             allow_audio_call = True
#         #         else:
#         #             allow_video_call = True

#         # if profile_obj.profile_image:
#         #     profile_image = f'{request.build_absolute_uri(settings.MEDIA_URL)}{str(profile_obj.profile_image)}'
#         # else:
#         #     profile_image = ''

#         serializer_profile_data = ProfileSerializer(instance=profile_obj,context={"request": request}).data

#         # earn_coins = 0
#         # balance_obj = Balance.objects.filter(user=user).first()
#         # if balance_obj:
#         #     earn_coins = balance_obj.earn_coins 

#         # title = profile_obj.streaming_title
#         # if title is None:
#         #     title = profile_obj.full_name

#         data = {
#         'uid': user.id, 
#         # 'title': f'Live streaming from {profile_obj.full_name}', 
#         'title': profile_obj.full_name,
#         'full_name': profile_obj.full_name,
#         'profile_image': serializer_profile_data['profile_image'],
#         'channelName': user.id, 
#         'active_calls': active_calls,
#         'allow_streaming': allow_streaming,
#         'allow_audio_call': allow_audio_call,
#         'allow_video_call': allow_video_call,
#         # 'earn_coins': profile_obj.earn_coins,
#         'loves': profile_obj.loves,
#         'gift_diamonds': profile_obj.gift_diamonds,
#         'followers': serializer_profile_data['followers'],
#         'blocks': serializer_profile_data['blocks'],
#         'country_name': profile_obj.country_name,
#         'country_code': profile_obj.iso_code,
#         'timestamp': timestamp, 
#         'datetime': str(timezone.now()), 
#         # 'views': []
#         } 

#          # Testing
#         channel_layer = get_channel_layer()
#         # self.room_group_name = 'live_streaming_%s' % self.room_name
#         # live_streamings is the room name
#         room_name = 'live_streamings'
#         async_to_sync(channel_layer.group_send)(
#             f'live_streaming_{room_name}',
#             {'type': 'live_streaming', 'message': data}
#         )
        
#         return Response(data,status=HTTP_200_OK)

class NotifyFollowersCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        # profile_obj = user.profile

        # base_url = f'{request.build_absolute_uri(settings.MEDIA_URL)}'
        # notify_streaming_to_followers.delay(uid=user.id,base_url=base_url)
        notify_streaming_to_followers(user=user)

        
        return Response(status=HTTP_201_CREATED)
    
def notify_streaming_to_followers(user):
    profile_obj = user.profile

    if profile_obj.last_notification_datetime is not None and profile_obj.last_notification_datetime >= timezone.now():
        return
    profile_obj.last_notification_datetime = timezone.now() + timedelta(minutes=30)
    profile_obj.save(force_update=True)
    
    followers = profile_obj.followers.all()
    
    if len(followers) > 0:
        uid = user.id
        title = profile_obj.full_name
        image = get_profile_image(profile_obj=profile_obj)

        # Notify to followers
        message = 'Is Live now'
        registration_ids = []
        for follower_obj in followers:
            try:
                device_obj = follower_obj.device_token
                if device_obj:
                    registration_ids.append(device_obj.token) 
            except:
                pass
            
        if len(registration_ids) > 0:
            if image is None:
                image = ""
            # payload_data = {
            #     'data': {
            #         'title': title,
            #         'message': message,
            #         'image': image,
            #         'peered_uid': uid,
            #         'peered_name': title,
            #         'call_type': '',
            #         'event_type':'STREAM_LIVE',
            #         'channel': f'{uid}',
            #     }
            # }
            payload_data = {
                    'title': title,
                    'message': message,
                    'image': image,
                    'peered_uid': f"{uid}",
                    'peered_name': title,
                    'call_type': '',
                    'event_type':'STREAM_LIVE',
                    'channel': f'{uid}',
            }

            # firebase_obj = Firebase()
            firebase_client = FirebaseClient()
            if len(registration_ids) == 1:
                # firebase_obj.send(registration_ids[0],payload_data)
                firebase_client.send_single_fcm(registration_token=registration_ids[0],data=payload_data)
            else:
                # firebase_obj.send_multicast(registration_ids,payload_data)
                firebase_client.send_multicast_fcm(registration_tokens=registration_ids,data=payload_data)
                
def get_profile_image(profile_obj):
    if profile_obj.profile_image:
        return f"{settings.BASE_URL}/media/{profile_obj.profile_image}"
    return profile_obj.photo_url

# class LiveStreamingGiftCreateApiView(CreateAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated & HasAPIKey]

#     def create(self, request, *args, **kwargs):
#         data_obj = request.data

#         user = request.user
#         profile_obj = user.profile

#         room_name = data_obj.get('room_name',None)
#         sender_uid = data_obj.get('sender_uid',0)
#         receiver_uid = data_obj.get('receiver_uid',0)
#         gift_type = data_obj.get('gift_type',None)
#         gift_id = int(data_obj.get('gift_id',0))
#         diamonds = int(data_obj.get('diamonds',0))
#         vat = int(data_obj.get('vat',0))
#         full_name = data_obj.get('full_name',None)
#         receiver_full_name = data_obj.get('receiver_full_name',None)
#         profile_image = data_obj.get('profile_image',None)
#         level = data_obj.get('level',None)
#         gift_image = data_obj.get('gift_image',None)
#         gif = data_obj.get('gif',None)
#         audio = data_obj.get('audio',None)
#         vvip_or_vip_preference = data_obj.get('vvip_or_vip_preference',None)
        
#         data = {
#             'gift_type':gift_type,
#             'gift_id': gift_id,
#         }

#         if receiver_uid is None or receiver_uid <= 0 or receiver_uid == user.id:
#             return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

#         data['vat'] = vat

#         if profile_obj.diamonds < diamonds:
#             return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

#         data['sender_uid'] = sender_uid
#         data['receiver_uid'] = receiver_uid
#         data['uid'] = sender_uid
#         data['type'] = 'gift'
#         data['action'] = 'activity'
#         data['full_name'] = full_name
#         data['receiver_full_name'] = receiver_full_name
#         data['profile_image'] = profile_image
#         data['level'] = level
#         data['diamonds'] = diamonds
#         data['gift_image'] = gift_image
#         data['gif'] = gif
#         data['audio'] = audio
#         data['vvip_or_vip_preference'] = vvip_or_vip_preference

#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             f'live_room_{room_name}',
#             {'type': 'live_room', 'message': data}
#         ) 
#         async_to_sync(channel_layer.group_send)(
#             f'live_streaming_livekit_streamings',
#             {
#                 'type': 'live_streaming', 
#                 'message': data
#             }
#         )
        
#         gifting_execution.delay(sender_uid,receiver_uid,diamonds,vat)

#         # # Temporary solution
#         # # Sender diamonds
#         # profile_obj.diamonds -= diamonds
#         # profile_obj.save(force_update=True) 

#         # # Receiver diamonds
#         # # receiver_uid is the ID of receiver user
#         # receiver_user_obj = User.objects.filter(id=int(receiver_uid)).first()
#         # receiver_profile_obj = receiver_user_obj.profile
#         # receiver_profile_obj.diamonds += diamonds - vat
#         # receiver_profile_obj.gift_diamonds += diamonds - vat
#         # receiver_profile_obj.save(force_update=True)

#         # # earning_history_obj = EarningHistory()
#         # # earning_history_obj.user = receiver_user_obj 
#         # # earning_history_obj.gift_sender = user
#         # # earning_history_obj.diamonds = int(diamonds)

#         # # earning_history_obj.save()

#         # gift_send_vat_diamonds_obj = GiftSendVatDiamonds.objects.first()
#         # if gift_send_vat_diamonds_obj is None:
#         #     gift_send_vat_diamonds_obj = GiftSendVatDiamonds()
#         #     gift_send_vat_diamonds_obj.gift_vat_diamonds = vat
#         #     gift_send_vat_diamonds_obj.save(force_insert=True)
#         # else:
#         #     gift_send_vat_diamonds_obj.gift_vat_diamonds += vat
#         #     gift_send_vat_diamonds_obj.save(force_update=True)

#         # # Contribution
#         # contribution_obj = Contribution.objects.filter(user=receiver_user_obj,contributor=user).first() 
#         # if contribution_obj is None:
#         #     contribution_obj = Contribution()
#         #     contribution_obj.user = receiver_user_obj
#         #     contribution_obj.contributor = user
#         #     contribution_obj.diamonds = diamonds - vat
#         #     contribution_obj.datetime = timezone.now()
#         #     contribution_obj.save(force_insert=True)
#         # else:
#         #     # Update coins contribution
#         #     contribution_obj.diamonds += diamonds - vat
#         #     contribution_obj.datetime = timezone.now()
#         #     contribution_obj.save(force_update=True)


#         # # Firebase
#         # db_ref = firestore_db.collection("LiveRoom").document(f"{receiver_uid}")
#         # doc = db_ref.get()
        
#         # if doc.exists:
#         #     firestore_json_data = doc.to_dict()
#         #     try:
#         #         update_data = {
#         #             "diamonds":  firestore_json_data["diamonds"] + diamonds - vat
#         #         }
#         #         db_ref.update(update_data)
#         #     except:
#         #         pass
     

#         return Response(status=HTTP_201_CREATED)
 
class LiveStreamingGiftV2CreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def create(self, request, *args, **kwargs):
        data_obj = request.data

        user = request.user
        profile_obj = user.profile

        if profile_obj.is_host == True:
            # Disable conversion for Host
            return Response(status=HTTP_204_NO_CONTENT)

        room_name = data_obj.get('room_name',None)
        sender_uid = data_obj.get('sender_uid',0)
        receiver_uid = data_obj.get('receiver_uid',0)
        gift_type = data_obj.get('gift_type',None)
        gift_id = int(data_obj.get('gift_id',0))
        diamonds = int(data_obj.get('diamonds',0))
        vat = int(data_obj.get('vat',0))
        full_name = data_obj.get('full_name',None)
        receiver_full_name = data_obj.get('receiver_full_name',None)
        profile_image = data_obj.get('profile_image',None)
        level = data_obj.get('level',None)
        gift_image = data_obj.get('gift_image',None)
        gif = data_obj.get('gif',None)
        audio = data_obj.get('audio',None)
        vvip_or_vip_preference = data_obj.get('vvip_or_vip_preference',None)

        if profile_image == "null":
            profile_image = None
        if level == 'null':
            level = None
        if audio == "null":
            audio = None
        if gift_image == "null":
            gift_image = None
        
        data = {
            'gift_type':gift_type,
            'gift_id': gift_id,
        }

        if receiver_uid is None or receiver_uid <= 0 or receiver_uid == user.id:
            return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        data['vat'] = vat

        if profile_obj.diamonds < diamonds:
            return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        data['sender_uid'] = sender_uid
        data['receiver_uid'] = receiver_uid
        data['uid'] = sender_uid
        data['type'] = 'gift'
        data['action'] = 'activity'
        data['full_name'] = full_name
        data['receiver_full_name'] = receiver_full_name
        data['profile_image'] = profile_image
        data['level'] = level
        data['diamonds'] = diamonds
        data['gift_image'] = gift_image
        data['gif'] = gif
        data['audio'] = audio
        data['vvip_or_vip_preference'] = vvip_or_vip_preference

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'live_streaming_livekit_streamings',
            {
                'type': 'live_streaming', 
                'message': data
            }
        )

        # External websocket
        ws = create_connection(f"{liveRoomSocketBaseUrl}/{room_name}/")
        ws.send(json.dumps({"message": data}))
        ws.close()
        
        gifting_execution.delay(sender_uid,receiver_uid,diamonds,vat)

        return Response(status=HTTP_201_CREATED)

class PayingDiamondsForLiveLockCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        data_obj = request.data
        host_id = data_obj.get('host_id',0)
        group_callers = data_obj.get('group_callers',[])
      
        user = request.user
        host_profile_obj = user.profile

        if user.id != host_id:
            return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        if len(group_callers) > 1:
            paying_live_lock_diamonds.delay(host_id=host_id,group_callers=group_callers)

        return Response(status=HTTP_201_CREATED)
    
class PayingDiamondsForCallLockCreateApiView(CreateAPIView):
    authentication_classes = []
    permission_classes = [HasAPIKey]

    def create(self, request, *args, **kwargs):

        data_obj = request.data
        host_id = data_obj.get('host_id',0)
        uid = data_obj.get('uid',0)
        diamonds = data_obj.get('diamonds',0)

        paying_call_lock_diamonds.delay(host_id=host_id,uid=uid,paying_diamonds=diamonds)

        return Response(status=HTTP_201_CREATED)