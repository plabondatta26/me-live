import json
from django.core.cache import cache
from rest_framework import serializers
from livekit_stuffs.models import (
    LiveRoom
    )
from products.models import Level
from profiles.models import Profile
from profiles.api.serializers import ProfileSerializer

class LiveRoomSerializer(serializers.ModelSerializer):
    owner_profile = serializers.SerializerMethodField()
    group_caller_ids = serializers.SerializerMethodField()

    class Meta:
        model = LiveRoom
        fields = ['id','channel_id','title','is_pk','is_video','is_locked','allow_send','cm_flt_nm','owner_profile','group_caller_ids','reacts','viewers_count','locked_datetime','created_datetime',
                ]
        
    def get_owner_profile(self,obj):
        profile_cache = cache.get(f'profile_{obj.channel_id}')
        if profile_cache is None:
            # profile_obj = Profile.objects.filter(user__id=obj.channel_id).first()
            profile_obj = Profile.objects.filter(user__id=obj.channel_id).select_related('user').first()
            if profile_obj:
                serializer_profile = ProfileSerializer(instance=profile_obj)
                profile_cache = serializer_profile.data
                cache.set(f'profile_{obj.channel_id}',profile_cache,timeout=60*60*24*30)

        try:
            profile_cache['vvip_or_vip_preference'] = json.loads(profile_cache['vvip_or_vip_preference'])
        except:
            pass

        try:
            profile_cache['package_theme'] = json.loads(profile_cache['package_theme'])
        except:
            pass

        profile_image = profile_cache['profile_image']
        if profile_image is None:
            profile_image = profile_cache['photo_url']

        # level_number = 0
        # if profile_cache['level'] is not None:
        #     level_number = profile_cache['level']['level']

        vvip_vip_rank = 0
        vvip_or_vip_gif = None 
        if profile_cache['vvip_or_vip_preference'] is not None:
            vvip_vip_rank = profile_cache['vvip_or_vip_preference']['rank']
            vvip_or_vip_gif = profile_cache['vvip_or_vip_preference']['vvip_or_vip_gif']

        level_no = 0
        if profile_cache['level'] is not None:
            level_no = profile_cache['level']['level']


        designation = 'user'
        if profile_cache['is_agent'] == True:
            designation = 'agent'
        elif profile_cache['is_reseller'] == True:
            designation = 'reseller'
        elif profile_cache['is_host'] == True:
            designation = 'host'
        elif profile_cache['is_moderator'] == True:
            designation = 'modarator'

        profile_cache = {
            'uid': profile_cache['user']['uid'],
            'full_name': profile_cache['full_name'],
            'profile_image': profile_image,
            'vvip_or_vip_gif': vvip_or_vip_gif,
            'theme_gif': profile_cache['package_theme']['theme_gif'],
            'diamonds': profile_cache['diamonds'],
            'ranking': vvip_vip_rank,
            'level_no': level_no,
            'blocks': profile_cache['blocks'],
            'designation': designation,
        }

        return profile_cache

    def get_group_caller_ids(self,obj):
        return json.loads(obj.group_caller_ids)
    