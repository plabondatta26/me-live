from django.urls import path
from .views import (
    RegisterDeviceCreateApiView,UserTokenUpdateApiView,PeerDeviceUpdateApiView,
    SinglePushCreateApiView,SinglePushForCallingCreateApiView,
    # NotifyGroupMembersCreateApiView,
)

urlpatterns=[ 
    # FCM stuffs
    path('device-create/',RegisterDeviceCreateApiView.as_view()),
    path('token-update/',UserTokenUpdateApiView.as_view()),
    path('peer-device-update/',PeerDeviceUpdateApiView.as_view()),
    path('single-push-create/',SinglePushCreateApiView.as_view()),
    path('single-push-for-calling-create/',SinglePushForCallingCreateApiView.as_view()),
    # path('notify-group-members-create/',NotifyGroupMembersCreateApiView.as_view()),

]