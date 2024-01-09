import os
import requests
import json
from get_secret import get_secret
from speaker_diarization import speaker_diarization
from utils.file_utils import write_srt, write_txt
from utils.s3_utils import upload_file, get_file

def get_tasks(secret):

    # Get Api URL and Transcription Servive API Key
    API_URL = secret["API_URL"]
    TRANSCRIPTION_SERVICE_API_KEY = secret["TRANSCRIPTION_SERVICE_API_KEY"]

    print(str(API_URL)+" Key: "+str(TRANSCRIPTION_SERVICE_API_KEY))

    # Call API
    # Set up the parameters for the API request
    params = {'key': TRANSCRIPTION_SERVICE_API_KEY}
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

def transcribe(tasks):
    import whisper
    import torch
    from pathlib import Path
    model = whisper.load_model("tiny")
    files = tasks["transcripts"]

    # Check Cuda availability
    print("GPU: " + str(torch.cuda.is_available()))
    print("Torch version:" + str(torch.__version__))

    # Get Secret
    secret = get_secret()
    #with open('env.json') as secret_file:
    #  secret = json.load(secret_file)

    for file in files:
        filename = str(file["filename"])
        if ".wav" in filename or ".mp3" in filename:
            try:
                update_status(file["id"], "PROCESSING", secret)
                print("Transcription of:"+filename)
                get_file(filename, secret)
                print(os.path.exists(filename))
                result = model.transcribe(filename)
                print(result["text"])
                os.remove(filename)

                filepath = Path(filename)
                srt_path = filepath.with_suffix('.srt')
                txt_path = filepath.with_suffix('.txt')

                write_srt(result, srt_path)
                upload_file(srt_path, secret)
                write_txt(result["text"], txt_path)
                upload_file(txt_path, secret)
                os.remove(srt_path)
                os.remove(txt_path)
                update_status(file["id"], "SUCCESS", secret, result["text"][0:500])

            except Exception as error:
                print("Transcription failed:", error)
                update_status(file["id"],"FAILED", secret)


tasks = get_tasks()
if tasks != None:
    transcribe(tasks)
