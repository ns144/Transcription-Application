import requests
import json

def get_tasks(secret):

    # Get Api URL and Transcription Servive API Key
    API_URL = secret["API_URL"]
    TRANSCRIPTION_SERVICE_API_KEY = secret["TRANSCRIPTION_SERVICE_API_KEY"]

    print(str(API_URL)+" Key: "+str(TRANSCRIPTION_SERVICE_API_KEY))

    # Call API
    # Set up the parameters for the API request
    params = {'key': TRANSCRIPTION_SERVICE_API_KEY, 'filter': 'PENDING'}
    # Make the API request
    try:
        response = requests.get(API_URL, params=params)
        # Check if the status code is 200 (OK)
        if response.status_code == 200:
            # Parse the JSON response and assign it to the 'tasks' variable
            tasks = response.json()
            print("API call successful. Tasks:", tasks)
            return tasks
        else:
            # If the status code is not 200, print an error message
            print(f"Error: API call failed with status code {response.status_code}")
            return None
    except Exception as error:
        # handle the exception
        print("An exception occurred:", error)
        return None

    
def update_status(id, status, secret, preview=None):
    MODIFY_URL = secret["MODIFY_URL"] + id
    TRANSCRIPTION_SERVICE_API_KEY = secret["TRANSCRIPTION_SERVICE_API_KEY"]
    params = {'key': TRANSCRIPTION_SERVICE_API_KEY}
    if preview == None:
        body = {'status': status}
    else:
        body = {'status': status, 'preview': preview}

    json_body = json.dumps(body)

    # Make the API request
    try:
        response = requests.post(MODIFY_URL, params=params, data=json_body)
        # Check if the status code is 200 (OK)
        if response.status_code == 200:
            # Parse the JSON response and assign it to the 'tasks' variable
            updated = response.json()
            print("API call successful. Updated Task:", updated)
            return updated
        else:
            # If the status code is not 200, print an error message
            print(f"Error: API call failed with status code {response.status_code}")
            return None
    except Exception as error:
        # handle the exception
        print("An exception occurred:", error)
        return None
    
def shutdown_ec2(ec2_id, secret):
    STOP_URL = secret["STOP_URL"]
    TRANSCRIPTION_SERVICE_API_KEY = secret["TRANSCRIPTION_SERVICE_API_KEY"]
    params = {'key': TRANSCRIPTION_SERVICE_API_KEY, 'ec2_id': ec2_id}
    # Make the API request
    try:
        response = requests.get(STOP_URL, params=params)
        # Check if the status code is 200 (OK)
        if response.status_code == 200:
            # Parse the JSON response and assign it to the 'tasks' variable
            res = response.json()
            print("API call successful. Shutdown Machine: ", res)
            return res
        else:
            # If the status code is not 200, print an error message
            print(f"Error: API call failed with status code {response.status_code}")
            return None
    except Exception as error:
        # handle the exception
        print("An exception occurred:", error)
        return None