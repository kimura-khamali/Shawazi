from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

# from django.urls import path
# from transaction.views import api_interaction_view  # replace 'your_app' with your actual app name

# urlpatterns = [
#     # ... your existing URL patterns ...
#     path('api-interaction/', api_interaction_view, name='api_interaction'),
# ]


# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import TransactionViewSet, api_interaction_view

# router = DefaultRouter()
# router.register(r'transactions', TransactionViewSet)

# urlpatterns = [
#     path('api/', include(router.urls)),
#     path('api-interaction/', api_interaction_view, name='api_interaction'),
# ]