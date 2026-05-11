from django.utils import timezone
from rest_framework.generics import (
    RetrieveAPIView,CreateAPIView,UpdateAPIView,
    ListAPIView, DestroyAPIView
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,HTTP_203_NON_AUTHORITATIVE_INFORMATION,HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from devices.models import UserDeviceInfo, UserDeviceBlocked
from .serializers import UserDeviceInfoSerializer, UserDeviceBlockedSerializer

class UserDeviceInfoUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user_obj = request.user
        data_obj = request.data
        device_name = data_obj.get('device_name',None)
        device_id = data_obj.get('device_id',None)
        entry_datetime = timezone.now()

        device_info_obj = UserDeviceInfo.objects.filter(device_id=device_id).first()
        if device_info_obj is None:
            device_info_obj = UserDeviceInfo()
            device_info_obj.device_id = device_id
        device_info_obj.user_id = user_obj.id
        device_info_obj.device_name = device_name 
        device_info_obj.entry_datetime = entry_datetime
        device_info_obj.save()

        return Response({'device_blocked':device_info_obj.blocked},status=HTTP_200_OK)

class SearchUserDeviceInfoListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'user_id'

    def list(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]

        user_devices_objs = UserDeviceInfo.objects.filter(user_id=user_id,blocked=False)
        user_devices_info_serializer = UserDeviceInfoSerializer(instance=user_devices_objs,many=True)

        return Response({'user_devices_info':user_devices_info_serializer.data,},status=HTTP_200_OK)

class UserDeviceBlockCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        user_id = data_obj.get('user_id',0)
        device_id = data_obj.get('device_id',None)

        user_obj = request.user
        profile_obj = user_obj.profile

        if profile_obj.is_moderator == False or user_id == user_obj.id:
            return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        user_device_info_obj = UserDeviceInfo.objects.filter(user_id=user_id,device_id=device_id).first()
        # user_device_info_obj = UserDeviceInfo.objects.filter(user_id=user_id,device_id=device_id,blocked=False).first()
        if user_device_info_obj is None:
            return Response(status=HTTP_204_NO_CONTENT)

        user_device_info_obj.blocked_moderator = user_obj
        blocked = True
        if user_device_info_obj.blocked == True:
            user_device_info_obj.blocked = False
            blocked = False
        else:
            user_device_info_obj.blocked = True
        user_device_info_obj.save(force_update=True)

        return Response({'blocked':blocked},status=HTTP_201_CREATED)
        
        # user_device_info_serializer = UserDeviceInfoSerializer(instance=user_devices_objs,)
        # return Response({'reseller_history':user_device_info_serializer.data,},status=HTTP_201_CREATED)

class UserDeviceBlockedHistoryListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user_obj = request.user

        user_blocked_devices_objs = UserDeviceBlocked.objects.filter(device_info__blocked_moderator=user_obj)
        user_blocked_devices_serializer = UserDeviceBlockedSerializer(instance=user_blocked_devices_objs,many=True)

        return Response({'user_blocked_devices':user_blocked_devices_serializer.data,},status=HTTP_200_OK)
