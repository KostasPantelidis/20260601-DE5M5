import unittest
import random
from calc import Calculator

class TestOperation(unittest.TestCase):
    
    def setUp(self):
        self.num1 = random.randint(1, 100)
        self.num2 = random.randint(1, 100)
        
        self.calculator = Calculator(self.num1, self.num2)

    def test_sum(self):
        self.assertEqual(self.calculator.get_sum(), self.num1 + self.num2, "Not what expected") 

    def test_diff(self):
        self.assertEqual(self.calculator.get_diff(), self.num1 - self.num2, "Not what expected") 

    def test_product(self):
        self.assertEqual(self.calculator.get_product(), self.num1 * self.num2, "Not what expected") 

    def test_quotient(self):
        self.assertEqual(self.calculator.get_quotient(), self.num1 / self.num2, "Not what expected") 

if __name__ == "__main__":
    unittest.main()