import unittest
import os
import sys
import json


# Test for the api_utils - checks if the get_tasks function returs a task of instance dict
class TestAPIUtils(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    def test_get_tasks(self):
        from utils.api_utils import get_tasks
        from get_secret import get_secret
        secret = get_secret()

        tasks = get_tasks(secret)
        self.assertIsInstance(tasks, dict)


if __name__ == '__main__':
    unittest.main()
