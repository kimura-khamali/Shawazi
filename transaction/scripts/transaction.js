const { ethers } = require("hardhat");
const fs = require('fs');
const path = require('path');

// Update the ABI file path
const contractABIPath = path.resolve(__dirname, '..', 'artifacts', 'transaction', 'smart_contract', 'LandTransaction.json');
const contractABI = JSON.parse(fs.readFileSync('/home/studen/Shawazi/transaction/artifacts/transaction/smart_contract/LandTransaction.json', 'utf8')).abi;
console.log("ABI file path:", contractABIPath);

let abi;
try {
  abi = JSON.parse(fs.readFileSync(contractABIPath, 'utf8'));
} catch (error) {
  console.error("Error reading ABI file:", error);
  process.exit(1);
}

const contractAddress = '0xB402A0B53044c145B922cc7960bf2c4010B8CDE5'; // Replace with your contract address

async function main() {
  // Connect to the Hardhat network
  const provider = new ethers.providers.JsonRpcProvider("http://localhost:8545");

  // Get the contract factory and attach it to the deployed contract
  const contract = new ethers.Contract(contractAddress, abi, provider);

  // Function to get transaction details
  async function getTransactionDetails(agreementId) {
    try {
      const txn = await contract.getTransactionDetails(agreementId);
      console.log(`Transaction Details for Agreement ${agreementId}:`);
      console.log(`Total Amount: ${ethers.utils.formatEther(txn[0])} ETH`);
      console.log(`Down Payment: ${ethers.utils.formatEther(txn[1])} ETH`);
      console.log(`Penalty Rate: ${txn[2]}%`);
      console.log(`Expiration Date: ${new Date(txn[3] * 1000).toLocaleDateString()}`);
      console.log(`Total Installments: ${txn[4]}`);
      console.log(`Installments Paid: ${txn[5]}`);
      console.log(`Last Installment Date: ${new Date(txn[6] * 1000).toLocaleDateString()}`);
      console.log(`Installment Amount: ${ethers.utils.formatEther(txn[7])} ETH`);
      console.log(`Current Amount Paid: ${ethers.utils.formatEther(txn[8])} ETH`);
      console.log(`Cancellation Fee: ${ethers.utils.formatEther(txn[9])} ETH`);
      console.log(`Refund Fee: ${ethers.utils.formatEther(txn[10])} ETH`);
      console.log(`Terms Hash: ${txn[11]}`);
      console.log(`Verification Status: ${txn[12]}`);
      console.log(`Payment Recorded: ${txn[13]}`);
      console.log(`Agreement Signed: ${txn[14]}`);
      console.log(`Canceled: ${txn[15]}`);
      console.log("---");
    } catch (error) {
      console.error("Error fetching transaction details:", error);
    }
  }

  // Function to get remaining installments
  async function getRemainingInstallments(agreementId) {
    try {
      const remaining = await contract.getRemainingInstallments(agreementId);
      console.log(`Remaining Installments for Agreement ${agreementId}: ${remaining}`);
    } catch (error) {
      console.error("Error getting remaining installments:", error);
    }
  }

  // Function to get penalty
  async function getPenalty(agreementId) {
    try {
      const penalty = await contract.getPenalty(agreementId);
      console.log(`Penalty for Agreement ${agreementId}: ${penalty} ETH`);
    } catch (error) {
      console.error("Error getting penalty:", error);
    }
  }

  // Function to check if contract expired
  async function isContractExpired(agreementId) {
    try {
      const isExpired = await contract.isContractExpired(agreementId);
      console.log(`Is Agreement ${agreementId} expired? ${isExpired}`);
    } catch (error) {
      console.error("Error checking expiration:", error);
    }
  }

  // Main execution
  const agreementIds = [1, 2, 3]; // Replace with actual agreement IDs
  for (const agreementId of agreementIds) {
    console.log(`Processing Agreement ${agreementId}:`);
    await getTransactionDetails(agreementId);
    await getRemainingInstallments(agreementId);
    await getPenalty(agreementId);
    await isContractExpired(agreementId);
    console.log("---");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });












































// const { ethers } = require("hardhat");
// const fs = require("fs");
// const path = require("path");
// require("dotenv").config();

// async function main() {
//   // Load environment variables
//   const provider = new ethers.providers.JsonRpcProvider(process.env.BLOCKCHAIN_PROVIDER_URL);
//   const contractAddress = process.env.SMART_CONTRACT_ADDRESS;
  
//   // Resolve the path to the ABI file
//   const contractABIPath = path.resolve(__dirname, '..', '..', 'LandTransaction.json');
//   console.log("ABI file path:", contractABIPath);

//   let contractABI;
//   try {
//     contractABI = JSON.parse(fs.readFileSync(contractABIPath, "utf8"));
//   } catch (error) {
//     console.error("Error reading ABI file:", error);
//     return;
//   }

//   if (!contractAddress || !contractABI) {
//     console.error("Contract address or ABI is missing.");
//     return;
//   }

//   // Attach to the contract
//   const contract = new ethers.Contract(contractAddress, contractABI, provider);

//   // Example function call
//   async function getTransactionDetails(agreementId) {
//     try {
//       const txn = await contract.getTransactionDetails(agreementId);
//       console.log(`Transaction Details for Agreement ${agreementId}:`, txn);
//     } catch (error) {
//       console.error("Error fetching transaction details:", error);
//     }
//   }

//   // Example usage
//   const agreementIds = [1, 2, 3]; // Replace with actual agreement IDs
//   for (const agreementId of agreementIds) {
//     console.log(`Processing Agreement ${agreementId}:`);
//     await getTransactionDetails(agreementId);
//     console.log("---");
//   }
// }

// main()
//   .then(() => process.exit(0))
//   .catch((error) => {
//     console.error(error);
//     process.exit(1);
//   });


