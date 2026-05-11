from django.contrib import admin
from .models import LiveGroupRoomConfig, LiveRoom

admin.site.register(LiveGroupRoomConfig)

@admin.register(LiveRoom)
class CustomLiveRoom(admin.ModelAdmin):
    list_display = ['get_channel_id',
                    'title',
                    'get_is_video',
                    'viewers_count',
                    ]
    list_display_links = ['get_channel_id','get_is_video','title']
    ordering = ['id',]

    def get_channel_id(self, obj):
        return obj.channel_id

    get_channel_id.short_description = 'User ID'

    def get_is_video(self, obj):
        status = "Video"
        if obj.is_video == False:
            status = "Audio"
        return status
    
    get_is_video.short_description = 'Type'
