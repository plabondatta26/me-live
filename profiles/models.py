import uuid
import os 
from django.core.cache import cache
from django.db import models
from accounts.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver 
# from core.models import Visibility
# from core.utils import unique_slug_generator

def profile_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('profiles/profile_images/',filename) 

def cover_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('profiles/cover_images/',filename) 

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    login_type = models.CharField(max_length=20,blank=True,null=True)
    uid = models.CharField(max_length=50,blank=True,null=True)
    full_name = models.CharField(max_length=200)
    # Custom Slug
    # slug = models.CharField(max_length=250,unique=True,blank=True,null=True)
    email = models.EmailField(max_length=250,blank=True,null=True)
    profile_image   = models.ImageField(upload_to=profile_image_path, blank=True, null=True)
    # cover_image   = models.ImageField(upload_to=cover_image_path, blank=True, null=True)
    photo_url = models.CharField(max_length=250,blank=True,null=True)
    birthday = models.DateField(auto_now=False,auto_now_add=False,blank=True,null=True)
    gender = models.CharField(max_length=20,blank=True,null=True,help_text='male , female or others')

    # # Country(isoCode: 'BD', iso3Code: 'BGD', phoneCode: '880', name: 'Bangladesh')
    # phone_code = models.CharField(max_length=10,help_text="E.g. 880 excluding + ( i.e. 880 not +880 )",blank=True,null=True)
    # password = models.CharField(max_length=50,help_text='(Must match with User table)',blank=True,null=True)
    # reset_password = models.CharField(max_length=50,blank=True,null=True,help_text="Password must contain at least 8 characters.")
    
    # Streaming stuffs
    streaming_title = models.CharField(max_length=200,blank=True,null=True)
    followers = models.ManyToManyField(User,related_name='streaming_followers',blank=True)
    blocks = models.ManyToManyField(User,related_name='streaming_blocks',blank=True)
    diamonds = models.BigIntegerField(default=0,help_text='Present diamonds')
    outgoing_diamonds = models.BigIntegerField(default=0,help_text='Outgoing diamonds')
    # gift_diamonds = models.BigIntegerField(default=0, help_text='Total diamonds')
    # converted_coins = models.BigIntegerField(default=0,help_text='Converted coins')
    # loves = models.IntegerField(default=0)

    # Business Stuffs
    is_allow_video_live = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    is_reseller = models.BooleanField(default=False)
    is_host = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)

    be_agent_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True,)
    be_reseller_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True,)
    be_host_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True,)
    be_moderator_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True,)

    last_notification_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True,)

    # Date Only
    registered_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True,blank=True,null=True)

    def save(self, *args, **kwargs):        
        super().save(*args, **kwargs)
        uid = self.user.id
        profile_cache = cache.get(f'profile_{uid}')
        if profile_cache is not None:
            profile_cache['full_name'] = self.full_name
            profile_cache['diamonds'] = self.diamonds
            profile_cache['outgoing_diamonds'] = self.outgoing_diamonds
            profile_cache['is_allow_video_live'] = self.is_allow_video_live
            profile_cache['is_agent'] = self.is_agent
            profile_cache['is_reseller'] = self.is_reseller
            profile_cache['is_host'] = self.is_host
            profile_cache['is_moderator'] = self.is_moderator

            cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*2)

    def __str__(self):
        return self.full_name

@receiver(post_delete,sender=Profile)
def profile_submission_delete(sender,instance,**kwargs):
    instance.profile_image.delete(False)
    # instance.cover_image.delete(False)

# def profile_pre_save_receiver(sender,instance, *args, **kwargs):
#     if not instance.slug:
#         title = instance.full_name.lower()
#         words = title.split(' ')
#         temp = ''
#         for word in words:
#             if word.strip() != '':
#                 word_separation = word.split('-')
#                 inner_temp = ''
#                 for x in word_separation:
#                     if x.strip() != '':
#                         if inner_temp != '':
#                             inner_temp += f"-{x.strip()}"
#                         else:
#                             inner_temp += x.strip()
#                 if inner_temp != '':
#                     if temp != '':
#                         temp += f"-{inner_temp}"
#                     else:
#                         temp += inner_temp
#         # Checking for existing slug
#         profile_objs = Profile.objects.filter(slug=temp)
#         if profile_objs.exists():
#             temp += f"-{profile_objs.count()+1}"
#         instance.slug = temp

# pre_save.connect(profile_pre_save_receiver, sender=Profile)
