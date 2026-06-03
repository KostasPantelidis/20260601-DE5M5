import unittest
import random
from tests_demo.calc import Calculator

class TestOperations(unittest.TestCase):

    def setUp(self):
        self.calculator = Calculator(8,2)

    def test_sum(self):
        self.assertEqual(self.calculator.get_sum(), 10, "The answer was not 10.")

    def tearDown(self):
        # use this function to delete any resources created and UNDO the setUP actions/
        pass
        


if __name__=="__main__":
    unittest.main()

##testcomment
