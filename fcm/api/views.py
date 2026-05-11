from rest_framework.generics import (
    CreateAPIView,UpdateAPIView
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .functions import get_token_by_user, get_token_by_user_to_send_push_call, register_device,update_token,update_peer_user
from accounts.models import User
from livekit_stuffs.api.firebase_client import FirebaseClient


class RegisterDeviceCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data_obj = request.data

        token = data_obj.get('token',None)
        user = request.user

        result = register_device(user,token)
        response = {
            'error': True,
            'response': 'Invalid Request...',
        }
        if result == 0:
            response['error'] = False
            response['message'] = 'Device registered successfully'
        elif result == 2:
            response['error'] = True
            response['message'] = 'Device already registered'
        else:
            response['error'] = True
            response['message'] = 'Device not registered'

        return Response(response,status=HTTP_201_CREATED)

class UserTokenUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        data_obj = request.data

        user = request.user
        token = data_obj.get('token',None)

        result = update_token(user,token)

        return Response({'response':result},status=HTTP_200_OK)

class PeerDeviceUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        data_obj = request.data

        user = request.user
        peer_user_id = data_obj.get('peer_user_id',None)
        
        peer_user = User.objects.filter(id=peer_user_id).first()
        if peer_user is None:
            return Response(status=HTTP_204_NO_CONTENT)

        result = update_peer_user(user,peer_user) 

        return Response({'response':result},status=HTTP_200_OK)

class SinglePushCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data_obj = request.data

        # print(data_obj)

        title = data_obj.get('title',None)
        message = data_obj.get('message',None)
        receiver_uid = data_obj.get('receiver_uid',None)
        image = data_obj.get('image',None)
        event_type = data_obj.get('event_type',"")
        channel = data_obj.get('channel',"")
        user = request.user
        # Sender data
        peered_uid = user.id
        peered_name = user.profile.full_name

        if title is not None and message is not None and receiver_uid is not None:
            receiver_user = User.objects.filter(id=receiver_uid).first()
            if receiver_user is None:
                return Response(status=HTTP_204_NO_CONTENT)
            # title, message, image, peeredUid, peeredName, callType
            # push_obj = None
            # if image is not None:
            #     push_obj = Push(title,message,image,None,None,None)
            # else:
            #     push_obj = Push(title,message,None,None,None,None)

            # push_notification_obj = push_obj.get_push()

            # payload_data = {
            #     'data': {
            #         'title': title,
            #         'message': message,
            #         'image': image,
            #         'peered_uid': peered_uid,
            #         'peered_name': peered_name,
            #         'call_type': '',
            #         'event_type':event_type,
            #         'channel': channel,
            #     }
            # }
            if image is None:
                image = ""
            payload_data = {
                    "title": title,
                    "message": message,
                    "image": image,
                    "peered_uid": f"{peered_uid}",
                    "peered_name": peered_name,
                    "call_type": "",
                    "event_type":event_type,
                    "channel": channel,
            }
            device_token = get_token_by_user(receiver_user,user)
            # firebase_obj = Firebase()

            # # firebase_obj.send(device_token,push_notification_obj)
            # firebase_obj.send(device_token,payload_data)

            firebase_client = FirebaseClient()
            firebase_client.send_single_fcm(registration_token=device_token,data=payload_data)
            return Response(status=HTTP_201_CREATED)

        else:
            return Response(status=HTTP_204_NO_CONTENT)

class SinglePushForCallingCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        user = request.user

        title = data_obj.get('title',None)
        message = data_obj.get('message',None)
        image = data_obj.get('image',None)
        receiver_uid = data_obj.get('receiver_uid',None)
        # Sender data
        peered_uid = user.id
        peered_name = user.profile.full_name
        call_type = data_obj.get('call_type',None)
        # Event type
        event_type = data_obj.get('event_type','')
        channel = data_obj.get('channel','')

        if title is not None and message is not None and receiver_uid is not None:
            receiver_user = User.objects.filter(id=receiver_uid).first()
            if receiver_user is None:
                return Response(status=HTTP_204_NO_CONTENT)
            # title, message, image, peeredUid, peeredName, callType
            # push_obj = None
            # if image is not None:
            #     push_obj = Push(title,message,image,peered_uid,peered_name,call_type)
            # else:
            #     push_obj = Push(title,message,None,peered_uid,peered_name,call_type)

            # push_notification_obj = push_obj.get_push()
            payload_data = {
                'data': {
                    'title': title,
                    'message': message,
                    'image': image,
                    'peered_uid': peered_uid,
                    'peered_name': peered_name,
                    'call_type': call_type,
                    'event_type':event_type,
                    'channel': channel,
                }
            }
            device_token = get_token_by_user_to_send_push_call(receiver_user)

            firebase_obj = Firebase()

            # firebase_obj.send(device_token,push_notification_obj)
            firebase_obj.send(device_token,payload_data)

            return Response(status=HTTP_201_CREATED)
        else:
            return Response(status=HTTP_204_NO_CONTENT)

# class NotifyGroupMembersCreateApiView(CreateAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         data_obj = request.data
#         user = request.user
#         members_str = data_obj.get('members_str',None)
#         title = data_obj.get('title',None)
#         message = data_obj.get('message',None)
#         group_id = data_obj.get('group_id',None)
#         admin_id = data_obj.get('admin_id',0)

#         if members_str is not None:
#             notify_to_group_members.delay(uid=user.id,members_str=members_str,title=title,message=message,group_id=group_id,admin_id=admin_id)

#         return Response(status=HTTP_201_CREATED)