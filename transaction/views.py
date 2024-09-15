import datetime
import os
import re
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer
from google.cloud import vision
from web3 import Web3
from .utils import load_contract_abi

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    @action(detail=False, methods=['post'])
    def create_transaction(self, request):
        if 'total_amount' not in request.data or 'terms' not in request.data:
            return Response({"error": "Total amount and terms must be provided"}, status=400)

        total_amount = float(request.data['total_amount'])
        terms = request.data['terms']

        transaction = self.save_transaction(total_amount, terms)
        return Response({
            "message": "Transaction created",
            "transaction_id": transaction.id,
            "total_amount": transaction.total_amount,
            "terms_hash": transaction.terms_hash
        }, status=201)

    def save_transaction(self, total_amount, terms):
        terms_hash = Web3.keccak(text=terms).hex()
        transaction = Transaction.objects.create(
            total_amount=total_amount,
            buyer="Buyer Name",
            seller="Seller Name",
            lawyer_details="Lawyer details",
            seller_details="Seller details",
            smart_contract_address=settings.SMART_CONTRACT_ADDRESS,
            terms_hash=terms_hash
        )
        return transaction

    @action(detail=True, methods=['post'])
    def upload_and_verify(self, request, pk=None):
        transaction = self.get_object()

        if 'document1' not in request.FILES or 'document2' not in request.FILES:
            return Response({"error": "Both documents must be provided"}, status=400)

        document1 = request.FILES['document1']
        document2 = request.FILES['document2']

        data1 = self.extract_data_from_image(document1)
        data2 = self.extract_data_from_image(document2)

        if self.compare_transaction_data(data1, data2):
            transaction.status = 'Verified'
            transaction.save()
            return Response({"message": "Documents verified successfully."}, status=200)
        else:
            return Response({"error": "Verification failed."}, status=400)

    def trigger_smart_contract(self, transaction):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract_address = transaction.smart_contract_address

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        try:
            tx_hash = contract.functions.updateContract(
                transaction.id,
                transaction.terms_hash
            ).transact({'from': w3.eth.accounts[0]})

            w3.eth.wait_for_transaction_receipt(tx_hash)
            return True
        except Exception as e:
            print(f"Error updating smart contract: {e}")
            return False

    def extract_data_from_image(self, image_file):
        client = vision.ImageAnnotatorClient()
        try:
            image_content = image_file.read()
            image = vision.Image(content=image_content)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            extracted_text = texts[0].description if texts else ""
        except Exception as e:
            raise ValueError(f"Failed to process image: {str(e)}")

        patterns = {
            'amount': [r'Ksh\s*([\d,]+\.\d{2})', r'KES\s*([\d,]+\.\d{2})'],
            'date': [r'on\s*(\d{1,2}/\d{1,2}/\d{2,4})', r'(\d{1,2}/\d{1,2}/\d{4})'],
            'code': [r'\b([A-Z0-9]{10})\b']
        }

        matches = {}
        for key, regex_list in patterns.items():
            for pattern in regex_list:
                match = re.search(pattern, extracted_text)
                if match:
                    matches[key] = match.group(1)
                    break
        return matches

    def compare_transaction_data(self, data1, data2):
        try:
            amount1 = float(data1['amount'].replace(',', ''))
            amount2 = float(data2['amount'].replace(',', ''))
            date1 = datetime.datetime.strptime(data1['date'], '%d/%m/%y').date()
            date2 = datetime.datetime.strptime(data2['date'], '%d/%m/%y').date()
            return (amount1 == amount2 and date1 == date2 and data1['code'] == data2['code'])
        except (ValueError, KeyError):
            return False

    def verify_payment_on_blockchain(self, transaction):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract_address = transaction.smart_contract_address

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        try:
            tx_hash = contract.functions.verifyPayment(
                transaction.id,
                int(transaction.amount * 100)
            ).transact({'from': w3.eth.accounts[0]})

            w3.eth.wait_for_transaction_receipt(tx_hash)

            is_verified = contract.functions.isPaymentVerified(transaction.id).call()
            return is_verified
        except Exception as e:
            print(f"Error verifying payment on blockchain: {e}")
            return False

    def record_payment_on_blockchain(self, transaction, amount):
        w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        contract_abi = load_contract_abi()
        contract_address = transaction.smart_contract_address

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        try:
            tx_hash = contract.functions.recordPayment(
                transaction.id,
                int(amount * 100) 
            ).transact({'from': w3.eth.accounts[0]})

            w3.eth.wait_for_transaction_receipt(tx_hash)

            remaining_amount = contract.functions.getRemainingAmount(transaction.id).call()
            is_fully_paid = contract.functions.isFullyPaid(transaction.id).call()

            return True
        except Exception as e:
            print(f"Error recording payment on blockchain: {e}")
            return False

