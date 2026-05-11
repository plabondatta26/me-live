from django.urls import path
from .views import (
    UserDeviceInfoUpdateApiView,SearchUserDeviceInfoListApiView, UserDeviceBlockCreateApiView,
    UserDeviceBlockedHistoryListApiView,
)

urlpatterns=[ 
    path('user-device-info-update/',UserDeviceInfoUpdateApiView.as_view()),
    path('search-user-device-info-list/<int:user_id>/',SearchUserDeviceInfoListApiView.as_view()),
    path('user-device-block-create/',UserDeviceBlockCreateApiView.as_view()),
    path('user-device-blocked-history-list/',UserDeviceBlockedHistoryListApiView.as_view()),
]