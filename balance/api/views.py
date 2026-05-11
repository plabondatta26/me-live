import json
from django.core.cache import cache
from rest_framework.generics import (
    RetrieveAPIView,CreateAPIView,ListAPIView,
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
from balance.models import (
    PaymentMethod,WithdrawRequest,
    # DepositRequest,Balance,
    # Plan,PlanPurchased,EarningHistory,EarnCoinExchanger,
    Contribution,
    )
from accounts.models import User
from products.models import WithdrawPackage
from profiles.models import Profile
from .serializers import (
    PaymentMethodSerializer,WithdrawRequestSerializer,
    # DepositRequestSerializer,BalanceSerializer,
    # PlanSerializer,PlanPurchasedSerializer,EarningHistorySerializer,EarnCoinExchangerSerializer,
    ContributionSerializer,
    )
from profiles.api.serializers import ProfileForUserInfoSerializer, ProfileSerializer, ProfileSimpleSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class TopContributorRankingListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def list(self, request, *args, **kwargs):
        method_dict = request.GET
        list_range = int(method_dict.get("list_range",20))

        top_contributors = []
        if list_range == 5:
            top_contributors = cache.get("top_sliding_contributors",[])
            # if top_contributors is None:
            #     top_contributors = getTopContributorList(list_range=list_range,request=request)
            #     # cache.set("top_sliding_contributors",top_contributors,timeout=60*30)
            #     cache.set("top_sliding_contributors",top_contributors,timeout=60*60)

        else:
            top_contributors = cache.get("top_contributors",[])
            # if top_contributors is None:
            #     top_contributors = getTopContributorList(list_range=list_range,request=request)
            #     # cache.set("top_contributors",top_contributors,timeout=60*10)
            #     cache.set("top_contributors",top_contributors,timeout=60*60)
                
        return Response({"top_contributors":top_contributors,},status=HTTP_200_OK)
    
def contributionFunc(e):
  return e['diamonds']
    
def getTopContributorList(list_range,request):
    top_contributors = []
    contribution_objs = Contribution.objects.all().select_related('contributor')
    if contribution_objs:

        tracking_array = []
        json_data = {}
        for contribution_obj in contribution_objs:
            try:
                json_data[f"{contribution_obj.contributor.id}"] = json_data[f"{contribution_obj.contributor.id}"] + contribution_obj.diamonds
            except:
                json_data[f"{contribution_obj.contributor.id}"] = contribution_obj.diamonds

        str_json_data = json.dumps(json_data)

        str_json_data = str_json_data.split("{")[1].split("}")[0]

        str_array = str_json_data.split(",")

        for str_item in str_array:
            inner_item_array = str_item.split(":")

            str_item = inner_item_array[0].strip().split("\"")[1].split("\"")[0]
            data = {
                "uid": int(str_item),
                "diamonds": int(inner_item_array[1]),
            }
            tracking_array.append(data)

        tracking_array.sort(reverse=True,key=contributionFunc)

        top_list = tracking_array[:list_range]

        for top_item in top_list:
            profile_cache = cache.get(f'profile_{top_item["uid"]}')
            if profile_cache is None:
                profile_obj = Profile.objects.filter(user__id=top_item["uid"]).first()
                if profile_obj:
                    # serializer_profile = ProfileForUserInfoSerializer(instance=profile_obj)
                    serializer_profile = ProfileSerializer(instance=profile_obj,context={"request": request})
                    profile_cache = serializer_profile.data
                    cache.set(f'profile_{top_item["uid"]}',profile_cache,timeout=60*60*24*2)

            try:
                profile_cache['vvip_or_vip_preference'] = json.loads(profile_cache['vvip_or_vip_preference'])
            except:
                pass


            data = {
                "uid": top_item["uid"],
                "level": profile_cache["level"],
                "vvip_or_vip_preference": profile_cache["vvip_or_vip_preference"],
                "full_name": profile_cache["full_name"],
                "profile_image": profile_cache["profile_image"],
                "diamonds": top_item["diamonds"],
                "is_agent": profile_cache["is_agent"],
                "is_reseller": profile_cache["is_reseller"],
                "is_host": profile_cache["is_host"],
                "is_moderator": profile_cache["is_moderator"],
            }

            top_contributors.append(data)
    return top_contributors

# class TopContributorRankingListApiView(ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated & HasAPIKey]

#     def list(self, request, *args, **kwargs):
#         method_dict = request.GET
#         list_range = int(method_dict.get("list_range",20))

#         top_contributors = []
#         if list_range == 5:
#             top_contributors = cache.get("top_sliding_contributors")
#             if top_contributors is None:
#                 top_contributors = getTopContributorList(list_range=list_range)
#                 cache.set("top_sliding_contributors",top_contributors,timeout=60*10)
#         else:
#             top_contributors = cache.get("top_contributors")
#             if top_contributors is None:
#                 top_contributors = getTopContributorList(list_range=list_range)
#                 cache.set("top_contributors",top_contributors,timeout=60*10)
                
#         return Response({"top_contributors":top_contributors,},status=HTTP_200_OK)
    
# def contributionFunc(e):
#   return e['diamonds']
    
# def getTopContributorList(list_range):
#     top_contributors = []
#     contribution_objs = Contribution.objects.all().select_related('contributor')
#     if contribution_objs:

#         tracking_array = []
#         json_data = {}
#         for contribution_obj in contribution_objs:
#             try:
#                 json_data[f"{contribution_obj.contributor.id}"] = json_data[f"{contribution_obj.contributor.id}"] + contribution_obj.diamonds
#             except:
#                 json_data[f"{contribution_obj.contributor.id}"] = contribution_obj.diamonds

#         str_json_data = json.dumps(json_data)

#         str_json_data = str_json_data.split("{")[1].split("}")[0]

#         str_array = str_json_data.split(",")

#         for str_item in str_array:
#             inner_item_array = str_item.split(":")

#             str_item = inner_item_array[0].strip().split("\"")[1].split("\"")[0]
#             data = {
#                 "uid": int(str_item),
#                 "diamonds": int(inner_item_array[1]),
#             }
#             tracking_array.append(data)

#         tracking_array.sort(reverse=True,key=contributionFunc)

#         top_list = tracking_array[:list_range]

#         for top_item in top_list:
#             profile_obj = Profile.objects.filter(user__id=top_item["uid"]).first()
#             if profile_obj:
#                 profile_data = ProfileForUserInfoSerializer(instance=profile_obj).data

#                 data = {
#                     "uid": top_item["uid"],
#                     "level": profile_data["level"],
#                     "vvip_or_vip_preference": profile_data["vvip_or_vip_preference"],
#                     "full_name": profile_data["full_name"],
#                     "profile_image": profile_data["profile_image"],
#                     "diamonds": top_item["diamonds"],
#                     "is_agent": profile_data["is_agent"],
#                     "is_reseller": profile_data["is_reseller"],
#                     "is_host": profile_data["is_host"],
#                     "is_moderator": profile_data["is_moderator"],
#                 }

#                 top_contributors.append(data)
#     return top_contributors

class ContributionListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ContributionSerializer
    lookup_field = 'user_id'

    def get_queryset(self):
        user_id = self.kwargs[self.lookup_field]
        return Contribution.objects.filter(user__id=user_id).order_by('-diamonds')[:20]

class CountributionByContributorIdRetrieveApiView(RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'channel_id'

    def retrieve(self, request, *args, **kwargs):
        channel_id = self.kwargs[self.lookup_field]
        method_dict = request.GET
        build_number = method_dict.get('build_number',0)
        device_id = method_dict.get('device_id',None)
        user = request.user

        mininum_required_build_number = 24

        if int(build_number) < mininum_required_build_number:
            host_user_obj = User.objects.filter(id=channel_id).first()
            if host_user_obj:
                serializer_profile = ProfileSimpleSerializer(instance=host_user_obj.profile,context={"request": request})

                channel_layer = get_channel_layer()

                disallowed_data = {
                    "action": 'blocks',
                    "uid": user.id,
                    'blocks':serializer_profile.data['blocks']
                }


                async_to_sync(channel_layer.group_send)(
                    f'live_streaming_{channel_id}_actions',
                    {
                        'type': 'live_streaming', 
                        'message': disallowed_data
                    }
                )


                if device_id is not None:

                    data = {
                            'type': 'device_block',
                            'device_blocked': True,
                            'device_id': device_id,
                            'user_id': user.id,
                        }
                    
                    async_to_sync(channel_layer.group_send)(
                        f'live_streaming_livekit_streamings',
                        {
                            'type': 'live_streaming', 
                            'message': data
                        }
                    )

                time.sleep(3)
                async_to_sync(channel_layer.group_send)(
                    f'live_streaming_{channel_id}_actions',
                    {
                        'type': 'live_streaming', 
                        'message': disallowed_data
                    }
                )
                time.sleep(2)
                async_to_sync(channel_layer.group_send)(
                    f'live_streaming_{channel_id}_actions',
                    {
                        'type': 'live_streaming', 
                        'message': disallowed_data
                    }
                )
                time.sleep(2)
                async_to_sync(channel_layer.group_send)(
                    f'live_streaming_{channel_id}_actions',
                    {
                        'type': 'live_streaming', 
                        'message': disallowed_data
                    }
                )
                time.sleep(2)
                async_to_sync(channel_layer.group_send)(
                    f'live_streaming_{channel_id}_actions',
                    {
                        'type': 'live_streaming', 
                        'message': disallowed_data
                    }
                )


                return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        contributor_id = user.id
        contribution_diamonds = 0
        contribution_obj = Contribution.objects.filter(contributor__id=contributor_id).filter(user__id=channel_id).first()
        if contribution_obj:
            contribution_diamonds = contribution_obj.diamonds
        return Response({'contribution_diamonds':contribution_diamonds,},status=HTTP_200_OK)


# class PlanListApiView(ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = PlanSerializer
#     queryset = Plan.objects.all()

# class PlanPurchasedListApiView(ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = PlanPurchasedSerializer
    
#     def get_queryset(self):
#         present_datetime = timezone.now()
#         return PlanPurchased.objects.filter(user=self.request.user,expired_datetime__gte=present_datetime)

# class EarningHistoryListApiView(ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = EarningHistorySerializer
    
#     def get_queryset(self):
#         return EarningHistory.objects.filter(user=self.request.user)

# class EarnCoinExchangerRetrieveApiView(RetrieveAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def retrieve(self, request, *args, **kwargs):
#         earn_coin_exchange_obj = EarnCoinExchanger.objects.first()
#         serializer_plan_earn_coin_exchanger = EarnCoinExchangerSerializer(instance=earn_coin_exchange_obj,context={'request': request})
#         return Response({'earn_coin_exchanger':serializer_plan_earn_coin_exchanger.data,},status=HTTP_200_OK)

# class PlanPurchasedRemaingMinutesRetrieveApiView(RetrieveAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def retrieve(self, request, *args, **kwargs):
#         present_datetime = timezone.now()
#         allow_streaming = False
#         plan_purchased_objs = PlanPurchased.objects.filter(user=request.user,expired_datetime__gte=present_datetime)
#         if plan_purchased_objs:
#             allow_streaming = True
#         return Response({'allow_streaming':allow_streaming,},status=HTTP_200_OK)

# class PlanPurchasedCreateApiView(CreateAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         data_obj = request.data
#         user = request.user

#         plan_id = data_obj.get('plan_id',None)
#         if plan_id:
#             plan_obj = Plan.objects.filter(id=plan_id).first()
#             if plan_obj:
#                 balance_obj = Balance.objects.filter(user=user).first()
#                 # No sufficient amount to purchase plan
#                 if balance_obj is None or balance_obj.amount < plan_obj.price:
#                     return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

#                 # Paid for Plan
#                 balance_obj.amount -= plan_obj.price
#                 balance_obj.save()
#                 plan_purchased_obj = PlanPurchased.objects.filter(user=user,plan=plan_obj).first()
#                 if plan_purchased_obj:
#                     # Update
#                     # Extend the validity
#                     plan_purchased_obj.expired_datetime += timedelta(days=plan_obj.days)
#                     plan_purchased_obj.save()
#                 else:
#                     # Create
#                     expired_datetime = timezone.now() + timedelta(days=plan_obj.days)
#                     plan_purchased_obj = PlanPurchased()
#                     plan_purchased_obj.user = user
#                     plan_purchased_obj.plan = plan_obj
#                     plan_purchased_obj.expired_datetime = expired_datetime
#                     plan_purchased_obj.save()
#                 serializer_plan_purchased = PlanPurchasedSerializer(instance=plan_purchased_obj,context={'request': request})
#                 return Response({'purchased_plan':serializer_plan_purchased.data,},status=HTTP_201_CREATED)

#         return Response(status=HTTP_204_NO_CONTENT)

class PaymentMethodListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentMethodSerializer

    def list(self, request, *args, **kwargs):
        user = request.user
        payment_methods_objs = PaymentMethod.objects.all()
        serializer_payment_methods = PaymentMethodSerializer(instance=payment_methods_objs,many=True,context={'request': request})

        return Response({'payment_methods':serializer_payment_methods.data,},status=HTTP_200_OK)
    
# class BalanceRetrieveApiView(RetrieveAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def retrieve(self, request, *args, **kwargs):
#         balance_obj = Balance.objects.filter(user=request.user).first()
#         serializer_balance = BalanceSerializer(instance=balance_obj,context={'request': request})
#         earn_coin_exchange_obj = EarnCoinExchanger.objects.first()
#         serializer_plan_earn_coin_exchanger = EarnCoinExchangerSerializer(instance=earn_coin_exchange_obj,context={'request': request})
#         return Response({'balance':serializer_balance.data,'earn_coin_exchanger':serializer_plan_earn_coin_exchanger.data,},status=HTTP_200_OK)

# class DepositRequestListApiView(ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def list(self, request, *args, **kwargs):
#         user = request.user
#         deposit_request_objs = DepositRequest.objects.filter(user=user)
#         serializer_deposit_request_list = DepositRequestSerializer(instance=deposit_request_objs,many=True,context={'request': request})

#         return Response({'deposit_request_list':serializer_deposit_request_list.data,},status=HTTP_200_OK)

# class DepositRequestCreateApiView(CreateAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         data_obj = request.data
#         user = request.user

#         payment_method_id = data_obj.get('payment_method',None)
#         amount = data_obj.get('amount',None)
#         screenshot = data_obj.get('screenshot',None)
#         sender_number = data_obj.get('sender_number',None)
#         transaction_id = data_obj.get('transaction_id',None)

#         if payment_method_id is not None and amount is not None and screenshot is not None and sender_number is not None:

#             payment_method_obj = PaymentMethod.objects.filter(id=payment_method_id).first()
#             if payment_method_obj:
#                 deposit_request_obj = DepositRequest()
#                 deposit_request_obj.user = user
#                 deposit_request_obj.payment_method = payment_method_obj
#                 deposit_request_obj.amount = amount
#                 deposit_request_obj.sender_number = sender_number
#                 deposit_request_obj.transaction_id = transaction_id

#                 compressed_image = compress(screenshot)
#                 # Choosing smaller image size
#                 if compressed_image.size > screenshot.size:
#                     compressed_image = screenshot
#                 deposit_request_obj.screenshot = compressed_image

#                 deposit_request_obj.save()
#                 # serializer_deposit_request = DepositRequestSerializer(instance=deposit_request_obj,context={'request': request})
#                 return Response(status=HTTP_201_CREATED)

#         return Response(status=HTTP_204_NO_CONTENT)

class WithdrawRequestListApiView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        withdraw_request_objs = WithdrawRequest.objects.filter(user=user)
        serializer_withdraw_request_list = WithdrawRequestSerializer(instance=withdraw_request_objs,many=True,context={'request': request})

        return Response({'withdraw_request_list':serializer_withdraw_request_list.data,},status=HTTP_200_OK)

class WithdrawRequestCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        user = request.user

        withdraw_package_id = data_obj.get('withdraw_package_id',None)
        payment_method_id = data_obj.get('payment_method_id',None)
        receiver_number = data_obj.get('receiver_number',None)
        account_type = data_obj.get('account_type',None)

        if withdraw_package_id and payment_method_id and receiver_number:
            payment_method_obj = PaymentMethod.objects.filter(id=payment_method_id).first()
            if payment_method_obj is None:
                return Response(status=HTTP_204_NO_CONTENT)
            withdraw_package_obj = WithdrawPackage.objects.filter(id=withdraw_package_id).first()
            if withdraw_package_obj:
                profile_obj = user.profile
                if profile_obj.diamonds < withdraw_package_obj.diamonds:
                    return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)
                profile_obj.diamonds -= withdraw_package_obj.diamonds
                profile_obj.save()

                withdraw_request_obj = WithdrawRequest()
                withdraw_request_obj.user = user
                withdraw_request_obj.payment_method = payment_method_obj
                withdraw_request_obj.withdraw_package = withdraw_package_obj
                withdraw_request_obj.payment_method_name = payment_method_obj.title
                withdraw_request_obj.account_type = account_type
                withdraw_request_obj.diamonds = withdraw_package_obj.diamonds
                withdraw_request_obj.amount = withdraw_package_obj.price
                withdraw_request_obj.received_amount = withdraw_package_obj.price - payment_method_obj.charge
                withdraw_request_obj.receiver_number = receiver_number
                withdraw_request_obj.save()

                data = {
                    'profile': ProfileSerializer(instance=profile_obj,context={"request": request}).data,
                    # 'withdraw_history': WithdrawRequestSerializer(instance=withdraw_request_obj,context={"request": request}).data,
                }
                return Response(data,status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)
