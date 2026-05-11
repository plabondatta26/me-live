from rest_framework import serializers
from ..models import ChatMessage, LastChatMessage

class LastChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastChatMessage
        fields = "__all__"

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = "__all__"