import os
from dotenv import load_dotenv
import boto3
def get_tasks():
    import requests
    import json

    # Load Environment Variable File
    load_dotenv()

    # Get Api URL and Transcription Servive API Key
    API_URL = os.getenv('API_URL')
    TRANSCRIPTION_SERVICE_API_KEY = os.getenv('TRANSCRIPTION_SERVICE_API_KEY')

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

def get_s3_client():
    #load_dotenv()
    SECRET_KEY =  os.getenv('SECRET_KEY')
    ACCESS_KEY =  os.getenv('ACCESS_KEY')
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    return s3

def get_file(filename):
    #load_dotenv()
    BUCKET_NAME = os.getenv('BUCKET_NAME')

    s3 = get_s3_client()
    s3.download_file(BUCKET_NAME, filename, filename)

def upload_file(filename):
    s3 = get_s3_client()
    BUCKET_NAME = os.getenv('BUCKET_NAME')
    try:
        response = s3.upload_file(filename, BUCKET_NAME, str(filename))
    except Exception as error:
        print("An exception occurred:", error)
    

def transcribe(tasks):
    import whisper
    from whisper.utils import get_writer
    from pathlib import Path
    model = whisper.load_model("base")
    files = tasks["transcripts"]

    for file in files:
        filename = str(file["filename"])
        if ".wav" in filename:
            print("Transcription of:"+filename)
            get_file(filename)
            print(os.path.exists(filename))
            result = model.transcribe(filename)
            print(result["text"])
            os.remove(filename)

            filepath = Path(filename)
            srt_path = filepath.with_suffix('.srt')
            writer = get_writer("srt","")
            options = dict()
            options["max_line_width"] = None
            options["max_line_count"] = None
            options["highlight_words"] = False

            try:
                writer(result, srt_path, options)
            except:
                print("Attempting to use an older Version of Whisper")
                writer(result, srt_path)
            print("DONE writing SRT: " + str(srt_path))
            upload_file(srt_path)
            #os.remove(srt_path)

tasks = get_tasks()
if tasks != None:
    transcribe(tasks)
