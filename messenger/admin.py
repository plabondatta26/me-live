from django.contrib import admin
from .models import LastChatMessage, ChatMessage, ChatBlock
# Register your models here.

admin.site.register(LastChatMessage)
admin.site.register(ChatMessage)
admin.site.register(ChatBlock)
