from django.contrib import admin,messages
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.shortcuts import redirect
from .forms import UserAdminCreationForm, UserAdminChangeForm
from django.contrib.auth import get_user_model
from .models import PhoneOTP
import me_live.monkey_patching

# Register your models here.
User = get_user_model()

# admin.site.register(PhoneOTP)
admin.site.unregister(Group)

class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    list_display = ('id','phone','admin',)
    list_display_links = ['id','phone',]
    list_filter = ('staff','active','admin',)
    fieldsets = (
        (None,{'fields':('phone','password')}),
        # ("Personal info",{'fields':('name',)}),
        ('Permissions',{'fields':('admin','staff','active')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2')
        }),
    )

    search_fields = ('phone','id')
    ordering = ('id',)
    filter_horizontal = ()

    def get_inline_instances(self,request,obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request,obj)

# admin.site.register(User, UserAdmin)

@admin.register(User)
class AccountAdmin(UserAdmin):
    change_form_template = "go_to_profile.html"


    def response_change(self, request, obj):
        if "_view-profile" in request.POST:
            profile_obj = obj.profile
            if profile_obj:
                return redirect(f"/profiles/profile/{profile_obj.id}/change")
            else:
                messages.add_message(request, messages.ERROR, "Account doesn't have Profile")
        
        return redirect(f"/accounts/user/{obj.id}/change")
        # return super().response_change(request, obj)