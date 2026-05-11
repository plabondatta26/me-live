from decouple import config

from livekit import (
    RoomServiceClient,
)

LIVEKIT_HOST= config("LIVEKIT_HOST") 
LIVEKIT_API_KEY = config("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET_KEY = config("LIVEKIT_API_SECRET_KEY")

# LIVEKIT_HOST_2= config("LIVEKIT_HOST_2") 
# LIVEKIT_API_KEY_2 = config("LIVEKIT_API_KEY_2")
# LIVEKIT_API_SECRET_KEY_2 = config("LIVEKIT_API_SECRET_KEY_2")

class RoomServiceClientSingleton:
  room_service_client_obj = None

  def __new__(cls):
    if cls.room_service_client_obj is None:
      # print('Creating the room_service_client_obj object')
      cls.room_service_client_obj = RoomServiceClient(LIVEKIT_HOST,LIVEKIT_API_KEY,LIVEKIT_API_SECRET_KEY)
    return cls.room_service_client_obj
  
# class RoomServiceClientSingleton2:
#   room_service_client_obj = None

#   def __new__(cls):
#     if cls.room_service_client_obj is None:
#       # print('Creating the room_service_client_obj object')
#       cls.room_service_client_obj = RoomServiceClient(LIVEKIT_HOST_2,LIVEKIT_API_KEY_2,LIVEKIT_API_SECRET_KEY_2)
#     return cls.room_service_client_obj
