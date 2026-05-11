from django.contrib import admin
from .models import UserDeviceInfo, UserDeviceBlocked

@admin.register(UserDeviceInfo)
class UserDeviceInfoAdmin(admin.ModelAdmin):
	list_display = ('user_id','device_name','device_id','blocked','entry_datetime')
	list_display_links = ['user_id','device_name','device_id']
	search_fields = ('user_id',)
	ordering = ('user_id',)
	list_filter = ('blocked',)
	readonly_fields = ['user_id','device_name','device_id','entry_datetime','blocked_moderator']

@admin.register(UserDeviceBlocked)
class UserBlockedDeviceInfoAdmin(admin.ModelAdmin):
	list_display = ('user_id','device_name','device_id','blocked_datetime')
	list_display_links = ['user_id','device_name','device_id']
	search_fields = ('user_id',)
	ordering = ('user_id',)
	readonly_fields = ['user_id','device_name','device_id','device_info']
