import subprocess
from get_secret import get_secret
import urllib.request
import requests
import threading


def run_tests():
    result = subprocess.run(
        ["python3", "-m", "unittest", "discover"], capture_output=True, text=True)

    print(result.stdout)
    print(result.stderr)

    if result.returncode == 0:
        print("Tests passed")
        print("Initiating the creation of a new AMI and Launch Template")
        secret = get_secret()
        AMI_URL = secret["AMI_URL"]
        TRANSCRIPTION_SERVICE_API_KEY = secret["TRANSCRIPTION_SERVICE_API_KEY"]

        try:
            instanceid = urllib.request.urlopen(
                'http://169.254.169.254/latest/meta-data/instance-id').read().decode()
        except Exception as error:
            print(f"Could not get EC2 id: {error}")
            instanceid = 0
            # exit(1)

        params = {'key': TRANSCRIPTION_SERVICE_API_KEY, 'ec2_id': instanceid}

        def make_api_call():
            try:
                response = requests.get(AMI_URL, params=params)
                # Optionally log the response if needed
                if response.status_code == 200:
                    res = response.json()
                    print("API call successful. Response:", res)
                else:
                    print(
                        f"Error: API call failed with status code {response.status_code}")
            except Exception as error:
                print("An exception occurred during the API call:", error)

        make_api_call()
    else:
        print("Tests failed!")


if __name__ == "__main__":
    run_tests()
