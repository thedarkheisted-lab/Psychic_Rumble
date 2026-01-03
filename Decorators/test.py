import logging
from functools import wraps
from datetime import datetime

def transaction_logger(orig_func):

    @wraps(orig_func)
    def wrapper(self,*args,**kwargs):
        result = orig_func(self, *args, **kwargs)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        func_name = orig_func.__name__
        amount = args[0]if args else 'N/A'
        log_line = f"[{timestamp}] {func_name}: Rs.{amount:.2f}"

        try:
            with open (f"{self.number}.txt", "a") as f:
                f.write(log_line)
        
        except Exception as e:
            print(f"Logging failed:{e} \n")

        return result
    return wrapper


class Account:
    def __init__(self, name, number, balance):
        self.name = name
        self.__number = number
        self.__balance = balance

    @property
    def number(self):
        return self.__number
    
    @property
    def balance(self):
        return self.__balance
    
    @transaction_logger
    def withdraw(self, withdraw_amnt):
        if not isinstance(withdraw_amnt, (int,float)):
            raise ValueError("amount is not a number")
        if withdraw_amnt > self.__balance:
            raise ValueError(f"insufficient funds in account, current available balance:{self.__balance}")
        self.__balance -=withdraw_amnt  
  
    @transaction_logger
    def deposit(self, deposit_amnt):
        if not isinstance(deposit_amnt, (int,float)):
            raise ValueError("Deposit amount must be a number")
        if deposit_amnt<=0:
            raise ValueError("Depost amount must be positive")
        self.__balance += deposit_amnt

        

