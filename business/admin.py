from django.contrib import admin
from .models import (
    Agent, AgentRequest, HostRequest, Reseller, ResellerRequest,
    Moderator, ModeratorRequest,
    )

@admin.register(Moderator)
class CustomModerator(admin.ModelAdmin):
    list_display = [
                    'get_uid',
                    # 'get_all_hosts',
                    'datetime',
                    ]
    list_display_links = ['get_uid',]
    ordering = ['-id',]
    search_fields = ['user__id','user__phone','user__profile__full_name',] 
    readonly_fields = ['user','datetime',]

    # def has_delete_permission(self, request, obj=None): 
    #     return False

    def get_uid(self, obj):
      return obj.user.id

    get_uid.short_description = 'User ID'

    # def get_all_hosts(self, obj):
    # 	return obj.hosts.count()

    # get_all_hosts.short_description = 'All Hosts'
 
@admin.register(ModeratorRequest)
class CustomModeratorRequest(admin.ModelAdmin):
    list_display = [
                    'get_uid',
                    'get_profile',
                    'is_approved',
                    'is_declined',
                    'datetime',
                    ]
    list_display_links = ['get_profile','get_uid']
    ordering = ['-id',]
    search_fields = ['user__id','user__phone','user__profile__full_name',] 
    # readonly_fields = ['user']

    def get_uid(self, obj):
      return obj.user.id

    get_uid.short_description = 'User ID'

    def get_profile(self, obj):
    	return obj.user.profile

    get_profile.short_description = 'Profile'

@admin.register(Agent)
class CustomAgent(admin.ModelAdmin):
    list_display = [
                    'get_uid',
                    'get_all_hosts',
                    'get_audio_hosts',
                    'get_video_hosts',
                    # 'get_host_diamonds',
                    'get_host_diamonds',
                    'get_audio_host_diamonds',
                    'get_video_host_diamonds',
                    'last_hosts_diamonds_clear_datetime',
                    ]
    list_display_links = ['get_uid',]
    ordering = ['-id',]
    search_fields = ['user__id','user__phone','user__profile__full_name',] 
    readonly_fields = ['user','hosts','host_joining_dates','last_hosts_diamonds_clear_datetime',]

    # def has_delete_permission(self, request, obj=None): 
    #     return False

    def get_uid(self, obj):
      return obj.user.id

    get_uid.short_description = 'User ID'

    def get_all_hosts(self, obj):
        return obj.hosts.count()

    get_all_hosts.short_description = 'All Hosts'


    def get_audio_hosts(self, obj):
        audio_hosts = 0
        for host_obj in obj.hosts.all():
            host_profile_obj = host_obj.profile
            if host_profile_obj.is_allow_video_live == False:
                audio_hosts += 1
          
        return audio_hosts

    get_audio_hosts.short_description = 'Audio Hosts'


    def get_video_hosts(self, obj):
        video_hosts = 0
        for host_obj in obj.hosts.all():
            host_profile_obj = host_obj.profile
            if host_profile_obj.is_allow_video_live == True:
                video_hosts += 1
          
        return video_hosts

    get_video_hosts.short_description = 'Video Hosts'

    # def get_host_diamonds(self, obj):
    #   diamonds = 0
    #   for user_obj in obj.hosts.all():
    #      diamonds += user_obj.profile.diamonds
    #   return diamonds

    # get_host_diamonds.short_description = 'Hosts Diamonds'

    def get_host_diamonds(self, obj):
      diamonds = 0
      for user_obj in obj.hosts.all():
         diamonds += user_obj.profile.diamonds
      return diamonds

    get_host_diamonds.short_description = 'Hosts Total Diamonds'

    def get_audio_host_diamonds(self, obj):
        diamonds = 0
        for user_obj in obj.hosts.all():
            profile_obj = user_obj.profile
            if profile_obj.is_allow_video_live == False:
                diamonds += profile_obj.diamonds
        return diamonds

    get_audio_host_diamonds.short_description = 'Audio Diamonds'


    def get_video_host_diamonds(self, obj):
        diamonds = 0
        for user_obj in obj.hosts.all():
            profile_obj = user_obj.profile
            if profile_obj.is_allow_video_live == True:
                diamonds += profile_obj.diamonds
        return diamonds

    get_video_host_diamonds.short_description = 'Video Diamonds'

@admin.register(AgentRequest)
class CustomAgentRequest(admin.ModelAdmin):
    list_display = [
                    'get_uid',
                    'get_profile',
                    'is_approved',
                    'is_declined',
                    'get_diamonds',
                    'datetime',
                    ]
    list_display_links = ['get_profile','get_uid']
    ordering = ['-id',]
    search_fields = ['user__id','user__phone','user__profile__full_name',] 
    # readonly_fields = ['user']

    def get_uid(self, obj):
      return obj.user.id

    get_uid.short_description = 'User ID'

    def get_profile(self, obj):
        return obj.user.profile

    get_profile.short_description = 'Profile'

    def get_diamonds(self, obj):
      return obj.user.profile.diamonds

    get_diamonds.short_description = 'Diamonds'

@admin.register(HostRequest)
class CustomHostRequest(admin.ModelAdmin):
    list_display = [
                    'get_uid',
                    'get_agent_id',
                    'is_approved',
                    'is_declined',
                    'get_diamonds',
                    'datetime',
                    ]
    list_display_links = ['get_agent_id','get_uid']
    ordering = ['-id',]
    search_fields = ['user__id','user__phone','user__profile__full_name',] 
    readonly_fields = ['user','agent','is_allow_video_live']

    def get_uid(self, obj):
      return obj.user.id

    get_uid.short_description = 'User ID'

    def get_agent_id(self, obj):
        return obj.agent.id

    get_agent_id.short_description = 'Agent ID'

    def get_diamonds(self, obj):
      return obj.user.profile.diamonds

    get_diamonds.short_description = 'Diamonds'

@admin.register(Reseller)
class CustomReseller(admin.ModelAdmin):
    list_display = [
                    'get_uid',
                    'get_diamonds',
                    'last_assigned_diamonds',
                    'diamond_updated_datetime',
                    ]
    list_display_links = ['get_uid','last_assigned_diamonds']
    ordering = ['-id',]
    search_fields = ['user__id','user__phone','user__profile__full_name',] 
    readonly_fields = ['user','last_assigned_diamonds','diamond_updated_datetime']

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def get_uid(self, obj):
      return obj.user.id

    get_uid.short_description = 'User ID'

    def get_diamonds(self, obj):
      return obj.user.profile.diamonds

    get_diamonds.short_description = 'Diamonds'

@admin.register(ResellerRequest)
class CustomResellerRequest(admin.ModelAdmin):
    list_display = [
                    'get_uid',
                    'get_profile',
                    'is_approved',
                    'is_declined',
                    'get_diamonds',
                    'datetime',
                    ]
    list_display_links = ['get_profile','get_uid']
    ordering = ['-id',]
    search_fields = ['user__id','user__phone','user__profile__full_name',] 
    # readonly_fields = ['user']

    def get_uid(self, obj):
      return obj.user.id

    get_uid.short_description = 'User ID'

    def get_profile(self, obj):
        return obj.user.profile

    get_profile.short_description = 'Profile'

    def get_diamonds(self, obj):
      return obj.user.profile.diamonds

    get_diamonds.short_description = 'Diamonds'
