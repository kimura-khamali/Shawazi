// scripts/deploy.js

async function main() {
    const [deployer] = await ethers.getSigners();

    console.log("Deploying contracts with the account:", deployer.address);

    const MyContract = await ethers.getContractFactory("MyContract");
    const contract = await MyContract.deploy();

    console.log("Contract deployed to address:", contract.address);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});




















// async function main() {
//     const [deployer] = await ethers.getSigners();
//     console.log("Deploying contracts with the account:", deployer.address);

//     const LandTransaction = await ethers.getContractFactory("LandTransaction");
//     const landTransaction = await LandTransaction.deploy();

//     console.log("LandTransaction contract deployed to:", landTransaction.address);
// }

// main()
//     .then(() => process.exit(0))
//     .catch((error) => {
//         console.error(error);
//         process.exit(1);
//     });










































// // async function main() {
    
// //     const [deployer] = await ethers.getSigners();

// //     console.log("Deploying contracts with the account:", deployer.address);

    
// //     const MyContract = await ethers.getContractFactory("MyContract");
// //     const myContract = await MyContract.deploy;

// //     console.log("Contract deployed to address:", myContract.address);
// // }

// // main()
// //     .then(() => process.exit(0))
// //     .catch((error) => {
// //         console.error(error);
// //         process.exit(1);
// //     });



// // scripts/deploy.js

// async function main() {
//     const [deployer] = await ethers.getSigners();

//     console.log("Deploying contracts with the account:", deployer.address);

//     // Replace 'MyContract' with the actual name of your contract
//     const MyContract = await ethers.getContractFactory("MyContract");
//     const contract = await MyContract.deploy();

//     console.log("Contract deployed to address:", contract.address);
// }

// main().catch((error) => {
//     console.error(error);
//     process.exitCode = 1;
// });
