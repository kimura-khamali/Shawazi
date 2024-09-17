require('@nomiclabs/hardhat-ethers');
require('@nomiclabs/hardhat-etherscan');
require('dotenv').config();

const { INFURA_PROJECT_ID, PRIVATE_KEY, ETHERSCAN_API_KEY } = process.env;

module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      },
      viaIR: true
    }
  },
  paths: {
    sources: "./transaction/smart_contract",
    tests: "./transaction/test",
    cache: "./transaction/cache",
    artifacts: "./transaction/artifacts"
  },
  networks: {
    hardhat: {
      chainId: 1337
    },
    localhost: {
      url: "http://127.0.0.1:8545"
    },
    ...(INFURA_PROJECT_ID && PRIVATE_KEY ? {
      rinkeby: {
        url: `https://rinkeby.infura.io/v3/${INFURA_PROJECT_ID}`,
        accounts: [`0x${PRIVATE_KEY}`]
      },
      mainnet: {
        url: `https://mainnet.infura.io/v3/${INFURA_PROJECT_ID}`,
        accounts: [`0x${PRIVATE_KEY}`]
      }
    } : {})
  },
  etherscan: {
    apiKey: ETHERSCAN_API_KEY
  }
};




























// require('@nomiclabs/hardhat-ethers');
// require('@nomiclabs/hardhat-etherscan');
// require('dotenv').config();

// const { INFURA_PROJECT_ID, PRIVATE_KEY, ETHERSCAN_API_KEY } = process.env;

// module.exports = {
//   solidity: {
//     version: "0.8.24",
//     settings: {
//       optimizer: {
//         enabled: true,
//         runs: 200
//       },
//       viaIR: true 
//     }
//   },
//   paths: {
//     sources: "./transaction/smart_contract",
//     tests: "./transaction/test",
//     cache: "./transaction/cache",
//     artifacts: "./transaction/artifacts"
//   },
//   networks: {
//     hardhat: {
//       chainId: 1337
//     },
//     localhost: {
//       url: "http://127.0.0.1:8545"
//     },
//     ...(INFURA_PROJECT_ID && PRIVATE_KEY ? {
//       rinkeby: {
//         url: `https://rinkeby.infura.io/v3/${INFURA_PROJECT_ID}`,
//         accounts: [`0x${PRIVATE_KEY}`]
//       },
//       mainnet: {
//         url: `https://mainnet.infura.io/v3/${INFURA_PROJECT_ID}`,
//         accounts: [`0x${PRIVATE_KEY}`]
//       }
//     } : {})
//   },
//   etherscan: {
//     apiKey: ETHERSCAN_API_KEY
//   }
// };

































// // hardhat.config.js

// require('@nomiclabs/hardhat-ethers');



// module.exports = {
//   solidity: {
//     version: "0.8.24",
//     settings: {
//       optimizer: {
//         enabled: true,
//         runs: 200
//       },
//       viaIR: true // Enable viaIR to help with stack too deep errors
//     }
//   },
//   paths: {
//     sources: "./transaction/smart_contract",
//     tests: "./transaction/test",
//     cache: "./transaction/cache",
//     artifacts: "./transaction/artifacts"
//   },
//   networks: {
//     localhost: {
//       url: "http://127.0.0.1:8545"
//     }
//   }
// };





















// // hardhat.config.js

// require('@nomiclabs/hardhat-ethers');

// module.exports = {
//   solidity: "0.8.18", // Make sure this matches your contract's Solidity version
//   paths: {
//     sources: "./transaction/smart_contract",
//     tests: "./transaction/test",
//     cache: "./transaction/cache",
//     artifacts: "./transaction/artifacts"
//   },
//   networks: {
//     localhost: {
//       url: "http://127.0.0.1:8545"
//     }
//   }
// };















// require('@nomiclabs/hardhat-ethers');
// require('dotenv').config();

// /** @type import('hardhat/config').HardhatUserConfig */

// module.exports = {
//   solidity: {
//     version: "0.8.24",
//     settings: {
//       optimizer: {
//         enabled: true,
//         runs: 1000,
//       },
//     },
//   },
// };

























// require('@nomiclabs/hardhat-ethers');
// require('dotenv').config();

// /** @type import('hardhat/config').HardhatUserConfig */
// module.exports = {
//   solidity: "0.8.24",
//   paths: {
//     sources: "./transaction/smart_contract",
//     artifacts: "./transaction/artifacts",
//   },
//   networks: {
//     development: {
//       url: "http://localhost:8545",
//       accounts: [`${process.env.PRIVATE_KEY}`] // Ensure PRIVATE_KEY is correctly defined in your .env file
//     }
//   }
// };


// require('@nomiclabs/hardhat-ethers');

// module.exports = {
//   solidity: "0.8.24",
//   networks: {
//     localhost: {
//       url: "http://127.0.0.1:8545",
//       accounts: [`0x${process.env.PRIVATE_KEY}`]  // Ensure you have a valid private key here
//     }
//   }
// };




























// /** @type import('hardhat/config').HardhatUserConfig */
// module.exports = {
//   solidity: "0.8.24",
//   paths: {
//     sources: "./transaction/smart_contract",
//     artifacts: "./transaction/artifacts",
//   },
// };


// require('@nomiclabs/hardhat-ethers');
// require('dotenv').config(); // if you use .env for environment variables

// module.exports = {
//   solidity: "0.8.24",
//   networks: {
//     development: {
//       url: "http://localhost:8545", // URL for your local Ganache CLI or Hardhat Network
//       accounts: [`0x${process.env.PRIVATE_KEY}`] // Replace with your account's private key
//     }
    
//   }
// };


// require('@nomiclabs/hardhat-ethers');
// require('dotenv').config();

// module.exports = {
//   solidity: "0.8.24",
//   networks: {
//     development: {
//       url: "http://localhost:8545", // URL for your local Ganache CLI or Hardhat Network
//       accounts: [`0x${process.env.PRIVATE_KEY}`] // Replace with actual private key or use environment variables
//     }
//   }
// };
