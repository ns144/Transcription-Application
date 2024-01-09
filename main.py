import os
import requests
import json
from get_secret import get_secret
from speaker_diarization import speaker_diarization
from utils.file_utils import write_srt, write_txt
from utils.s3_utils import upload_file, get_file
from utils.api_utils import update_status, get_tasks

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
