from django.urls import path
from .views import (
    PurchasedStreamingJoiningGifListApiView, PurchasedVipPackageListApiView, PurchasedVvipPackageListApiView, StreamingJoiningGifPurchaseCreateApiView,
    PurchasedStreamingJoiningGifRetrieveApiView, PurchasedStreamingJoiningGifActivationUpdateApiView,
    DiamondPackageListApiView ,WithdrawPackageListApiView,DiamodPackagePurchaseCreateApiView,GiftListApiView,
    PurchasedPackageThemeRetrieveApiView, PurchasedPackageThemeActivationUpdateApiView, 
    PurchasedPackageThemeListApiView, PackageThemePurchaseCreateApiView,
    CustomPackageThemeImageDestroyApiView,
    # YouTubeVideoListApiView,
)

urlpatterns = [
    # Joining gif
    path('purchased-streaming-joining-gif-retrieve/',PurchasedStreamingJoiningGifRetrieveApiView.as_view()),
    path('purchased-streaming-joining-gif-list/',PurchasedStreamingJoiningGifListApiView.as_view()),
    path('streaming-joining-gif-purchase-create/',StreamingJoiningGifPurchaseCreateApiView.as_view()),
    path('purchased-streaming-joining-gif-activation-update/<int:purchased_joining_gif_id>/',PurchasedStreamingJoiningGifActivationUpdateApiView.as_view()),
    # Package Theme
    path('purchased-package-theme-retrieve/',PurchasedPackageThemeRetrieveApiView.as_view()),
    path('purchased-package-theme-list/',PurchasedPackageThemeListApiView.as_view()),
    path('package-theme-purchase-create/',PackageThemePurchaseCreateApiView.as_view()),
    path('purchased-package-theme-activation-update/<int:purchased_package_theme_id>/',PurchasedPackageThemeActivationUpdateApiView.as_view()),
    path('custom-package-theme-image-delete/',CustomPackageThemeImageDestroyApiView.as_view()),
    # Diamond Stuffs
    path('diamond-package-list/',DiamondPackageListApiView.as_view()),
    path('diamond-package-purchase-create/',DiamodPackagePurchaseCreateApiView.as_view()),
    # Gift
    path('gift-list/',GiftListApiView.as_view()),
    # Withdraw
    path('withdraw-package-list/',WithdrawPackageListApiView.as_view()),
     # VVIP
    path('purchased-vvip-package-list/',PurchasedVvipPackageListApiView.as_view()),
    # VIP
    path('purchased-vip-package-list/',PurchasedVipPackageListApiView.as_view()),
    # path('youtube-video-list/',YouTubeVideoListApiView.as_view()),

]
