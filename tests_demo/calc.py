class Calculator:
    def __init__(self, num1, num2):
        self.num1 = num1
        self.num2 = num2

    def get_sum(self):
        return self.num1 + self.num2

    def get_diff(self):
        return self.num1 - self.num2

    def get_product(self):
        return self.num1 * self.num2
    
    def get_quotient(self):
        # Fix: Check for division by zero
        if self.num2 == 0:
            return "Error: Can't devide by 0"
        return self.num1 / self.num2
    

    
#myCalc = Calculator(2,3)
#print(myCalc.get_sum())

