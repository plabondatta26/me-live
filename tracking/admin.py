from datetime import timedelta
from django.contrib import admin
from .models import (
	AppLock, TotalUsersAndDiamonds, AccountDeleteAndUsernameChangeDiamonds, GiftSendVatDiamonds,
	ReferBonusDiamonds, FlyingMessageAndBoostDiamonds, WithdrawDiamonds,
	RechargeDiamonds, TotalDeviceBlocks, GamesDiamonds, BroadcasterHistory,
    ClearBroadcasterHistory,ChatSendVatDiamonds,
)

admin.site.register(TotalUsersAndDiamonds)
admin.site.register(AccountDeleteAndUsernameChangeDiamonds)
admin.site.register(ReferBonusDiamonds)
admin.site.register(FlyingMessageAndBoostDiamonds)
admin.site.register(WithdrawDiamonds)
admin.site.register(RechargeDiamonds)
admin.site.register(TotalDeviceBlocks)
admin.site.register(GamesDiamonds)
admin.site.register(ChatSendVatDiamonds)

@admin.register(GiftSendVatDiamonds)
class CustomGiftSendVatDiamonds(admin.ModelAdmin):
    list_display = [
                    'gift_vat_diamonds',
                    'live_lock_vat_diamonds',
                    'updated_datetime',
                    ]
    list_display_links = ['gift_vat_diamonds','live_lock_vat_diamonds']
  
    # readonly_fields = ['updated_datetime',]

@admin.register(BroadcasterHistory)
class CustomerProfile(admin.ModelAdmin):
    list_display = ['get_uid',
                    'audio_broadcast_in_second',
                    'video_broadcast_in_second',
                    'broadcasting_date',
                    # 'get_utc'
                    ]
    ordering = ['-id',]
    search_fields = ['user__id',]

    def get_uid(self, obj):
      return obj.user.id

    get_uid.short_description = 'User ID'

    # def get_utc(self, obj):
    # 	print(obj.broadcasting_date + timedelta(hours=6))
    # 	return obj.broadcasting_date + timedelta(hours=6)

    # get_utc.short_description = 'Time in (UTC)'

@admin.register(ClearBroadcasterHistory)
class CustomClearBroadcasterHistory(admin.ModelAdmin):
    list_display = [
                    'make_clear_all_broadcasters_histories',
                    'last_clear_datetime',
                    ]
    list_display_links = ['make_clear_all_broadcasters_histories','last_clear_datetime']
    readonly_fields = ['last_clear_datetime']

@admin.register(AppLock)
class CustomAppLock(admin.ModelAdmin):
    list_display = [
                    'build_number',
                    'updated_datetime',
                    ]
    list_display_links = ['build_number','updated_datetime']
    readonly_fields = ['updated_datetime',]
