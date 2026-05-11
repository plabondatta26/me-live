from rest_framework.generics import (
    RetrieveAPIView,CreateAPIView,
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_226_IM_USED, 
    HTTP_208_ALREADY_REPORTED,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from refer_bonus.models import ReferBonusAmount, ReferHistory
from accounts.models import User
from tracking.models import ReferBonusDiamonds
from devices.models import UserDeviceInfo
from .serializers import (
    ReferBonusAmountSerializer,ReferHistorySerializer,
    )

class ReferHistoryRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'device_id'

    def retrieve(self, request, *args, **kwargs):
        device_id = self.kwargs[self.lookup_field]

        data = {
            'refer_history': None,
            'refer_bonus_amont': None,
        }
        refer_history_obj = ReferHistory.objects.filter(device_id=device_id).first()
        if refer_history_obj:
            serializer_refer_history = ReferHistorySerializer(instance=refer_history_obj)
            data['refer_history'] = serializer_refer_history.data
        else:
            refer_bonus_amount_obj = ReferBonusAmount.objects.first()
            serializer_refer_bonus_amont = ReferBonusAmountSerializer(instance=refer_bonus_amount_obj)
            data['refer_bonus_amont'] = serializer_refer_bonus_amont.data

        return Response({'my_refer':data,},status=HTTP_200_OK)

class ReferBonusCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'device_id'

    def post(self, request, *args, **kwargs):
        # # Temporarily blocking Refer system
        # return Response(status=HTTP_204_NO_CONTENT)
        
        device_id = self.kwargs[self.lookup_field]
        data_obj = request.data
        user = request.user
        refered_uid = data_obj.get('refered_uid',0)

        refer_history_obj = ReferHistory.objects.filter(device_id=device_id).first()
        if refer_history_obj:
            return Response(status=HTTP_226_IM_USED)
        device_info_obj = UserDeviceInfo.objects.filter(device_id=device_id).first()
        if device_info_obj is None:
            return Response(status=HTTP_204_NO_CONTENT)
        refer_bonus_amount_obj = ReferBonusAmount.objects.first()
        if refer_bonus_amount_obj is None:
            return Response(status=HTTP_204_NO_CONTENT)
        refered_user_obj = User.objects.filter(id=refered_uid).first()
        if refered_user_obj is None:
            return Response(status=HTTP_208_ALREADY_REPORTED)
        refered_user_obj.profile.diamonds += refer_bonus_amount_obj.diamonds
        refered_user_obj.profile.save()

        refer_history_obj = ReferHistory()
        refer_history_obj.device_info = device_info_obj
        refer_history_obj.refered_uid = refered_uid
        refer_history_obj.referer_uid = user.id
        refer_history_obj.device_name = device_info_obj.device_name
        refer_history_obj.device_id = device_id
        refer_history_obj.diamonds = refer_bonus_amount_obj.diamonds
        refer_history_obj.save()
        serializer_refer_history = ReferHistorySerializer(instance=refer_history_obj)

        tracking_refer_bonus_diamonds_obj = ReferBonusDiamonds.objects.first()
        if tracking_refer_bonus_diamonds_obj is None:
            tracking_refer_bonus_diamonds_obj = ReferBonusDiamonds()
            tracking_refer_bonus_diamonds_obj.total_diamonds = refer_bonus_amount_obj.diamonds
        else:
            tracking_refer_bonus_diamonds_obj.total_diamonds += refer_bonus_amount_obj.diamonds

        tracking_refer_bonus_diamonds_obj.save()

        return Response({'refer_history':serializer_refer_history.data},status=HTTP_201_CREATED)

