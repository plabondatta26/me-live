from django.urls import path
from .views import (
    # NewsFeedPostRetrieveApiView,
    PostCreateApiView,NewsfeedListApiView,
    PostCommentCreateApiView,LikeCreateApiView,
    PostDestroyApiView, CommentDestroyApiView,
    # NewsFeedPostWebsocketSendCreateApiView,
    )

urlpatterns=[ 
    path('newsfeed/',NewsfeedListApiView.as_view()),
    # path('newsfeed-websocket-send-create/',NewsFeedPostWebsocketSendCreateApiView.as_view()),
    #path('news-feed-post-retrieve/<int:post_id>/',NewsFeedPostRetrieveApiView.as_view()),

    path('post-create/',PostCreateApiView.as_view()),
    path('post-delete/<int:post_id>/',PostDestroyApiView.as_view()),
    path('post-comment-create/<int:post_id>/',PostCommentCreateApiView.as_view()),
    path('comment-delete/<int:comment_id>/',CommentDestroyApiView.as_view()),
    # Perform both add and remove
    path('like-create/<int:id>/',LikeCreateApiView.as_view()),
]