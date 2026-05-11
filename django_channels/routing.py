from django.urls import path,re_path

from django_channels.consumers.livekit_live_room_consumer import LiveKitLiveRoomConsumer
from django_channels.consumers.running_games_consumer import RunningGamesConsumer

from .consumers.livekit_streaming_consumer import LiveKitStreamingConsumer
from .consumers.newsfeed_consumer import NewsfeedConsumer
from .consumers.chat_room_consumer import ChatRoomConsumer

websocket_urlpatterns = [
    re_path(r'ws/livekit-streaming/(?P<room_name>\w+)/(?P<device_id>\w+)/(?P<device_name>\w+)/$', LiveKitStreamingConsumer.as_asgi()),
    re_path(r'ws/livekit-live-room/(?P<room_name>\w+)/$', LiveKitLiveRoomConsumer.as_asgi()),
    re_path(r'ws/chat-room/(?P<room_name>\w+)/$', ChatRoomConsumer.as_asgi()),

    re_path(r'ws/running-games/', RunningGamesConsumer.as_asgi()),
    path('ws/newsfeed/', NewsfeedConsumer.as_asgi()),

]