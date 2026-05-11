from django.utils import timezone

from datetime import datetime
from django.conf import settings
from pymediainfo import MediaInfo
import ffmpeg_streaming
from ffmpeg_streaming import Formats , Bitrate, Representation, Size
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .utils.utils import delete_file
from devices.models import UserDeviceBlocked, UserDeviceInfo

# from games.models import FortuneWheel
# from games.api.serializers import FortuneWheelSerializer
from accounts.models import User
from tracking.models import BroadcasterHistory

LOAD_GIFTS = 'load_gifts'
LOAD_PROFILE = 'load_profile'
CHECK_DEVICE_BLOCKED = 'check_device_blocked'

def monitor(ffmpeg, duration, time_, time_left, process): 
    """
    Handling proccess.

    Examples:
    1. Logging or printing ffmpeg command
    logging.info(ffmpeg) or print(ffmpeg)

    2. Handling Process object
    if "something happened":
        process.terminate()

    3. Email someone to inform about the time of finishing process
    if time_left > 3600 and not already_send:  # if it takes more than one hour and you have not emailed them already
        ready_time = time_left + time.time()
        Email.send(
            email='someone@somedomain.com',
            subject='Your video will be ready by %s' % timedelta(seconds=ready_time),
            message='Your video takes more than %s hour(s) ...' % round(time_left / 3600)
        )
       already_send = True

    4. Create a socket connection and show a progress bar(or other parameters) to your users
    Socket.broadcast(
        address=127.0.0.1
        port=5050
        data={
            percentage = per,
            time_left = timedelta(seconds=int(time_left))
        }
    )

    :param ffmpeg: ffmpeg command line
    :param duration: duration of the video
    :param time_: current time of transcoded video
    :param time_left: seconds left to finish the video process
    :param process: subprocess object
    :return: None
    """
    per = round(time_ / duration * 100)

    # sys.stdout.write(
    #     "\rTranscoding...(%s%%) %s left [%s%s]" %
    #     (per, timedelta(seconds=int(time_left)), '#' * per, '-' * (100 - per))
    # )
    # sys.stdout.flush()

    global room
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'upload_{room}',
        # {'type': 'upload_progress', 'message': per}
        {'type': 'upload_progress', 'message': per}
    )

@shared_task
def process_hls_encryption(room_name,path,base_path,access_key_url,date_s):
    global room
    room = room_name
    if path:
        # Checking Resolution 
        media_info = MediaInfo.parse(path)
        original_video_width = 0
        original_video_height = 0
        for track in media_info.tracks:
            if track.track_type == 'Video':
                original_video_width = track.width
                original_video_height = track.height

        # base_path = f'{settings.MEDIA_ROOT}/converted/videos'

        video = ffmpeg_streaming.input(path)
        # date_s = (datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f'))
        # Video Representation
        if original_video_height > original_video_width:
            # Turn video width to hight
            _360p  = Representation(Size(360, 640), Bitrate(128 * 1024, 276 * 1024))
            _480p  = Representation(Size(480, 854), Bitrate(192 * 1024, 750 * 1024))
        else:
            _360p  = Representation(Size(640, 360), Bitrate(276 * 1024, 128 * 1024))
            _480p  = Representation(Size(854, 480), Bitrate(750 * 1024, 192 * 1024))
        # _720p  = Representation(Size(1280, 720), Bitrate(2048 * 1024, 320 * 1024))
        # _1080p = Representation(Size(1920, 1080), Bitrate(4096 * 1024, 320 * 1024))
        # Key based encryption
        #A path you want to save a random key to your local machine
        key_save_to = f'{base_path}/keys/{date_s}/key'

        #A URL (or a path) to access the key on your website
        # access_key_url = f'{settings.BACKEND_BASE_URL}/media/converted/videos/keys/{date_s}/key'

        # or url = '/"PATH TO THE KEY DIRECTORY"/key';
        key_rotation = 1
        hls = video.hls(Formats.h264())
        hls.encryption(key_save_to, access_key_url,key_rotation)

        # if original_video_width < 1920 or original_video_height < 1080:
        #     if original_video_width < 1280 or original_video_height < 720:
        #         hls.representations(_360p,_480p)
        #     else:
        #         hls.representations(_360p,_480p,_720p)
        # else:
        #     hls.representations(_360p,_480p,_720p,_1080p)

        # For Easy loading restricted resolution to 480 or 360
        if original_video_height > original_video_width:
            # Turn video width to hight
            if original_video_width < 480 or original_video_height < 854:
                hls.representations(_360p)
            else:
                hls.representations(_480p)
        else:
            if original_video_width < 854 or original_video_height < 480:
                hls.representations(_360p)
            else:
                hls.representations(_480p)

        output_path = f'{base_path}/{date_s}/{date_s}.m3u8'
        hls.output(output_path,monitor=monitor)

        # # Updating Model with appropriate links
        delete_file(path)
        # instance.video = ''
        # instance.hls_url = f'/media/converted/videos/{date_s}/{date_s}.m3u8'
        # instance.hls_path = f'{base_path}/{date_s}'
        # instance.hls_keys_path = f'{base_path}/keys/{date_s}'
        # instance.save()
    return 'process_hls_encryption is processing'


# @shared_task
# def notify_streaming_to_followers(uid,base_url):
#     profile_obj = Profile.objects.filter(user__id=uid).first()
#     if profile_obj:
#         followers = profile_obj.followers.all()
    
#         if len(followers) > 0:
#             title = profile_obj.full_name
#             image = get_profile_image(profile_obj=profile_obj)

#             # Notify to followers
#             message = 'Is Live now'
#             registration_ids = []
#             for follower_obj in followers:
#                 try:
#                     device_obj = follower_obj.device_token
#                     if device_obj:
#                         registration_ids.append(device_obj.token) 
#                 except:
#                     pass
                
#             if len(registration_ids) > 0:
#                 payload_data = {
#                     'data': {
#                         'title': title,
#                         'message': message,
#                         'image': image,
#                         'peered_uid': uid,
#                         'peered_name': title,
#                         'call_type': '',
#                         'event_type':'STREAM_LIVE',
#                         'channel': f'{uid}',
#                     }
#                 }
#                 firebase_obj = Firebase()
#                 if len(registration_ids) == 1:
#                     firebase_obj.send(registration_ids[0],payload_data)
#                 else:
#                     firebase_obj.send_multicast(registration_ids,payload_data)
                
#     return 'notify_streaming_to_followers is processing'

def get_profile_image(profile_obj):
    if profile_obj.profile_image:
        return f"{settings.BASE_URL}/media/{profile_obj.profile_image}"
    return profile_obj.photo_url

# @shared_task
# def notify_to_group_members(uid,members_str,title,message,group_id,admin_id):
#     # Notify to memebers
#     members_list = members_str.split(',')
#     for member_uid in members_list:
#         member_uid = int(member_uid)
#         if member_uid != uid:
#             device_obj = FCMDeviceToken.objects.filter(user__id=member_uid).first()
#             if device_obj:
#                 device_token = device_obj.token
               
#                 payload_data = {
#                     'data': {
#                         'title': title,
#                         'message': message,
#                         'image': None,
#                         'peered_uid': admin_id,
#                         'peered_name': '',
#                         'call_type': '',
#                         'event_type':'GROUP_CHAT',
#                         'channel': group_id,
#                     }
#                 }
#                 firebase_obj = Firebase()

#                 firebase_obj.send(device_token,payload_data)
    
#     return 'notify_to_group_members is processing'

@shared_task
def track_broadcaster_state(uid,connection_state,is_video,):
    user_obj = User.objects.filter(id=uid).first()
    if user_obj:
        broadcaster_history_obj = BroadcasterHistory.objects.filter(user=user_obj,broadcasting_date=datetime.now().date()).first()
        if broadcaster_history_obj:
            if is_video == False:
                broadcaster_history_obj.audio_broadcast_in_second += 1
            else:
                broadcaster_history_obj.video_broadcast_in_second += 1
        else:
            broadcaster_history_obj = BroadcasterHistory()
            broadcaster_history_obj.user = user_obj
            if is_video == False:
                broadcaster_history_obj.audio_broadcast_in_second = 1
            else:
                broadcaster_history_obj.video_broadcast_in_second = 1
        broadcaster_history_obj.save()
    return 'Track broadcaster is processing'


@shared_task
def load_all_mendatory_data(uid, device_id, device_name):
    user_obj = User.objects.filter(id=uid).first()
    if user_obj:
        channel_layer = get_channel_layer()
        
        # Load device info
        device_blocked_checker_data = device_blocked_checker(user_obj, device_id, device_name)
        device_blocked_checker_data['type'] = CHECK_DEVICE_BLOCKED
        device_blocked_checker_data['uid'] = user_obj.id

        async_to_sync(channel_layer.group_send)(
            f'live_streaming_livekit_streamings',
            {'type': 'live_streaming', 'message': device_blocked_checker_data}
        )
        
        # # Load gifts
        # gift_list_message = get_gift_list()
        # gift_list_message['type'] = LOAD_GIFTS
        # gift_list_message['uid'] = user_obj.id

        # async_to_sync(channel_layer.group_send)(
        #     f'live_streaming_livekit_streamings',
        #     {'type': 'live_streaming', 'message': gift_list_message}
        # )

        # # Load profile
        # serializer_profile_data = get_profile_data(user_obj)
        # serializer_profile_data['type'] = LOAD_PROFILE

        # async_to_sync(channel_layer.group_send)(
        #     f'live_streaming_livekit_streamings',
        #     {'type': 'live_streaming', 'message': serializer_profile_data}
        # )

        
    return 'Loading all mendatory data'

 

# def get_profile_data(user):
#     return ProfileSerializer(instance=user.profile,).data

# def get_gift_list():
#     normal_gift_objs = NormalGift.objects.all()
#     animated_gift_objs = AnimatedGift.objects.all()

#     data = {
#         'normal_gifts': [],
#         'animated_gifts': [],
#     }
#     data['normal_gifts'] = NormalGiftSerializer(instance=normal_gift_objs,many=True,).data
#     data['animated_gifts'] = AnimatedGiftSerializer(instance=animated_gift_objs,many=True,).data
#     return data

def device_blocked_checker(user,device_id,device_name):
    # Modified version
    if UserDeviceBlocked.objects.filter(user_id=user.id).exists():
        return {'device_blocked':True}
    entry_datetime = timezone.now()

    device_info_obj = UserDeviceInfo.objects.filter(device_id=device_id).first()
    if device_info_obj is None:
        device_info_obj = UserDeviceInfo()
        device_info_obj.device_id = device_id
    device_info_obj.user_id = user.id
    device_info_obj.device_name = device_name
    device_info_obj.entry_datetime = entry_datetime
    device_info_obj.save()

    return {'device_blocked':device_info_obj.blocked}

