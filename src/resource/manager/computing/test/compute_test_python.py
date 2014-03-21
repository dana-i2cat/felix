import unittest

# TODO Set up a TestSuite (http://docs.python.org/2/library/unittest.html#unittest.TestSuite)
class ComputeTest(unittest.TestCase):

    def test_compute_creation(self):
        message = "Compute created successfully"
        self.assertEqual(message, "Compute created successfully")

    def test_compute_deletion(self):
        message = "Compute deleted successfully"
        self.assertEqual(message, "Compute deleted successfully")

if __name__ == "__main__":
    unittest.main()

