import json
import os
from django.core.cache import cache
from json import JSONEncoder
from datetime import date, datetime
import shutil
import subprocess
#For Image Compression
from io import BytesIO
from PIL import Image, ExifTags
from django.core.files import File
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from websocket import create_connection
from profiles.api.serializers import ProfileSerializer
from me_live.utils.constants import liveRoomSocketBaseUrl


""" Deletes file from filesystem. """
def delete_file(path):
   if os.path.isfile(path):
      os.remove(path) 
   elif os.path.isdir(path):
      shutil.rmtree(path)

def delete_video_files_or_directories(instance):
    if instance.video:
        instance.video.delete(False)
    if instance.hls_path:
        subprocess.call(['chmod', '-R', '+w', instance.hls_path])
        delete_file(instance.hls_path)
    if instance.hls_keys_path:
        subprocess.call(['chmod', '-R', '+w', instance.hls_keys_path])
        delete_file(instance.hls_keys_path)

#image compression method
def compress(image):
    # im = Image.open(image)
    # im_io = BytesIO() 
    # ext = image.name.split('.')[-1] 
    # # if im.mode in ("RGBA", "P"):
    # #     im = im.convert("RGB")
    # if ext == 'png':
    #     #Convert mode RGBA as JPEG
    #     # rgb_im = im.convert('RGB')
    #     # rgb_im.save(im_io, 'JPEG', quality=60) 
    #     im.save(im_io, 'PNG', quality=60) 
    # else:
    #     im.save(im_io, 'JPEG', quality=60) 
   
    # new_image = File(im_io, name=image.name)
    # return new_image

    # Solved (Orientation remain unchanged)
    # Reference: https://stackoverflow.com/questions/53459792/compressing-the-image-using-pil-without-changing-the-orientation-of-the-image
    mywidth = 500
    im = Image.open(image)
    im_io = BytesIO() 

    if hasattr(im, '_getexif'):
        exif = im._getexif()

        if exif:
            for tag, label in ExifTags.TAGS.items():
                if label == 'Orientation':
                    orientation = tag
                    break
            if orientation in exif:
                if exif[orientation] == 3:
                    im = im.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    im = im.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    im = im.rotate(90, expand=True)

    wpercent = (mywidth / float(im.size[0]))
    hsize = int((float(im.size[1]) * float(wpercent)))
    im = im.resize((mywidth, hsize), Image.ANTIALIAS)
    im.save(im_io,'PNG')
    new_image = File(im_io, name=image.name)
    return new_image

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()

def updateProfileInGlobalWebsocket(profile_obj):
    profile_cache = ProfileSerializer(instance=profile_obj,).data
    cache.set(f'profile_{profile_obj.user.id}',profile_cache,timeout=60*60*24*2)
    profile_cache['type'] = 'load_profile'

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'live_streaming_livekit_streamings',
        {
            'type': 'live_streaming',
            'message': profile_cache
        }
    )

    # Singnal into Live
    purchased_package_theme = json.loads(profile_cache['package_theme'])['theme_gif']
    if purchased_package_theme is not None:
        user_id = profile_obj.user.id
        # async_to_sync(channel_layer.group_send)(
        #     f'live_room_{user_id}',
        #     {
        #         'type': 'live_room',  
        #         'message': {
        #             'action': 'package_theme',
        #             'theme_gif': purchased_package_theme,
        #             'uid': user_id,
        #         }
        #     }
        # )
        # External websocket
        ws = create_connection(f"{liveRoomSocketBaseUrl}/{user_id}/")
        ws.send(json.dumps({"message": {
            'action': 'package_theme',
            'theme_gif': purchased_package_theme,
            'uid': user_id,
        }}))
        ws.close()


def sendDataInGlobalWebsocket(data):
    # Sending to websocket
    channel_layer = get_channel_layer()
    # Send message to room group
    async_to_sync(channel_layer.group_send)(
        f'live_streaming_livekit_streamings',
        {
            'type': 'live_streaming', 
            'message': data 
        }
    )