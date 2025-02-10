import unittest
import os
import sys
import json
import time


class TestHeartbeatThread(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    def test_thread(self):
        from main import start_hearbeat_thread, stop_heartbeat_thread
        with open('env.json') as secret_file:
            secret = json.load(secret_file)
        thread = start_hearbeat_thread("cm6z5dprl0001l203zdelpo6a", secret)
        time.sleep(30)
        stop_heartbeat_thread()


if __name__ == '__main__':
    unittest.main()
