from rest_framework import serializers
from tracking.models import BroadcasterHistory

class BroadcasterHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BroadcasterHistory
        fields = "__all__"