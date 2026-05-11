import json
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import date, datetime
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView,UpdateAPIView,CreateAPIView,
    DestroyAPIView,
    )
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from business.models import Agent
from profiles.models import Profile
from accounts.models import User
from .serializers import (
    ProfileBlockSerializer, ProfileSerializer, UserWithProfileSerializer,
    )
from accounts.api.serializers import UserSerializer
from tracking.models import BroadcasterHistory
from tracking.api.serializers import BroadcasterHistorySerializer
from products.models import Level
from me_live.utils.utils import compress,delete_file, sendDataInGlobalWebsocket
from me_live.utils.constants import liveRoomSocketBaseUrl

# from livekit_stuffs.api.constants import firestore_db

class MakeZeroDiamondRelatedStuffsOnProfile(CreateAPIView):
    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        profiles_objs = Profile.objects.all()
        for profile_obj in profiles_objs:
            profile_obj.diamonds = 0
            profile_obj.outgoing_diamonds = 0
            profile_obj.save()
        return Response(status=HTTP_201_CREATED)

class MissingProfileAccountListApiView(ListAPIView):
    authentication_classes = []
    permission_classes = []

    def list(self, request, *args, **kwargs):
        user_objs = User.objects.filter(admin=False,staff=False,profile=None)
        serializer_users = UserSerializer(instance=user_objs,many=True)
        return Response({'Total':user_objs.count(),'User_list_without_Profile':serializer_users.data},status=HTTP_200_OK)

class ProfileRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]
    lookup_field = 'user_id'

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        user_id = self.kwargs[self.lookup_field]
        my_uid = user.id
        # profile_cache = None

        # if user_id == user.id:
        #     # # Always get Updated Level
        #     # level_data = get_level(user.profile)
        #     # profile_cache['level'] = level_data
        #     # cache.delete(f'profile_{user_id}')
        #     # cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)
        #     serializer_profile = ProfileSerializer(instance=user.profile,context={"request": request})
        #     profile_cache = serializer_profile.data
        #     cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)
        # else:
        #     profile_cache = cache.get(f'profile_{user_id}')
        #     if profile_cache is None:
        #         profile_obj = Profile.objects.filter(user__id=user_id).first()
        #         if profile_obj:
        #             serializer_profile = ProfileSerializer(instance=profile_obj,context={"request": request})
        #             profile_cache = serializer_profile.data
        #             cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)

     
        profile_cache = cache.get(f'profile_{user_id}')
        if profile_cache is None:
            profile_obj = Profile.objects.filter(user__id=user_id).first()
            if profile_obj:
                serializer_profile = ProfileSerializer(instance=profile_obj,context={"request": request})
                profile_cache = serializer_profile.data
                cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)
                
        elif user_id == my_uid:
            profile_obj = user.profile
            # Always get Updated Level
            level_data = get_level(profile_obj)
            profile_cache['level'] = level_data
            profile_cache['diamonds'] = profile_obj.diamonds
            # cache.delete(f'profile_{user_id}')

            # Always Update
            # serializer_profile = ProfileSerializer(instance=profile_obj,context={"request": request})
            # profile_cache = serializer_profile.data

            datetime_str = json.loads(profile_cache['vvip_or_vip_preference'])['expired_datetime']
            if datetime_str is not None:
                datetime_object = datetime.fromisoformat(datetime_str)
                if datetime_object < timezone.now():
                    json_data = {"rank": 0, "expired_datetime": None, "vvip_or_vip_gif": None,}
                    profile_cache['vvip_or_vip_preference'] = json.dumps(json_data)

            datetime_str = json.loads(profile_cache['streaming_joining'])['expired_datetime']
            if datetime_str is not None:
                datetime_object = datetime.fromisoformat(datetime_str)
                if datetime_object < timezone.now():
                    json_data = {"expired_datetime": None, "joining_gif": None,}
                    profile_cache['streaming_joining'] = json.dumps(json_data)

            datetime_str = json.loads(profile_cache['package_theme'])['expired_datetime']
            if datetime_str is not None:
                datetime_object = datetime.fromisoformat(datetime_str)
                if datetime_object < timezone.now():
                    json_data = {"expired_datetime": None, "theme_gif": None,}
                    profile_cache['package_theme'] = json.dumps(json_data)

            cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)
            

        data = {
                'profile': profile_cache,
                "websocket_base_url": liveRoomSocketBaseUrl,
            }
        # try:
        #     profile_cache['vvip_or_vip_preference'] = DateTimeEncoder().encode(profile_cache['vvip_or_vip_preference'])
        # except:
        #     pass
        # data['profile'] = profile_cache

        return Response(data, status=HTTP_200_OK)

def get_level(obj):
        # outgoing_diamonds = 3500 
        outgoing_diamonds = obj.outgoing_diamonds
        level_obj = Level.objects.filter(diamonds__lte=outgoing_diamonds).last()
        if level_obj:
            frame_gif = ""
            if level_obj.frame_gif:
                frame_gif = f"{settings.BASE_URL}/media/{level_obj.frame_gif}"
            return {
                "id": level_obj.id,
                "level": level_obj.level,
                "diamonds": level_obj.diamonds,
                "frame_gif": frame_gif,
            }
        return None
    
class ProfileForUserInfoRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]
    lookup_field = 'user_id'

    # cache requested url (in Seconds)
    # @method_decorator(cache_page(60*60*1))
    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        my_uid = request.user.id
        profile_cache = cache.get(f'profile_{user_id}')

        if profile_cache is None:
            profile_obj = Profile.objects.filter(user__id=user_id).first()
            if profile_obj:
                serializer_profile = ProfileSerializer(instance=profile_obj,context={"request": request})
                profile_cache = serializer_profile.data
                cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)

        profile_cache['fans'] = len(profile_cache['followers'])
        if user_id != my_uid:
            profile_cache['blocks'] = []
            try:
                index = profile_cache['followers'].index(my_uid)
                # Found
                profile_cache['followers'] = [my_uid]
                # print('Found')
            except ValueError:
                # Not found
                profile_cache['followers'] = []
                # print('Not Found')

        data = {
                'profile': None,
            }
        try:
            profile_cache['vvip_or_vip_preference'] = json.loads(profile_cache['vvip_or_vip_preference'])
        except:
            pass

        data['profile'] = profile_cache
        
        return Response(data, status=HTTP_200_OK)
    
class ProfileCoverImageDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def destroy(self, request, *args, **kwargs):
        user = request.user
        profile_obj = user.profile
        if profile_obj.cover_image:
            delete_file(profile_obj.cover_image.path)
            profile_obj.cover_image = None
            profile_obj.save()
            user_id = user.id
            profile_cache = cache.get(f'profile_{user_id}')
            if profile_cache is not None:
                profile_cache['cover_image'] = None
                cache.delete(f'profile_{user_id}')
                cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)
            return Response(status=HTTP_200_OK)
        
        return Response(status=HTTP_204_NO_CONTENT)

class ProfileUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def update(self, request, *args, **kwargs):
        data_obj = request.data
        user = request.user
        uid = user.id
        full_name = data_obj.get('full_name',None)
        email = data_obj.get('email',None)
        birthday = data_obj.get('birthday',None)
        gender = data_obj.get('gender',None)
        profile_image = data_obj.get('profile_image',None)
        # cover_image = data_obj.get('cover_image',None)

        # 'iso_code','iso3_code','phone_code','country_name'
        # phone_code = data_obj.get('phone_code',None)
        # streaming_title = data_obj.get('streaming_title',None)

        profile_obj = user.profile

        # if streaming_title:
        #     profile_obj.streaming_title = streaming_title

        if profile_image:
            if profile_obj.profile_image:
                delete_file(profile_obj.profile_image.path)
            compressed_image = compress(profile_image)
            # Choosing smaller image size
            if compressed_image.size > profile_image.size:
                compressed_image = profile_image
            profile_obj.profile_image = compressed_image

        # if cover_image:
        #     if profile_obj.cover_image:
        #         delete_file(profile_obj.cover_image.path)
        #     compressed_image = compress(cover_image)
        #     # Choosing smaller image size
        #     if compressed_image.size > cover_image.size:
        #         compressed_image = cover_image
        #     profile_obj.cover_image = compressed_image

        if full_name:
            profile_obj.full_name = full_name
        if email:
            profile_obj.email = email
        if gender:
            profile_obj.gender = gender
        # if phone_code:
        #     profile_obj.phone_code = phone_code

        if birthday:
            # 2014-08-14T00:00:00.000
            birthday = birthday.split('T')[0]
            birthday_list = birthday.split('-')
            birthday = date(int(birthday_list[0]),int(birthday_list[1]),int(birthday_list[2]))
            profile_obj.birthday = birthday

        # if profile_obj.mobile_number is None:
        #     profile_obj.mobile_number = f"+{profile_obj.phone_code}{user.phone}"

        profile_obj.updated_date = timezone.now().date()
        profile_obj.save(force_update=True)
        profile_cache = cache.get(f'profile_{uid}')
        if profile_cache is None:
            profile_cache = ProfileSerializer(instance=profile_obj,context={"request": request}).data
            cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*2)
        else:
            profile_cache['full_name'] = profile_obj.full_name
            profile_cache['email'] = profile_obj.email
            profile_cache['gender'] = profile_obj.gender
            try:
                profile_cache['birthday'] = json.dumps(profile_obj.birthday)
            except:
                pass
            if profile_obj.profile_image:
                profile_cache['profile_image'] = f"{settings.BASE_URL}/media/{profile_obj.profile_image}"
            # if profile_obj.cover_image:
            #     profile_cache['cover_image'] = f"{settings.BASE_URL}/media/{profile_obj.cover_image}"

            cache.delete(f'profile_{uid}')
            cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*2)

        return Response({'profile':profile_cache}, status=HTTP_200_OK)
    
class DiamondsUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        data_obj = request.data
        user = request.user
        profile_obj = user.profile
        diamonds = data_obj.get('diamonds',0)
        if diamonds > 0:
            profile_obj.diamonds += diamonds
            profile_obj.save()
            return Response({'grab_diamonds':diamonds},status=HTTP_200_OK)

        return Response(status=HTTP_204_NO_CONTENT) 

# Perform both add and remove
class FollowerCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]
    lookup_field = 'uid'

    def create(self, request, *args, **kwargs):
        user = request.user
        uid = self.kwargs[self.lookup_field]
        my_uid = user.id

        being_followed_user_obj = User.objects.filter(id=uid).first()

        if being_followed_user_obj:
            profile_obj = being_followed_user_obj.profile
            followers = []

            profile_cache = cache.get(f'profile_{uid}')

            if profile_cache is not None:
                try:
                    index = profile_cache['followers'].index(my_uid)
                    # Found
                    profile_obj.followers.remove(user)
                    profile_cache['followers'].remove(my_uid)
                    # print('Found')
                except ValueError:
                    # Not found
                    profile_obj.followers.add(user)
                    profile_cache['followers'].append(my_uid)
                    followers = [my_uid]
                    # print('Not Found')

                cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*2)

                # # mongoDB
                # melive_mongo_db = MeLiveMongoDB()
                # collection_live_room = melive_mongo_db["LiveRoom"]
                # filtered_rooms = collection_live_room.find({"channelName": f"{uid}",}).limit(1)

                # try:
                #     temp = filtered_rooms[0]
                #     # print('Exists')
                #     collection_live_room.update_one(filter={"channelName": f"{uid}",},update={'$set':{"followers":profile_cache['followers']}})
                # except:
                #     # print('Not Exist')
                #     pass

                # try:
                #     firebase_client = FirebaseClient()
                #     firebase_client.firestore_db.collection("LiveRoom").document(f"{uid}").update({"followers":profile_cache['followers']})
                # except:
                #     pass

            else:
                        
                if user in profile_obj.followers.all():
                    profile_obj.followers.remove(user)
                else:
                    profile_obj.followers.add(user)
                    followers = [user.id]

                # try:
                #     index = list(profile_obj.followers.all()).index(user)
                #     # Found
                #     profile_obj.followers.remove(user)
                #     # print('Found')
                # except ValueError:
                #     # Not found
                #     profile_obj.followers.add(user)
                #     followers = [user.id]
                #     # print('Not Found')

                # serialized_profile_data = ProfileSimpleSerializer(instance=profile_obj,context={"request": request}).data

                # # mongoDB
                # melive_mongo_db = MeLiveMongoDB()
                # collection_live_room = melive_mongo_db["LiveRoom"]
                # filtered_rooms = collection_live_room.find({"channelName": f"{uid}",}).limit(1)

                # try:
                #     temp = filtered_rooms[0]
                #     # print('Exists')
                #     collection_live_room.update_one(filter={"channelName": f"{uid}",},update={'$set':{"followers":serialized_profile_data['followers']}})
                # except:
                #     # print('Not Exist')
                #     pass

                # try:
                #     firebase_client = FirebaseClient()
                #     firebase_client.firestore_db.collection("LiveRoom").document(f"{uid}").update({"followers":serialized_profile_data["followers"]})
                # except:
                #     pass

                # profile_cache = cache.get(f'profile_{uid}')
                # if profile_cache is not None:
                #     profile_cache['followers'] = serialized_profile_data['followers']
                #     # cache.delete(f'profile_{uid}')
                #     cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*2)

                # return Response({'followers':serialized_profile_data['followers']},status=HTTP_201_CREATED)
            return Response({'followers':followers},status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)

class FollowerV2CreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]
    lookup_field = 'uid'

    def create(self, request, *args, **kwargs):
        user = request.user
        uid = self.kwargs[self.lookup_field]
        my_uid = user.id

        being_followed_user_obj = User.objects.filter(id=uid).select_related('profile').only('id','profile__id','profile__followers').first()

        if being_followed_user_obj:
            profile_obj = being_followed_user_obj.profile
            followers = []

            profile_cache = cache.get(f'profile_{uid}')

            if profile_cache is not None:
                try:
                    index = profile_cache['followers'].index(my_uid)
                    # Found
                    profile_obj.followers.remove(user)
                    profile_cache['followers'].remove(my_uid)
                    # print('Found')
                except ValueError:
                    # Not found
                    profile_obj.followers.add(user)
                    profile_cache['followers'].append(my_uid)
                    followers = [my_uid]
                    # print('Not Found')

                cache.set(f'profile_{uid}',profile_cache,timeout=60*60*24*30)

            else:
                        
                if user in profile_obj.followers.all():
                    profile_obj.followers.remove(user)
                else:
                    profile_obj.followers.add(user)
                    followers = [user.id]

            return Response({'followers':followers},status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)

# class BlockCreateApiView(CreateAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated & HasAPIKey]
#     lookup_field = 'uid'

#     def create(self, request, *args, **kwargs):
#         user = request.user
#         uid = self.kwargs[self.lookup_field]

#         being_blocked_user_obj = User.objects.filter(id=uid).first()

#         if being_blocked_user_obj and being_blocked_user_obj.profile.is_moderator == False:
#             profile_obj = user.profile
#             if being_blocked_user_obj in profile_obj.blocks.all():
#                 profile_obj.blocks.remove(being_blocked_user_obj)
#             else:
#                 profile_obj.blocks.add(being_blocked_user_obj)

#             # try:
#             #     index = list(profile_obj.blocks.all()).index(being_blocked_user_obj)
#             #     # Found
#             #     profile_obj.blocks.remove(being_blocked_user_obj)
#             #     # print('Found')
#             # except ValueError:
#             #     # Not found
#             #     profile_obj.blocks.add(being_blocked_user_obj)
#             #     # print('Not Found')

#             serialized_profile_data = ProfileSimpleSerializer(instance=profile_obj,context={"request": request}).data

#             # mongoDB
#             melive_mongo_db = MeLiveMongoDB()
#             collection_live_room = melive_mongo_db["LiveRoom"]
#             # filtered_rooms = collection_live_room.find({"channelName": f"{user.id}",}).limit(1)

#             # try:
#             #     temp = filtered_rooms[0]
#             #     # print('Exists')
#             #     collection_live_room.update_one(filter={"channelName": f"{user.id}",},update={'$set':{"blocks":serialized_profile_data['blocks']}})
#             # except:
#             #     # print('Not Exist')
#             #     pass
#             collection_live_room.update_one(filter={"channelName": f"{user.id}",},update={'$set':{"blocks":serialized_profile_data['blocks']}})
#             filtered_rooms = collection_live_room.find({"channelName": f"{user.id}",}).limit(1)
            
#             json_encoded = json.dumps(filtered_rooms[0], sort_keys=True, indent=4, default=json_util.default)
#             json_data = json.loads(json_encoded)

#             # Websocket
#             json_data['creation_time'] = json_data['creation_time']['$date']
#             json_data['type'] = 'add_live_room'

#             channel_layer = get_channel_layer()
#             async_to_sync(channel_layer.group_send)(
#                 f'live_streaming_livekit_streamings',
#                 {
#                     'type': 'live_streaming', 
#                     'message': json_data
#                 }
#             )

#             # try:
#             #     firebase_client = FirebaseClient()
#             #     firebase_client.firestore_db.collection("LiveRoom").document(f"{user.id}").update({"blocks":serialized_profile_data["blocks"]})
#             # except:
#             #     pass

#             profile_cache = cache.get(f'profile_{user.id}')
#             if profile_cache is not None:
#                 profile_cache['blocks'] = serialized_profile_data['blocks']
#                 # cache.delete(f'profile_{user.id}')
#                 cache.set(f'profile_{user.id}',profile_cache,timeout=60*60*24*2)
#             return Response({'blocks':serialized_profile_data['blocks']},status=HTTP_201_CREATED)

#         return Response(status=HTTP_204_NO_CONTENT)

class BlockV2CreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    lookup_field = 'uid'

    def create(self, request, *args, **kwargs):
        user = request.user
        uid = self.kwargs[self.lookup_field]

        being_blocked_user_obj = User.objects.filter(id=uid).select_related('profile').only('id','profile__id','profile__is_moderator').first()

        if being_blocked_user_obj and being_blocked_user_obj.profile.is_moderator == False:
            profile_obj = Profile.objects.filter(user=user).only('id','blocks').first()
            if being_blocked_user_obj in profile_obj.blocks.all():
                profile_obj.blocks.remove(being_blocked_user_obj)
            else:
                profile_obj.blocks.add(being_blocked_user_obj)

            serialized_profile_data = ProfileBlockSerializer(instance=profile_obj,context={"request": request}).data

            channel_id = user.id
            profile_cache = cache.get(f'profile_{channel_id}')
            if profile_cache is not None: 
                profile_cache['blocks'] = serialized_profile_data['blocks']
                # cache.delete(f'profile_{channel_id}')
                cache.set(f'profile_{channel_id}',profile_cache,timeout=60*60*24*30)

            live_room_data = cache.get(f"live_room_{channel_id}")
            if live_room_data is not None:
                live_room_data['owner_profile']['blocks'] = serialized_profile_data['blocks']
                cache.set(f"live_room_{channel_id}",live_room_data,timeout=60*60*24)

            data = {
                'type': 'live_room_blocks',
                'channel_id': channel_id,
                'uid': uid,
            }
            sendDataInGlobalWebsocket(data=data)
            return Response({'blocks':serialized_profile_data['blocks']},status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)
    
class FollowerListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user 

        profile_obj = Profile.objects.filter(user=user).prefetch_related('followers','followers__profile').only('followers',).first()

        # serializer_user_with_profiles = UserWithProfileSerializer(instance=user.profile.followers,many=True,context={"request": request})
        serializer_user_with_profiles = UserWithProfileSerializer(instance=profile_obj.followers,many=True,context={"request": request})
        return Response({'list_user_with_profile':serializer_user_with_profiles.data},status=HTTP_200_OK)

class BlockListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user 
        profile_obj = Profile.objects.filter(user=user).prefetch_related('blocks','blocks__profile').only('blocks',).first()
        serializer_user_with_profiles = UserWithProfileSerializer(instance=profile_obj.blocks,many=True,context={"request": request})
        return Response({'list_user_with_profile':serializer_user_with_profiles.data},status=HTTP_200_OK)

class BroadcasterHistoryListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]
    lookup_field = 'uid'

    # cache requested url (in Seconds)
    # @method_decorator(cache_page(60*60*1))
    # @method_decorator(vary_on_headers("Authorization",))
    def list(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        method_dict = request.GET
        is_agent_search = method_dict.get('is_agent_search','false')
        agent_uid = int(method_dict.get('agent_uid','0'))
        broadcaster_histories = []

        user_obj = None
        if is_agent_search == 'true':
            # Agent is searching host's history
            agent_obj = None
            if agent_uid > 0:
                agent_obj = Agent.objects.filter(user__id=agent_uid).prefetch_related('hosts').first()
            else:
                agent_obj = Agent.objects.filter(user=request.user).prefetch_related('hosts').first()
            if agent_obj:
                user_obj = agent_obj.hosts.filter(id=user_id).first()
                
        else:
            user_obj = User.objects.filter(id=user_id).first()
        if user_obj:
            broadcaster_histories_objs = BroadcasterHistory.objects.filter(user=user_obj)
            broadcaster_histories = BroadcasterHistorySerializer(instance=broadcaster_histories_objs,many=True,context={"request": request}).data
        return Response({'broadcaster_histories':broadcaster_histories},status=HTTP_200_OK)