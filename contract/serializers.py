from rest_framework import serializers
from .models import DraftedContract

class DraftedContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftedContract
        fields = '__all__'