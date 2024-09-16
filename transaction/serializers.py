from rest_framework import serializers
from .models import Transaction

# class TransactionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Transaction
#         fields = '__all__'



# class TransactionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Transaction
#         fields = '__all__'
#         extra_kwargs = {
#             'amount': {'required': True},
#         }


class TransactionSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        model = Transaction
        fields = '__all__'