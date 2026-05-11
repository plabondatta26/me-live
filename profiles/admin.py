from django.contrib import admin,messages
from .models import Profile

# admin.site.register(Profile)

# @admin.register(Profile)
# class CustomerProfile(admin.ModelAdmin):
#     list_display = ['user',
#                     'full_name',
#                     'diamonds',
#                     ]
#     ordering = ['-id',]
#     search_fields = ['user__id','user__phone','full_name','diamonds',]

@admin.register(Profile)
class CustomProfile(admin.ModelAdmin):
    list_display = ['get_uid',
                    'get_user',
                    'login_type',
                    'full_name',
                    'get_designation',
                    'diamonds',
                    'outgoing_diamonds',
                    ]
    list_display_links = ['get_uid','get_user','full_name']
    ordering = ['-id',]
    search_fields = ['user__id','full_name','diamonds','outgoing_diamonds',] 
    readonly_fields = ['user','login_type','uid','email','photo_url','followers','blocks','is_allow_video_live','is_agent','is_host','is_reseller','is_moderator',
                       'be_agent_datetime','be_host_datetime','be_reseller_datetime','be_moderator_datetime',]

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def get_uid(self, obj):
        return obj.user.id

    get_uid.short_description = 'User ID'

    def get_user(self, obj):
        return obj.user

    get_user.short_description = 'Phone / Email'

    def get_designation(self, obj):
        designation = 'User'
        if obj.is_agent:
            designation = "Agent"
        elif obj.is_reseller:
            designation = "Reseller"
        elif obj.is_host:
            designation = "Host"
        elif obj.is_moderator:
            designation = 'Moderator'
        return designation
    
    get_designation.short_description = 'Designation'

    # def save_model(self, request, obj, form, change):
    #     """
    #     Given a model instance save it to the database.
    #     """
    #     if obj.reset_password:
    #         if len(obj.reset_password) < 8:
    #             messages.add_message(request, messages.ERROR, "Password must contain at least 8 characters.")

    #         elif obj.login_type != "google_login":
    #             # set user new password
    #             user_obj = obj.user
    #             user_obj.set_password(obj.reset_password)
    #             user_obj.save()
    #             obj.password = obj.reset_password
    #             obj.reset_password = None
    #             obj.save()
    #             messages.add_message(request, messages.SUCCESS, "Password has been set successfully.")
    #         else:
    #             messages.add_message(request, messages.ERROR, "Can't set Password on Google Login")  
                
            
    #     else:
    #         obj.save()
