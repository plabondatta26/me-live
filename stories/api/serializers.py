from django.utils import timezone
from rest_framework import serializers
from profiles.api.serializers import ProfileSerializer
from stories.models import Story,CoverStory

class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = '__all__'
        # fields = ['id','user','caption','image','likes','views','created_datetime','expired_datetime',]

class CoverStorySerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    stories = serializers.SerializerMethodField()
    
    class Meta: 
        model = CoverStory
        fields = ['id','user','profile','stories','expired_datetime',]

    def get_stories(self,obj):
        present_datetime = timezone.now()
        return StorySerializer(instance=obj.stories.filter(expired_datetime__gte=present_datetime),many=True,context={"request": self._context['request']}).data

    def get_profile(self,obj):
        return ProfileSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data