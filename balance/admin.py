from django.utils.safestring import mark_safe
from django.contrib import admin
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from .models import (
    PaymentMethod,PaymentMethodAccountType,WithdrawRequest,
    # DepositRequest,Balance,
    # Plan,PlanPurchased,EarningHistory,EarnCoinExchanger,
    Contribution,
    ClearContributionRanking,
    )

admin.site.site_header = "Me Live Admin"
admin.site.site_title = "Me Live Admin"
admin.site.index_title = "Welcome to Me Live"

class PaymentMethodAccountTypeInline(admin.StackedInline):
    model = PaymentMethodAccountType

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    inlines = [PaymentMethodAccountTypeInline,]
    readonly_fields = ['logo_preview']
    # search_fields = ['title','slug']

    def logo_preview(self, obj):
        return mark_safe('<img src="{url}" width="100" />'.format(
                url = obj.logo.url,
                width=obj.logo.width,
                height=obj.logo.height,
            )
        )

# admin.site.register(DepositRequest)
@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
	readonly_fields = ['user','payment_method','withdraw_package','payment_method_name','account_type','diamonds','amount','received_amount','receiver_number','updated_datetime']
# admin.site.register(Balance)
# admin.site.register(Plan)
# admin.site.register(PlanPurchased)
# admin.site.register(EarningHistory)
# admin.site.register(EarnCoinExchanger)
# admin.site.register(Contribution)

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = [
                    'user','contributor',
                    'diamonds','datetime'
                    ]
    search_fields = ['contributor__phone']


@admin.register(ClearContributionRanking)
class ClearContributionRankingAdmin(admin.ModelAdmin):
    list_display = [
                    'last_contribution_ranking_clear_datetime',
                    'upcoming_contribution_ranking_clear_datetime',
                    ]
    list_display_links = ['last_contribution_ranking_clear_datetime','upcoming_contribution_ranking_clear_datetime']
    readonly_fields = ['last_contribution_ranking_clear_datetime']