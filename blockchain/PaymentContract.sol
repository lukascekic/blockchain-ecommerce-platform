// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PaymentContract {
    address payable public customer;
    address payable public owner;
    address payable public courier;
    uint256 public amount;
    bool public isPaid;

    constructor(address _customer, uint256 _amount) {
        customer = payable(_customer);
        owner = payable(msg.sender);
        amount = _amount;
        isPaid = false;
    }

    function pay() public payable {
        require(msg.sender == customer, "Only customer can pay");
        require(msg.value == amount, "Incorrect payment amount");
        require(!isPaid, "Already paid");

        isPaid = true;
    }

    function assignCourier(address _courier) public {
        require(msg.sender == owner, "Only owner can assign courier");
        require(isPaid, "Payment not complete");

        courier = payable(_courier);
    }

    function confirmDelivery() public {
        require(msg.sender == owner, "Only owner can confirm delivery");
        require(isPaid, "Payment not complete");
        require(courier != address(0), "Courier not assigned");

        uint256 ownerAmount = (amount * 80) / 100;
        uint256 courierAmount = amount - ownerAmount;

        owner.transfer(ownerAmount);
        courier.transfer(courierAmount);
    }
}
