// SPDX-License-Identifier: MIT
// compiler version must be greater than or equal to 0.8.17 and less than 0.9.0
pragma solidity ^0.8.17;

contract MyContract{
    
    address payable public ownerAddress;
    address payable public customerAddress;
    address public courierAddress;

    bool public isCouriererAssigned;
    bool public isPaymentSet;
    bool public isFinished;

    uint256 public payment;
    uint256 public orderPrice;

    constructor(uint256 _orderPrice, address _customerAddress, address _ownerAddress) {
        customerAddress = payable(_customerAddress);
        ownerAddress = payable(_ownerAddress);
        orderPrice = _orderPrice; 
        isCouriererAssigned = false;
        isPaymentSet = false;
    }

    modifier contractNotFinished(){
        require(!isFinished, "Invalid adress.");
        _;
    }

    modifier paymentSetMod() {
        require(isPaymentSet == false, "Payment is not set.");
        _; 
    }
    function getCustomerAddress() public view returns (address) {
        return customerAddress;
    }

    function getPayment() public view returns (uint256) {
        return payment;
    }

    function getIsCourierAssigned() public view returns (bool) {
       return isCouriererAssigned;
    }

    function getIsPaymentSet() public view returns (bool) {
       return isPaymentSet;
    }

    function transferFromContract() public  {
        require(msg.sender == customerAddress, "Invalid customer account.");
        require(isPaymentSet, "Transfer not complete.");
        require(isCouriererAssigned, "Delivery not complete."); 
        
        uint256 ownerAmount = (payment * 80) / 100; 
        uint256 courierAmount = payment - ownerAmount; 
    
        ownerAddress.transfer(ownerAmount); 
        (payable(courierAddress)).transfer(courierAmount); 
        isFinished = true;
    }

    function setCourierAddress(address _courierAddress) public {
        courierAddress = _courierAddress;
        isCouriererAssigned = true;
    }

    function setPayment() public payable { 
        require(isPaymentSet == false, "Payment is not set.");
        payment = msg.value;
        isPaymentSet = true;
    }

}