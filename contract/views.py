from rest_framework import viewsets
from .models import DraftedContract
from .serializers import DraftedContractSerializer

class DraftedContractViewSet(viewsets.ModelViewSet):
    queryset = DraftedContract.objects.all()
    serializer_class = DraftedContractSerializer
