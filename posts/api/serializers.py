from rest_framework import serializers
from posts.models import Post,PostComment,PostImage,PostVideo
from profiles.api.serializers import ProfileSimpleSerializer

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
   

class PostNormalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id','likes']

# class PostSerializer(serializers.ModelSerializer):
#     images = serializers.SerializerMethodField()
#     video = serializers.SerializerMethodField()
#     comments = serializers.SerializerMethodField()

#     class Meta:
#         model = Post
#         fields = ['id','text','likes','images','video','comments','created_datetime','updated_datetime','created_date','updated_date',]

#     def get_images(self,obj):
#         if obj.page.type == VIDEO:
#             return []
#         return PostImageSerializer(instance=obj.images.all(),many=True,context={"request": self._context['request']}).data

#     def get_video(self,obj):
#         if obj.page.type == TEXT_AND_IMAGE:
#             return None
#         return PostVideoSerializer(instance=obj.video,context={"request": self._context['request']}).data

#     def get_comments(self,obj):
#         return PostCommentSerializer(instance=obj.comments.order_by('-id').all(),many=True,context={"request": self._context['request']}).data

class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = '__all__'

class PostVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVideo
        fields = '__all__'

class PostCommentNormalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ['id','likes']

class PostCommentSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    class Meta:
        model = PostComment
        fields = ['id','profile','text','likes','created_datetime','updated_datetime',]

    def get_profile(self,obj):
        return ProfileSimpleSerializer(instance=obj.user.profile,context={"request": self._context['request']}).data

