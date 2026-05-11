import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

class NewsfeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'newsfeed'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
       
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        ) 

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'newsfeed',
                'message': message 
            }
        )

    # Receive message from room group
    async def newsfeed(self, event):
        message = event['message']
        message['datetime'] = str(timezone.now())

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


