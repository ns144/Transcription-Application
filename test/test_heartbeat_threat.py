import unittest
import os
import sys
import json
import time

# Checks if the heartbeat thread can be started and stopped as expected


class TestHeartbeatThread(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    def test_thread(self):
        from main import start_hearbeat_thread, stop_heartbeat_thread
        from get_secret import get_secret
        secret = get_secret()
        thread = start_hearbeat_thread("cm6z5dprl0001l203zdelpo6a", secret)
        # Check if thread is alive / started correctly
        self.assertTrue(thread.is_alive())
        time.sleep(30)
        stop_heartbeat_thread()
        thread.join()
        # Check if thread is terminated
        self.assertFalse(thread.is_alive())


if __name__ == '__main__':
    unittest.main()
