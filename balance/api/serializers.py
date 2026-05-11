from rest_framework import serializers
from balance.models import (
    PaymentMethod,PaymentMethodAccountType, WithdrawRequest,
    # DepositRequest,Balance,
    # Plan,PlanPurchased,EarningHistory,EarnCoinExchanger,
    Contribution,
    )
from products.models import Level
from products.api.serializers import LevelSerializer
from profiles.api.serializers import ProfileSerializer

class PaymentMethodAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethodAccountType
        fields = '__all__'

class PaymentMethodSerializer(serializers.ModelSerializer):
    account_types = serializers.SerializerMethodField()

    class Meta:
        model = PaymentMethod
        fields = ['id','title','slug','logo','charge','account_types']

    def get_account_types(self,obj):
        account_type_objs = PaymentMethodAccountType.objects.filter(payment_method=obj)
        if account_type_objs:
            return PaymentMethodAccountTypeSerializer(instance=account_type_objs,many=True,context={"request": self._context['request']}).data
        return None

# class DepositRequestSerializer(serializers.ModelSerializer):
#     payment_method = serializers.SerializerMethodField()
   
#     class Meta:
#         model = DepositRequest
#         fields = ['id','payment_method','screenshot','amount','sender_number','transaction_id','feedback','is_pending','is_accepted','is_declined','requested_datetime']

#     def get_payment_method(self,obj):
#         payment_method_obj = obj.payment_method
#         return PaymentMethodSerializer(instance=payment_method_obj,context={"request": self._context['request']}).data

class WithdrawRequestSerializer(serializers.ModelSerializer):
    payment_method = serializers.SerializerMethodField()
    
    class Meta:
        model = WithdrawRequest
        fields = ['id','payment_method','payment_method_name','account_type','amount','received_amount','receiver_number','feedback','is_pending','is_accepted','is_declined','requested_datetime']

    def get_payment_method(self,obj):
        payment_method_obj = obj.payment_method
        return PaymentMethodSerializer(instance=payment_method_obj,context={"request": self._context['request']}).data


# class BalanceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Balance
#         fields = '__all__'

# class EarnCoinExchangerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EarnCoinExchanger
#         fields = '__all__'

# class PlanSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Plan
#         fields = '__all__'

# class PlanPurchasedSerializer(serializers.ModelSerializer):
#     plan = serializers.SerializerMethodField()
   
#     class Meta:
#         model = PlanPurchased
#         fields = ['id','user','plan','expired_datetime']

#     def get_plan(self,obj):
#         plan_obj = obj.plan
#         return PlanSerializer(instance=plan_obj,context={"request": self._context['request']}).data

# class EarningHistorySerializer(serializers.ModelSerializer):
#     gift_sender_user_profile = serializers.SerializerMethodField()
#     class Meta:
#         model = EarningHistory
#         fields = ['id','user','gift_sender_user_profile','diamonds','datetime']

#     def get_gift_sender_user_profile(self,obj):
#         gift_sender_profile_obj = obj.gift_sender.profile
#         return ProfileSerializer(instance=gift_sender_profile_obj,context={"request": self._context['request']}).data

class ContributionSerializer(serializers.ModelSerializer):
    contributor_profile = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    class Meta:
        model = Contribution
        fields = ['id','user','contributor_profile','level','diamonds','datetime']

    def get_contributor_profile(self,obj):
        contributor_profile_obj = obj.contributor.profile 
        return ProfileSerializer(instance=contributor_profile_obj,context={"request": self._context['request']}).data

    def get_level(self,obj):
        # outgoing_diamonds = 3500
        outgoing_diamonds = obj.contributor.profile.outgoing_diamonds
        level_obj = Level.objects.filter(diamonds__lte=outgoing_diamonds).first()
        if level_obj:
            return LevelSerializer(instance=level_obj,context={"request": self._context['request']}).data
        return None