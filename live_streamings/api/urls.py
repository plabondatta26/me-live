from django.urls import path
from .views import (
    # LiveStreamingStateUpdateApiView,LiveStreamingCommentCreateApiView,
    # LiveStreamingActionCreateApiView,
    # LiveStreamingGiftCreateApiView,
    LiveStreamingGiftV2CreateApiView,
    NotifyFollowersCreateApiView,
    PayingDiamondsForLiveLockCreateApiView,
    PayingDiamondsForCallLockCreateApiView,
)

urlpatterns=[ 
    # path('agora-rtc-token-retrieve/',AgoraRtcTokenRetrieveApiView.as_view()),
    # FCM stuffs
    # path('live-streaming-state-update/',LiveStreamingStateUpdateApiView.as_view()),
    # path('live-streaming-comment-create/',LiveStreamingCommentCreateApiView.as_view()),
    # path('live-streaming-gift-create/',LiveStreamingGiftV2CreateApiView.as_view()),
    # path('live-streaming-gift-create/',LiveStreamingGiftCreateApiView.as_view()),
    path('live-streaming-gift-v2-create/',LiveStreamingGiftV2CreateApiView.as_view()),

    # path('live-streaming-action-create/',LiveStreamingActionCreateApiView.as_view()),
    # Popup notification
    path('notify-followers-create/',NotifyFollowersCreateApiView.as_view()),
    path('paying-diamonds-for-live-lock-create/',PayingDiamondsForLiveLockCreateApiView.as_view()),
    path('paying-diamonds-for-call-lock-create/',PayingDiamondsForCallLockCreateApiView.as_view()),


]

