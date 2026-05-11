from rest_framework import serializers
from support.models import SupportPost, SupportPostImage, SupportPostReply
from profiles.api.serializers import ProfileSimpleSerializer

class SupportPostSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = SupportPost
        fields = ['id','text','profile','images','replies','created_datetime',]

    def get_images(self,obj):
        support_post_image_objs = obj.support_post_images.all() 
        if support_post_image_objs.count() > 0:
            return SupportPostImageSerializer(instance=support_post_image_objs,many=True,context={"request": self._context['request']}).data
        return []

    def get_replies(self,obj):
        return SupportPostReplySerializer(instance=obj.support_post_replies.all(),many=True,context={"request": self._context['request']}).data

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data

class SupportPostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportPostImage
        fields = '__all__'

class SupportPostReplySerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    class Meta:
        model = SupportPostReply
        fields = ['id','profile','text','created_datetime',]

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data

