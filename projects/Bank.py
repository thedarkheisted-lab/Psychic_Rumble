class Account:
    def __init__(self, name, number, amount):
        assert amount >= 0, "Balance cannot be in negative"

        self.name = name
        self.__number = number
        self.amount = amount

    @property
    def number(self):
        return self.__number

    def deposit(self, deposit_amount):
        self.amount = self.amount + deposit_amount
    
    def withdraw(self, withdraw_amount):
        if withdraw_amount > self.amount:
            raise ValueError("Insufficient Funds")
        self.amount = self.amount - withdraw_amount
  
    def transfer(self, target_account, amount):
        if amount <= 0:
            raise ValueError("Transfer amount not valid")
        if amount > self.amount:
            raise ValueError("Insufficient Funds")
        if not isinstance(target_account, Account):
            raise TypeError("target account does not exist")
        
        self.withdraw(amount)
        target_account.deposit(amount)

    def to_dict(self):
        return {
            "name": self.name,
            "number": self.number,
            "amount": self.amount,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            number=data["number"],
            amount=data["amount"],
        )


if __name__ == "__main__":
    account1 = Account("John Smith", 1004005, 5000)
    account2 = Account("John Doe", 1003006, 10000)
    print(account1.amount)
