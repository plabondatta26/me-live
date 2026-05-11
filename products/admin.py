from django.contrib import admin
from .models import (
	PurchasedVVipPackage, PurchasedVipPackage, StreamingJoiningGif, PurchasedStreamingJoiningGif,
	DiamondPackage, VVipPackage, VVipPackageOrderingInfo, VipPackage, VipPackageOrderingInfo,WithdrawPackage, NormalGift,AnimatedGift,
	Level, PackageTheme, PurchasedPackageTheme, YouTubeVideo
	)

admin.site.register(StreamingJoiningGif)
# admin.site.register(PurchasedStreamingJoiningGif)
admin.site.register(PackageTheme)
# admin.site.register(PurchasedPackageTheme)
admin.site.register(DiamondPackage)
admin.site.register(WithdrawPackage)
# admin.site.register(NormalGift)
admin.site.register(AnimatedGift)
admin.site.register(Level)

admin.site.register(VipPackage)
admin.site.register(PurchasedVipPackage)
admin.site.register(VipPackageOrderingInfo)
admin.site.register(VVipPackage)
admin.site.register(PurchasedVVipPackage)
admin.site.register(VVipPackageOrderingInfo)
admin.site.register(YouTubeVideo)

# @admin.register(Level)
# class LevelAdmin(admin.ModelAdmin):
#     # inlines = [PaymentMethodAccountTypeInline,]
#     # readonly_fields = ['logo_preview']
#     # search_fields = ['title','slug']

#     list_per_page = 5

# list_per_page