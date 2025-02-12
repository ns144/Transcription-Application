import json
import os
import requests
import sys


def update_json(status, prog_speaker=0, prog_transcription=0, transcript_id=0):
    file_name = "progress.json"
    temp_file = file_name + ".tmp"

    if transcript_id == 0:
        with open('progress.json', 'r') as file:
            progress_data = json.load(file)
            transcript_id = progress_data['TRANSCRIPT_ID']
    if transcript_id == "test":
        return None

    progress_data = {
        "STATUS": status,
        "PROG_TRANSCRIPTION": prog_transcription,
        "PROG_SPEAKER": prog_speaker,
        "TRANSCRIPT_ID": transcript_id
    }

    with open(temp_file, "w") as f:
        json.dump(progress_data, f, indent=4)

    # Atomic replace
    os.replace(temp_file, file_name)


def heartbeat(secret):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))
    try:
        with open('progress.json', 'r') as file:
            progress_data = json.load(file)
            STATUS = progress_data['STATUS']
            PROG_TRANSCRIPTION = progress_data['PROG_TRANSCRIPTION']
            PROG_SPEAKER = progress_data['PROG_SPEAKER']
            TRANSCRIPT_ID = progress_data['TRANSCRIPT_ID']
        # print(str(STATUS), str(PROG_SPEAKER), str(PROG_TRANSCRIPTION))

        MODIFY_URL = secret["MODIFY_URL"] + str(TRANSCRIPT_ID)
        TRANSCRIPTION_SERVICE_API_KEY = secret["TRANSCRIPTION_SERVICE_API_KEY"]
        params = {'key': TRANSCRIPTION_SERVICE_API_KEY}
        body = {'status': STATUS, 'speakerDiarizationProgress': PROG_SPEAKER,
                'transcriptionProgress': PROG_TRANSCRIPTION}

        json_body = json.dumps(body)

        response = requests.post(MODIFY_URL, params=params, data=json_body)
        # Check if the status code is 200 (OK)
        if response.status_code == 200:
            # Parse the JSON response and assign it to the 'tasks' variable
            updated = response.json()
            print(
                f"API call successfull with status code {response.status_code} for API call = {str(MODIFY_URL)} with body = {str(json_body)}")
            # print("API call successful. Updated Task:", updated)
            return updated
        else:
            # If the status code is not 200, print an error message
            print(
                f"Error: API call failed with status code {response.status_code} for API call = {str(MODIFY_URL)} with body = {str(json_body)}")
            return None
    except FileNotFoundError:
        print("File not found. Waiting for it to be created.")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON. Waiting for a valid file.")
        return None
    except Exception as error:
        # handle the exception
        print("An exception occurred:", error)
        return None
