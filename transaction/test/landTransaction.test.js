const { expect } = require('chai');
const { ethers } = require('hardhat');

describe("LandTransaction", function () {
  let LandTransaction;
  let landTransaction;
  let owner;
  let oracle;
  let addr1;
  let addr2;

  const agreementId = 1;
  const totalAmount = ethers.utils.parseEther("10");
  const downPayment = ethers.utils.parseEther("2");
  const penaltyRate = 5; // 5%
  const termsHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Terms and conditions"));
  const expirationDate = Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60; // 30 days from now
  const totalInstallments = 12;
  const cancellationFee = ethers.utils.parseEther("0.5");
  const refundFee = ethers.utils.parseEther("0.1");

  beforeEach(async function () {
    [owner, oracle, addr1, addr2] = await ethers.getSigners();
    LandTransaction = await ethers.getContractFactory("LandTransaction");
    landTransaction = await LandTransaction.deploy(oracle.address);
    await landTransaction.deployed();
  });

  it("Should deploy the contract", async function () {
    expect(await landTransaction.owner()).to.equal(owner.address);
    expect(await landTransaction.oracleAddress()).to.equal(oracle.address);
  });

  it("Should add a new transaction", async function () {
    await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
    await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);

    const txDetails = await landTransaction.getTransactionDetails(agreementId);
    expect(txDetails.numericDetails[0].toString()).to.equal(totalAmount.toString());
    expect(txDetails.numericDetails[1].toString()).to.equal(downPayment.toString());
    expect(txDetails.numericDetails[2].toString()).to.equal(penaltyRate.toString());
  });

  it("Should sign an agreement", async function () {
    await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
    await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
    await landTransaction.signAgreement(agreementId);

    const txDetails = await landTransaction.getTransactionDetails(agreementId);
    expect(txDetails.booleanDetails[2]).to.be.true; // isAgreementSigned
  });

  it("Should verify payment", async function () {
    await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
    await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
    await landTransaction.signAgreement(agreementId);
    await landTransaction.connect(oracle).verifyPayment(agreementId, downPayment, termsHash);

    expect(await landTransaction.isPaymentVerified(agreementId)).to.be.true;
  });

  it("Should record payment", async function () {
    await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
    await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
    await landTransaction.signAgreement(agreementId);
    await landTransaction.connect(oracle).verifyPayment(agreementId, downPayment, termsHash);
    const paymentAmount = ethers.utils.parseEther("1");
    await landTransaction.connect(oracle).recordPayment(agreementId, paymentAmount);

    const txDetails = await landTransaction.getTransactionDetails(agreementId);
    expect(txDetails.numericDetails[8].toString()).to.equal(paymentAmount.toString()); // currentAmountPaid
  });

  it("Should pay installment", async function () {
    await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
    await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
    await landTransaction.signAgreement(agreementId);
    await landTransaction.connect(oracle).verifyPayment(agreementId, downPayment, termsHash);
    const installmentAmount = ethers.utils.parseEther("1");
    await landTransaction.payInstallment(agreementId, installmentAmount);

    const txDetails = await landTransaction.getTransactionDetails(agreementId);
    expect(txDetails.numericDetails[8].toString()).to.equal(installmentAmount.toString()); // currentAmountPaid
    expect(txDetails.numericDetails[5].toString()).to.equal("1"); // installmentsPaid
  });

  it("Should get remaining installments", async function () {
    await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
    await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
    await landTransaction.signAgreement(agreementId);
    await landTransaction.connect(oracle).verifyPayment(agreementId, downPayment, termsHash);
    await landTransaction.payInstallment(agreementId, ethers.utils.parseEther("1"));

    const remainingInstallments = await landTransaction.getRemainingInstallments(agreementId);
    expect(remainingInstallments.toString()).to.equal((totalInstallments - 1).toString());
  });

  it("Should get penalty", async function () {
    await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
    await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);

    const expectedPenalty = totalAmount.mul(penaltyRate).div(100);
    const penalty = await landTransaction.getPenalty(agreementId);
    expect(penalty.toString()).to.equal(expectedPenalty.toString());
  });

  it("Should check if contract is expired", async function () {
    await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
    await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);

    expect(await landTransaction.isContractExpired(agreementId)).to.be.false;

    // Advance time to after expiration date
    await ethers.provider.send("evm_increaseTime", [31 * 24 * 60 * 60]);
    await ethers.provider.send("evm_mine");

    expect(await landTransaction.isContractExpired(agreementId)).to.be.true;
  });
});


















// const { expect } = require("chai");
// const { ethers } = require("hardhat");

// describe("LandTransaction", function () {
//   let LandTransaction;
//   let landTransaction;
//   let owner;
//   let oracle;
//   let addr1;
//   let addr2;

//   const agreementId = 1;
//   const totalAmount = ethers.utils.parseEther("10");
//   const downPayment = ethers.utils.parseEther("2");
//   const penaltyRate = 5; // 5%
//   const termsHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("Terms and conditions"));
//   const expirationDate = Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60; // 30 days from now
//   const totalInstallments = 12;
//   const cancellationFee = ethers.utils.parseEther("0.5");
//   const refundFee = ethers.utils.parseEther("0.1");

//   beforeEach(async function () {
//     [owner, oracle, addr1, addr2] = await ethers.getSigners();
//     LandTransaction = await ethers.getContractFactory("LandTransaction");
//     landTransaction = await LandTransaction.deploy(oracle.address);
//     await landTransaction.deployed();
//   });

//   it("Should deploy the contract", async function () {
//     expect(await landTransaction.owner()).to.equal(owner.address);
//     expect(await landTransaction.oracleAddress()).to.equal(oracle.address);
//   });

//   it("Should add a new transaction", async function () {
//     await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
//     await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);

//     const txDetails = await landTransaction.getTransactionDetails(agreementId);
//     expect(txDetails.numericDetails[0].toString()).to.equal(totalAmount.toString());
//     expect(txDetails.numericDetails[1].toString()).to.equal(downPayment.toString());
//     expect(txDetails.numericDetails[2].toString()).to.equal(penaltyRate.toString());
//   });

//   it("Should sign an agreement", async function () {
//     await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
//     await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
//     await landTransaction.signAgreement(agreementId);

//     const txDetails = await landTransaction.getTransactionDetails(agreementId);
//     expect(txDetails.booleanDetails[2]).to.be.true; // isAgreementSigned
//   });

//   it("Should verify payment", async function () {
//     await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
//     await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
//     await landTransaction.signAgreement(agreementId);
//     await landTransaction.connect(oracle).verifyPayment(agreementId, downPayment, termsHash);

//     expect(await landTransaction.isPaymentVerified(agreementId)).to.be.true;
//   });

//   it("Should record payment", async function () {
//     await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
//     await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
//     await landTransaction.signAgreement(agreementId);
//     await landTransaction.connect(oracle).verifyPayment(agreementId, downPayment, termsHash);
//     const paymentAmount = ethers.utils.parseEther("1");
//     await landTransaction.connect(oracle).recordPayment(agreementId, paymentAmount);

//     const txDetails = await landTransaction.getTransactionDetails(agreementId);
//     expect(txDetails.numericDetails[8].toString()).to.equal(paymentAmount.toString()); // currentAmountPaid
//   });

//   it("Should pay installment", async function () {
//     await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
//     await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
//     await landTransaction.signAgreement(agreementId);
//     await landTransaction.connect(oracle).verifyPayment(agreementId, downPayment, termsHash);
//     const installmentAmount = ethers.utils.parseEther("1");
//     await landTransaction.payInstallment(agreementId, installmentAmount);

//     const txDetails = await landTransaction.getTransactionDetails(agreementId);
//     expect(txDetails.numericDetails[8].toString()).to.equal(installmentAmount.toString()); // currentAmountPaid
//     expect(txDetails.numericDetails[5].toString()).to.equal("1"); // installmentsPaid
//   });

//   it("Should get remaining installments", async function () {
//     await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
//     await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);
//     await landTransaction.signAgreement(agreementId);
//     await landTransaction.connect(oracle).verifyPayment(agreementId, downPayment, termsHash);
//     await landTransaction.payInstallment(agreementId, ethers.utils.parseEther("1"));

//     const remainingInstallments = await landTransaction.getRemainingInstallments(agreementId);
//     expect(remainingInstallments.toString()).to.equal((totalInstallments - 1).toString());
//   });

//   it("Should get penalty", async function () {
//     await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
//     await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);

//     const expectedPenalty = totalAmount.mul(penaltyRate).div(100);
//     const penalty = await landTransaction.getPenalty(agreementId);
//     expect(penalty.toString()).to.equal(expectedPenalty.toString());
//   });

//   it("Should check if contract is expired", async function () {
//     await landTransaction.addTransactionPart1(agreementId, totalAmount, downPayment, penaltyRate);
//     await landTransaction.addTransactionPart2(agreementId, termsHash, expirationDate, totalInstallments, cancellationFee, refundFee);

//     expect(await landTransaction.isContractExpired(agreementId)).to.be.false;

//     // Advance time to after expiration date
//     await ethers.provider.send("evm_increaseTime", [31 * 24 * 60 * 60]);
//     await ethers.provider.send("evm_mine");

//     expect(await landTransaction.isContractExpired(agreementId)).to.be.true;
//   });
// });