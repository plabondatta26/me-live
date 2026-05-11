import os
import json
from django.conf import settings
from rest_framework.generics import (
    CreateAPIView,ListAPIView, DestroyAPIView
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,HTTP_203_NON_AUTHORITATIVE_INFORMATION,HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from posts.models import Post,PostImage,PostVideo,PostComment
from .serializers import (
    PostCommentSerializer ,NewsfeedPostSerializer,
    PostNormalSerializer, PostCommentNormalSerializer,
    )
from rest_framework.pagination import PageNumberPagination
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from me_live.utils.utils import compress 
from me_live.tasks import process_hls_encryption

from .constants import TEXT_AND_IMAGE, VIDEO, POST_LIKE, COMMENT_LIKE

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 15
    page_query_param = 'page'

class NewsfeedListApiView(ListAPIView):
    authentication_classes = []
    permission_classes = []
    queryset = Post.objects.filter(is_pending=False).order_by('-updated_datetime')
    serializer_class = NewsfeedPostSerializer
    pagination_class = StandardResultsSetPagination

    # cache requested url (in Seconds)
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        is_allow_post = False

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = {'posts':serializer.data,'is_allow_post': is_allow_post,}
            # return self.get_paginated_response(serializer.data)
            return self.get_paginated_response(data)


        serializer = self.get_serializer(queryset, many=True)
        return Response({'posts':serializer.data,'is_allow_post': is_allow_post,})

# class NewsfeedListApiView(ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = NewsfeedPostSerializer

#     def get_queryset(self):
#         return Post.objects.filter(is_pending=False).order_by('-updated_datetime')[:20]

#     def list(self, request, *args, **kwargs):
#         post_queryset = self.filter_queryset(self.get_queryset())

#         serializer_post_objs = self.get_serializer(post_queryset, many=True)
#         return Response({'posts':serializer_post_objs.data})

class PostCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        data_obj = request.data

        text = data_obj.get('text',None)
        post_type = data_obj.get('type',None)

        is_pending_post = data_obj.get('is_pending_post','true')

        if is_pending_post == 'true':
            is_pending_post = True
        else:
            is_pending_post = False

        post_obj = Post()
        post_obj.user = user
        post_obj.pending_text = text
        post_obj.is_pending = is_pending_post
        post_obj.pending_datetime = timezone.now()
        post_obj.save()

        if post_type == TEXT_AND_IMAGE:

            try:
                files = dict((data_obj).lists())['files']
                if files and len(files) > 0:
                    for image in files:
                        post_image_obj = PostImage()
                        post_image_obj.post = post_obj
                        compressed_image = compress(image)
                        # Choosing smaller image size
                        if compressed_image.size > image.size:
                            compressed_image = image
                        post_image_obj.image = compressed_image
                        post_image_obj.is_pending = is_pending_post
                        post_image_obj.save()
            except:
                pass
        
        elif post_type == VIDEO:
            video = data_obj.get('video',None)
            video_thumbnail = data_obj.get('video_thumbnail',None)
            if video is not None and video_thumbnail is not None: 
                # Need to create
                video_obj = PostVideo()
                video_obj.post = post_obj
                
                # Processing with Celery
                date_s = timezone.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
                base_path = f'{settings.MEDIA_ROOT}/posts/videos/{post_obj.id}'
                hls_url = f'/media/posts/videos/{post_obj.id}/{date_s}/{date_s}.m3u8'
                access_key_url = f'/media/posts/videos/{post_obj.id}/keys/{date_s}/key'
                
                video_obj.video = video
                compressed_image = compress(video_thumbnail)
                # Choosing smaller image size
                if compressed_image.size > video_thumbnail.size:
                    compressed_image = video_thumbnail
                video_obj.video_thumbnail = compressed_image
                video_obj.is_pending = is_pending_post
                video_obj.save()

                video_path = video_obj.video.path
                # Don't use Slug for room_name in Django Channels
                room_name = f'{user.id}_{post_obj.id}'
                process_hls_encryption.delay(room_name,video_path,base_path,access_key_url,date_s)
                # Updating Model with appropriate links
                video_obj.video = ''
                video_obj.hls_url = hls_url
                video_obj.hls_path = f'{base_path}/{date_s}'
                video_obj.hls_keys_path = f'{base_path}/keys/{date_s}'
                video_obj.save()
                # Give the file permission
                os.chmod(video_path, 0o777)

        if is_pending_post == False:
            serializer_post = NewsfeedPostSerializer(instance=post_obj,context={"request": request})

            # Admin needs to be approved

            # # Testing
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'newsfeed',
                {'type': 'newsfeed', 'message': {'type':'post_added','post':json.dumps(serializer_post.data), }}
            )
     
        return Response(status=HTTP_201_CREATED)

# class NewsFeedPostRetrieveApiView(RetrieveAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = NewsfeedPostSerializer
#     lookup_field = 'post_id'

#     def get_object(self):
#         post_id = self.kwargs[self.lookup_field]   
#         return Post.objects.filter(id=post_id).first()

# class NewsFeedPostWebsocketSendCreateApiView(CreateAPIView):
#     authentication_classes = []
#     permission_classes = []
#     lookup_field = 'post_id'

#     def create(self, request, *args, **kwargs):
#         # print(request)
#         data_obj = request.data
#         post_id = data_obj.get('post_id',0)   
#         post_obj = Post.objects.filter(id=post_id).first()
#         # print(post_id,post_obj)
#         if post_obj and post_obj.is_pending == False:
#             serializer_post = NewsfeedPostSerializer(instance=post_obj,context={"request": request})
#             channel_layer = get_channel_layer()
#             async_to_sync(channel_layer.group_send)(
#                 f'newsfeed',
#                 {'type': 'newsfeed', 'message': {'type':'post_added','post':json.dumps(serializer_post.data), }}
#             )

class PostDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'post_id'

    def destroy(self, request, *args, **kwargs):
        post_id = self.kwargs[self.lookup_field]
        post_obj = Post.objects.filter(id=post_id).first()
        if post_obj and post_obj.user == request.user:
            self.perform_destroy(post_obj)
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class CommentDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'comment_id'

    def destroy(self, request, *args, **kwargs):
        user = request.user
        comment_id = self.kwargs[self.lookup_field]
        comment_obj = PostComment.objects.filter(id=comment_id).first()
        if comment_obj and (comment_obj.user == user or comment_obj.post.user == user):
            self.perform_destroy(comment_obj)
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class PostCommentCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'post_id'

    def create(self, request, *args, **kwargs):
        user = request.user
        data_obj = request.data
        post_id = self.kwargs[self.lookup_field]

        text = data_obj.get('text',None)

        post_obj = Post.objects.filter(id=post_id).first()

        if post_obj and text is not None:
            comment_obj = PostComment()
            comment_obj.user = user
            comment_obj.post = post_obj
            comment_obj.text = text
            comment_obj.save()

            serializer_comment = PostCommentSerializer(instance=comment_obj,context={"request": request})

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'newsfeed',
                {'type': 'newsfeed', 'message': {'type':'comment_added','comment':json.dumps(serializer_comment.data),'post_id': post_id }}
            )
            return Response({'comment':serializer_comment.data},status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)

# Perform both add and remove
class LikeCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def create(self, request, *args, **kwargs):
        user = request.user
        data_obj = request.data
        id = self.kwargs[self.lookup_field]
        like_type = data_obj.get('type',None)

        if like_type is not None:
            obj = None
            if like_type == POST_LIKE:
                obj = Post.objects.filter(id=id).first()
            elif like_type == COMMENT_LIKE:
                obj = PostComment.objects.filter(id=id).first()
            
            if obj:
                if user in obj.likes.all():
                    obj.likes.remove(user)
                else:
                    obj.likes.add(user)

                if like_type == POST_LIKE:
                    serializer_post = PostNormalSerializer(instance=obj,context={"request": request})
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'newsfeed',
                        {
                            'type': 'newsfeed', 
                            'message': {'type':'post_liked','likes':serializer_post.data['likes'],'post_id': obj.id }
                        }
                    )
                    return Response({'likes':serializer_post.data['likes']},status=HTTP_201_CREATED)
                elif like_type == COMMENT_LIKE:
                    serializer_comment = PostCommentNormalSerializer(instance=obj,context={"request": request})
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'newsfeed',
                        {
                            'type': 'newsfeed', 
                            'message': {
                                    'type':'comment_liked','likes':serializer_comment.data['likes'],
                                    'post_id': obj.post.id, 'comment_id': obj.id, 
                                }
                        }
                    )
                    return Response({'likes':serializer_comment.data['likes']},status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)
