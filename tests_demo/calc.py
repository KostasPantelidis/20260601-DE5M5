class Calculator:
    def __init__(self, num1, num2):
        self.num1 = num1
        self.num2 = num2 
    
    def get_sum(self):
        return self.num1 + self.num2
    
    def get_product(self):
        return self.num1 * self.num2
    
    def get_diff(self):
        return self.num1 - self.num2
    
    def get_quotient(self):
        return self.num1 / self.num2
    
    # Add the functions for difference, product and quotient
    # Stretch: Look into Matrix Dot Product vs Cross Product

if __name__ == "__main__":
    myCalc = Calculator(10,20)
    print(myCalc.get_sum())