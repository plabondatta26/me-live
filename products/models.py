import uuid
import os 
from django.core.cache import cache
from json import JSONEncoder
from datetime import date, datetime
from django.utils import timezone
from django.db import models
from accounts.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver 
from django.conf import settings
from rest_framework import serializers

# CKEditor
from ckeditor.fields import RichTextField
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from profiles.models import Profile

def level_frame_gif_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/level_frame_gifs/',filename) 

def streaming_joining_gif_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/streaming_joining_gifs/',filename) 

def package_theme_gif_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/package_theme_gifs/',filename) 

def package_theme_custom_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/package_theme_custom/',filename) 

def normal_gift_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/gifts/normal_gifts/',filename) 

def animated_gift_gif_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/gifts/animated_gift_gifs/',filename) 

def animated_gift_audio_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/gifts/animated_gift_audios/',filename) 

def vip_gif_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/vip_gifs/',filename) 

def vvip_gif_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('products/vvip_gifs/',filename) 

class YouTubeVideo(models.Model):
    title = models.CharField(max_length=250)
    thumbnails = models.URLField(max_length=250)
    video_id = models.CharField(max_length=50)
    created_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} > {self.created_datetime}'

class StreamingJoiningGif(models.Model): 
    gif = models.ImageField(upload_to=streaming_joining_gif_path,)
    diamonds = models.IntegerField(default=0)    

    days = models.IntegerField(verbose_name='Validity Days',default=0)

    def save(self, *args, **kwargs):
        try:
            cache.delete('joining_gif_list')
        except:
            pass
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['diamonds']

    def __str__(self):
        return f'{self.diamonds} diamonds > {self.days} days'

class PurchasedStreamingJoiningGif(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    joining_gif = models.ForeignKey(StreamingJoiningGif, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    
    purchased_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,)
    expired_datetime = models.DateTimeField(auto_now=False,auto_now_add=False)

    class Meta:
        ordering = ['-purchased_datetime']

    def __str__(self):
        return f'{self.user.profile.full_name} > Purchased on : {self.purchased_datetime} > Expired on : {self.expired_datetime}'

class PackageTheme(models.Model): 
    gif = models.ImageField(upload_to=package_theme_gif_path,)
    diamonds = models.IntegerField(default=0)    

    days = models.IntegerField(verbose_name='Validity Days',default=0)

    def save(self, *args, **kwargs):
        try:
            cache.delete('package_theme_list')
        except:
            pass
        super().save(*args, **kwargs)
 

    class Meta:
        ordering = ['diamonds']

    def __str__(self):
        return f'{self.diamonds} diamonds > {self.days} days'

class PurchasedPackageTheme(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    package_theme = models.ForeignKey(PackageTheme, on_delete=models.CASCADE,blank=True,null=True)
    custom_theme_image = models.ImageField(upload_to=package_theme_custom_path,blank=True,null=True)
    active = models.BooleanField(default=False)
    
    purchased_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,)
    expired_datetime = models.DateTimeField(auto_now=False,auto_now_add=False)

    class Meta:
        ordering = ['-purchased_datetime']

    def __str__(self):
        return f'{self.user.profile.full_name} > Purchased on : {self.purchased_datetime} > Expired on : {self.expired_datetime}'

class VipPackage(models.Model): 
    gif = models.ImageField(upload_to=vip_gif_path,)
    price = models.IntegerField(default=0,help_text="BDT")    

    days = models.IntegerField(verbose_name='Validity Days',default=0)

    def save(self, *args, **kwargs):
        try:
            cache.delete('vip_package_list')
        except:
            pass
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f'{self.price} BDT > {self.days} days'

class PurchasedVipPackage(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    purchased_from = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True,null=True,related_name="vip_purchased_from") 

    vip_package = models.ForeignKey(VipPackage, on_delete=models.CASCADE)
    
    purchased_datetime = models.DateTimeField(auto_now_add=True,)
    expired_datetime = models.DateTimeField(auto_now=False,auto_now_add=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        updateProfileInGlobalWebsocket(self.user.profile)

    class Meta:
        ordering = ['-purchased_datetime']

    def __str__(self):
        return f'{self.user.profile.full_name} > Expired on : {self.expired_datetime}'

class VipPackageOrderingInfo(models.Model):
    context = RichTextField()

    def save(self, *args, **kwargs):
        try:
            cache.delete('vip_package_ordering_info')
        except:
            pass
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Vip Package Ordering Info'

    def __str__(self):
        return self.context

class VVipPackage(models.Model): 
    gif = models.ImageField(upload_to=vvip_gif_path,)
    price = models.IntegerField(default=0,help_text="BDT")    

    days = models.IntegerField(verbose_name='Validity Days',default=0)

    def save(self, *args, **kwargs):
        try:
            cache.delete('vvip_package_list')
        except:
            pass
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'V Vip Packages'
        ordering = ['price']

    def __str__(self):
        return f'{self.price} BDT > {self.days} days'

class PurchasedVVipPackage(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    purchased_from = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True,null=True,related_name="vvip_purchased_from") 

    vvip_package = models.ForeignKey(VVipPackage, on_delete=models.CASCADE)
    
    purchased_datetime = models.DateTimeField(auto_now_add=True,)
    expired_datetime = models.DateTimeField(auto_now=False,auto_now_add=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        updateProfileInGlobalWebsocket(self.user.profile)

    class Meta:
        verbose_name_plural = 'Purchased V Vip Packages'
        ordering = ['-purchased_datetime']

    def __str__(self):
        return f'{self.user.profile.full_name} > Expired on : {self.expired_datetime}'

class VVipPackageOrderingInfo(models.Model):
    context = RichTextField()

    def save(self, *args, **kwargs):
        try:
            cache.delete('vvip_package_ordering_info')
        except:
            pass
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'V Vip Package Ordering Info'

    def __str__(self):
        return self.context

class DiamondPackage(models.Model):
    diamonds = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=8,decimal_places=2,default=0.0)    
    vat = models.DecimalField(max_digits=6,decimal_places=2,default=0.0)    

    def save(self, *args, **kwargs):
        try:
            cache.delete('diamond_packages')
        except:
            pass
        super().save(*args, **kwargs) 

    class Meta:
        ordering = ['diamonds']

    def __str__(self):
        return f'{self.diamonds} diamonds > {self.price} BDT'

class WithdrawPackage(models.Model):
    diamonds = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=8,decimal_places=2,default=0.0)   

    def save(self, *args, **kwargs):
        try:
            cache.delete('withdraw_packages')
        except:
            pass
        super().save(*args, **kwargs) 

    class Meta:
        ordering = ['diamonds']

    def __str__(self):
        return f'{self.diamonds} diamonds > {self.price} BDT'

class NormalGift(models.Model): 
    gift_image = models.ImageField(upload_to=normal_gift_path,)
    diamonds = models.IntegerField(default=0)    
    vat = models.IntegerField(default=0)   

    def save(self, *args, **kwargs):
        try:
            cache.delete('normal_gifts')
        except:
            pass
        super().save(*args, **kwargs)
 

    class Meta:
        ordering = ['diamonds']

    def __str__(self):
        return f'{self.diamonds} diamonds > {self.vat} vat'

class AnimatedGift(models.Model): 
    gif = models.ImageField(upload_to=animated_gift_gif_path,)
    audio = models.FileField(upload_to=animated_gift_audio_path,blank=True,null=True)
    diamonds = models.IntegerField(default=0)   
    vat = models.IntegerField(default=0)   

    def save(self, *args, **kwargs):
        try:
            cache.delete('animated_gifts')
        except:
            pass
        super().save(*args, **kwargs)
 

    class Meta:
        ordering = ['diamonds']

    def __str__(self):
        return f'{self.diamonds} diamonds  > {self.vat} vat'

class Level(models.Model): 
    level = models.IntegerField(default=0)
    diamonds = models.IntegerField(default=0)    
    frame_gif = models.ImageField(upload_to=level_frame_gif_path,blank=True,null=True)

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f'L.V.{self.level} > {self.diamonds} diamonds'


@receiver(post_delete,sender=Level)
def level_submission_delete(sender,instance,**kwargs):
    instance.frame_gif.delete(False)

@receiver(post_delete,sender=StreamingJoiningGif)
def streaming_joining_gif_submission_delete(sender,instance,**kwargs):
    instance.gif.delete(False)

@receiver(post_delete,sender=PackageTheme)
def package_theme_submission_delete(sender,instance,**kwargs):
    instance.gif.delete(False)

@receiver(post_delete,sender=PurchasedPackageTheme)
def purchased_package_theme_submission_delete(sender,instance,**kwargs):
    try:
        instance.custom_theme_image.delete(False)
    except:
        pass

@receiver(post_delete,sender=NormalGift)
def normal_gift_submission_delete(sender,instance,**kwargs):
    instance.gift_image.delete(False)

@receiver(post_delete,sender=AnimatedGift)
def animated_gift_submission_delete(sender,instance,**kwargs):
    instance.gif.delete(False)
    instance.audio.delete(False)

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

    def get_cover_image(self,obj):
        if obj.cover_image:
            return f"{settings.BASE_URL}/media/{obj.cover_image}"
        return None

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

        json_data = {"joining_gif":purchased_joining_gif, "expired_datetime": expired_datetime,}
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

        json_data = {"theme_gif":purchased_package_theme, "expired_datetime": expired_datetime,}
        return DateTimeEncoder().encode(json_data)

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()

def updateProfileInGlobalWebsocket(profile_obj):
    profile_cache = ProfileSerializer(instance=profile_obj,).data
    cache.set(f'profile_{profile_obj.user.id}',profile_cache,timeout=60*60*24*2)
    profile_cache['type'] = 'load_profile'

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'live_streaming_livekit_streamings',
        {
            'type': 'live_streaming', 
            'message': profile_cache
        }
    )

# package_theme_gif