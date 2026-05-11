from django.conf import settings
from rest_framework import serializers
from products.models import (
    PurchasedVVipPackage, PurchasedVipPackage, StreamingJoiningGif, PurchasedStreamingJoiningGif,
    DiamondPackage, VVipPackage, VVipPackageOrderingInfo, VipPackage, VipPackageOrderingInfo,WithdrawPackage, NormalGift,AnimatedGift,Level,
    PackageTheme, PurchasedPackageTheme, YouTubeVideo,
    )

class StreamingJoiningGifSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamingJoiningGif
        fields = '__all__'

class PurchasedStreamingJoiningGifSerializer(serializers.ModelSerializer):
    joining_gif = serializers.SerializerMethodField()
   
    class Meta:
        model = PurchasedStreamingJoiningGif
        fields = ['id','user','joining_gif','active','purchased_datetime','expired_datetime']

    def get_joining_gif(self,obj):
        joining_gif_obj = obj.joining_gif
        return StreamingJoiningGifSerializer(instance=joining_gif_obj,context={"request": self._context['request']}).data

class PackageThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageTheme
        fields = '__all__'

class PurchasedPackageThemeSerializer(serializers.ModelSerializer):
    package_theme = serializers.SerializerMethodField()
   
    class Meta:
        model = PurchasedPackageTheme
        fields = ['id','user','package_theme','custom_theme_image','active','purchased_datetime','expired_datetime']

    def get_package_theme(self,obj):
        package_theme_obj = obj.package_theme
        if package_theme_obj is None:
            return None
        return PackageThemeSerializer(instance=package_theme_obj,context={"request": self._context['request']}).data
    
class VipPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VipPackage
        fields = '__all__'

class PurchasedVipPackageSerializer(serializers.ModelSerializer):
    vip_package = serializers.SerializerMethodField()
   
    class Meta:
        model = PurchasedVipPackage
        fields = ['id','user','purchased_from','vip_package','purchased_datetime','expired_datetime']

    def get_vip_package(self,obj):
        vip_package_obj = obj.vip_package
        return VipPackageSerializer(instance=vip_package_obj,context={"request": self._context['request']}).data

class VipPackageOrderingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VipPackageOrderingInfo
        fields = '__all__'

class VVipPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VVipPackage
        fields = '__all__'

class PurchasedVVipPackageSerializer(serializers.ModelSerializer):
    vvip_package = serializers.SerializerMethodField()
   
    class Meta:
        model = PurchasedVVipPackage
        fields = ['id','user','purchased_from','vvip_package','purchased_datetime','expired_datetime']

    def get_vvip_package(self,obj):
        vvip_package_obj = obj.vvip_package
        return VVipPackageSerializer(instance=vvip_package_obj,context={"request": self._context['request']}).data

class VVipPackageOrderingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VVipPackageOrderingInfo
        fields = '__all__'

class DiamondPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiamondPackage
        fields = '__all__'

class WithdrawPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawPackage
        fields = '__all__'

class NormalGiftSerializer(serializers.ModelSerializer):
    gift_image = serializers.SerializerMethodField()
    class Meta:
        model = NormalGift
        # fields = '__all__' 
        fields = ['id','gift_image','diamonds','vat']

    def get_gift_image(self,obj):
        return f"{settings.BASE_URL}/media/{obj.gift_image}"

class AnimatedGiftSerializer(serializers.ModelSerializer):
    gif = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()
    class Meta:
        model = AnimatedGift
        # fields = '__all__'
        fields = ['id','gif','audio','diamonds','vat']

    def get_gif(self,obj):
        return f"{settings.BASE_URL}/media/{obj.gif}"

    def get_audio(self,obj):
        if obj.audio:
            return f"{settings.BASE_URL}/media/{obj.audio}"
        return None

class LevelSerializer(serializers.ModelSerializer):
    frame_gif = serializers.SerializerMethodField()
    class Meta:
        model = Level
        # fields = '__all__'
        fields = ['id','level','diamonds','frame_gif']

    def get_frame_gif(self,obj):
        if obj.frame_gif:
            return f"{settings.BASE_URL}/media/{obj.frame_gif}"
        return None
        
class YouTubeVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = YouTubeVideo
        fields = '__all__'
