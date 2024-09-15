// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LandTransaction {
    address public owner;
    address public oracleAddress;

    struct Transaction {
        uint256 amount;
        bool isVerified;
        bytes32 termsHash;
    }

    mapping(uint256 => Transaction) public transactions;

    event TransactionAdded(uint256 indexed transactionId, uint256 indexed parcelId, uint256 amount, bytes32 termsHash);
    event PaymentVerified(uint256 indexed transactionId);

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

    function addTransaction(uint256 _transactionId, uint256 _parcelId, uint256 _amount, bytes32 _termsHash) public onlyOwner {
        require(transactions[_transactionId].amount == 0, "Transaction already exists");
        transactions[_transactionId] = Transaction(_amount, false, _termsHash);
        emit TransactionAdded(_transactionId, _parcelId, _amount, _termsHash);
    }

    function verifyPayment(uint256 _transactionId, uint256 _amount, bytes32 _termsHash) public onlyOracle {
        require(transactions[_transactionId].amount == _amount, "Amount mismatch");
        require(transactions[_transactionId].termsHash == _termsHash, "Terms mismatch");
        require(!transactions[_transactionId].isVerified, "Payment already verified");
        
        transactions[_transactionId].isVerified = true;
        emit PaymentVerified(_transactionId);
    }

    function isPaymentVerified(uint256 _transactionId) public view returns (bool) {
        return transactions[_transactionId].isVerified;
    }

    function getTransactionTermsHash(uint256 _transactionId) public view returns (bytes32) {
        return transactions[_transactionId].termsHash;
    }
}
