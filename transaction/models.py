from django.db import models

class Transaction(models.Model):
    buyer = models.CharField(max_length=100)
    seller = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proof_of_payment = models.ImageField(upload_to='proof_of_payments/')
    lawyer_details = models.TextField()
    seller_details = models.TextField()
    terms = models.TextField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    smart_contract_address = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    terms_hash = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Transaction {self.id} - {self.buyer} to {self.seller}"





























# from django.db import models

# class Transaction(models.Model):
#     buyer = models.CharField(max_length=100)
#     seller = models.CharField(max_length=100)
#     amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     # amount = models.DecimalField(max_digits=10, decimal_places=2)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
#     proof_of_payment = models.ImageField(upload_to='proof_of_payments/')
#     lawyer_details = models.TextField()
#     seller_details = models.TextField()
#     terms = models.TextField(null=True, blank=True) 
#     is_verified = models.BooleanField(default=False)
#     smart_contract_address = models.CharField(max_length=100)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     terms_hash = models.CharField(max_length=255, null=True, blank=True)

#     def __str__(self):
#         return f"Transaction {self.id} - {self.buyer} to {self.seller}"

