from django.urls import path
from .views import (
    PaymentMethodListApiView, WithdrawRequestListApiView, WithdrawRequestCreateApiView,
    # BalanceRetrieveApiView,
    # DepositRequestCreateApiView,
    # DepositRequestListApiView, 
    # PlanListApiView,PlanPurchasedListApiView,PlanPurchasedRemaingMinutesRetrieveApiView,
    # PlanPurchasedCreateApiView,EarningHistoryListApiView,EarnCoinExchangerRetrieveApiView,
    ContributionListApiView,CountributionByContributorIdRetrieveApiView,
    TopContributorRankingListApiView,
)

urlpatterns = [
    path('payment-method-list/',PaymentMethodListApiView.as_view()),
    # path('balance-retrieve/',BalanceRetrieveApiView.as_view()),
    # path('deposit-request-list/',DepositRequestListApiView.as_view()),
    # path('deposit-request-create/',DepositRequestCreateApiView.as_view()),
    path('withdraw-request-list/',WithdrawRequestListApiView.as_view()),
    path('withdraw-request-create/',WithdrawRequestCreateApiView.as_view()),
    # # Plan
    # path('plan-list/',PlanListApiView.as_view()),
    # path('purchased-plan-list/',PlanPurchasedListApiView.as_view()),
    # path('earning-history-list/',EarningHistoryListApiView.as_view()),
    # path('plan-purchased-create/',PlanPurchasedCreateApiView.as_view()),
    # path('check-for-streaming-allowed/',PlanPurchasedRemaingMinutesRetrieveApiView.as_view()),
    # # Earn
    # path('earn-coin-exchanger-retrieve/',EarnCoinExchangerRetrieveApiView.as_view()),

    # Contribution
    path('top-contributor-ranking-list/',TopContributorRankingListApiView.as_view()),
    path('contribution-ranking-list/<int:user_id>/',ContributionListApiView.as_view()),
    path('contribution-by-contributor-id-retrieve/<int:channel_id>/',CountributionByContributorIdRetrieveApiView.as_view()),

]