from django.urls import path
from .views import (
    AppLockRetrieveApiView
    )

urlpatterns=[  
    path('applock-retrieve/',AppLockRetrieveApiView.as_view()),
]