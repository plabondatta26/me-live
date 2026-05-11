from rest_framework import serializers
from business.models import (
    Agent, AgentRechargedHistory, AgentRequest, HostRequest, Reseller, ResellerRequest, ResellerHistory,
    Moderator, ModeratorRequest,
    )
from accounts.models import User
from profiles.api.serializers import ProfileSimpleSerializer

class ModeratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moderator
        fields = '__all__'

class ModeratorRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeratorRequest
        fields = '__all__'

class AgentSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = ['id','user','profile','mobile_number','datetime','hosts','host_joining_dates']

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data

class AgentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRequest
        fields = '__all__'

class HostRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostRequest
        fields = '__all__'

class HostRequestDetailsSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = HostRequest
        fields = ['id','agent','profile','is_allow_video_live','is_approved','is_declined','datetime']

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data

class HostSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id','profile']

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.profile,context={"request": self._context['request']}).data


class ResellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reseller
        fields = '__all__'

class ResellerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResellerRequest
        fields = '__all__'

class ResellerHistorySerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = ResellerHistory
        fields = ['id','profile','reseller','recharged_diamonds','datetime']

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data

class AgentRechargedHistorySerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = AgentRechargedHistory
        fields = ['id','profile','agent','recharged_diamonds','datetime']

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data


