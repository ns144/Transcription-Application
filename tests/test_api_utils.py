import unittest
import os
import sys
import json


class TestAPIUtils(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    def test_get_tasks(self):
        from utils.api_utils import get_tasks

        with open('env.json') as secret_file:
            secret = json.load(secret_file)

        tasks = get_tasks(secret)
        self.assertIsInstance(tasks, dict)


if __name__ == '__main__':
    unittest.main()
