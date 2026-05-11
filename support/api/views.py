from rest_framework.generics import (
    CreateAPIView,ListAPIView, DestroyAPIView
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,HTTP_203_NON_AUTHORITATIVE_INFORMATION,HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from support.models import SupportPost, SupportPostImage, SupportPostReply
from .serializers import SupportPostSerializer, SupportPostReplySerializer
from me_live.utils.utils import compress

class SupportPostListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user

        posts_objs = SupportPost.objects.filter(user=user)

        serializer_posts = SupportPostSerializer(instance=posts_objs,many=True,context={"request": request})

        return Response({'posts':serializer_posts.data},status=HTTP_200_OK)

class SupportPostCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        data_obj = request.data

        text = data_obj.get('text',None)

        post_obj = SupportPost()
        post_obj.user = user
        post_obj.text = text
        post_obj.save()


        try:
            files = dict((data_obj).lists())['files']
            if files and len(files) > 0:
                for image in files:
                    post_image_obj = SupportPostImage()
                    post_image_obj.post = post_obj
                    compressed_image = compress(image)
                    # Choosing smaller image size
                    if compressed_image.size > image.size:
                        compressed_image = image
                    post_image_obj.image = compressed_image

                    post_image_obj.save()
        except:
            pass
        

        serializer_post = SupportPostSerializer(instance=post_obj,context={"request": request})

        return Response({'post':serializer_post.data},status=HTTP_201_CREATED)

class SupportPostReplyCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'post_id'

    def create(self, request, *args, **kwargs):
        user = request.user
        data_obj = request.data
        post_id = self.kwargs[self.lookup_field]

        text = data_obj.get('text',None)

        post_obj = SupportPost.objects.filter(id=post_id).first()

        if post_obj and text is not None:
            reply_obj = SupportPostReply()
            reply_obj.user = user
            reply_obj.post = post_obj
            reply_obj.text = text
            reply_obj.save()

            serializer_reply = SupportPostReplySerializer(instance=reply_obj,context={"request": request})

            return Response({'reply':serializer_reply.data},status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)


class SupportPostDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'post_id'

    def destroy(self, request, *args, **kwargs):
        post_id = self.kwargs[self.lookup_field]
        post_obj = SupportPost.objects.filter(id=post_id).first()
        if post_obj and post_obj.user == request.user:
            self.perform_destroy(post_obj)
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class SupportPostReplyDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'reply_id'

    def destroy(self, request, *args, **kwargs):
        user = request.user
        reply_id = self.kwargs[self.lookup_field]
        reply_obj = SupportPostReply.objects.filter(id=reply_id).first()
        if reply_obj and (reply_obj.user == user or reply_obj.post.user == user):
            self.perform_destroy(reply_obj)
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)
