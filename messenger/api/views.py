from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

from math import floor
from rest_framework.generics import (
    RetrieveAPIView,UpdateAPIView,CreateAPIView,ListAPIView,
    )
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from accounts.models import User
from chats.models import ChatCost
from fcm.models import FCMDeviceToken
from livekit_stuffs.api.firebase_client import FirebaseClient
from profiles.models import Profile
from ..models import LastChatMessage,ChatMessage, ChatBlock
from .serializers import LastChatMessageSerializer, ChatMessageSerializer
from tracking.models import ChatSendVatDiamonds

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 15
    page_query_param = 'page'

class LastChatMessageListApiView(ListAPIView):
    authentication_classes = []
    permission_classes = []
    queryset = []
    serializer_class = LastChatMessageSerializer
    pagination_class = StandardResultsSetPagination
    lookup_field = 'user_id'

    # cache requested url (in Seconds)
    def list(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        last_messages_objs = LastChatMessage.objects.filter(user_id=user_id).order_by('-datetime')
        queryset = self.filter_queryset(last_messages_objs)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = {'last_message_list':serializer.data,}
            # return self.get_paginated_response(serializer.data)
            return self.get_paginated_response(data)


        serializer = self.get_serializer(queryset, many=True)
        return Response({'last_message_list':serializer.data,})
    
class ChatMessageListApiView(ListAPIView):
    authentication_classes = []
    permission_classes = []
    queryset = []
    serializer_class = ChatMessageSerializer
    pagination_class = StandardResultsSetPagination
    lookup_field = 'chat_id'

    def list(self, request, *args, **kwargs):
        method_dict = request.GET
        chat_id = self.kwargs[self.lookup_field]
        # User ID = 0 if Own ID otherwise > 0
        user_id = int(method_dict.get('user_id',0))

        is_blocked = False
        blocked_by = 0

        receiver_id = 0
        ids = str(chat_id).split("_")
        if int(ids[0]) == user_id:
            receiver_id = int(ids[1]) 
        else:
            receiver_id = int(ids[0]) 

        receiver_user_obj = User.objects.filter(id=receiver_id).only('id').first()
        sender_user_obj = User.objects.filter(id=user_id).only('id').first()

        chat_messages_objs = ChatMessage.objects.filter(chat_id=chat_id).order_by('-id')
        queryset = self.filter_queryset(chat_messages_objs)

        page = self.paginate_queryset(queryset)
        if page is not None:
            page_number = int(method_dict.get('page',0))
            serializer = self.get_serializer(page, many=True)
            data = {'message_list':serializer.data,}
            if page_number == 0 or page_number == 1:
                # Block

                if ChatBlock.objects.filter(user_id=user_id,blocks__in=[receiver_user_obj]).exists():
                    is_blocked = True
                    blocked_by = user_id
                elif ChatBlock.objects.filter(user_id=receiver_id,blocks__in=[sender_user_obj]).exists():
                    is_blocked = True
                    blocked_by = receiver_id
                data['is_blocked'] = is_blocked
                data['blocked_by'] = blocked_by

                chat_cost = cache.get(key="chat_cost",)
                if chat_cost is None:
                    chat_vat_obj = ChatCost.objects.first()
                    if chat_vat_obj is None:
                        chat_vat_obj = ChatCost.objects.create()
                    chat_cost = {"cost_diamonds": chat_vat_obj.cost_diamonds, "vat_diamonds": chat_vat_obj.vat_diamonds,}
                data['chat_cost'] = chat_cost

            # return self.get_paginated_response(serializer.data)
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)

        # Block
        if ChatBlock.objects.filter(user_id=user_id,blocks__in=[receiver_user_obj]).exists():
            is_blocked = True
            blocked_by = user_id
        elif ChatBlock.objects.filter(user_id=receiver_id,blocks__in=[sender_user_obj]).exists():
            is_blocked = True
            blocked_by = receiver_id
       
        chat_cost = cache.get(key="chat_cost",)
        if chat_cost is None:
            chat_vat_obj = ChatCost.objects.first()
            if chat_vat_obj is None:
                chat_vat_obj = ChatCost.objects.create()
            chat_cost = {"cost_diamonds": chat_vat_obj.cost_diamonds, "vat_diamonds": chat_vat_obj.vat_diamonds,}
            
        return Response(data={'message_list':serializer.data,'is_blocked':is_blocked,'blocked_by':blocked_by,'chat_cost':chat_cost,},status=HTTP_200_OK)


class ChatMessageCreateApiView(CreateAPIView):
    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        data_obj = request.data

        key = data_obj.get('key','0')
        chat_id = data_obj.get('chat_id','0')
        sender_id = data_obj.get('sender_id',0)
        receiver_id = data_obj.get('receiver_id',0)
        # diamonds = data_obj.get('diamonds',0)
        cost_diamonds = data_obj.get('cost_diamonds',0)
        vat_diamonds = data_obj.get('vat_diamonds',0)

        type = data_obj.get('type','text')
        message = data_obj.get('message','')
        sender_image = data_obj.get('sender_image',None)
        receiver_image = data_obj.get('receiver_image',None)
        sender_full_name = data_obj.get('sender_full_name',None)
        receiver_full_name = data_obj.get('receiver_full_name',None)     

       
        # Cost Diamonds
        if cost_diamonds > 0:
            receiver_profile_obj = Profile.objects.filter(user__id=receiver_id).only('id','diamonds').first()
            sender_profile_obj = Profile.objects.filter(user__id=sender_id).only('id','diamonds').first()

            sender_profile_obj.diamonds -= cost_diamonds
            sender_profile_obj.save(force_update=True)

            receiver_profile_obj.diamonds += cost_diamonds - vat_diamonds
            receiver_profile_obj.save(force_update=True)


            data = {
                'type': 'update_messenger_diamonds',
                'sender_id': sender_id,
                'sender_diamonds': sender_profile_obj.diamonds,
                'receiver_id': receiver_id,
                'receiver_diamonds': receiver_profile_obj.diamonds,
            }

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'live_streaming_livekit_streamings',
                {
                    'type': 'live_streaming', 
                    'message': data,
                }
            )

            track_chat_send_vat_obj =  ChatSendVatDiamonds.objects.first()
            if track_chat_send_vat_obj is None:
                track_chat_send_vat_obj = ChatSendVatDiamonds()
                track_chat_send_vat_obj.chat_vat_diamonds = vat_diamonds
                track_chat_send_vat_obj.save(force_insert=True)
            else:
                track_chat_send_vat_obj.chat_vat_diamonds += vat_diamonds
                track_chat_send_vat_obj.save(force_update=True)

        # Chat Message
        ChatMessage.objects.create(chat_id=chat_id,key=key,sender_id=sender_id,receiver_id=receiver_id,type=type,message=message)

        hasSenderLastMessage = LastChatMessage.objects.filter(chat_id=chat_id,user_id=sender_id).exists()
        hasReceiverLastMessage = LastChatMessage.objects.filter(chat_id=chat_id,user_id=receiver_id).exists()


        # Last Message
        if hasSenderLastMessage == True and hasReceiverLastMessage == True:
            sender_last_chat_obj = LastChatMessage.objects.filter(chat_id=chat_id,user_id=sender_id).first()
            receiver_last_chat_obj = LastChatMessage.objects.filter(chat_id=chat_id,user_id=receiver_id).first()

            sender_last_chat_obj.type = type
            sender_last_chat_obj.message = message
            sender_last_chat_obj.sender_id = sender_id
            sender_last_chat_obj.full_name = receiver_full_name
            sender_last_chat_obj.profile_image = receiver_image
            sender_last_chat_obj.datetime = timezone.now()

            receiver_last_chat_obj.type = type
            receiver_last_chat_obj.message = message
            receiver_last_chat_obj.sender_id = sender_id
            receiver_last_chat_obj.full_name = sender_full_name
            receiver_last_chat_obj.profile_image = sender_image
            receiver_last_chat_obj.datetime = timezone.now()

            LastChatMessage.objects.bulk_update([sender_last_chat_obj,receiver_last_chat_obj],fields=['type','message','full_name','profile_image','datetime'])

        elif hasSenderLastMessage == False and hasReceiverLastMessage == False:
            # Create

            sender_last_chat_obj = LastChatMessage()
            receiver_last_chat_obj = LastChatMessage()

            sender_last_chat_obj.chat_id = chat_id
            sender_last_chat_obj.key = key
            sender_last_chat_obj.user_id = sender_id
            sender_last_chat_obj.type = type
            sender_last_chat_obj.message = message
            sender_last_chat_obj.sender_id = sender_id
            sender_last_chat_obj.full_name = receiver_full_name
            sender_last_chat_obj.profile_image = receiver_image

            receiver_last_chat_obj.chat_id = chat_id
            receiver_last_chat_obj.key = key
            receiver_last_chat_obj.user_id = receiver_id
            receiver_last_chat_obj.type = type
            receiver_last_chat_obj.message = message
            receiver_last_chat_obj.sender_id = sender_id
            receiver_last_chat_obj.full_name = sender_full_name
            receiver_last_chat_obj.profile_image = sender_image

            LastChatMessage.objects.bulk_create([sender_last_chat_obj,receiver_last_chat_obj])
            
        elif hasSenderLastMessage == True and hasReceiverLastMessage == False:
            sender_last_chat_obj = LastChatMessage.objects.filter(chat_id=chat_id,user_id=sender_id).first()
            sender_last_chat_obj.type = type
            sender_last_chat_obj.message = message
            sender_last_chat_obj.sender_id = sender_id
            sender_last_chat_obj.full_name = receiver_full_name
            sender_last_chat_obj.profile_image = receiver_image
            sender_last_chat_obj.save(force_update=True)

            receiver_last_chat_obj = LastChatMessage()
            receiver_last_chat_obj.chat_id = chat_id
            receiver_last_chat_obj.key = key
            receiver_last_chat_obj.user_id = receiver_id
            receiver_last_chat_obj.type = type
            receiver_last_chat_obj.message = message
            receiver_last_chat_obj.sender_id = sender_id
            receiver_last_chat_obj.full_name = sender_full_name
            receiver_last_chat_obj.profile_image = sender_image
            receiver_last_chat_obj.save(force_insert=True)

        elif hasSenderLastMessage == False and hasReceiverLastMessage == True:    
            sender_last_chat_obj = LastChatMessage()
            sender_last_chat_obj.chat_id = chat_id
            sender_last_chat_obj.key = key
            sender_last_chat_obj.user_id = sender_id
            sender_last_chat_obj.type = type
            sender_last_chat_obj.message = message
            sender_last_chat_obj.sender_id = sender_id
            sender_last_chat_obj.full_name = receiver_full_name
            sender_last_chat_obj.profile_image = receiver_image
            sender_last_chat_obj.save(force_insert=True)

            receiver_last_chat_obj = LastChatMessage.objects.filter(chat_id=chat_id,user_id=receiver_id).first()
            receiver_last_chat_obj.type = type
            receiver_last_chat_obj.message = message
            receiver_last_chat_obj.sender_id = sender_id
            receiver_last_chat_obj.full_name = sender_full_name
            receiver_last_chat_obj.profile_image = sender_image
            receiver_last_chat_obj.save(force_update=True)

        # Notification
        payload_data = {
            "title": sender_full_name,
            "message": message,
            "image": sender_image,
            "peered_uid": f"{sender_id}",
            "peered_name": sender_full_name,
            "call_type": "",
            "event_type": "CHAT",
            "channel": chat_id,
        }

        device_token = None
        device_obj = FCMDeviceToken.objects.filter(user__id=receiver_id).only('token').first()
        if device_obj:
            device_token = device_obj.token

        if device_token is not None:
            firebase_client = FirebaseClient()
            firebase_client.send_single_fcm(registration_token=device_token,data=payload_data)
        
        return Response(status=HTTP_201_CREATED)

class ChatMessageDestroyApiView(CreateAPIView):
    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        action = data_obj.get('action',None)
        chat_id = data_obj.get('chat_id',"0")

        if action == 'last_message':
            user_id = data_obj.get('user_id',0)
            LastChatMessage.objects.filter(chat_id=chat_id,user_id=user_id).delete()
            return Response(status=HTTP_200_OK)
        elif action == 'one_message':
            message_id = data_obj.get('message_id',None)
            key = data_obj.get('key','0')

            if message_id is None:
                ChatMessage.objects.filter(chat_id=chat_id,key=key).delete()
            else:
                ChatMessage.objects.filter(id=message_id).delete()

            return Response(status=HTTP_200_OK)

        return Response(status=HTTP_204_NO_CONTENT)
    
class ChatBlockUpdateApiView(UpdateAPIView):
    authentication_classes = []
    permission_classes = []

    def update(self, request, *args, **kwargs):
        data_obj = request.data
        user_id = data_obj.get('user_id',0)
        chat_id = data_obj.get('chat_id',"0")

        is_blocked = False
        receiver_id = 0
        ids = str(chat_id).split("_")
        if int(ids[0]) == user_id:
            receiver_id = int(ids[1]) 
        else:
            receiver_id = int(ids[0]) 

        receiver_user_obj = User.objects.filter(id=receiver_id).only('id').first()

        if ChatBlock.objects.filter(user_id=user_id).exists():
            # Check on Existings Block Object
            if ChatBlock.objects.filter(user_id=user_id,blocks__in=[receiver_user_obj]).exists():
                chat_block_obj = ChatBlock.objects.filter(user_id=user_id).first()
                chat_block_obj.blocks.remove(receiver_user_obj)
                is_blocked = False
            else:
                chat_block_obj = ChatBlock.objects.filter(user_id=user_id).first()
                chat_block_obj.blocks.add(receiver_user_obj)
                is_blocked = True
        else:
            # Create new Block Object
            chat_block_obj = ChatBlock()
            chat_block_obj.user_id = user_id
            chat_block_obj.save(force_insert=True)
            chat_block_obj.blocks.add(receiver_user_obj)
            is_blocked = True

        channel_layer = get_channel_layer() 
                
        async_to_sync(channel_layer.group_send)(
            f'chat_room_{chat_id}',
            {
                'type': 'chat_room',  
                'message': {
                    'action': 'update_chat_block',
                    'is_blocked': is_blocked,
                    'blocked_by': user_id,
                }
            }
        )

        return Response(data={'is_blocked':is_blocked,'blocked_by': user_id,},status=HTTP_200_OK)
    
class ChatBlockListApiView(ListAPIView):
    authentication_classes = []
    permission_classes = []
    lookup_field = 'user_id'

    def list(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]

        block_list = []
        if ChatBlock.objects.filter(user_id=user_id).exists():
            chat_block_obj = ChatBlock.objects.filter(user_id=user_id).prefetch_related('blocks','blocks__profile').only('blocks',).first()
            blocks = chat_block_obj.blocks.all()
            if len(blocks) > 0:
                for block in blocks:
                    profile_obj = block.profile
                    data = {
                        "full_name": profile_obj.full_name,
                        "profile_image": get_profile_image(profile_obj),
                        "user_id": profile_obj.user.id,
                    }
                    block_list.append(data)

        return Response(data={'block_list':block_list,},status=HTTP_200_OK)
    

def get_profile_image(obj):
    if obj.profile_image:
        return f"{settings.BASE_URL}/media/{obj.profile_image}"
    return obj.photo_url
    

# {
#     "key": "13434",
#     "chat_id": "2_3",
#     "sender_id": 2,
#     "receiver_id": 3,
#     "diamonds": 10,
#     "type": "text",
#     "message": "message 3232",
#     "sender_image": "https://w7.pngwing.com/pngs/205/731/png-transparent-default-avatar-thumbnail.png",
#     "receiver_image": "https://png.pngtree.com/element_our/20200610/ourmid/pngtree-character-default-avatar-image_2237203.jpg",
#     "sender_full_name": "Than Aung Kyow",
#     "receiver_full_name": "Sun Wen"
# }