from rest_framework import serializers
from devices.models import (
    UserDeviceInfo, UserDeviceBlocked
    )

class UserDeviceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeviceInfo
        fields = '__all__'

class UserDeviceBlockedSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeviceBlocked
        fields = '__all__'
 