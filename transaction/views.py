import logging
from django.conf import settings
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from web3 import Web3
from .models import Transaction
from .serializers import TransactionSerializer
from .utils import load_contract_abi, deploy_smart_contract

logger = logging.getLogger(__name__)

def api_interaction_view(request):
    return render(request, 'api_interaction.html')

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    @action(detail=False, methods=['post'])
    def create_transaction(self, request):
        data = request.data
        logger.debug("Incoming Data: %s", data)

        required_fields = ['total_amount', 'terms', 'parcel_id', 'buyer', 'seller']
        for field in required_fields:
            if field not in data:
                return Response({"error": f"{field} must be provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            total_amount = float(data['total_amount'])
        except ValueError:
            return Response({"error": "Invalid total amount provided"}, status=status.HTTP_400_BAD_REQUEST)

        if not hasattr(settings, 'LAND_TRANSACTION_CONTRACT_ADDRESS'):
            contract_address = deploy_smart_contract("oracle_address_placeholder")
            settings.LAND_TRANSACTION_CONTRACT_ADDRESS = contract_address
        else:
            contract_address = settings.LAND_TRANSACTION_CONTRACT_ADDRESS

        transaction = self.save_transaction(data, contract_address)

        try:
            self.add_transaction_to_contract(
                contract_address,
                transaction.id,
                int(data['parcel_id']),
                total_amount,
                transaction.terms_hash
            )
        except Exception as e:
            logger.error(f"Failed to add transaction to smart contract: {str(e)}")
            transaction.delete()
            return Response({"error": "Failed to add transaction to smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Transaction created",
            "agreement_id": transaction.id,
            "total_amount": transaction.total_amount,
            "terms_hash": transaction.terms_hash,
            "smart_contract_address": transaction.smart_contract_address
        }, status=status.HTTP_201_CREATED)

    def save_transaction(self, data, contract_address):
        terms_hash = Web3.keccak(text=data['terms']).hex()
        transaction = Transaction.objects.create(
            total_amount=float(data['total_amount']),
            buyer=data['buyer'],
            seller=data['seller'],
            parcel_id=data['parcel_id'],
            terms=data['terms'],
            smart_contract_address=contract_address,
            terms_hash=terms_hash,
            cancellation_fee=0,  
            refund_fee=0  
        )
        return transaction

    @action(detail=True, methods=['post'])
    def sign_agreement(self, request, pk=None):
        transaction = self.get_object()
        transaction.is_agreement_signed = True
        transaction.save()
        
        try:
            self.sign_agreement_on_blockchain(transaction.smart_contract_address, transaction.id)
            return Response({"message": "Agreement signed successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to sign agreement on smart contract: {str(e)}")
            return Response({"error": "Failed to sign agreement on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        transaction = self.get_object()

        try:
            self.verify_payment_on_blockchain(
                transaction.smart_contract_address,
                transaction.id,
                transaction.total_amount,
                transaction.terms_hash
            )
        except Exception as e:
            logger.error(f"Failed to verify payment on smart contract: {str(e)}")
            return Response({"error": "Failed to verify payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        transaction.is_verified = True
        transaction.save()

        return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def check_verification(self, request, pk=None):
        transaction = self.get_object()
        is_verified = self.is_payment_verified(transaction.smart_contract_address, transaction.id)
        
        return Response({"is_verified": is_verified}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        transaction = self.get_object()
        amount = request.data.get('amount')

        if not amount:
            return Response({"error": "Amount must be provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount)
            if self.record_payment_on_blockchain(transaction, amount):
                transaction.current_amount_paid += amount
                transaction.installments_paid += 1
                transaction.save()
                return Response({"message": "Payment recorded successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to record payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Failed to record payment: {str(e)}")
            return Response({"error": "Invalid amount provided"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel_transaction(self, request, pk=None):
        transaction = self.get_object()

        try:
            if self.cancel_transaction_on_blockchain(transaction.smart_contract_address, transaction.id):
                refund_amount = transaction.current_amount_paid - transaction.cancellation_fee
                if refund_amount > 0:
                    
                    pass

                transaction.is_canceled = True
                transaction.save()
                return Response({"message": "Transaction cancelled successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to cancel transaction on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Failed to cancel transaction: {str(e)}")
            return Response({"error": "Failed to cancel transaction"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def sign_agreement_on_blockchain(self, contract_address, agreement_id):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        try:
            tx_hash = contract.functions.signAgreement(agreement_id).transact({'from': w3.eth.accounts[0]})
            w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            raise Exception(f"Error signing agreement on blockchain: {e}")

    def add_transaction_to_contract(self, contract_address, agreement_id, parcel_id, total_amount, terms_hash):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        try:
            tx_hash = contract.functions.addTransaction(
                agreement_id,
                parcel_id,
                total_amount,
                terms_hash
            ).transact({'from': w3.eth.accounts[0]})
            w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            raise Exception(f"Error adding transaction to contract: {e}")

    def verify_payment_on_blockchain(self, contract_address, agreement_id, total_amount, terms_hash):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        try:
            tx_hash = contract.functions.verifyPayment(
                agreement_id,
                int(total_amount * 100)  # Convert to smallest unit if necessary
            ).transact({'from': w3.eth.accounts[0]})
            w3.eth.wait_for_transaction_receipt(tx_hash)

            is_verified = contract.functions.isPaymentVerified(agreement_id).call()
            return is_verified
        except Exception as e:
            raise Exception(f"Error verifying payment on blockchain: {e}")

    def record_payment_on_blockchain(self, transaction, amount):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract = w3.eth.contract(address=transaction.smart_contract_address, abi=contract_abi)

        try:
            tx_hash = contract.functions.recordPayment(
                transaction.id,
                int(amount * 100) 
            ).transact({'from': w3.eth.accounts[0]})
            w3.eth.wait_for_transaction_receipt(tx_hash)
            return True
        except Exception as e:
            raise Exception(f"Error recording payment on blockchain: {e}")

    def cancel_transaction_on_blockchain(self, contract_address, agreement_id):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        try:
            tx_hash = contract.functions.cancelTransaction(agreement_id).transact({'from': w3.eth.accounts[0]})
            w3.eth.wait_for_transaction_receipt(tx_hash)
            return True
        except Exception as e:
            raise Exception(f"Error canceling transaction on blockchain: {e}")

    def is_payment_verified(self, contract_address, agreement_id):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        try:
            is_verified = contract.functions.isPaymentVerified(agreement_id).call()
            return is_verified
        except Exception as e:
            raise Exception(f"Error checking payment verification on blockchain: {e}")


















































































# import logging
# from django.conf import settings
# from django.shortcuts import render
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from web3 import Web3
# from .models import Transaction
# from .serializers import TransactionSerializer
# from .utils import load_contract_abi,deploy_smart_contract

# logger = logging.getLogger(__name__)

# def api_interaction_view(request):
#     return render(request, 'api_interaction.html')

# class TransactionViewSet(viewsets.ModelViewSet):
#     queryset = Transaction.objects.all()
#     serializer_class = TransactionSerializer

#     @action(detail=False, methods=['post'])
#     def create_transaction(self, request):
#     data = request.data
#     logger.debug("Incoming Data: %s", data)

#     required_fields = ['total_amount', 'terms', 'parcel_id', 'buyer', 'seller']
#     for field in required_fields:
#         if field not in data:
#             return Response({"error": f"{field} must be provided"}, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         total_amount = float(data['total_amount'])
#     except ValueError:
#         return Response({"error": "Invalid total amount provided"}, status=status.HTTP_400_BAD_REQUEST)

#     if not hasattr(settings, 'LAND_TRANSACTION_CONTRACT_ADDRESS'):
#         contract_address = deploy_smart_contract("oracle_address_placeholder")
#         settings.LAND_TRANSACTION_CONTRACT_ADDRESS = contract_address
#     else:
#         contract_address = settings.LAND_TRANSACTION_CONTRACT_ADDRESS

#     transaction = self.save_transaction(data, contract_address)

#     try:
#         self.add_transaction_to_contract(
#             contract_address,
#             transaction.id,
#             int(data['parcel_id']),
#             total_amount,
#             transaction.terms_hash
#         )
#     except Exception as e:
#         logger.error(f"Failed to add transaction to smart contract: {str(e)}")
#         transaction.delete()
#         return Response({"error": "Failed to add transaction to smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     return Response({
#         "message": "Transaction created",
#         "agreement_id": transaction.id,
#         "total_amount": transaction.total_amount,
#         "terms_hash": transaction.terms_hash,
#         "smart_contract_address": transaction.smart_contract_address
#     }, status=status.HTTP_201_CREATED)





























#     # def create_transaction(self, request):
#     #     data = request.data
#     #     logger.debug("Incoming Data: %s", data)

#     #     required_fields = ['total_amount', 'terms', 'parcel_id', 'buyer', 'seller']
#     #     for field in required_fields:
#     #         if field not in data:
#     #             return Response({"error": f"{field} must be provided"}, status=status.HTTP_400_BAD_REQUEST)

#     #     try:
#     #         total_amount = float(data['total_amount'])
#     #     except ValueError:
#     #         return Response({"error": "Invalid total amount provided"}, status=status.HTTP_400_BAD_REQUEST)

#     #     if not hasattr(settings, 'LAND_TRANSACTION_CONTRACT_ADDRESS'):
#     #         contract_address = deploy_smart_contract()
#     #         settings.LAND_TRANSACTION_CONTRACT_ADDRESS = contract_address
#     #     else:
#     #         contract_address = settings.LAND_TRANSACTION_CONTRACT_ADDRESS

#     #     transaction = self.save_transaction(data, contract_address)

#     #     try:
#     #         self.add_transaction_to_contract(
#     #             contract_address,
#     #             transaction.id,
#     #             int(data['parcel_id']),
#     #             total_amount,
#     #             transaction.terms_hash
#     #         )
#     #     except Exception as e:
#     #         logger.error(f"Failed to add transaction to smart contract: {str(e)}")
#     #         transaction.delete()
#     #         return Response({"error": "Failed to add transaction to smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     #     return Response({
#     #         "message": "Transaction created",
#     #         "agreement_id": transaction.id,
#     #         "total_amount": transaction.total_amount,
#     #         "terms_hash": transaction.terms_hash,
#     #         "smart_contract_address": transaction.smart_contract_address
#     #     }, status=status.HTTP_201_CREATED)

#     def save_transaction(self, data, contract_address):
#         terms_hash = Web3.keccak(text=data['terms']).hex()
#         transaction = Transaction.objects.create(
#             total_amount=float(data['total_amount']),
#             buyer=data['buyer'],
#             seller=data['seller'],
#             parcel_id=data['parcel_id'],
#             terms=data['terms'],
#             smart_contract_address=contract_address,
#             terms_hash=terms_hash,
#             cancellation_fee=0,  
#             refund_fee=0  
#         )
#         return transaction

#     @action(detail=True, methods=['post'])
#     def sign_agreement(self, request, pk=None):
#         transaction = self.get_object()
#         transaction.is_agreement_signed = True
#         transaction.save()
        
#         try:
#             self.sign_agreement_on_blockchain(transaction.smart_contract_address, transaction.id)
#             return Response({"message": "Agreement signed successfully"}, status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.error(f"Failed to sign agreement on smart contract: {str(e)}")
#             return Response({"error": "Failed to sign agreement on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     @action(detail=True, methods=['post'])
#     def verify_payment(self, request, pk=None):
#         transaction = self.get_object()

#         try:
#             self.verify_payment_on_blockchain(
#                 transaction.smart_contract_address,
#                 transaction.id,
#                 transaction.total_amount,
#                 transaction.terms_hash
#             )
#         except Exception as e:
#             logger.error(f"Failed to verify payment on smart contract: {str(e)}")
#             return Response({"error": "Failed to verify payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         transaction.is_verified = True
#         transaction.save()

#         return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)

#     @action(detail=True, methods=['get'])
#     def check_verification(self, request, pk=None):
#         transaction = self.get_object()
#         is_verified = self.is_payment_verified(transaction.smart_contract_address, transaction.id)
        
#         return Response({"is_verified": is_verified}, status=status.HTTP_200_OK)

#     @action(detail=True, methods=['post'])
#     def record_payment(self, request, pk=None):
#         transaction = self.get_object()
#         amount = request.data.get('amount')

#         if not amount:
#             return Response({"error": "Amount must be provided"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             amount = float(amount)
#             if self.record_payment_on_blockchain(transaction, amount):
#                 transaction.current_amount_paid += amount
#                 transaction.installments_paid += 1
#                 transaction.save()
#                 return Response({"message": "Payment recorded successfully"}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"error": "Failed to record payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         except Exception as e:
#             logger.error(f"Failed to record payment: {str(e)}")
#             return Response({"error": "Invalid amount provided"}, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=['post'])
#     def cancel_transaction(self, request, pk=None):
#         transaction = self.get_object()

#         try:
#             if self.cancel_transaction_on_blockchain(transaction.smart_contract_address, transaction.id):
#                 refund_amount = transaction.current_amount_paid - transaction.cancellation_fee
#                 if refund_amount > 0:
#                     # Handle the refund logic here
#                     pass

#                 transaction.is_canceled = True
#                 transaction.save()
#                 return Response({"message": "Transaction cancelled successfully"}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"error": "Failed to cancel transaction on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         except Exception as e:
#             logger.error(f"Failed to cancel transaction: {str(e)}")
#             return Response({"error": "Failed to cancel transaction"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def sign_agreement_on_blockchain(self, contract_address, agreement_id):
#         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#         contract_abi = load_contract_abi()
#         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

#         try:
#             tx_hash = contract.functions.signAgreement(agreement_id).transact({'from': w3.eth.accounts[0]})
#             w3.eth.wait_for_transaction_receipt(tx_hash)
#         except Exception as e:
#             raise Exception(f"Error signing agreement on blockchain: {e}")

#     def add_transaction_to_contract(self, contract_address, agreement_id, parcel_id, total_amount, terms_hash):
#         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#         contract_abi = load_contract_abi()
#         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

#         try:
#             tx_hash = contract.functions.addTransaction(
#                 agreement_id,
#                 parcel_id,
#                 total_amount,
#                 terms_hash
#             ).transact({'from': w3.eth.accounts[0]})
#             w3.eth.wait_for_transaction_receipt(tx_hash)
#         except Exception as e:
#             raise Exception(f"Error adding transaction to contract: {e}")

#     def verify_payment_on_blockchain(self, contract_address, agreement_id, total_amount, terms_hash):
#         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#         contract_abi = load_contract_abi()
#         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

#         try:
#             tx_hash = contract.functions.verifyPayment(
#                 agreement_id,
#                 int(total_amount * 100)  # Convert to smallest unit if necessary
#             ).transact({'from': w3.eth.accounts[0]})
#             w3.eth.wait_for_transaction_receipt(tx_hash)

#             is_verified = contract.functions.isPaymentVerified(agreement_id).call()
#             return is_verified
#         except Exception as e:
#             raise Exception(f"Error verifying payment on blockchain: {e}")

#     def record_payment_on_blockchain(self, transaction, amount):
#         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#         contract_abi = load_contract_abi()
#         contract = w3.eth.contract(address=transaction.smart_contract_address, abi=contract_abi)

#         try:
#             tx_hash = contract.functions.recordPayment(
#                 transaction.id,
#                 int(amount * 100) 
#             ).transact({'from': w3.eth.accounts[0]})
#             w3.eth.wait_for_transaction_receipt(tx_hash)
#             return True
#         except Exception as e:
#             raise Exception(f"Error recording payment on blockchain: {e}")

#     def cancel_transaction_on_blockchain(self, contract_address, agreement_id):
#         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#         contract_abi = load_contract_abi()
#         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

#         try:
#             tx_hash = contract.functions.cancelTransaction(agreement_id).transact({'from': w3.eth.accounts[0]})
#             w3.eth.wait_for_transaction_receipt(tx_hash)
#             return True
#         except Exception as e:
#             raise Exception(f"Error canceling transaction on blockchain: {e}")

#     def is_payment_verified(self, contract_address, agreement_id):
#         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
#         contract_abi = load_contract_abi()
#         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

#         try:
#             is_verified = contract.functions.isPaymentVerified(agreement_id).call()
#             return is_verified
#         except Exception as e:
#             raise Exception(f"Error checking payment verification on blockchain: {e}")






































# # import datetime
# # import re
# # import logging
# # from django.conf import settings
# # from django.shortcuts import render
# # from rest_framework import viewsets, status
# # from rest_framework.decorators import action
# # from rest_framework.response import Response
# # from web3 import Web3
# # from .models import Transaction
# # from .serializers import TransactionSerializer
# # from google.cloud import vision
# # from .utils import load_contract_abi, deploy_smart_contract

# # logger = logging.getLogger(__name__)

# # def api_interaction_view(request):
# #     return render(request, 'api_interaction.html')

# # class TransactionViewSet(viewsets.ModelViewSet):
# #     queryset = Transaction.objects.all()
# #     serializer_class = TransactionSerializer

# #     @action(detail=False, methods=['post'])
# #     def create_transaction(self, request):
# #         data = request.data
# #         logger.debug("Incoming Data: %s", data)

# #         required_fields = ['total_amount', 'terms', 'parcel_id', 'buyer', 'seller']
# #         for field in required_fields:
# #             if field not in data:
# #                 return Response({"error": f"{field} must be provided"}, status=status.HTTP_400_BAD_REQUEST)

# #         try:
# #             total_amount = float(data['total_amount'])
# #         except ValueError:
# #             return Response({"error": "Invalid total amount provided"}, status=status.HTTP_400_BAD_REQUEST)

# #         if not hasattr(settings, 'LAND_TRANSACTION_CONTRACT_ADDRESS'):
# #             contract_address = deploy_smart_contract()
# #             settings.LAND_TRANSACTION_CONTRACT_ADDRESS = contract_address
# #         else:
# #             contract_address = settings.LAND_TRANSACTION_CONTRACT_ADDRESS

# #         transaction = self.save_transaction(data, contract_address)

# #         try:
# #             self.add_transaction_to_contract(
# #                 contract_address,
# #                 transaction.id,
# #                 int(data['parcel_id']),
# #                 total_amount,
# #                 transaction.terms_hash
# #             )
# #         except Exception as e:
# #             logger.error(f"Failed to add transaction to smart contract: {str(e)}")
# #             transaction.delete()
# #             return Response({"error": "Failed to add transaction to smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #         return Response({
# #             "message": "Transaction created",
# #             "transaction_id": transaction.id,
# #             "total_amount": transaction.total_amount,
# #             "terms_hash": transaction.terms_hash,
# #             "smart_contract_address": transaction.smart_contract_address
# #         }, status=status.HTTP_201_CREATED)

# #     def save_transaction(self, data, contract_address):
# #         terms_hash = Web3.keccak(text=data['terms']).hex()
# #         transaction = Transaction.objects.create(
# #             total_amount=float(data['total_amount']),
# #             buyer=data['buyer'],
# #             seller=data['seller'],
# #             parcel_id=data['parcel_id'],
# #             terms=data['terms'],
# #             smart_contract_address=contract_address,
# #             terms_hash=terms_hash,
# #             cancellation_fee=0,  
# #             refund_fee=0  
# #         )
# #         return transaction

# #     @action(detail=True, methods=['post'])
# #     def sign_agreement(self, request, pk=None):
# #         transaction = self.get_object()
# #         transaction.is_agreement_signed = True
# #         transaction.save()
        
# #         try:
# #             self.sign_agreement_on_blockchain(transaction.smart_contract_address, transaction.id)
# #             return Response({"message": "Agreement signed successfully"}, status=status.HTTP_200_OK)
# #         except Exception as e:
# #             logger.error(f"Failed to sign agreement on smart contract: {str(e)}")
# #             return Response({"error": "Failed to sign agreement on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #     @action(detail=True, methods=['post'])
# #     def verify_payment(self, request, pk=None):
# #         transaction = self.get_object()

# #         try:
# #             self.verify_payment_on_blockchain(
# #                 transaction.smart_contract_address,
# #                 transaction.id,
# #                 transaction.total_amount,
# #                 transaction.terms_hash
# #             )
# #         except Exception as e:
# #             logger.error(f"Failed to verify payment on smart contract: {str(e)}")
# #             return Response({"error": "Failed to verify payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #         transaction.is_verified = True
# #         transaction.save()

# #         return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)

# #     @action(detail=True, methods=['get'])
# #     def check_verification(self, request, pk=None):
# #         transaction = self.get_object()
# #         is_verified = self.is_payment_verified(transaction.smart_contract_address, transaction.id)
        
# #         return Response({"is_verified": is_verified}, status=status.HTTP_200_OK)

# #     @action(detail=True, methods=['post'])
# #     def record_payment(self, request, pk=None):
# #         transaction = self.get_object()
# #         amount = request.data.get('amount')

# #         if not amount:
# #             return Response({"error": "Amount must be provided"}, status=status.HTTP_400_BAD_REQUEST)

# #         try:
# #             amount = float(amount)
# #             if self.record_payment_on_blockchain(transaction, amount):
# #                 transaction.current_amount_paid += amount
# #                 transaction.installments_paid += 1
# #                 transaction.save()
# #                 return Response({"message": "Payment recorded successfully"}, status=status.HTTP_200_OK)
# #             else:
# #                 return Response({"error": "Failed to record payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# #         except Exception as e:
# #             logger.error(f"Failed to record payment: {str(e)}")
# #             return Response({"error": "Invalid amount provided"}, status=status.HTTP_400_BAD_REQUEST)

# #     @action(detail=True, methods=['post'])
# #     def cancel_transaction(self, request, pk=None):
# #         transaction = self.get_object()

# #         try:
# #             if self.cancel_transaction_on_blockchain(transaction.smart_contract_address, transaction.id):
# #                 refund_amount = transaction.current_amount_paid - transaction.cancellation_fee
# #                 if refund_amount > 0:
# #                     # Handle the refund logic here
# #                     pass

# #                 transaction.is_canceled = True
# #                 transaction.save()
# #                 return Response({"message": "Transaction cancelled successfully"}, status=status.HTTP_200_OK)
# #             else:
# #                 return Response({"error": "Failed to cancel transaction on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# #         except Exception as e:
# #             logger.error(f"Failed to cancel transaction: {str(e)}")
# #             return Response({"error": "Failed to cancel transaction"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #     def sign_agreement_on_blockchain(self, contract_address, transaction_id):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.signAgreement(transaction_id).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)
# #         except Exception as e:
# #             raise Exception(f"Error signing agreement on blockchain: {e}")

# #     def add_transaction_to_contract(self, contract_address, transaction_id, parcel_id, total_amount, terms_hash):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.addTransaction(
# #                 transaction_id,
# #                 parcel_id,
# #                 total_amount,
# #                 terms_hash
# #             ).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)
# #         except Exception as e:
# #             raise Exception(f"Error adding transaction to contract: {e}")

# #     def verify_payment_on_blockchain(self, contract_address, transaction_id, total_amount, terms_hash):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.verifyPayment(
# #                 transaction_id,
# #                 int(total_amount * 100)  # Convert to smallest unit if necessary
# #             ).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)

# #             is_verified = contract.functions.isPaymentVerified(transaction_id).call()
# #             return is_verified
# #         except Exception as e:
# #             raise Exception(f"Error verifying payment on blockchain: {e}")

# #     def record_payment_on_blockchain(self, transaction, amount):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=transaction.smart_contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.recordPayment(
# #                 transaction.id,
# #                 int(amount * 100) 
# #             ).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)
# #             return True
# #         except Exception as e:
# #             raise Exception(f"Error recording payment on blockchain: {e}")

# #     def cancel_transaction_on_blockchain(self, contract_address, transaction_id):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.cancelTransaction(transaction_id).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)
# #             return True
# #         except Exception as e:
# #             raise Exception(f"Error canceling transaction on blockchain: {e}")

# #     def is_payment_verified(self, contract_address, transaction_id):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             is_verified = contract.functions.isPaymentVerified(transaction_id).call()
# #             return is_verified
# #         except Exception as e:
# #             raise Exception(f"Error checking payment verification on blockchain: {e}")


















































# # import datetime
# # import re
# # import logging
# # from django.conf import settings
# # from django.shortcuts import render
# # from rest_framework import viewsets, status
# # from rest_framework.decorators import action
# # from rest_framework.response import Response
# # from web3 import Web3
# # from .models import Transaction
# # from .serializers import TransactionSerializer
# # from google.cloud import vision
# # from .utils import load_contract_abi, deploy_script

# # logger = logging.getLogger(__name__)

# # def api_interaction_view(request):
# #     return render(request, 'api_interaction.html')

# # class TransactionViewSet(viewsets.ModelViewSet):
# #     queryset = Transaction.objects.all()
# #     serializer_class = TransactionSerializer

# #     @action(detail=False, methods=['post'])
# #     def create_transaction(self, request):
# #         data = request.data
# #         logger.debug("Incoming Data: %s", data)

# #         required_fields = ['total_amount', 'terms', 'parcel_id', 'buyer', 'seller']
# #         for field in required_fields:
# #             if field not in data:
# #                 return Response({"error": f"{field} must be provided"}, status=status.HTTP_400_BAD_REQUEST)

# #         try:
# #             total_amount = float(data['total_amount'])
# #         except ValueError:
# #             return Response({"error": "Invalid total amount provided"}, status=status.HTTP_400_BAD_REQUEST)

# #         if not hasattr(settings, 'LAND_TRANSACTION_CONTRACT_ADDRESS'):
# #             contract_address = deploy_script(settings.ORACLE_ADDRESS)
# #             settings.LAND_TRANSACTION_CONTRACT_ADDRESS = contract_address
# #         else:
# #             contract_address = settings.LAND_TRANSACTION_CONTRACT_ADDRESS

# #         transaction = self.save_transaction(data, contract_address)

# #         try:
# #             self.add_transaction_to_contract(
# #                 contract_address,
# #                 transaction.id,
# #                 int(data['parcel_id']),
# #                 total_amount,
# #                 transaction.terms_hash
# #             )
# #         except Exception as e:
# #             logger.error(f"Failed to add transaction to smart contract: {str(e)}")
# #             transaction.delete()
# #             return Response({"error": "Failed to add transaction to smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #         return Response({
# #             "message": "Transaction created",
# #             "transaction_id": transaction.id,
# #             "total_amount": transaction.total_amount,
# #             "terms_hash": transaction.terms_hash,
# #             "smart_contract_address": transaction.smart_contract_address
# #         }, status=status.HTTP_201_CREATED)

# #     def save_transaction(self, data, contract_address):
# #         terms_hash = Web3.keccak(text=data['terms']).hex()
# #         transaction = Transaction.objects.create(
# #             total_amount=float(data['total_amount']),
# #             buyer=data['buyer'],
# #             seller=data['seller'],
# #             parcel_id=data['parcel_id'],
# #             terms=data['terms'],
# #             smart_contract_address=contract_address,
# #             terms_hash=terms_hash,
# #             cancellation_fee=0,  
# #             refund_fee=0  
# #         )
# #         return transaction

# #     @action(detail=True, methods=['post'])
# #     def verify_payment(self, request, pk=None):
# #         transaction = self.get_object()

# #         try:
# #             self.verify_payment_on_blockchain(
# #                 transaction.smart_contract_address,
# #                 transaction.id,
# #                 transaction.total_amount,
# #                 transaction.terms_hash
# #             )
# #         except Exception as e:
# #             logger.error(f"Failed to verify payment on smart contract: {str(e)}")
# #             return Response({"error": "Failed to verify payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #         transaction.is_verified = True
# #         transaction.save()

# #         return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)

# #     @action(detail=True, methods=['get'])
# #     def check_verification(self, request, pk=None):
# #         transaction = self.get_object()
# #         is_verified = self.is_payment_verified(transaction.smart_contract_address, transaction.id)
        
# #         return Response({"is_verified": is_verified}, status=status.HTTP_200_OK)

# #     @action(detail=True, methods=['post'])
# #     def record_payment(self, request, pk=None):
# #         transaction = self.get_object()
# #         amount = request.data.get('amount')

# #         if not amount:
# #             return Response({"error": "Amount must be provided"}, status=status.HTTP_400_BAD_REQUEST)

# #         try:
# #             amount = float(amount)
# #             if self.record_payment_on_blockchain(transaction, amount):
# #                 transaction.current_amount_paid += amount
# #                 transaction.installments_paid += 1
# #                 transaction.save()
# #                 return Response({"message": "Payment recorded successfully"}, status=status.HTTP_200_OK)
# #             else:
# #                 return Response({"error": "Failed to record payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# #         except Exception as e:
# #             logger.error(f"Failed to record payment: {str(e)}")
# #             return Response({"error": "Invalid amount provided"}, status=status.HTTP_400_BAD_REQUEST)

# #     @action(detail=True, methods=['post'])
# #     def cancel_transaction(self, request, pk=None):
# #         transaction = self.get_object()

# #         try:
# #             if self.cancel_transaction_on_blockchain(transaction.smart_contract_address, transaction.id):
# #                 refund_amount = transaction.current_amount_paid - transaction.cancellation_fee
# #                 if refund_amount > 0:
                    
# #                     pass

# #                 transaction.is_canceled = True
# #                 transaction.save()
# #                 return Response({"message": "Transaction cancelled successfully"}, status=status.HTTP_200_OK)
# #             else:
# #                 return Response({"error": "Failed to cancel transaction on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# #         except Exception as e:
# #             logger.error(f"Failed to cancel transaction: {str(e)}")
# #             return Response({"error": "Failed to cancel transaction"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #     def deploy_new_smart_contract(self, total_amount, terms):
# #         try:
# #             contract_address = deploy_smart_contract(total_amount, terms)
# #             return contract_address
# #         except Exception as e:
# #             logger.error(f"Failed to deploy smart contract: {str(e)}")
# #             return None

# #     def add_transaction_to_contract(self, contract_address, transaction_id, parcel_id, total_amount, terms_hash):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.addTransaction(
# #                 transaction_id,
# #                 parcel_id,
# #                 total_amount,
# #                 terms_hash
# #             ).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)
# #         except Exception as e:
# #             raise Exception(f"Error adding transaction to contract: {e}")

# #     def verify_payment_on_blockchain(self, contract_address, transaction_id, total_amount, terms_hash):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.verifyPayment(
# #                 transaction_id,
# #                 int(total_amount * 100)  # Convert to smallest unit if necessary
# #             ).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)

# #             is_verified = contract.functions.isPaymentVerified(transaction_id).call()
# #             return is_verified
# #         except Exception as e:
# #             raise Exception(f"Error verifying payment on blockchain: {e}")

# #     def record_payment_on_blockchain(self, transaction, amount):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=transaction.smart_contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.recordPayment(
# #                 transaction.id,
# #                 int(amount * 100) 
# #             ).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)
# #             return True
# #         except Exception as e:
# #             raise Exception(f"Error recording payment on blockchain: {e}")

# #     def cancel_transaction_on_blockchain(self, contract_address, transaction_id):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.cancelTransaction(transaction_id).transact({'from': w3.eth.accounts[0]})
# #             w3.eth.wait_for_transaction_receipt(tx_hash)
# #             return True
# #         except Exception as e:
# #             raise Exception(f"Error cancelling transaction on blockchain: {e}")

# #     @action(detail=True, methods=['post'])
# #     def upload_and_verify(self, request, pk=None):
# #         transaction = self.get_object()

# #         if 'document1' not in request.FILES or 'document2' not in request.FILES:
# #             return Response({"error": "Both documents must be provided"}, status=status.HTTP_400_BAD_REQUEST)

# #         document1 = request.FILES['document1']
# #         document2 = request.FILES['document2']

# #         data1 = self.extract_data_from_image(document1)
# #         data2 = self.extract_data_from_image(document2)

# #         if self.compare_transaction_data(data1, data2):
# #             transaction.status = 'Verified'
# #             transaction.save()
# #             return Response({"message": "Documents verified successfully."}, status=status.HTTP_200_OK)
# #         else:
# #             return Response({"error": "Verification failed."}, status=status.HTTP_400_BAD_REQUEST)

# #     def extract_data_from_image(self, image_file):
# #         client = vision.ImageAnnotatorClient()
# #         try:
# #             image_content = image_file.read()
# #             image = vision.Image(content=image_content)
# #             response = client.text_detection(image=image)
# #             texts = response.text_annotations
# #             extracted_text = texts[0].description if texts else ""
# #         except Exception as e:
# #             raise ValueError(f"Failed to process image: {str(e)}")

# #         patterns = {
# #             'amount': [r'Ksh\s*([\d,]+\.\d{2})', r'KES\s*([\d,]+\.\d{2})'],
# #             'date': [r'on\s*(\d{1,2}/\d{1,2}/\d{2,4})', r'(\d{1,2}/\d{1,2}/\d{4})'],
# #             'code': [r'\b([A-Z0-9]{10})\b']
# #         }

# #         matches = {}
# #         for key, regex_list in patterns.items():
# #             for pattern in regex_list:
# #                 match = re.search(pattern, extracted_text)
# #                 if match:
# #                     matches[key] = match.group(1)
# #                     break
# #         return matches

# #     def compare_transaction_data(self, data1, data2):
# #         try:
# #             amount1 = float(data1['amount'].replace(',', ''))
# #             amount2 = float(data2['amount'].replace(',', ''))
# #             date1 = datetime.datetime.strptime(data1['date'], '%d/%m/%y').date()
# #             date2 = datetime.datetime.strptime(data2['date'], '%d/%m/%y').date()
# #             return (amount1 == amount2 and date1 == date2 and data1['code'] == data2['code'])
# #         except (ValueError, KeyError):
# #             return False







































































































# # import datetime
# # import os
# # import re
# # from django.conf import settings
# # from rest_framework import viewsets, status
# # from rest_framework.decorators import action
# # from rest_framework.response import Response
# # from .models import Transaction
# # from .serializers import TransactionSerializer
# # from google.cloud import vision
# # from web3 import Web3
# # from .utils import load_contract_abi

# # from django.shortcuts import render
# # import logging

# # logger = logging.getLogger(__name__)

# # def api_interaction_view(request):
# #     return render(request, 'api_interaction.html')

# # class TransactionViewSet(viewsets.ModelViewSet):
# #     queryset = Transaction.objects.all()
# #     serializer_class = TransactionSerializer



# #     @action(detail=False, methods=['post'])
# #     def create_transaction(self, request):
# #         data = request.data
# #         logger.debug("Incoming Data: %s", data)
        
# #         required_fields = ['total_amount', 'terms', 'parcel_id', 'buyer', 'seller']
# #         for field in required_fields:
# #             if field not in data:
# #                 return Response({"error": f"{field} must be provided"}, status=status.HTTP_400_BAD_REQUEST)

# #         try:
# #             total_amount = float(data['total_amount'])
# #         except ValueError:
# #             return Response({"error": "Invalid total amount provided"}, status=status.HTTP_400_BAD_REQUEST)

        
# #         if not hasattr(settings, 'LAND_TRANSACTION_CONTRACT_ADDRESS'):
# #             contract_address = deploy_smart_contract(settings.ORACLE_ADDRESS)
# #             settings.LAND_TRANSACTION_CONTRACT_ADDRESS = contract_address
# #         else:
# #             contract_address = settings.LAND_TRANSACTION_CONTRACT_ADDRESS

# #         transaction = self.save_transaction(data, contract_address)
        
       
# #         try:
# #             add_transaction(
# #                 contract_address,
# #                 transaction.id,
# #                 int(data['parcel_id']),
# #                 total_amount,
# #                 transaction.terms_hash
# #             )
# #         except Exception as e:
# #             logger.error(f"Failed to add transaction to smart contract: {str(e)}")
# #             transaction.delete()  
# #             return Response({"error": "Failed to add transaction to smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #         return Response({
# #             "message": "Transaction created",
# #             "transaction_id": transaction.id,
# #             "total_amount": transaction.total_amount,
# #             "terms_hash": transaction.terms_hash,
# #             "smart_contract_address": transaction.smart_contract_address
# #         }, status=status.HTTP_201_CREATED)

# #     def save_transaction(self, data, contract_address):
# #         terms_hash = Web3.keccak(text=data['terms']).hex()
# #         transaction = Transaction.objects.create(
# #             total_amount=float(data['total_amount']),
# #             buyer=data['buyer'],
# #             seller=data['seller'],
# #             parcel_id=data['parcel_id'],
# #             terms=data['terms'],
# #             smart_contract_address=contract_address,
# #             terms_hash=terms_hash
# #         )
# #         return transaction

# #     @action(detail=True, methods=['post'])
# #     def verify_payment(self, request, pk=None):
# #         transaction = self.get_object()
        
# #         try:
# #             verify_payment(
# #                 transaction.smart_contract_address,
# #                 transaction.id,
# #                 transaction.total_amount,
# #                 transaction.terms_hash
# #             )
# #         except Exception as e:
# #             logger.error(f"Failed to verify payment on smart contract: {str(e)}")
# #             return Response({"error": "Failed to verify payment on smart contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #         transaction.is_verified = True
# #         transaction.save()

# #         return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)

# #     @action(detail=True, methods=['get'])
# #     def check_verification(self, request, pk=None):
# #         transaction = self.get_object()
# #         is_verified = is_payment_verified(transaction.smart_contract_address, transaction.id)
        
# #         return Response({"is_verified": is_verified}, status=status.HTTP_200_OK)

# #     def deploy_new_smart_contract(self, total_amount, terms):
# #         try:
            
# #             contract_address = deploy_smart_contract(total_amount, terms)
# #             return contract_address
# #         except Exception as e:
# #             logger.error(f"Failed to deploy smart contract: {str(e)}")
# #             return None

# #     def save_transaction(self, total_amount, terms, contract_address):
# #         terms_hash = Web3.keccak(text=terms).hex()
# #         transaction = Transaction.objects.create(
# #             total_amount=total_amount,
# #             buyer="Buyer Name",
# #             seller="Seller Name",
# #             lawyer_details="Lawyer details",
# #             seller_details="Seller details",
# #             smart_contract_address=contract_address,
# #             terms_hash=terms_hash
# #         )
# #         return transaction

# #     @action(detail=True, methods=['post'])
# #     def upload_and_verify(self, request, pk=None):
# #         transaction = self.get_object()

# #         if 'document1' not in request.FILES or 'document2' not in request.FILES:
# #             return Response({"error": "Both documents must be provided"}, status=400)

# #         document1 = request.FILES['document1']
# #         document2 = request.FILES['document2']

# #         data1 = self.extract_data_from_image(document1)
# #         data2 = self.extract_data_from_image(document2)

# #         if self.compare_transaction_data(data1, data2):
# #             transaction.status = 'Verified'
# #             transaction.save()
# #             return Response({"message": "Documents verified successfully."}, status=200)
# #         else:
# #             return Response({"error": "Verification failed."}, status=400)

# #     def trigger_smart_contract(self, transaction):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract_address = transaction.smart_contract_address

# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.updateContract(
# #                 transaction.id,
# #                 transaction.terms_hash
# #             ).transact({'from': w3.eth.accounts[0]})

# #             w3.eth.wait_for_transaction_receipt(tx_hash)
# #             return True
# #         except Exception as e:
# #             print(f"Error updating smart contract: {e}")
# #             return False

# #     def extract_data_from_image(self, image_file):
# #         client = vision.ImageAnnotatorClient()
# #         try:
# #             image_content = image_file.read()
# #             image = vision.Image(content=image_content)
# #             response = client.text_detection(image=image)
# #             texts = response.text_annotations
# #             extracted_text = texts[0].description if texts else ""
# #         except Exception as e:
# #             raise ValueError(f"Failed to process image: {str(e)}")

# #         patterns = {
# #             'amount': [r'Ksh\s*([\d,]+\.\d{2})', r'KES\s*([\d,]+\.\d{2})'],
# #             'date': [r'on\s*(\d{1,2}/\d{1,2}/\d{2,4})', r'(\d{1,2}/\d{1,2}/\d{4})'],
# #             'code': [r'\b([A-Z0-9]{10})\b']
# #         }

# #         matches = {}
# #         for key, regex_list in patterns.items():
# #             for pattern in regex_list:
# #                 match = re.search(pattern, extracted_text)
# #                 if match:
# #                     matches[key] = match.group(1)
# #                     break
# #         return matches

# #     def compare_transaction_data(self, data1, data2):
# #         try:
# #             amount1 = float(data1['amount'].replace(',', ''))
# #             amount2 = float(data2['amount'].replace(',', ''))
# #             date1 = datetime.datetime.strptime(data1['date'], '%d/%m/%y').date()
# #             date2 = datetime.datetime.strptime(data2['date'], '%d/%m/%y').date()
# #             return (amount1 == amount2 and date1 == date2 and data1['code'] == data2['code'])
# #         except (ValueError, KeyError):
# #             return False

# #     def verify_payment_on_blockchain(self, transaction):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract_address = transaction.smart_contract_address

# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.verifyPayment(
# #                 transaction.id,
# #                 int(transaction.amount * 100)
# #             ).transact({'from': w3.eth.accounts[0]})

# #             w3.eth.wait_for_transaction_receipt(tx_hash)

# #             is_verified = contract.functions.isPaymentVerified(transaction.id).call()
# #             return is_verified
# #         except Exception as e:
# #             print(f"Error verifying payment on blockchain: {e}")
# #             return False

# #     def record_payment_on_blockchain(self, transaction, amount):
# #         w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
# #         contract_abi = load_contract_abi()
# #         contract_address = transaction.smart_contract_address

# #         contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# #         try:
# #             tx_hash = contract.functions.recordPayment(
# #                 transaction.id,
# #                 int(amount * 100) 
# #             ).transact({'from': w3.eth.accounts[0]})

# #             w3.eth.wait_for_transaction_receipt(tx_hash)

# #             remaining_amount = contract.functions.getRemainingAmount(transaction.id).call()
# #             is_fully_paid = contract.functions.isFullyPaid(transaction.id).call()

# #             return True
# #         except Exception as e:
# #             print(f"Error recording payment on blockchain: {e}")
# #             return False

