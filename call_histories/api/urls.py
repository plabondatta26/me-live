from django.urls import path
from .views import CallHistoryListApiView, CallHistoryCreateApiView

urlpatterns=[ 
    path('call-history-list/',CallHistoryListApiView.as_view()),
    path('call-history-create/',CallHistoryCreateApiView.as_view()),

]