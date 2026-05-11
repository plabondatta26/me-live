from django.urls import path
from .views import (
    FortuneWheelItemSelectionCreateApiView, GameViewersUpdateApiView,
    )

urlpatterns=[ 
    path('fortune-wheel-item-selection-create/',FortuneWheelItemSelectionCreateApiView.as_view()),
    path('game-viewers-update/',GameViewersUpdateApiView.as_view()),
]