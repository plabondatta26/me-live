import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from livekit_stuffs.models import LiveRoom
from me_live.tasks import load_all_mendatory_data

class LiveKitStreamingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.device_id = self.scope['url_route']['kwargs']['device_id']
        self.device_name = self.scope['url_route']['kwargs']['device_name']

        self.room_group_name = 'live_streaming_%s' % self.room_name

        # self.scope['user'] = await self.get_user(int(self.scope["query_string"]))
        try:
            self.scope['user'].id = int(self.scope["query_string"])
        except:
            return None

        # if self.scope['user'] == AnonymousUser():
        #     return None
       
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        if self.room_name == 'livekit_streamings':
            load_all_mendatory_data.delay(self.scope['user'].id, self.device_id, self.device_name)
           
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
                'type': 'live_streaming',
                'message': message 
            }
        )

    # Receive message from room group
    async def live_streaming(self, event):
        message = event['message']
     
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

        if message['type'] == 'device_block':
            await self.delete_live_room(message)

    @database_sync_to_async
    def delete_live_room(self,data):
        try:
            LiveRoom.objects.filter(channel_id=data['user_id']).delete()  
        except:
            pass

        return None

