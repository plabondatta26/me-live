from django.urls import path
from .views import CoverStoryListApiView,StoryCreateApiView

urlpatterns=[ 
    path('cover-story-list/',CoverStoryListApiView.as_view()),
    path('story-create/',StoryCreateApiView.as_view()),
]