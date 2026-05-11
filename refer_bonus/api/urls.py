from django.urls import path
from .views import (
    ReferHistoryRetrieveApiView, ReferBonusCreateApiView
)

urlpatterns = [
    path('refer-history-retrieve/<str:device_id>/',ReferHistoryRetrieveApiView.as_view()),
    path('refer-bonus-create/<str:device_id>/',ReferBonusCreateApiView.as_view()),

]