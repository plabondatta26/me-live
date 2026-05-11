from django.urls import path
from .views import (
    AgentRequestCreateApiView, HostRequestCreateApiView, AgentForHostRetrieveApiView,
    AgentListApiView,TopRatedAgentListApiView, SearchAgentRetrieveApiView, AgentRequestRetrieveApiView, HostRequestRetrieveApiView, SearchHostRequestRetrieveApiView,
    HostRequestListApiView, HostListApiView, ConfirmHostRequestCreateApiView,
    HostDestroyApiView, HostRequestDestroyApiView, AgentRequestDestroyApiView,
    ResellerRequestCreateApiView, ResellerRequestRetrieveApiView, ResellerRequestDestroyApiView,
    ResellerRechargeCreateApiView, ResellerRechargeHistoryListApiView, ResellerRechargeHistoryDestroyApiView,
    ModeratorRequestCreateApiView, ModeratorRequestRetrieveApiView, ModeratorRequestDestroyApiView,
    AgentRechargedCreateApiView, AgentRechargedHistoryListApiView, AgentRechargedHistoryDestroyApiView,
    )

urlpatterns=[ 
    path('moderator-request-create/',ModeratorRequestCreateApiView.as_view()),
    path('moderator-request-retrieve/',ModeratorRequestRetrieveApiView.as_view()),
    path('moderator-request-delete/',ModeratorRequestDestroyApiView.as_view()),

    path('agent-request-create/',AgentRequestCreateApiView.as_view()),
    path('agent-list/',AgentListApiView.as_view()),
    path('top-rated-agent-list/',TopRatedAgentListApiView.as_view()),
    path('search-agent-retrieve/<int:user_id>/',SearchAgentRetrieveApiView.as_view()),
    path('agent-request-retrieve/',AgentRequestRetrieveApiView.as_view()),
    path('agent-request-delete/',AgentRequestDestroyApiView.as_view()),
    path('agent-for-host-retrieve/',AgentForHostRetrieveApiView.as_view()),
    # Agent Recharged
    path('agent-recharge-create/',AgentRechargedCreateApiView.as_view()),
    path('agent-recharge-history-list/',AgentRechargedHistoryListApiView.as_view()),
    path('agent-recharge-history-delete/',AgentRechargedHistoryDestroyApiView.as_view()),
    
    path('host-request-create/',HostRequestCreateApiView.as_view()),
    path('host-request-retrieve/',HostRequestRetrieveApiView.as_view()),
    path('search-host-request-retrieve/<int:user_id>/',SearchHostRequestRetrieveApiView.as_view()),
    path('host-request-list/',HostRequestListApiView.as_view()),
    path('host-list/',HostListApiView.as_view()),
    path('confirm-host-request-create/',ConfirmHostRequestCreateApiView.as_view()),
    path('host-remove/',HostDestroyApiView.as_view()),
    path('host-request-delete/',HostRequestDestroyApiView.as_view()),

    path('reseller-request-create/',ResellerRequestCreateApiView.as_view()),
    path('reseller-request-retrieve/',ResellerRequestRetrieveApiView.as_view()),
    path('reseller-request-delete/',ResellerRequestDestroyApiView.as_view()),
    path('reseller-recharge-create/',ResellerRechargeCreateApiView.as_view()),
    path('reseller-recharge-history-list/',ResellerRechargeHistoryListApiView.as_view()),
    path('reseller-recharge-history-delete/',ResellerRechargeHistoryDestroyApiView.as_view()),

]
