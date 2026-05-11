from django.urls import path
from .views import (
        SupportPostCreateApiView, SupportPostReplyCreateApiView, SupportPostDestroyApiView,
        SupportPostReplyDestroyApiView,SupportPostListApiView,
    )

urlpatterns=[ 
    path('support-post-list/',SupportPostListApiView.as_view()),
    path('support-post-create/',SupportPostCreateApiView.as_view()),
    path('support-post-reply-create/<int:post_id>/',SupportPostReplyCreateApiView.as_view()),
    path('support-post-delete/<int:post_id>/',SupportPostDestroyApiView.as_view()),
    path('support-post-reply-delete/<int:reply_id>/',SupportPostReplyDestroyApiView.as_view()),
]