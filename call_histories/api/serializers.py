from rest_framework import serializers
from call_histories.models import CallHistory
from profiles.api.serializers import ProfileSerializer

class CallHistorySerializer(serializers.ModelSerializer):
    peer_user_profile = serializers.SerializerMethodField()
    class Meta:
        model = CallHistory
        fields = ['id','user','peer_user_profile','call_type','is_outgoing_call','is_incoming_call','is_missed_call','datetime']

    def get_peer_user_profile(self,obj):
        peer_user_obj = obj.peer_user.profile
        return ProfileSerializer(instance=peer_user_obj,context={"request": self._context['request']}).data
