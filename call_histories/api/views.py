from rest_framework.generics import (
    RetrieveAPIView,CreateAPIView,UpdateAPIView,
    ListAPIView, DestroyAPIView
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,HTTP_203_NON_AUTHORITATIVE_INFORMATION,HTTP_204_NO_CONTENT,
    HTTP_207_MULTI_STATUS,HTTP_226_IM_USED,HTTP_208_ALREADY_REPORTED,HTTP_202_ACCEPTED,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .constants import *
from .serializers import CallHistorySerializer
from call_histories.models import CallHistory
from accounts.models import User

class CallHistoryListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user_obj = request.user
        call_histories_objs = CallHistory.objects.filter(user=user_obj)
        
        serializer_call_histories = CallHistorySerializer(instance=call_histories_objs,many=True,context={"request": request})
        return Response({'call_histories':serializer_call_histories.data}, status=HTTP_200_OK)

class CallHistoryCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user_obj = request.user
        data_obj = request.data

        type = data_obj.get('type',None)
        call_type = data_obj.get('call_type',None)

        receiver_uid = data_obj.get('receiver_uid',0)

        receiver_obj = User.objects.filter(id=receiver_uid).first()


        if type is None or receiver_obj is None or call_type is None:
            return Response({},status=HTTP_204_NO_CONTENT)

        caller_history_obj = CallHistory()
        receiver_history_obj = CallHistory()

        if type == RECEIVED_CALL:
    		# Owner state is OutGoing Call, receiver state is InComing Call
            caller_history_obj.user = user_obj
            caller_history_obj.call_type = call_type
            caller_history_obj.is_outgoing_call = True
            caller_history_obj.peer_user = receiver_obj
            caller_history_obj.save()

            receiver_history_obj.user = receiver_obj
            receiver_history_obj.call_type = call_type
            receiver_history_obj.is_incoming_call = True
            receiver_history_obj.peer_user = user_obj
            receiver_history_obj.save()

        elif type == MISSED_CALL:
    		# Owner state is OutGoing Call, receiver state is Missed Call
            caller_history_obj.user = user_obj
            caller_history_obj.call_type = call_type
            caller_history_obj.is_outgoing_call = True
            caller_history_obj.peer_user = receiver_obj
            caller_history_obj.save()

            receiver_history_obj.user = receiver_obj
            receiver_history_obj.call_type = call_type
            receiver_history_obj.is_missed_call = True
            receiver_history_obj.peer_user = user_obj
            receiver_history_obj.save()

        return Response(status=HTTP_201_CREATED)