from django.urls import path
from .views import (
    # Chats
    ChatMessageCreateApiView,LastChatMessageListApiView, ChatMessageListApiView, ChatMessageDestroyApiView,
    ChatBlockListApiView,ChatBlockUpdateApiView,
)

urlpatterns=[ 
    # Chats
    path('last-chat-message-list/<int:user_id>/',LastChatMessageListApiView.as_view()),
    path('chat-message-create/',ChatMessageCreateApiView.as_view()),
    path('chat-message-list/<str:chat_id>/',ChatMessageListApiView.as_view()),
    path('chat-message-delete/',ChatMessageDestroyApiView.as_view()),
    path('chat-block-list/<int:user_id>/',ChatBlockListApiView.as_view()),
    path('chat-block-update/',ChatBlockUpdateApiView.as_view()),

]