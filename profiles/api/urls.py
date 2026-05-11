from django.urls import path
from .views import (
    ProfileRetrieveApiView,ProfileUpdateApiView,
    FollowerCreateApiView,
    FollowerV2CreateApiView,BlockV2CreateApiView,
    FollowerListApiView, BlockListApiView,
    MissingProfileAccountListApiView,
    DiamondsUpdateApiView,
    # MakeZeroDiamondRelatedStuffsOnProfile,
    ProfileForUserInfoRetrieveApiView, ProfileCoverImageDestroyApiView,
    BroadcasterHistoryListApiView,
    )

urlpatterns=[  
    # path('make-zero-diamonds-related-stuffs-on-profile/',MakeZeroDiamondRelatedStuffsOnProfile.as_view()),
    path('missing-profile-account-list/',MissingProfileAccountListApiView.as_view()),
    path('profile-retrieve/<int:user_id>/',ProfileRetrieveApiView.as_view()),
    path('profile-for-user-info-retrieve/<int:user_id>/',ProfileForUserInfoRetrieveApiView.as_view()),

    path('self-profile-cover-image-delete/',ProfileCoverImageDestroyApiView.as_view()),
    path('self-profile-update/',ProfileUpdateApiView.as_view()),
    path('follower-list/',FollowerListApiView.as_view()),
    # Perform both add and remove
    path('follower-create/<int:uid>/',FollowerCreateApiView.as_view()),
    path('follower-v2-create/<int:uid>/',FollowerV2CreateApiView.as_view()),

    path('block-list/',BlockListApiView.as_view()),
    # Perform both add and remove
    path('block-v2-create/<int:uid>/',BlockV2CreateApiView.as_view()),

    # Grab diamonds
    path('diamonds-update/',DiamondsUpdateApiView.as_view()),
    # Broadcasting histories
    path('broadcasting-history-list/<int:uid>/',BroadcasterHistoryListApiView.as_view()),

]