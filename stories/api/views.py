from django.utils import timezone
from datetime import timedelta
from rest_framework.generics import (
    CreateAPIView,ListAPIView
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import CoverStorySerializer
from me_live.utils.utils import compress
from stories.models import Story,CoverStory

class CoverStoryListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CoverStorySerializer

    def list(self, request, *args, **kwargs):
        cover_story_objs = []
        user = request.user
        present_datetime = timezone.now()
        own_cover_story_obj = CoverStory.objects.filter(user=user,expired_datetime__gte=present_datetime).first()
        if own_cover_story_obj:
            cover_story_objs.append(own_cover_story_obj)
        # TODO: Frinds stories need to implement later
        others_cover_story_objs = CoverStory.objects.filter(expired_datetime__gte=present_datetime).exclude(user=user).order_by('-id')
        if others_cover_story_objs:
            cover_story_objs.extend(others_cover_story_objs)

        serializer_cover_story_objs = self.get_serializer(cover_story_objs, many=True)
        return Response({'cover_stories':serializer_cover_story_objs.data})

class StoryCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        data_obj = request.data

        caption = data_obj.get('caption',None)
        image = data_obj.get('image',None)

        if caption is None and image is None:
            return Response({},status=HTTP_204_NO_CONTENT)

        story_obj = Story()
        story_obj.user = user
        if caption is not None:
            story_obj.caption = caption
        if image is not None:
            compressed_image = compress(image)
            # Choosing smaller image size
            if compressed_image.size > image.size:
                compressed_image = image
            story_obj.image = compressed_image
        expired_datetime = timezone.now() + timedelta(days=1)
        story_obj.expired_datetime = expired_datetime
        story_obj.save()

        cover_story_obj = CoverStory.objects.filter(user=user).first()
        if cover_story_obj is None:
            cover_story_obj = CoverStory()
            cover_story_obj.user = user
        cover_story_obj.expired_datetime = expired_datetime
        cover_story_obj.save()
        cover_story_obj.stories.add(story_obj)

        serializer_cover_story = CoverStorySerializer(instance=cover_story_obj,context={"request": request})
     
        return Response({'cover_story':serializer_cover_story.data}, status=HTTP_201_CREATED)
