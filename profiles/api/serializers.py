from django.utils import timezone
from json import JSONEncoder
from datetime import date, datetime
from django.core.cache import cache

from rest_framework import serializers
from django.conf import settings
from profiles.models import Profile
from products.models import Level

from products.models import Level, PurchasedVipPackage, PurchasedVVipPackage, PurchasedStreamingJoiningGif, PurchasedPackageTheme
from accounts.models import User

class UserWithProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
 
    class Meta:
        model = User
        fields = ['id','profile',]

    def get_profile(self,obj):
        profile_cache = cache.get(f'profile_{obj.id}')
        if profile_cache is None:
            # profile_cache = ProfileSerializer(instance=obj.profile,context={"request": self._context['request']}).data
            # cache.set(f'profile_{obj.id}',profile_cache,timeout=60*60*24*30)
            profile_cache = ProfileSimpleSerializer(instance=obj.profile,).data
        else:
            profile_cache = {
                "id": profile_cache['id'],
                "user": {
                    "uid": profile_cache['user']['uid'],
                    "phone": profile_cache['user']['phone'],
                },
                "level": profile_cache['level'],
                "vvip_or_vip_preference": profile_cache['vvip_or_vip_preference'],
                "full_name": profile_cache['full_name'],
                "profile_image": profile_cache['profile_image'],
                "photo_url": profile_cache['photo_url'],
                "diamonds": profile_cache['diamonds'],
                "is_allow_video_live": profile_cache['is_allow_video_live'],
                "is_agent": profile_cache['is_agent'],
                "is_reseller": profile_cache['is_reseller'],
                "is_host": profile_cache['is_host'],
                "is_moderator": profile_cache['is_moderator'],
                "be_agent_datetime": profile_cache['be_agent_datetime'],
                "be_reseller_datetime": profile_cache['be_reseller_datetime'],
                "be_host_datetime": profile_cache['be_host_datetime'],
                "be_moderator_datetime": profile_cache['be_moderator_datetime'],
            }
        return profile_cache

class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    vvip_or_vip_preference = serializers.SerializerMethodField()
    streaming_joining = serializers.SerializerMethodField()
    package_theme = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    # cover_image = serializers.SerializerMethodField()

    # Must Sync with products.models ProfileSerializer
    class Meta:
        model = Profile
        fields = ['id','user','level','vvip_or_vip_preference','streaming_joining','package_theme','login_type','full_name','email','profile_image','photo_url','birthday','gender',
        'streaming_title','followers','blocks','diamonds','outgoing_diamonds',
        'is_allow_video_live','is_agent','is_reseller','is_host','is_moderator','be_agent_datetime','be_reseller_datetime','be_host_datetime', 'be_moderator_datetime',
        ]

    def get_user(self,obj):
        user_obj = obj.user
        return {
            'uid': user_obj.id,
            'phone': user_obj.phone 
        }

    def get_profile_image(self,obj):
        if obj.profile_image:
            return f"{settings.BASE_URL}/media/{obj.profile_image}"
        return obj.photo_url

    # def get_cover_image(self,obj):
    #     if obj.cover_image:
    #         return f"{settings.BASE_URL}/media/{obj.cover_image}"
    #     return None

    def get_level(self,obj):
        # outgoing_diamonds = 3500 
        outgoing_diamonds = obj.outgoing_diamonds
        level_obj = Level.objects.filter(diamonds__lte=outgoing_diamonds).last()
        if level_obj:
            frame_gif = ""
            if level_obj.frame_gif:
                frame_gif = f"{settings.BASE_URL}/media/{level_obj.frame_gif}"
            return {
                "id": level_obj.id,
                "level": level_obj.level,
                "diamonds": level_obj.diamonds,
                "frame_gif": frame_gif,
            }
        return None

    def get_vvip_or_vip_preference(self,obj):
        
        vvip = 0
        vip = 0
        rank = 0
        expired_datetime = None
        vvip_or_vip_gif = None
        purchased_vvip_package_obj = PurchasedVVipPackage.objects.filter(user=obj.user,expired_datetime__gte=timezone.now()).select_related('vvip_package').last()
        if purchased_vvip_package_obj:
            vvip = 90000 # Ninety thousands
            expired_datetime = purchased_vvip_package_obj.expired_datetime
            vvip_or_vip_gif = f"{settings.BASE_URL}/media/{purchased_vvip_package_obj.vvip_package.gif}" 
        else:
            purchased_vip_package_obj = PurchasedVipPackage.objects.filter(user=obj.user,expired_datetime__gte=timezone.now()).select_related('vip_package').last()
            if purchased_vip_package_obj:
                vip = 10000 # Ten thousands
                expired_datetime = purchased_vip_package_obj.expired_datetime
                vvip_or_vip_gif = f"{settings.BASE_URL}/media/{purchased_vip_package_obj.vip_package.gif}" 

        rank = vvip + vip
        if rank > 0:
            outgoing_diamonds = obj.outgoing_diamonds
            level_obj = Level.objects.filter(diamonds__lte=outgoing_diamonds).last()
            if level_obj:
                rank += level_obj.level
        json_data = {"rank": rank, "expired_datetime": expired_datetime, "vvip_or_vip_gif": vvip_or_vip_gif,}
        return DateTimeEncoder().encode(json_data)

    def get_streaming_joining(self,obj):
        present_datetime = timezone.now()
        purchased_streaming_joining_gif_objs = PurchasedStreamingJoiningGif.objects.filter(user=obj.user,expired_datetime__gte=present_datetime).select_related('joining_gif')

        expired_datetime = None
        purchased_joining_gif = None
        if purchased_streaming_joining_gif_objs:
            purchased_streaming_joining_gif_obj = purchased_streaming_joining_gif_objs.filter(active=True).first()
            if purchased_streaming_joining_gif_obj is None:
                purchased_streaming_joining_gif_obj = purchased_streaming_joining_gif_objs.first()
                purchased_streaming_joining_gif_obj.active = True
                purchased_streaming_joining_gif_obj.save()
            purchased_joining_gif = f"{settings.BASE_URL}/media/{purchased_streaming_joining_gif_obj.joining_gif.gif}" 
            expired_datetime = purchased_streaming_joining_gif_obj.expired_datetime

        json_data = {"joining_gif":purchased_joining_gif, "expired_datetime": expired_datetime, }
        return DateTimeEncoder().encode(json_data)

    def get_package_theme(self,obj):
        present_datetime = timezone.now()
        purchased_package_theme_objs = PurchasedPackageTheme.objects.filter(user=obj.user,expired_datetime__gte=present_datetime).select_related('package_theme')

        expired_datetime = None
        purchased_package_theme = None
        if purchased_package_theme_objs:
            purchased_package_theme_obj = purchased_package_theme_objs.filter(active=True).first()
            if purchased_package_theme_obj is None:
                purchased_package_theme_obj = purchased_package_theme_objs.first()
                purchased_package_theme_obj.active = True
                purchased_package_theme_obj.save()
            if purchased_package_theme_obj.package_theme is not None:
                purchased_package_theme = f"{settings.BASE_URL}/media/{purchased_package_theme_obj.package_theme.gif}" 
            else:
                purchased_package_theme = f"{settings.BASE_URL}/media/{purchased_package_theme_obj.custom_theme_image}" 

            expired_datetime = purchased_package_theme_obj.expired_datetime

        json_data = {"theme_gif":purchased_package_theme, "expired_datetime": expired_datetime,}
        return DateTimeEncoder().encode(json_data)
       
class ProfileForUserInfoSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()
    vvip_or_vip_preference = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    # Must Sync with products.models ProfileSerializer
    class Meta:
        model = Profile
        fields = ['id','level','vvip_or_vip_preference','full_name','profile_image', 'diamonds','outgoing_diamonds',
        'is_allow_video_live','is_agent','is_reseller','is_host','is_moderator',
        ]

    def get_profile_image(self,obj):
        if obj.profile_image:
            return f"{settings.BASE_URL}/media/{obj.profile_image}"
        return obj.photo_url
    
    def get_level(self,obj):
        # outgoing_diamonds = 3500 
        outgoing_diamonds = obj.outgoing_diamonds
        level_obj = Level.objects.filter(diamonds__lte=outgoing_diamonds).last()
        if level_obj:
            frame_gif = ""
            if level_obj.frame_gif:
                frame_gif = f"{settings.BASE_URL}/media/{level_obj.frame_gif}"
            return {
                "id": level_obj.id,
                "level": level_obj.level,
                "diamonds": level_obj.diamonds,
                "frame_gif": frame_gif,
            }
        return None

    def get_vvip_or_vip_preference(self,obj):
        
        vvip = 0
        vip = 0
        rank = 0
        expired_datetime = None
        vvip_or_vip_gif = None
        purchased_vvip_package_obj = PurchasedVVipPackage.objects.filter(user=obj.user,expired_datetime__gte=timezone.now()).select_related('vvip_package').last()
        if purchased_vvip_package_obj:
            vvip = 90000 # Ninety thousands
            expired_datetime = purchased_vvip_package_obj.expired_datetime
            vvip_or_vip_gif = f"{settings.BASE_URL}/media/{purchased_vvip_package_obj.vvip_package.gif}" 
        else:
            purchased_vip_package_obj = PurchasedVipPackage.objects.filter(user=obj.user,expired_datetime__gte=timezone.now()).select_related('vip_package').last()
            if purchased_vip_package_obj:
                vip = 10000 # Ten thousands
                expired_datetime = purchased_vip_package_obj.expired_datetime
                vvip_or_vip_gif = f"{settings.BASE_URL}/media/{purchased_vip_package_obj.vip_package.gif}" 

        rank = vvip + vip
        if rank > 0:
            outgoing_diamonds = obj.outgoing_diamonds
            level_obj = Level.objects.filter(diamonds__lte=outgoing_diamonds).last()
            if level_obj:
                rank += level_obj.level
        json_data = {"rank": rank,"expired_datetime": expired_datetime, "vvip_or_vip_gif": vvip_or_vip_gif,}
        return json_data

class ProfileSimpleSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id','user','login_type','full_name','email','profile_image','photo_url','streaming_title','followers','blocks','diamonds','outgoing_diamonds',
        'is_allow_video_live','is_agent','is_reseller','is_host','is_moderator','be_agent_datetime','be_reseller_datetime','be_host_datetime', 'be_moderator_datetime',
        ]

    def get_profile_image(self,obj):
        if obj.profile_image:
            return f"{settings.BASE_URL}/media/{obj.profile_image}"
        return obj.photo_url

    def get_user(self,obj):
        user_obj = obj.user
        return {
            'uid': user_obj.id,
            'phone': user_obj.phone 
        }

class ProfileFollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['followers']

class ProfileBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['blocks']

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        
