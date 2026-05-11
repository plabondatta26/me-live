from django.conf import settings
from django.contrib import admin
from django.urls import path,include
from .views import app_ads

urlpatterns = [
    # Deep link
    # path('.well-known/assetlinks.json',deeplink_json_view,name='assetlinks'),
    # app-ads.txt
    path('app-ads.txt',app_ads),
    # # API Urls 
    path('api/v1/auth/',include("accounts.api.urls")),
    path('api/v1/balance/',include("balance.api.urls")),
    path('api/v1/business/', include("business.api.urls")),

    # path('api/v1/call-histories/',include("call_histories.api.urls")),
    path('api/v1/devices/',include("devices.api.urls")),
    path('api/v1/games/',include("games.api.urls")),
    path('api/v1/live-streamings/',include("live_streamings.api.urls")),
    path('api/v1/livekit-stuffs/',include("livekit_stuffs.api.urls")),

    # path('api/v1/notifications/',include("notifications.api.urls")),
    path('api/v1/messenger/',include("messenger.api.urls")),
    path('api/v1/posts/',include("posts.api.urls")),
    path('api/v1/products/',include("products.api.urls")),
    path('api/v1/profiles/',include("profiles.api.urls")),
    path('api/v1/refer/',include("refer_bonus.api.urls")),
    path('api/v1/support/',include("support.api.urls")),
    path('api/v1/tracking/',include("tracking.api.urls")),

    # path('api/v1/searches/',include("searches.api.urls")),
    # path('api/v1/stories/',include("stories.api.urls")),
    # # Firebase Cloud Messaging (FCM)
    path('api/v1/fcm/',include("fcm.api.urls")),

    path("__debug__/", include("debug_toolbar.urls")), 
    
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns.append(path('', admin.site.urls))