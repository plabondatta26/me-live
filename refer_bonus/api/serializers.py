from rest_framework import serializers
from refer_bonus.models import ReferBonusAmount, ReferHistory

class ReferBonusAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferBonusAmount
        fields = '__all__'

class ReferHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferHistory
        fields = '__all__'