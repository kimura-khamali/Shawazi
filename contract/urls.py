from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DraftedContractViewSet

router = DefaultRouter()
router.register(r'drafted_contracts', DraftedContractViewSet)

urlpatterns = [
    path('', include(router.urls)),
]