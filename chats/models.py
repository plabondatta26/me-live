from django.db import models
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from rest_framework import serializers

class ChatCost(models.Model):
	cost_diamonds = models.IntegerField(default=200)
	vat_diamonds = models.IntegerField(default=50)

	def save(self, *args, **kwargs):
		channel_layer = get_channel_layer()
		async_to_sync(channel_layer.group_send)(
            f'live_streaming_livekit_streamings', 
            {
                'type': 'live_streaming', 
                'message': {
                    'type': 'update_chat_vat',
                    'cost_diamonds': self.cost_diamonds,
                    'vat_diamonds': self.vat_diamonds,
                }
            }
        )
		super().save(*args, **kwargs)
		chat_vat_data = ChatCostSerializer(instance=self).data
		cache.set(key="chat_cost",value=chat_vat_data,timeout=60*60*24*7,)

	class Meta:
	    verbose_name_plural = "Chat Cost Diamonds"

	def __str__(self):
		return f"Cost diamonds: {self.cost_diamonds} > Vat diamonds: {self.vat_diamonds}"
	
class ChatCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatCost
        fields = '__all__'
