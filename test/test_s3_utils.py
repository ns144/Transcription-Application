import unittest
import os
import sys
import json
import boto3

# Tests for s3_utils


class TestS3Utils(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    # Check if we can get an s3 client with the function get_s3_client
    def test_get_s3_client(self):
        from utils.s3_utils import get_s3_client
        from get_secret import get_secret

        secret = get_secret()
        s3_client = get_s3_client(secret)
        self.assertIsInstance(
            s3_client, object, "No S3 Client created!")

    # Check if a file is uploaded correctly to s3 and can be downloaded again
    def test_upload(self):
        from utils.s3_utils import upload_file, get_file, get_s3_client
        from get_secret import get_secret

        secret = get_secret()

        # Create simple test file
        file_name = "test.txt"
        with open(file_name, "w") as file:
            file.write("Moin, this is a test file!")

        # Upload file to S3
        upload_file(file_name, secret)
        # Delete file locally
        os.remove(file_name)
        # Download file form s3 with get_file function
        get_file(file_name, secret)
        # Check if file is downloaded successfully
        file_exists = os.path.exists(file_name)
        self.assertEqual(
            file_exists, True, "File not upload/downloaded successfully!")
        # Clean up file locally and in S3
        os.remove(file_name)
        s3_client = get_s3_client(secret)
        response = s3_client.delete_object(
            Bucket=secret["BUCKET_NAME"], Key=str(file_name))


if __name__ == '__main__':
    unittest.main()
