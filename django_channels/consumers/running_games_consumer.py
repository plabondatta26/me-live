import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RunningGamesConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.room_group_name = 'running_games_group'

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
                'type': 'running_games',
                'message': message 
            }
        )
    
    # Receive message from room group
    async def running_games(self, event):
        message = event['message']
     
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

