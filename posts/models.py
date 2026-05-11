import uuid
import os
import json
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver 
from django.utils import timezone
from django.conf import settings
from accounts.models import User
from profiles.models import Profile
from me_live.utils.utils import delete_video_files_or_directories
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import serializers

def post_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('posts/post_images/',filename) 

def post_video_path(instance, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = f'{name}-{uuid.uuid4()}.{ext}'
    return os.path.join('posts/videos/',filename)

def post_video_thumbnail_path(instance, filename):
    ext = filename.split('.')[-1]
    name = filename.split('.')[0]
    filename = f'{name}-{uuid.uuid4()}.{ext}'
    return os.path.join('posts/videos/thumbnails/',filename)

class Post(models.Model): 
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    pending_text = models.TextField(blank=True,null=True)
    text = models.TextField(blank=True,null=True)
    likes = models.ManyToManyField(User,related_name='post_likes',blank=True)

    pending_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True)

    is_pending = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # # Restrict not to update again
        # if self.pending_datetime is None:
        #     return
        if self.is_pending == False:
            self.pending_datetime = None
            self.updated_datetime = timezone.now()
            if self.pending_text is not None:
                self.text = self.pending_text
                self.pending_text = None

        super(Post, self).save(*args, **kwargs)

        # if self.pending_datetime is None and self.is_pending == False:
        serializer_post = NewsfeedPostSerializer(instance=self,context={"request": None})
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'newsfeed',
            {'type': 'newsfeed', 'message': {'type':'post_added','post':json.dumps(serializer_post.data), }}
        )

    class Meta:
        ordering = ['-id',]

    def __str__(self):
        msg = ''
        if self.is_pending:
            msg = f"Pending > {str(self.pending_datetime).split('.')[0]}"
        else:
            msg = f"Approved > {str(self.updated_datetime).split('.')[0]}"

        return f'Post > {self.id}: {msg}' 

class PostImage(models.Model):
    post = models.ForeignKey(Post,on_delete=models.CASCADE,related_name='images')
    image   = models.ImageField(upload_to=post_image_path, )
    likes = models.ManyToManyField(User,related_name='image_likes')

    created_datetime = models.DateTimeField(auto_now_add=True)
    is_pending = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Images'
        ordering = ['-id']

    def __str__(self):
        return f'Post Image > {self.id}' 

class PostVideo(models.Model): 
    post = models.OneToOneField(Post,on_delete=models.CASCADE,related_name='video')

    video = models.FileField(upload_to=post_video_path,blank=True,null=True)
    hls_url = models.CharField(max_length=250,unique=True,blank=True,null=True)
    hls_path = models.CharField(max_length=250,unique=True,blank=True,null=True)
    hls_keys_path = models.CharField(max_length=250,unique=True,blank=True,null=True)

    video_thumbnail = models.ImageField(upload_to=post_video_thumbnail_path)

    likes = models.ManyToManyField(User,related_name='video_likes')

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True)

    is_pending = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Videos'
        ordering = ['-id']

    def __str__(self):
        if self.hls_url:
            return f'Post Video > {self.hls_url}' 
        else:
            return f"Post Video > {str(self.created_datetime).split('.')[0]}" 

class PostComment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    post = models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')
    text = models.TextField()
    likes = models.ManyToManyField(User,related_name='comment_likes')
    
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=False,auto_now_add=False,blank=True,null=True)

    class Meta:
        # verbose_name_plural = 'Comments'
        ordering = ['-id']

    def __str__(self):
        return f'Comment > {self.id}' 

@receiver(post_delete,sender=Post)
def post_submission_delete(sender,instance,**kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'newsfeed',
        {'type': 'newsfeed', 'message': {'type':'post_deleted','post_id': instance.id, }}
    )

@receiver(post_delete,sender=PostComment)
def post_comment_submission_delete(sender,instance,**kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'newsfeed',
        {'type': 'newsfeed', 'message': {'type':'comment_deleted','post_id': instance.post.id,'comment_id': instance.id, }}
    )

@receiver(post_delete,sender=PostImage)
def post_image_submission_delete(sender,instance,**kwargs):
    instance.image.delete(False)

@receiver(post_delete,sender=PostVideo)
def video_submission_delete(sender,instance,**kwargs):
    delete_video_files_or_directories(instance)
    instance.video_thumbnail.delete(False)

# Serializers needed to work with same model instance
class NewsfeedPostSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id','pending_text','text','likes','profile','images','video','comments','created_datetime','updated_datetime','pending_datetime','is_pending']

    def get_images(self,obj):
        post_image_objs = obj.images.filter(is_pending=False)
        if post_image_objs.count() > 0:
            return PostImageSerializer(instance=post_image_objs,many=True,context={"request": self._context['request']}).data
        return []

    def get_video(self,obj):
        try:
            if obj.video.is_pending == True:
                return None
            return PostVideoSerializer(instance=obj.video,context={"request": self._context['request']}).data
        except:
            return None

    def get_comments(self,obj):
        return PostCommentSerializer(instance=obj.comments.all(),many=True,context={"request": self._context['request']}).data

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data

class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = PostImage
        fields = ['id','post','image','likes','created_datetime','is_pending']

    def get_image(self,obj):
        return f'{settings.BASE_URL}/media/{obj.image}'

class PostVideoSerializer(serializers.ModelSerializer):
    video_thumbnail = serializers.SerializerMethodField()
    class Meta:
        model = PostVideo
        fields = ['id','post','video','hls_url','hls_path','hls_keys_path','video_thumbnail','likes','created_datetime','updated_datetime','is_pending']
    
    def get_video_thumbnail(self,obj):
        return f'{settings.BASE_URL}/media/{obj.video_thumbnail}'

class PostCommentSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    class Meta:
        model = PostComment
        fields = ['id','profile','text','likes','created_datetime','updated_datetime',]

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data

class ProfileSimpleSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id','user','full_name','profile_image',
        ]

    def get_user(self,obj):
        user_obj = obj.user
        return {
            'uid': user_obj.id,
            'phone': user_obj.phone 
        }

    def get_profile_image(self,obj):
        if obj.profile_image:
            return f'{settings.BASE_URL}/media/{obj.profile_image}'
        return obj.photo_url
