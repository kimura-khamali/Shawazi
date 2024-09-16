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
        uint256 cancellationFee;
        uint256 refundFee;
        bytes32 termsHash;
        bool isVerified;
        bool isPaymentRecorded;
        bool isAgreementSigned;
        bool isCanceled;
    }

    mapping(uint256 => Transaction) public transactions;

    event TransactionAdded(uint256 indexed agreementId, uint256 indexed parcelId);
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
        require(msg.sender == owner, "Only owner");
        _;
    }

    modifier onlyOracle() {
        require(msg.sender == oracleAddress, "Only oracle");
        _;
    }

    function addTransactionPart1(
        uint256 _agreementId,
        uint256 _totalAmount,
        uint256 _downPayment,
        uint256 _penaltyRate
    ) public onlyOwner {
        require(transactions[_agreementId].totalAmount == 0, "Exists");
        
        Transaction storage newTxn = transactions[_agreementId];
        newTxn.totalAmount = _totalAmount;
        newTxn.downPayment = _downPayment;
        newTxn.penaltyRate = _penaltyRate;
    }

    function addTransactionPart2(
        uint256 _agreementId,
        bytes32 _termsHash,
        uint256 _expirationDate,
        uint256 _totalInstallments,
        uint256 _cancellationFee,
        uint256 _refundFee
    ) public onlyOwner {
        Transaction storage newTxn = transactions[_agreementId];
        require(newTxn.totalAmount > 0, "Part 1 not called");
        
        newTxn.termsHash = _termsHash;
        newTxn.expirationDate = _expirationDate;
        newTxn.totalInstallments = _totalInstallments;
        newTxn.cancellationFee = _cancellationFee;
        newTxn.refundFee = _refundFee;
        newTxn.installmentAmount = (newTxn.totalAmount - newTxn.downPayment) / _totalInstallments;

        emit TransactionAdded(_agreementId, _agreementId); 
    }

    function signAgreement(uint256 _agreementId) public onlyOwner {
        Transaction storage txn = transactions[_agreementId];
        require(!txn.isAgreementSigned, "Signed");
        txn.isAgreementSigned = true;
        emit AgreementSigned(_agreementId);
    }

    function verifyPayment(uint256 _agreementId, uint256 _amount, bytes32 _termsHash) public onlyOracle {
        Transaction storage txn = transactions[_agreementId];
        require(txn.totalAmount > 0, "Not exist");
        require(txn.termsHash == _termsHash, "Terms mismatch");
        require(txn.isAgreementSigned, "Not signed");
        require(!txn.isVerified, "Verified");
        require(_amount >= txn.downPayment, "Low amount");

        txn.isVerified = true;
        emit PaymentVerified(_agreementId);
    }

    function recordPayment(uint256 _agreementId, uint256 _amount) public onlyOracle {
        Transaction storage txn = transactions[_agreementId];
        require(txn.isVerified, "Not verified");
        require(!txn.isPaymentRecorded, "Recorded");
        require(_amount >= txn.installmentAmount, "Low amount");

        txn.currentAmountPaid += _amount;
        txn.installmentsPaid += 1;
        txn.lastInstallmentDate = block.timestamp;

        if (txn.currentAmountPaid >= txn.totalAmount) {
            txn.isPaymentRecorded = true;
        }

        emit PaymentRecorded(_agreementId, _amount);
    }

    function payInstallment(uint256 _agreementId, uint256 _amount) public onlyOwner {
        Transaction storage txn = transactions[_agreementId];
        require(txn.totalAmount > 0, "Not exist");
        require(txn.isVerified, "Not verified");
        require(block.timestamp <= txn.expirationDate, "Expired");
        require(_amount >= txn.installmentAmount, "Low amount");

        txn.currentAmountPaid += _amount;
        txn.installmentsPaid += 1;
        txn.lastInstallmentDate = block.timestamp;

        if (txn.currentAmountPaid >= txn.totalAmount) {
            txn.isPaymentRecorded = true;
        }

        emit InstallmentPaid(_agreementId, txn.installmentsPaid, _amount);
    }

    function cancelTransaction(uint256 _agreementId) public onlyOwner {
        Transaction storage txn = transactions[_agreementId];
        require(!txn.isCanceled, "Cancelled");
        require(txn.totalAmount > 0, "Not exist");
        require(block.timestamp <= txn.expirationDate, "Expired");

        uint256 refundAmount = txn.currentAmountPaid > txn.cancellationFee ? txn.currentAmountPaid - txn.cancellationFee : 0;
        require(refundAmount > 0, "No refund");

        payable(msg.sender).transfer(refundAmount);
        txn.isCanceled = true;

        emit PaymentCancelled(_agreementId);
    }

    function getTransactionDetails(uint256 _agreementId) public view returns (
        uint256[11] memory numericDetails,
        bool[4] memory booleanDetails,
        bytes32 termsHash
    ) {
        Transaction storage txn = transactions[_agreementId];
        numericDetails = [
            txn.totalAmount,
            txn.downPayment,
            txn.penaltyRate,
            txn.expirationDate,
            txn.totalInstallments,
            txn.installmentsPaid,
            txn.lastInstallmentDate,
            txn.installmentAmount,
            txn.currentAmountPaid,
            txn.cancellationFee,
            txn.refundFee
        ];
        booleanDetails = [
            txn.isVerified,
            txn.isPaymentRecorded,
            txn.isAgreementSigned,
            txn.isCanceled
        ];
        termsHash = txn.termsHash;
    }

    function isPaymentVerified(uint256 _agreementId) public view returns (bool) {
        return transactions[_agreementId].isVerified;
    }

    function isContractExpired(uint256 _agreementId) public view returns (bool) {
        return block.timestamp > transactions[_agreementId].expirationDate;
    }

    function getRemainingInstallments(uint256 _agreementId) public view returns (uint256) {
        Transaction storage txn = transactions[_agreementId];
        return txn.totalInstallments - txn.installmentsPaid;
    }

    function getPenalty(uint256 _agreementId) public view returns (uint256) {
        Transaction storage txn = transactions[_agreementId];
        return (txn.totalAmount * txn.penaltyRate) / 100;
    }
}