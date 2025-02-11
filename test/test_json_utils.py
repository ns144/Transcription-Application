import unittest
import os
import sys
import json

# Check if the progress is written correctly to the json file by the json_utils


class TestJSONUtils(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    def test_update_json(self):
        from utils.json_utils import update_json

        update_json("PROCESSING", 10, 0)

        with open('progress.json') as secret_file:
            progress = json.load(secret_file)
        # Check if content matches expectations
        self.assertEqual(progress, {'STATUS': 'PROCESSING', 'PROG_TRANSCRIPTION': 0,
                         'PROG_SPEAKER': 10}, "JSON not correctly saved / updated!")


if __name__ == '__main__':
    unittest.main()
