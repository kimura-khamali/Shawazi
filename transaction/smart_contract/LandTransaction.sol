// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract LandTransaction {
    address public owner;
    address public oracleAddress;

    struct Transaction {
        uint256 totalAmount;        
        uint256 downPayment;        
        uint256 penaltyRate;        
        uint256 expirationDate;     
        uint256 totalInstallments; 
        uint256 installmentsPaid;   
        uint256 lastInstallmentDate;
        uint256 installmentAmount;  
        uint256 currentAmountPaid;  
        bool isVerified;            
        bool isPaymentRecorded;     
        bytes32 termsHash;          
        bool isAgreementSigned;     
        bool isCanceled;            
        uint256 cancellationFee;    
        uint256 refundFee;          
    }

    mapping(uint256 => Transaction) public transactions;

    event TransactionAdded(
        uint256 indexed agreementId,
        uint256 indexed parcelId,
        uint256 totalAmount,
        uint256 downPayment,
        bytes32 termsHash,
        uint256 penaltyRate,
        uint256 expirationDate,
        uint256 totalInstallments
    );

    event PaymentVerified(uint256 indexed agreementId);
    event AgreementSigned(uint256 indexed agreementId);
    event PaymentRecorded(uint256 indexed agreementId, uint256 amount);
    event InstallmentPaid(uint256 indexed agreementId, uint256 installmentNumber, uint256 amount);
    event PaymentCancelled(uint256 indexed agreementId);

    constructor(address _oracleAddress) {
        owner = msg.sender;
        oracleAddress = _oracleAddress;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can call this function");
        _;
    }

    modifier onlyOracle() {
        require(msg.sender == oracleAddress, "Only the oracle can call this function");
        _;
    }

    function addTransaction(
        uint256 _agreementId,
        uint256 _parcelId,
        uint256 _totalAmount,
        uint256 _downPayment,
        uint256 _penaltyRate,
        bytes32 _termsHash,
        uint256 _expirationDate,
        uint256 _totalInstallments,
        uint256 _cancellationFee,
        uint256 _refundFee
    ) public onlyOwner {
        require(transactions[_agreementId].totalAmount == 0, "Transaction already exists");

        uint256 installmentAmount = calculateInstallmentAmount(_totalAmount, _downPayment, _totalInstallments);
        transactions[_agreementId] = Transaction({
            totalAmount: _totalAmount,
            downPayment: _downPayment,
            penaltyRate: _penaltyRate,
            expirationDate: _expirationDate,
            totalInstallments: _totalInstallments,
            installmentsPaid: 0,
            lastInstallmentDate: 0,
            installmentAmount: installmentAmount,
            currentAmountPaid: 0,
            isVerified: false,
            isPaymentRecorded: false,
            termsHash: _termsHash,
            isAgreementSigned: false,
            isCanceled: false,
            cancellationFee: _cancellationFee,
            refundFee: _refundFee
        });

        emit TransactionAdded(_agreementId, _parcelId, _totalAmount, _downPayment, _termsHash, _penaltyRate, _expirationDate, _totalInstallments);
    }

    function calculateInstallmentAmount(uint256 _totalAmount, uint256 _downPayment, uint256 _totalInstallments) internal pure returns (uint256) {
        return (_totalAmount - _downPayment) / _totalInstallments;
    }

    function signAgreement(uint256 _agreementId) public onlyOwner {
        require(!transactions[_agreementId].isAgreementSigned, "Agreement already signed");
        transactions[_agreementId].isAgreementSigned = true;
        emit AgreementSigned(_agreementId);
    }

    function verifyPayment(uint256 _agreementId, uint256 _amount, bytes32 _termsHash) public onlyOracle {
        Transaction storage txn = transactions[_agreementId];
        require(txn.totalAmount > 0, "Transaction does not exist");
        require(txn.termsHash == _termsHash, "Terms mismatch");
        require(txn.isAgreementSigned, "Agreement not signed");
        require(!txn.isVerified, "Payment already verified");
        require(_amount >= txn.downPayment, "Amount less than down payment");

        txn.isVerified = true;
        emit PaymentVerified(_agreementId);
    }

    function recordPayment(uint256 _agreementId, uint256 _amount) public onlyOracle {
        Transaction storage txn = transactions[_agreementId];
        require(txn.isVerified, "Payment not verified");
        require(!txn.isPaymentRecorded, "Payment already recorded");
        require(_amount >= txn.installmentAmount, "Amount less than required installment");

        updateTransactionOnPayment(txn, _amount);
        emit PaymentRecorded(_agreementId, _amount);
    }

    function payInstallment(uint256 _agreementId, uint256 _amount) public onlyOwner {
        Transaction storage txn = transactions[_agreementId];
        require(txn.totalAmount > 0, "Transaction does not exist");
        require(txn.isVerified, "Payment not verified");
        require(block.timestamp <= txn.expirationDate, "Contract has expired");
        require(_amount > 0, "Amount must be greater than zero");
        require(_amount >= txn.installmentAmount, "Amount less than required installment");

        updateTransactionOnPayment(txn, _amount);
        emit InstallmentPaid(_agreementId, txn.installmentsPaid, _amount);
    }

    function updateTransactionOnPayment(Transaction storage txn, uint256 _amount) internal {
        txn.currentAmountPaid += _amount;
        txn.installmentsPaid += 1;
        txn.lastInstallmentDate = block.timestamp;

        if (txn.currentAmountPaid >= txn.totalAmount) {
            txn.isPaymentRecorded = true;
        }
    }

    function cancelTransaction(uint256 _agreementId) public onlyOwner {
        Transaction storage txn = transactions[_agreementId];
        require(!txn.isCanceled, "Transaction is already cancelled");
        require(txn.totalAmount > 0, "Transaction does not exist");
        require(block.timestamp <= txn.expirationDate, "Contract has expired");

        uint256 refundAmount = calculateRefundAmount(txn.currentAmountPaid, txn.cancellationFee);
        require(refundAmount > 0, "No refundable amount available");

        payable(msg.sender).transfer(refundAmount);
        txn.isCanceled = true;

        emit PaymentCancelled(_agreementId);
    }

    function calculateRefundAmount(uint256 _currentAmountPaid, uint256 _cancellationFee) internal pure returns (uint256) {
        return _currentAmountPaid > _cancellationFee ? _currentAmountPaid - _cancellationFee : 0;
    }

    function getTransactionDetails(uint256 _agreementId) public view returns (
        uint256 totalAmount,
        uint256 downPayment,
        uint256 penaltyRate,
        uint256 expirationDate,
        uint256 totalInstallments,
        uint256 installmentsPaid,
        uint256 lastInstallmentDate,
        uint256 installmentAmount,
        uint256 currentAmountPaid,
        bool isVerified,
        bool isPaymentRecorded,
        bytes32 termsHash,
        bool isAgreementSigned,
        bool isCanceled,
        uint256 cancellationFee,
        uint256 refundFee
    ) {
        Transaction memory txn = transactions[_agreementId];
        return (
            txn.totalAmount,
            txn.downPayment,
            txn.penaltyRate,
            txn.expirationDate,
            txn.totalInstallments,
            txn.installmentsPaid,
            txn.lastInstallmentDate,
            txn.installmentAmount,
            txn.currentAmountPaid,
            txn.isVerified,
            txn.isPaymentRecorded,
            txn.termsHash,
            txn.isAgreementSigned,
            txn.isCanceled,
            txn.cancellationFee,
            txn.refundFee
        );
    }

    function isPaymentVerified(uint256 _agreementId) public view returns (bool) {
        return transactions[_agreementId].isVerified;
    }

    function isContractExpired(uint256 _agreementId) public view returns (bool) {
        require(transactions[_agreementId].totalAmount > 0, "Transaction does not exist");
        return block.timestamp > transactions[_agreementId].expirationDate;
    }

    function getRemainingInstallments(uint256 _agreementId) public view returns (uint256) {
        require(transactions[_agreementId].totalAmount > 0, "Transaction does not exist");
        return transactions[_agreementId].totalInstallments - transactions[_agreementId].installmentsPaid;
    }

    function getPenalty(uint256 _agreementId) public view returns (uint256) {
        require(transactions[_agreementId].totalAmount > 0, "Transaction does not exist");
        return calculatePenalty(transactions[_agreementId].totalAmount, transactions[_agreementId].penaltyRate);
    }

    function calculatePenalty(uint256 _totalAmount, uint256 _penaltyRate) internal pure returns (uint256) {
        return (_totalAmount * _penaltyRate) / 100;
    }
}
