import os
import requests
import json
from get_secret import get_secret
from transcription.speaker_diarization import speaker_diarization
from utils.file_utils import write_srt, write_txt
from utils.s3_utils import upload_file, get_file
from utils.api_utils import update_status, get_tasks
from transcription.transcription_utils import condense_speakers, transcribe_segments, get_text

# Get Secret
secret = get_secret()
#with open('env.json') as secret_file:
#    secret = json.load(secret_file)

def transcribe(tasks):
    import whisper
    import torch
    from pathlib import Path
    model = whisper.load_model("tiny")
    files = tasks["transcripts"]

    # Check Cuda availability
    print("GPU: " + str(torch.cuda.is_available()))
    print("Torch version:" + str(torch.__version__))

    for file in files:
        filename = str(file["filename"])
        if ".wav" in filename or ".mp3" in filename:
            try:
                update_status(file["id"], "PROCESSING", secret)
                print("Transcription of:"+filename)
                # Download file from S3
                get_file(filename, secret)
                # Run speaker diarization
                speaker_segments = speaker_diarization(filename, secret)
                # Speaker parts are combined where multiple segments of a speaker are not interrupted by another speaker 
                speaker_segments = condense_speakers(speaker_segments)
                # transcription of the condensed segments
                transcribed_segments = transcribe_segments(filename, speaker_segments)

                # Raw text of transcription
                text = get_text(transcribed_segments)
                print(text)
                os.remove(filename)

                # Generation of srt compatible dict
                srt_segments = []
                for segment in transcribed_segments:
                    for s in segment.segments:
                        srt_segments.append(s)
                segments_as_dict = dict()
                segments_as_dict["segments"] = srt_segments

                # File paths for srt, txt and docx
                filepath = Path(filename)
                srt_path = filepath.with_suffix('.srt')
                txt_path = filepath.with_suffix('.txt')

                write_srt(segments_as_dict, srt_path)
                upload_file(srt_path, secret)
                write_txt(text, txt_path)
                upload_file(txt_path, secret)
                os.remove(srt_path)
                os.remove(txt_path)
                update_status(file["id"], "SUCCESS", secret, text[0:500])

            except Exception as error:
                print("Transcription failed:", error)
                update_status(file["id"],"FAILED", secret)


tasks = get_tasks(secret)
if tasks != None:
    transcribe(tasks)
