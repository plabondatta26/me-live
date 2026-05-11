import json
from django.core.cache import cache
from rest_framework.generics import (
    CreateAPIView,ListAPIView, RetrieveAPIView, DestroyAPIView
    )
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,HTTP_204_NO_CONTENT,
    HTTP_207_MULTI_STATUS,HTTP_226_IM_USED,HTTP_208_ALREADY_REPORTED,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from business.models import (
    Agent, AgentRechargedHistory, AgentRequest, HostRequest,
    Reseller, ResellerRequest, ResellerHistory, ModeratorRequest,
    )
from profiles.api.serializers import ProfileSerializer
from .serializers import (
    AgentRechargedHistorySerializer, AgentSerializer, AgentRequestSerializer, HostRequestSerializer, HostRequestDetailsSerializer, HostSerializer,
    ResellerRequestSerializer, ResellerHistorySerializer, ModeratorRequestSerializer,
)
from accounts.models import User
from profiles.models import Profile
from me_live.utils.utils import DateTimeEncoder, updateProfileInGlobalWebsocket

class ModeratorRequestCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        profile_obj = user.profile
        if profile_obj.is_moderator:
            return Response(status=HTTP_226_IM_USED)
        if profile_obj.is_agent or profile_obj.is_host or profile_obj.is_reseller:
            return Response(status=HTTP_207_MULTI_STATUS)
      
        moderator_request_obj = ModeratorRequest.objects.filter(user=user).first()
        if moderator_request_obj:
            return Response(status=HTTP_208_ALREADY_REPORTED)
        moderator_request_obj = ModeratorRequest()
        moderator_request_obj.user = user
        moderator_request_obj.save()
        moderator_request_serializer = ModeratorRequestSerializer(instance=moderator_request_obj)

        return Response({'moderator_request':moderator_request_serializer.data,},status=HTTP_201_CREATED)
    
class ModeratorRequestRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        data = {
            'moderator_request': {},
        }
        moderator_request_obj = ModeratorRequest.objects.filter(user=user).first()
        if moderator_request_obj:
            moderator_request_serializer = ModeratorRequestSerializer(instance=moderator_request_obj)
            data['moderator_request'] = moderator_request_serializer.data

        return Response(data,status=HTTP_200_OK)

class ModeratorRequestDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        user = request.user
       
        moderator_request_obj = ModeratorRequest.objects.filter(user=user).first()
        if moderator_request_obj:
            self.perform_destroy(moderator_request_obj)
            return Response(status=HTTP_200_OK)

        return Response(status=HTTP_204_NO_CONTENT)
 
class AgentListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        agents_serializer = AgentSerializer(instance=Agent.objects.all(),many=True,context={"request": request})
        return Response({'agents':agents_serializer.data,},status=HTTP_200_OK)
    
def sortingFunc(e):
  return e['host_diamonds']
    
class TopRatedAgentListApiView(ListAPIView):
    authentication_classes = []
    permission_classes = []

    def list(self, request, *args, **kwargs):
        agent_objs = Agent.objects.select_related('user')\
                    .only('id','user__id','hosts').all()
        top_rated_agent_list = []
        for agent_obj in agent_objs:
            data = {}
            profile_cache = cache.get(f'profile_{agent_obj.user.id}')
            if profile_cache is None:
                profile_obj = Profile.objects.filter(user__id=agent_obj.user.id).first()
                if profile_obj:
                    # serializer_profile = ProfileForUserInfoSerializer(instance=profile_obj)
                    serializer_profile = ProfileSerializer(instance=profile_obj,)
                    profile_cache = serializer_profile.data
                    cache.set(f'profile_{agent_obj.user.id}',profile_cache,timeout=60*60*24*2)

                # profile_obj = Profile.objects.filter(user__id=agent_obj.user.id).only('id','full_name','profile_image','photo_url').first()
                # full_name = profile_obj.full_name
                # profile_image = profile_obj.profile_image

                # if profile_image is None:
                #     profile_image = profile_obj.photo_url
                # else:
                #     profile_image = f"{settings.BASE_URL}/media/{profile_image}"

                # data = {
                #     "uid": agent_obj.user.id, 
                #     "level": None,
                #     "vvip_or_vip_preference": {"vvip_or_vip_gif":None},
                #     "full_name": full_name,
                #     "profile_image": profile_image,
                # }
            # else:
            try:
                profile_cache['vvip_or_vip_preference'] = json.loads(profile_cache['vvip_or_vip_preference'])
            except:
                pass
            data = {
                "uid": agent_obj.user.id,
                "level": profile_cache['level'],
                "vvip_or_vip_preference": profile_cache['vvip_or_vip_preference'],
                "full_name": profile_cache['full_name'],
                "profile_image": profile_cache['profile_image'],
            }
            # photo_url = profile_obj.photo_url
            host_diamonds = 0
            host_objs = agent_obj.hosts.all()
            for host_obj in host_objs:
                profile_cache = cache.get(f'profile_{host_obj.id}')
                if profile_cache is None:
                    host_profile_obj = Profile.objects.filter(user__id=host_obj.id).only('id','diamonds').first()
                    diamonds = host_profile_obj.diamonds
                    host_diamonds += diamonds
                else:
                    host_diamonds += profile_cache['diamonds']

            data['host_diamonds'] = host_diamonds
            data['host_count'] = len(host_objs)
            top_rated_agent_list.append(data)

        top_rated_agent_list.sort(reverse=True,key=sortingFunc)
        return Response({'top_rated_agent_list':top_rated_agent_list},status=HTTP_200_OK)

class SearchAgentRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'user_id'

    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        data = {
            'agent': None,
        }
        agent_obj = Agent.objects.filter(user__id=user_id).first()
        if agent_obj:
            agent_serializer = AgentSerializer(instance=agent_obj,context={"request": request})
            data['agent'] = agent_serializer.data

        return Response(data,status=HTTP_200_OK)

class AgentForHostRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        data = {
            'agent': None,
        }
        agent_obj = Agent.objects.filter(hosts__in=[user]).first()
        if agent_obj:
            agent_serializer = AgentSerializer(instance=agent_obj,context={"request": request})
            data['agent'] = agent_serializer.data

        return Response(data,status=HTTP_200_OK)

class AgentRequestCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        profile_obj = user.profile
        if profile_obj.is_agent:
            return Response(status=HTTP_226_IM_USED)
        if profile_obj.is_host or profile_obj.is_reseller or profile_obj.is_moderator:
            return Response(status=HTTP_207_MULTI_STATUS)

        agent_request_obj = AgentRequest.objects.filter(user=user).first()
        if agent_request_obj:
            return Response(status=HTTP_208_ALREADY_REPORTED)
        agent_request_obj = AgentRequest()
        agent_request_obj.user = user
        agent_request_obj.save()
        agent_request_serializer = AgentRequestSerializer(instance=agent_request_obj)

        return Response({'agent_request':agent_request_serializer.data,},status=HTTP_201_CREATED)
    
class AgentRequestRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        data = {
            'agent_request': {},
        }
        agent_request_obj = AgentRequest.objects.filter(user=user).first()
        if agent_request_obj:
            agent_request_serializer = AgentRequestSerializer(instance=agent_request_obj)
            data['agent_request'] = agent_request_serializer.data

        return Response(data,status=HTTP_200_OK)

class AgentRequestDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        user = request.user
       
        agent_request_obj = AgentRequest.objects.filter(user=user).first()
        if agent_request_obj:
            self.perform_destroy(agent_request_obj)
            return Response(status=HTTP_200_OK)

        return Response(status=HTTP_204_NO_CONTENT)
    
class HostRequestCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        data_obj = request.data
        live_type = data_obj.get('live_type','audio')
        # Not allowed audio requrest
        if live_type == 'audio':
            return Response(status=HTTP_204_NO_CONTENT)
        
        agent_id = data_obj.get('agent_id',0)
        agent_obj = Agent.objects.filter(id=agent_id).first()
        if agent_obj is None:
            return Response(status=HTTP_204_NO_CONTENT)
        profile_obj = user.profile
        if profile_obj.is_host:
            return Response(status=HTTP_226_IM_USED)
        if profile_obj.is_agent or profile_obj.is_reseller or profile_obj.is_moderator:
            return Response(status=HTTP_207_MULTI_STATUS)
        
        host_request_obj = HostRequest.objects.filter(user=user).first()
        if host_request_obj:
            return Response(status=HTTP_208_ALREADY_REPORTED)
        host_request_obj = HostRequest()
        host_request_obj.user = user
        host_request_obj.agent = agent_obj
        if live_type == 'video':
            host_request_obj.is_allow_video_live = True
        host_request_obj.save()
        host_request_serializer = HostRequestSerializer(instance=host_request_obj)
        return Response({'host_request':host_request_serializer.data,},status=HTTP_201_CREATED)

class SearchHostRequestRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'user_id'

    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        method_dict = request.GET
        agent_uid = int(method_dict.get('agent_uid','0'))

        data = {
            'host_request': None,
        }
        host_request_obj = None
        if agent_uid > 0:
            host_request_obj = HostRequest.objects.filter(user__id=user_id,agent__user__id=agent_uid).select_related('user').prefetch_related('user__profile').first()
        else:
            host_request_obj = HostRequest.objects.filter(user__id=user_id,agent__user=request.user).select_related('user').prefetch_related('user__profile').first()
        if host_request_obj:
            host_request_serializer = HostRequestDetailsSerializer(instance=host_request_obj,context={"request": request})
            data['host_request'] = host_request_serializer.data

        return Response(data,status=HTTP_200_OK)

class ConfirmHostRequestCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        data_obj = request.data
        host_uid = data_obj.get('host_uid',0)
        agent_uid = data_obj.get('agent_uid',0)
       
        host_request_obj = None
        if agent_uid > 0:
            host_request_obj = HostRequest.objects.filter(user__id=host_uid,agent__user__id=agent_uid).first()
        else:
            host_request_obj = HostRequest.objects.filter(user__id=host_uid,agent__user__id=request.user.id).first()
       
        if host_request_obj is None:
            return Response(status=HTTP_204_NO_CONTENT)

        profile_obj = host_request_obj.user.profile
        if profile_obj.is_host:
            return Response(status=HTTP_226_IM_USED)
        if profile_obj.is_agent or profile_obj.is_reseller or profile_obj.is_moderator:
            return Response(status=HTTP_207_MULTI_STATUS)
        
        # Only allow video live
        if host_request_obj.is_allow_video_live == False:
            return Response(status=HTTP_204_NO_CONTENT)
     
        host_request_obj.is_approved = True
        host_request_obj.save()
        # host_request_serializer = HostRequestDetailsSerializer(instance=host_request_obj,context={"request": request})
        # return Response({'host_request':host_request_serializer.data,},status=HTTP_201_CREATED)
        return Response(status=HTTP_201_CREATED)


class HostRequestRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        data = {
            'host_request': {}
        }
        host_request_obj = HostRequest.objects.filter(user=user).first()
        if host_request_obj:
            host_request_serializer = HostRequestSerializer(instance=host_request_obj)
            data['host_request'] = host_request_serializer.data

        return Response(data,status=HTTP_200_OK)

class HostRequestDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        user = request.user
       
        host_request_obj = HostRequest.objects.filter(user=user).first()
        if host_request_obj:
            self.perform_destroy(host_request_obj)
            return Response(status=HTTP_200_OK)

        return Response(status=HTTP_204_NO_CONTENT)

class HostRequestListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        method_dict = request.GET
        agent_uid = int(method_dict.get('agent_uid','0'))
        agent_obj = None
        if agent_uid > 0:
            agent_obj = Agent.objects.filter(user__id=agent_uid).first()
        else:
            agent_obj = Agent.objects.filter(user=request.user).first()
        if agent_obj:
            host_request_objs = HostRequest.objects.filter(agent=agent_obj).select_related('user').prefetch_related('user__profile')
            host_request_serializer = HostRequestDetailsSerializer(instance=host_request_objs,many=True,context={"request": request})
            return Response({'host_request_list':host_request_serializer.data,},status=HTTP_200_OK)
        return Response(status=HTTP_204_NO_CONTENT)

class HostListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        method_dict = request.GET
        agent_uid = int(method_dict.get('agent_uid','0'))
        agent_obj = None
        if agent_uid > 0:
            agent_obj = Agent.objects.filter(user__id=agent_uid).prefetch_related('hosts','hosts__profile').first()
        else:
            agent_obj = Agent.objects.filter(user=request.user).prefetch_related('hosts','hosts__profile').first()
        if agent_obj:
            hosts_diamonds = 0
            hosts_audio_diamonds = 0
            hosts_video_diamonds = 0

            host_objs = agent_obj.hosts.all()
            for host_obj in host_objs:
                host_profile_obj = host_obj.profile
                hosts_diamonds += host_profile_obj.diamonds
                if host_profile_obj.is_allow_video_live == True:
                    hosts_video_diamonds += host_profile_obj.diamonds
                else:
                    hosts_audio_diamonds += host_profile_obj.diamonds

            hosts_serializer = HostSerializer(instance=host_objs,many=True,context={"request": request})
            data = {
                'hosts':hosts_serializer.data,
                'hosts_diamonds':hosts_diamonds,
                'hosts_audio_diamonds':hosts_audio_diamonds,
                'hosts_video_diamonds':hosts_video_diamonds,
                'hosts_count': host_objs.count(),
                'allow_remove': False,
                }
            return Response(data,status=HTTP_200_OK)
        return Response(status=HTTP_204_NO_CONTENT)

class HostDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        data_obj = request.data
        host_uid = data_obj.get('host_uid',0)
        agent_uid = data_obj.get('agent_uid',0)
        agent_obj = None
        if agent_uid > 0:
            agent_obj = Agent.objects.filter(user__id=agent_uid).first()
        else:
            agent_obj = Agent.objects.filter(user=request.user).first()
        if agent_obj:
            host_user_obj = User.objects.filter(id=host_uid).first()
            if host_user_obj:
                if host_user_obj in agent_obj.hosts.all():
                    agent_obj.hosts.remove(host_user_obj)
                    host_profile_obj = host_user_obj.profile
                    host_profile_obj.is_host = False
                    host_profile_obj.save()
                    updateProfileInGlobalWebsocket(host_profile_obj)

                    json_data = json.loads(agent_obj.host_joining_dates)
                    json_data.pop(f"{host_user_obj.id}",None)
                    # Added to the agent Table
                    agent_obj.host_joining_dates = DateTimeEncoder().encode(json_data)
                    agent_obj.save()

                    return Response(status=HTTP_200_OK)
        return Response(status=HTTP_204_NO_CONTENT)


class ResellerRequestCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        profile_obj = user.profile
        if profile_obj.is_reseller:
            return Response(status=HTTP_226_IM_USED)
        if profile_obj.is_agent or profile_obj.is_host or profile_obj.is_moderator:
            return Response(status=HTTP_207_MULTI_STATUS)

        reseller_request_obj = ResellerRequest.objects.filter(user=user).first()
        if reseller_request_obj:
            return Response(status=HTTP_208_ALREADY_REPORTED)
        reseller_request_obj = ResellerRequest()
        reseller_request_obj.user = user
        reseller_request_obj.save()
        reseller_request_serializer = ResellerRequestSerializer(instance=reseller_request_obj)

        return Response({'reseller_request':reseller_request_serializer.data,},status=HTTP_201_CREATED)
    
class ResellerRequestRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        data = {
            'reseller_request': {},
        }
        reseller_request_obj = ResellerRequest.objects.filter(user=user).first()
        if reseller_request_obj:
            reseller_request_serializer = ResellerRequestSerializer(instance=reseller_request_obj)
            data['reseller_request'] = reseller_request_serializer.data

        return Response(data,status=HTTP_200_OK)

class ResellerRequestDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        user = request.user
       
        reseller_request_obj = ResellerRequest.objects.filter(user=user).first()
        if reseller_request_obj:
            self.perform_destroy(reseller_request_obj)
            return Response(status=HTTP_200_OK)

        return Response(status=HTTP_204_NO_CONTENT)

class ResellerRechargeCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        customer_id = data_obj.get('customer_id',0)
        diamonds = data_obj.get('diamonds',0)

        user = request.user
        profile_obj = user.profile
        if profile_obj.is_reseller == False:
            return Response(status=HTTP_204_NO_CONTENT)

        if profile_obj.diamonds < diamonds:
            return Response(status=HTTP_204_NO_CONTENT)

        reseller_obj = Reseller.objects.filter(user=user).first()
        if reseller_obj is None:
            return Response(status=HTTP_204_NO_CONTENT)

        customer_user_obj = User.objects.filter(id=customer_id).first()
        if customer_user_obj is None:
            return Response(status=HTTP_204_NO_CONTENT)

        customer_profile_obj = customer_user_obj.profile
        if diamonds <= 0:
            return Response(status=HTTP_204_NO_CONTENT)

        # Update customer profile
        customer_profile_obj.diamonds += diamonds
        customer_profile_obj.save()

        # Update reseller profile
        profile_obj.diamonds -= diamonds
        profile_obj.save()
        
        reseller_history_obj = ResellerHistory()
        reseller_history_obj.user = customer_user_obj
        reseller_history_obj.reseller = reseller_obj
        reseller_history_obj.recharged_diamonds = diamonds
        reseller_history_obj.save()
        reseller_history_serializer = ResellerHistorySerializer(instance=reseller_history_obj,context={"request": request})

        return Response({'reseller_history':reseller_history_serializer.data,},status=HTTP_201_CREATED)

class ResellerRechargeHistoryListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        reseller_histories_serializer = ResellerHistorySerializer(instance=ResellerHistory.objects.filter(reseller__user=request.user),many=True,context={"request": request})
        return Response({'reseller_histories':reseller_histories_serializer.data,},status=HTTP_200_OK)

class ResellerRechargeHistoryDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        data_obj = request.data
        history_id = data_obj.get('history_id',0)

        reseller_history_obj = ResellerHistory.objects.filter(id=history_id,reseller__user=request.user).first()
        if reseller_history_obj:
            self.perform_destroy(reseller_history_obj)
            return Response(status=HTTP_200_OK)
        return Response(status=HTTP_204_NO_CONTENT)

# Agent Recharged
class AgentRechargedCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        customer_id = data_obj.get('customer_id',0)
        diamonds = data_obj.get('diamonds',0)

        user = request.user
        profile_obj = user.profile
        if profile_obj.is_agent == False:
            # print('No agent')
            return Response(status=HTTP_204_NO_CONTENT)

        if profile_obj.diamonds < diamonds:
            # print('No sufficient diamonds')
            return Response(status=HTTP_204_NO_CONTENT)

        agent_obj = Agent.objects.filter(user=user).first()
        if agent_obj is None:
            # print('Not agent')
            return Response(status=HTTP_204_NO_CONTENT)

        customer_user_obj = User.objects.filter(id=customer_id).first()
        if customer_user_obj is None:
            # print('No Customer')
            return Response(status=HTTP_204_NO_CONTENT)

        customer_profile_obj = customer_user_obj.profile
        if diamonds <= 0:
            # print('Diamond is Zero')
            return Response(status=HTTP_204_NO_CONTENT)

        # Update customer profile
        customer_profile_obj.diamonds += diamonds
        customer_profile_obj.save()

        # Update reseller profile
        profile_obj.diamonds -= diamonds
        profile_obj.save()
        
        agent_recharged_history_obj = AgentRechargedHistory()
        agent_recharged_history_obj.user = customer_user_obj
        agent_recharged_history_obj.agent = agent_obj
        agent_recharged_history_obj.recharged_diamonds = diamonds
        agent_recharged_history_obj.save()
        agent_recharged_history_serializer = AgentRechargedHistorySerializer(instance=agent_recharged_history_obj,context={"request": request})

        return Response({'agent_recharged_history':agent_recharged_history_serializer.data,},status=HTTP_201_CREATED)

class AgentRechargedHistoryListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):
        agent_recharged_histories_serializer = AgentRechargedHistorySerializer(instance=AgentRechargedHistory.objects.filter(agent__user=request.user),many=True,context={"request": request})
        return Response({'agent_recharged_histories':agent_recharged_histories_serializer.data,},status=HTTP_200_OK)

class AgentRechargedHistoryDestroyApiView(DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def destroy(self, request, *args, **kwargs):
        data_obj = request.data
        history_id = data_obj.get('history_id',0)

        agent_recharged_history_obj = AgentRechargedHistory.objects.filter(id=history_id,agent__user=request.user).first()
        if agent_recharged_history_obj:
            self.perform_destroy(agent_recharged_history_obj)
            return Response(status=HTTP_200_OK)
        return Response(status=HTTP_204_NO_CONTENT)
