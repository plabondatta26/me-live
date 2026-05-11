from django.urls import path
from .views import (
    LiveKitTokenCreateApiView,
    # LiveKitTokenV2CreateApiView,
    ParticipantListApiView,
    LiveGroupRoomConfigUpdateApiView,
    # Live Room
    LiveRoomV2ListApiView,
    LiveRoomUpdateApiView,
    GroupCallerCreateApiView,
    FollowingLiveRoomListApiView,
    LiveRoomTestingListApiView,
)
from .views_webhook_livekit import livekit_webhook

urlpatterns=[ 
    path('livekit-token-create/',LiveKitTokenCreateApiView.as_view()),
    # path('livekit-token-v2-create/',LiveKitTokenV2CreateApiView.as_view()),

    path('participant-list/<str:channel_name>/',ParticipantListApiView.as_view()),
    path('live-group-room-config-update/',LiveGroupRoomConfigUpdateApiView.as_view()),

    # Live Room
    path('live-room-v2-list/',LiveRoomV2ListApiView.as_view()),
    path('live-room-update/',LiveRoomUpdateApiView.as_view()),
    path('group-caller-create/<str:channel_name>/',GroupCallerCreateApiView.as_view()),
    path('following-live-room-id-list/<int:user_id>/',FollowingLiveRoomListApiView.as_view()),

    # Testing
    path('live-room-test-list/',LiveRoomTestingListApiView.as_view()),

    # Livekit Webhook url
    path("livekit-webhook/", livekit_webhook, name="livekit_webhook"),

]


# pip install git+https://github.com/livekit/livekit-server-sdk-python.git
