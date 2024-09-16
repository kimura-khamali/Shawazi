from django.urls import path, include
from rest_framework.routers import DefaultRouter

from contract import views
from .views import TransactionViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    #  path('api/transactions/<int:pk>/sign_agreement/', views.sign_agreement, name='transaction-sign-agreement'),
]


