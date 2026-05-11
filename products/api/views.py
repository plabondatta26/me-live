from datetime import timedelta,datetime
import json
from django.utils import timezone
from django.core.cache import cache
from rest_framework.generics import (
    CreateAPIView,UpdateAPIView,ListAPIView, RetrieveAPIView,DestroyAPIView,
    )
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_203_NON_AUTHORITATIVE_INFORMATION,
    HTTP_204_NO_CONTENT,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from websocket import create_connection
from products.models import (
    StreamingJoiningGif, PurchasedStreamingJoiningGif,
    DiamondPackage,WithdrawPackage, NormalGift,AnimatedGift,
    PackageTheme, PurchasedPackageTheme,
    VipPackage, PurchasedVipPackage, VipPackageOrderingInfo,
    VVipPackage, PurchasedVVipPackage, VVipPackageOrderingInfo,
    )
from .serializers import (
    StreamingJoiningGifSerializer,PurchasedStreamingJoiningGifSerializer,
    DiamondPackageSerializer,WithdrawPackageSerializer, NormalGiftSerializer, AnimatedGiftSerializer,
    PackageThemeSerializer, PurchasedPackageThemeSerializer,
    VipPackageSerializer, PurchasedVipPackageSerializer, VipPackageOrderingInfoSerializer,
    VVipPackageSerializer, PurchasedVVipPackageSerializer, VVipPackageOrderingInfoSerializer,
    # YouTubeVideoSerializer,
    )

from profiles.api.serializers import ProfileSerializer
from me_live.utils.utils import DateTimeEncoder, compress, updateProfileInGlobalWebsocket
from me_live.utils.constants import liveRoomSocketBaseUrl


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_query_param = 'page'

# class YouTubeVideoListApiView(ListAPIView):
#     authentication_classes = []
#     permission_classes = [HasAPIKey]
#     queryset = YouTubeVideo.objects.all()
#     serializer_class = YouTubeVideoSerializer
#     pagination_class = StandardResultsSetPagination

#     # cache requested url (in Seconds)
#     @method_decorator(cache_page(60*60*24*7))
#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())

#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)

# class AddYouTubeVideoCreateApiView(CreateAPIView):
#     authentication_classes = []
#     permission_classes = [HasAPIKey]

#     def create(self, request, *args, **kwargs):

#         # url = "https://www.googleapis.com/youtube/v3/search?key=&maxResults=100&type=video&part=snippet&videoDefinition=standard&q=Taylor Swift music video"
#         # response = requests.get(url,)
#         # json_data = response.json()
#         # items = json_data['items']
#         # item_list = []
#         # for item in items:
#         #     youtube_vide_obj = YouTubeVideo(title=item['snippet']['title'],thumbnails=item['snippet']['thumbnails']['default']['url'],video_id=item['id']['videoId'])
#         #     item_list.append(youtube_vide_obj)

#         # if len(item_list) > 0:
#         #     YouTubeVideo.objects.bulk_create(item_list)
#         return Response(status=HTTP_201_CREATED)

class PurchasedStreamingJoiningGifRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def retrieve(self, request, *args, **kwargs):
        user = request.user

        present_datetime = timezone.now()
        purchased_streaming_joining_gif_objs = PurchasedStreamingJoiningGif.objects.filter(user=user,expired_datetime__gte=present_datetime)

        data = {
            'purchased_joining_gif': None,
        }
        if purchased_streaming_joining_gif_objs:
            purchased_streaming_joining_gif_obj = purchased_streaming_joining_gif_objs.filter(active=True).first()
            if purchased_streaming_joining_gif_obj is None:
                purchased_streaming_joining_gif_obj = purchased_streaming_joining_gif_objs.first()
                purchased_streaming_joining_gif_obj.active = True
                purchased_streaming_joining_gif_obj.save()
            data['purchased_joining_gif'] = PurchasedStreamingJoiningGifSerializer(instance=purchased_streaming_joining_gif_obj,context={'request': request}).data
       
        return Response(data,status=HTTP_200_OK)
# Working
class PurchasedStreamingJoiningGifActivationUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]
    lookup_field = 'purchased_joining_gif_id'

    def update(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        purchased_joining_gif_id = self.kwargs[self.lookup_field]
        present_datetime = timezone.now()
        purchased_streaming_joining_gif_obj = PurchasedStreamingJoiningGif.objects.filter(id=purchased_joining_gif_id,user=user,expired_datetime__gte=present_datetime).first()
        if purchased_streaming_joining_gif_obj:
            purchased_streaming_joining_gif_obj.active = True
            purchased_streaming_joining_gif_obj.save()

            # Inactivate Others
            inactivate_purchased_streaming_joining_gif_objs = PurchasedStreamingJoiningGif.objects.filter(user=user,expired_datetime__gte=present_datetime).exclude(id=purchased_streaming_joining_gif_obj.id)
            if inactivate_purchased_streaming_joining_gif_objs:
                for obj in inactivate_purchased_streaming_joining_gif_objs:
                    obj.active = False
                    obj.save()
            purchased_streaming_joining_gif_objs = PurchasedStreamingJoiningGif.objects.filter(user=user,expired_datetime__gte=present_datetime)

            purchased_streaming_joining_gif_data = PurchasedStreamingJoiningGifSerializer(instance=purchased_streaming_joining_gif_obj,context={'request': request}).data
            data = {
                'purchased_joining_gif_list': [],
                'selected_joining_gif': purchased_streaming_joining_gif_data,
            }
            data['purchased_joining_gif_list'] = PurchasedStreamingJoiningGifSerializer(instance=purchased_streaming_joining_gif_objs,many=True,context={'request': request}).data
            # updateProfileInGlobalWebsocket(user.profile)
            profile_cache = cache.get(f'profile_{user_id}')
            if profile_cache is not None:
                streaming_joining_gif = purchased_streaming_joining_gif_data['joining_gif']['gif']
                json_data = {"joining_gif":streaming_joining_gif, "expired_datetime": purchased_streaming_joining_gif_obj.expired_datetime, }
                profile_cache['streaming_joining'] = DateTimeEncoder().encode(json_data)

                cache.delete(f'profile_{user_id}')
                cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)

            return Response(data,status=HTTP_200_OK)
        return Response(status=HTTP_204_NO_CONTENT)

class PurchasedStreamingJoiningGifListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):
        user = request.user

        present_datetime = timezone.now()
        purchased_streaming_joining_gif_objs = PurchasedStreamingJoiningGif.objects.filter(user=user,expired_datetime__gte=present_datetime)

        data = {
            'purchased_joining_gif_list': [],
            'joining_gif_list': [],
        }
        data['purchased_joining_gif_list'] = PurchasedStreamingJoiningGifSerializer(instance=purchased_streaming_joining_gif_objs,many=True,context={'request': request}).data

        joining_gif_list = cache.get('joining_gif_list')
        if joining_gif_list is None:
            streaming_joining_gif_objs = StreamingJoiningGif.objects.all()
            joining_gif_list = StreamingJoiningGifSerializer(instance=streaming_joining_gif_objs,many=True,context={'request': request}).data
            cache.set('joining_gif_list',joining_gif_list,timeout=60*60*24*7)
        data['joining_gif_list'] = joining_gif_list


        return Response(data,status=HTTP_200_OK)

class StreamingJoiningGifPurchaseCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        user = request.user

        # TODO: Must correct joinging typo after published in playstore
        if data_obj.get('streaming_joining_gif_id',None):
            streaming_joining_gif_id = data_obj.get('streaming_joining_gif_id') 
        else:
            streaming_joining_gif_id = data_obj.get('streaming_joinging_gif_id',None)
        if streaming_joining_gif_id:
            streaming_joining_gif_obj = StreamingJoiningGif.objects.filter(id=streaming_joining_gif_id).first()
            if streaming_joining_gif_obj:
                profile_obj = user.profile
                # No sufficient diamond to purchase StreamingJoiningGif
                if profile_obj.diamonds < streaming_joining_gif_obj.diamonds:
                    return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

                # Paid for StreamingJoiningGif
                profile_obj.diamonds -= streaming_joining_gif_obj.diamonds
                profile_obj.save()
                streaming_joining_gif_purchased_obj = PurchasedStreamingJoiningGif.objects.filter(user=user,joining_gif=streaming_joining_gif_obj).first()
                # streaming_joining_gif_purchased_obj = PurchasedStreamingJoiningGif.objects.filter(user=user).first()

                present_datetime = timezone.now()
                
                if streaming_joining_gif_purchased_obj and streaming_joining_gif_purchased_obj.expired_datetime >= present_datetime:
                    # Update
                    # Extend the validity
                    streaming_joining_gif_purchased_obj.expired_datetime += timedelta(days=streaming_joining_gif_obj.days)
                    streaming_joining_gif_purchased_obj.purchased_datetime = timezone.now()
                    streaming_joining_gif_purchased_obj.save()

                    # expired_datetime = timezone.now() + timedelta(days=streaming_joining_gif_obj.days)
                    # streaming_joining_gif_purchased_obj.joining_gif = streaming_joining_gif_obj
                    # streaming_joining_gif_purchased_obj.expired_datetime = expired_datetime
                    # streaming_joining_gif_purchased_obj.purchased_datetime = timezone.now()
                    # streaming_joining_gif_purchased_obj.save()
                else:
                    # Create
                    expired_datetime = timezone.now() + timedelta(days=streaming_joining_gif_obj.days)
                    streaming_joining_gif_purchased_obj = PurchasedStreamingJoiningGif()
                    streaming_joining_gif_purchased_obj.user = user
                    streaming_joining_gif_purchased_obj.joining_gif = streaming_joining_gif_obj
                    streaming_joining_gif_purchased_obj.active = True
                    streaming_joining_gif_purchased_obj.expired_datetime = expired_datetime
                    streaming_joining_gif_purchased_obj.purchased_datetime = timezone.now()
                    streaming_joining_gif_purchased_obj.save()

                    # Inactivate Others
                    purchased_streaming_joining_gif_objs = PurchasedStreamingJoiningGif.objects.filter(user=user,expired_datetime__gte=present_datetime).exclude(id=streaming_joining_gif_purchased_obj.id)
                    if purchased_streaming_joining_gif_objs:
                        for obj in purchased_streaming_joining_gif_objs:
                            obj.active = False
                            obj.save()

                # serializer_streaming_joining_gif_purchased = PurchasedStreamingJoiningGifSerializer(instance=streaming_joining_gif_purchased_obj,context={'request': request})
                purchased_streaming_joining_gif_objs = PurchasedStreamingJoiningGif.objects.filter(user=user,expired_datetime__gte=present_datetime)
                data = {
                    'purchased_joining_gif_list': [],
                }
                data['purchased_joining_gif_list'] = PurchasedStreamingJoiningGifSerializer(instance=purchased_streaming_joining_gif_objs,many=True,context={'request': request}).data
                
                updateProfileInGlobalWebsocket(user.profile)
                return Response(data,status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)

class PurchasedPackageThemeRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def retrieve(self, request, *args, **kwargs):
        user = request.user

        present_datetime = timezone.now()
        purchased_package_theme_objs = PurchasedPackageTheme.objects.filter(user=user,expired_datetime__gte=present_datetime)

        data = {
            'purchased_package_theme': None,
        }
        if purchased_package_theme_objs:
            purchased_package_theme_obj = purchased_package_theme_objs.filter(active=True).first()
            if purchased_package_theme_obj is None:
                purchased_package_theme_obj = purchased_package_theme_objs.first()
                purchased_package_theme_obj.active = True
                purchased_package_theme_obj.save()
            data['purchased_package_theme'] = PurchasedPackageThemeSerializer(instance=purchased_package_theme_obj,context={'request': request}).data
       
        return Response(data,status=HTTP_200_OK)

# Working
class PurchasedPackageThemeActivationUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]
    lookup_field = 'purchased_package_theme_id'

    def update(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        purchased_package_theme_id = self.kwargs[self.lookup_field]
        present_datetime = timezone.now()
        purchased_package_theme_obj = PurchasedPackageTheme.objects.filter(id=purchased_package_theme_id,user=user,expired_datetime__gte=present_datetime).first()
        if purchased_package_theme_obj:
            purchased_package_theme_obj.active = True
            purchased_package_theme_obj.save()

            # Inactivate Others
            inactivate_purchased_package_theme_objs = PurchasedPackageTheme.objects.filter(user=user,expired_datetime__gte=present_datetime).exclude(id=purchased_package_theme_obj.id)
            if inactivate_purchased_package_theme_objs:
                for obj in inactivate_purchased_package_theme_objs:
                    obj.active = False
                    obj.save()
            purchased_package_theme_objs = PurchasedPackageTheme.objects.filter(user=user,expired_datetime__gte=present_datetime)
            purchased_package_theme_gif_data = PurchasedPackageThemeSerializer(instance=purchased_package_theme_obj,context={'request': request}).data
            data = {
                'purchased_package_theme_list': [],
                'selected_package_theme': purchased_package_theme_gif_data,
            }
            data['purchased_package_theme_list'] = PurchasedPackageThemeSerializer(instance=purchased_package_theme_objs,many=True,context={'request': request}).data
            # updateProfileInGlobalWebsocket(user.profile)
            profile_cache = cache.get(f'profile_{user_id}')
            if profile_cache is not None:
                # package_theme_gif = purchased_package_theme_gif_data['package_theme']['gif']
                if purchased_package_theme_obj.package_theme is not None:
                    purchased_package_theme = purchased_package_theme_gif_data['package_theme']['gif']
                else:
                    purchased_package_theme = purchased_package_theme_gif_data['custom_theme_image']

                json_data = {"theme_gif":purchased_package_theme, "expired_datetime": purchased_package_theme_obj.expired_datetime,}
                profile_cache['package_theme'] = DateTimeEncoder().encode(json_data)

                cache.delete(f'profile_{user_id}')
                cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)

                # # Singnal into Live
                # channel_layer = get_channel_layer() 
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
            return Response(data,status=HTTP_200_OK)
        return Response(status=HTTP_204_NO_CONTENT)

class PurchasedPackageThemeListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):
        user = request.user

        present_datetime = timezone.now()
        purchased_package_theme_objs = PurchasedPackageTheme.objects.filter(user=user,expired_datetime__gte=present_datetime)

        data = {
            'purchased_package_theme_list': [],
            'package_theme_list': [],
        }
        data['purchased_package_theme_list'] = PurchasedPackageThemeSerializer(instance=purchased_package_theme_objs,many=True,context={'request': request}).data

        package_theme_list = cache.get('package_theme_list')
        if package_theme_list is None:
            package_theme_objs = PackageTheme.objects.all()
            package_theme_list = PackageThemeSerializer(instance=package_theme_objs,many=True,context={'request': request}).data
            cache.set('package_theme_list',package_theme_list,timeout=60*60*24*7)
        data['package_theme_list'] = package_theme_list

        return Response(data,status=HTTP_200_OK)

class PackageThemePurchaseCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        user = request.user
        custom_theme_image = data_obj.get('custom_theme_image',None)

        if custom_theme_image == '':
            custom_theme_image = None

        if custom_theme_image is not None:
            compressed_image = compress(custom_theme_image)
            # Choosing smaller image size
            if compressed_image.size > custom_theme_image.size:
                compressed_image = custom_theme_image

            expired_datetime = data_obj.get('expired_datetime',None)
            datetime_str = expired_datetime.split('.')[0]
            datetime_format = '%Y-%m-%dT%H:%M:%S'

            expired_datetime = datetime.strptime(datetime_str, datetime_format)

            present_datetime = timezone.now()

            package_theme_purchased_obj = PurchasedPackageTheme()
            package_theme_purchased_obj.user = user
            package_theme_purchased_obj.active = False
            package_theme_purchased_obj.custom_theme_image = compressed_image
            package_theme_purchased_obj.expired_datetime = expired_datetime
            package_theme_purchased_obj.purchased_datetime = timezone.now()
            package_theme_purchased_obj.save()

            purchased_package_theme_objs = PurchasedPackageTheme.objects.filter(user=user,expired_datetime__gte=present_datetime)
            data = {
                'purchased_package_theme_list': [],
            }
            data['purchased_package_theme_list'] = PurchasedPackageThemeSerializer(instance=purchased_package_theme_objs,many=True,context={'request': request}).data
            
            return Response(data,status=HTTP_201_CREATED)

        package_theme_id = data_obj.get('package_theme_id',None)
        if package_theme_id:
            package_theme_obj = PackageTheme.objects.filter(id=package_theme_id).first()
            if package_theme_obj:
                profile_obj = user.profile
                # No sufficient diamond to purchase PackageTheme
                if profile_obj.diamonds < package_theme_obj.diamonds:
                    return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

                # Paid for PackageTheme
                profile_obj.diamonds -= package_theme_obj.diamonds
                profile_obj.save()
                package_theme_purchased_obj = PurchasedPackageTheme.objects.filter(user=user,package_theme=package_theme_obj).first()
                # package_theme_purchased_obj = PurchasedPackageTheme.objects.filter(user=user).first()

                present_datetime = timezone.now()
                
                if package_theme_purchased_obj and package_theme_purchased_obj.expired_datetime >= present_datetime:
                    # Update
                    # Extend the validity
                    package_theme_purchased_obj.expired_datetime += timedelta(days=package_theme_obj.days)
                    package_theme_purchased_obj.purchased_datetime = timezone.now()
                    package_theme_purchased_obj.save()

                    # expired_datetime = timezone.now() + timedelta(days=package_theme_obj.days)
                    # package_theme_purchased_obj.package_theme = package_theme_obj
                    # package_theme_purchased_obj.expired_datetime = expired_datetime
                    # package_theme_purchased_obj.purchased_datetime = timezone.now()
                    # package_theme_purchased_obj.save()
                else:
                    # Create
                    expired_datetime = timezone.now() + timedelta(days=package_theme_obj.days)
                    package_theme_purchased_obj = PurchasedPackageTheme()
                    package_theme_purchased_obj.user = user
                    package_theme_purchased_obj.package_theme = package_theme_obj
                    package_theme_purchased_obj.active = True
                    package_theme_purchased_obj.expired_datetime = expired_datetime
                    package_theme_purchased_obj.purchased_datetime = timezone.now()
                    package_theme_purchased_obj.save()

                    # Inactivate Others
                    purchased_package_theme_objs = PurchasedPackageTheme.objects.filter(user=user,expired_datetime__gte=present_datetime).exclude(id=package_theme_purchased_obj.id)
                    if purchased_package_theme_objs:
                        for obj in purchased_package_theme_objs:
                            obj.active = False
                            obj.save()

                # serializer_package_theme_purchased = PurchasedPackageThemeSerializer(instance=package_theme_purchased_obj,context={'request': request})
                purchased_package_theme_objs = PurchasedPackageTheme.objects.filter(user=user,expired_datetime__gte=present_datetime)
                data = {
                    'purchased_package_theme_list': [],
                }
                data['purchased_package_theme_list'] = PurchasedPackageThemeSerializer(instance=purchased_package_theme_objs,many=True,context={'request': request}).data
                
                updateProfileInGlobalWebsocket(user.profile)
                return Response(data,status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)

class PurchasedVipPackageListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):
        user = request.user

        present_datetime = timezone.now()
        purchased_vip_package_obj = PurchasedVipPackage.objects.filter(user=user,expired_datetime__gte=present_datetime).first()
 
        data = {
            'purchased_vip_package': None,
            'vip_package_ordering_info': None,
            'vip_package_list': [],
        }
        if purchased_vip_package_obj:
            data['purchased_vip_package'] = PurchasedVipPackageSerializer(instance=purchased_vip_package_obj,context={'request': request}).data
        
        vip_package_ordering_info = cache.get('vip_package_ordering_info')
        if vip_package_ordering_info is None:
            vip_package_ordering_info_obj = VipPackageOrderingInfo.objects.first()
            if vip_package_ordering_info_obj:
                vip_package_ordering_info = VipPackageOrderingInfoSerializer(instance=vip_package_ordering_info,context={'request': request}).data
                cache.set('vip_package_ordering_info',vip_package_ordering_info,timeout=60*60*24*7)
        data['vip_package_ordering_info'] = vip_package_ordering_info

        vip_package_list = cache.get('vip_package_list')
        if vip_package_list is None:
            vip_package_list_objs = VipPackage.objects.all()
            vip_package_list = VipPackageSerializer(instance=vip_package_list_objs,many=True,context={'request': request}).data
            cache.set('vip_package_list',vip_package_list,timeout=60*60*24*7)
        data['vip_package_list'] = vip_package_list

        return Response(data,status=HTTP_200_OK)
    
class CustomPackageThemeImageDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def destroy(self, request, *args, **kwargs):
        user = request.user
        purchased_package_theme_obj = PurchasedPackageTheme.objects.filter(user=user,package_theme = None).first()
        if purchased_package_theme_obj:
            purchased_package_theme_obj.delete()
            return Response(status=HTTP_200_OK)
            
        return Response(status=HTTP_204_NO_CONTENT)
    
class PurchasedVvipPackageListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):
        user = request.user

        present_datetime = timezone.now()
 
        data = {
            'purchased_vvip_package': None,
            'vvip_package_ordering_info': None,
            'vvip_package_list': [],
        }
        purchased_vvip_package_obj = PurchasedVVipPackage.objects.filter(user=user,expired_datetime__gte=present_datetime).first()
        if purchased_vvip_package_obj:
            data['purchased_vvip_package'] = PurchasedVVipPackageSerializer(instance=purchased_vvip_package_obj,context={'request': request}).data

        vvip_package_ordering_info = cache.get('vvip_package_ordering_info')
        if vvip_package_ordering_info is None:
            vvip_package_ordering_info_obj = VVipPackageOrderingInfo.objects.first()
            if vvip_package_ordering_info_obj:
                vvip_package_ordering_info = VVipPackageOrderingInfoSerializer(instance=vvip_package_ordering_info_obj,context={'request': request}).data
                cache.set('vvip_package_ordering_info',vvip_package_ordering_info,timeout=60*60*24*7)
        data['vvip_package_ordering_info'] = vvip_package_ordering_info

        vvip_package_list = cache.get('vvip_package_list')
        if vvip_package_list is None:
            vvip_package_list_objs = VVipPackage.objects.all()
            vvip_package_list = VVipPackageSerializer(instance=vvip_package_list_objs,many=True,context={'request': request}).data
            cache.set('vvip_package_list',vvip_package_list,timeout=60*60*24*7)
        data['vvip_package_list'] = vvip_package_list

        return Response(data,status=HTTP_200_OK)
# Working
class DiamondPackageListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):
        user = request.user
        profile_obj = user.profile
        user_id = user.id

        profile_cache = cache.get(f'profile_{user_id}')
        if profile_cache is None:
            profile_cache = ProfileSerializer(instance=profile_obj,context={"request": request}).data
            cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)

        data = {
            'diamond_packages': [],
            'profile': profile_cache,
        }
        diamond_packages_data = cache.get('diamond_packages')
        if diamond_packages_data is None:
            diamond_packages_objs = DiamondPackage.objects.all()
            diamond_packages_data = DiamondPackageSerializer(instance=diamond_packages_objs,many=True,context={'request': request}).data
            cache.set('diamond_packages',diamond_packages_data,timeout=60*60*24*7)            
        data['diamond_packages'] = diamond_packages_data

        return Response(data,status=HTTP_200_OK)
# Working
class WithdrawPackageListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):
        user = request.user
        profile_obj = user.profile
        user_id = user.id

        profile_cache = cache.get(f'profile_{user_id}')
        if profile_cache is None:
            profile_cache = ProfileSerializer(instance=profile_obj,context={"request": request}).data
            cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)

        data = {
            'withdraw_packages': [],
            'profile': profile_cache,
        }

        withdraw_packages_data = cache.get('withdraw_packages')
        if withdraw_packages_data is None:
            withdraw_packages_objs = WithdrawPackage.objects.all()
            withdraw_packages_data = WithdrawPackageSerializer(instance=withdraw_packages_objs,many=True,context={'request': request}).data
            cache.set('withdraw_packages',withdraw_packages_data,timeout=60*60*24*7)
        data['withdraw_packages'] = withdraw_packages_data

        return Response(data,status=HTTP_200_OK)

class DiamodPackagePurchaseCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        user = request.user

        diamond_package_id = data_obj.get('diamond_package_id',None)
        if diamond_package_id:
            diamond_package_obj = DiamondPackage.objects.filter(id=diamond_package_id).first()
            if diamond_package_obj:
                profile_obj = user.profile
                # TODO: Need to attached with Payment gateway
                # //////////////////////////////////////////////////
                # Testing purpose:
                profile_obj.diamonds += diamond_package_obj.diamonds
                profile_obj.save()

                data = {
                    'profile': ProfileSerializer(instance=profile_obj,context={"request": request}).data,
                }
                return Response(data,status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)

class GiftListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):

        data = {
            'normal_gifts': [],
            'animated_gifts': [],
        }
        normal_gifts = cache.get('normal_gifts')
        if normal_gifts is None:
            normal_gift_objs = NormalGift.objects.all()
            normal_gifts = NormalGiftSerializer(instance=normal_gift_objs,many=True,context={'request': request}).data
            cache.set('normal_gifts',normal_gifts,timeout=60*60*24*7)
        data['normal_gifts'] = normal_gifts

        animated_gifts =  cache.get('animated_gifts')
        if animated_gifts is None:
            animated_gift_objs = AnimatedGift.objects.all()
            animated_gifts = AnimatedGiftSerializer(instance=animated_gift_objs,many=True,context={'request': request}).data
            cache.set('animated_gifts',animated_gifts,timeout=60*60*24*7)
        data['animated_gifts'] = animated_gifts

        return Response(data,status=HTTP_200_OK)
