import os
import subprocess
import requests
import json
from get_secret import get_secret
from transcription.speaker_diarization import speaker_diarization
from utils.file_utils import write_srt, write_txt, write_docx
from utils.s3_utils import upload_file, get_file
from utils.api_utils import update_status, get_tasks
from transcription.transcription_utils import condense_speakers, transcribe_segments, get_text

# Get Secret
secret = get_secret()
#with open('env.json') as secret_file:
#   secret = json.load(secret_file)

def refresh_tasks():
    tasks = get_tasks(secret)
    if tasks != None and tasks['transcripts'] != []:
        transcribe(tasks)
    else:
        print("No more Tasks in Queue - Shutting Down")


def transcribe(tasks):
    import torch
    from pathlib import Path
    files = tasks["transcripts"]

    # Check Cuda availability
    print("GPU: " + str(torch.cuda.is_available()))
    print("Torch version:" + str(torch.__version__))

    for file in files:
        filename = str(file["fileNameWithExt"])
        try:
            update_status(file["id"], "PROCESSING", secret)
            print("Transcription of:"+filename)
            # Download file from S3
            get_file(filename, secret)
            # Normalization of Audio
            print("Convert File to Wav")
            subprocess.call(['ffmpeg', '-i', filename,"-filter:a", "loudnorm=I=-20:LRA=4","-ac", "1","-ar","48000", 'audio.wav', '-y', '-loglevel', "quiet"])
            normed_audio = 'audio.wav'
            # Run speaker diarization
            print("Speaker Diarization")
            speaker_segments = speaker_diarization(normed_audio, secret)
            # Speaker parts are combined where multiple segments of a speaker are not interrupted by another speaker 
            print("Condense Speakers")
            speaker_segments = condense_speakers(speaker_segments)
            # transcription of the condensed segments
            print("Transcribe Segments")
            transcribed_segments = transcribe_segments(normed_audio, speaker_segments)
            print("Write Files")
            # Raw text of transcription
            text = get_text(transcribed_segments)
            print(text[0:100])
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
            docx_path = filepath.with_suffix('.docx')
            write_srt(segments_as_dict, srt_path)
            upload_file(srt_path, secret)
            write_txt(text, txt_path)
            upload_file(txt_path, secret)
            write_docx(speaker_segments=transcribed_segments, translated_segments=transcribed_segments, scriptFilename=docx_path, sourcefile=filename, translated=False)
            upload_file(docx_path, secret)
            os.remove(srt_path)
            os.remove(txt_path)
            os.remove(docx_path)
            update_status(file["id"], "SUCCESS", secret, text[0:500])
        except Exception as error:
            print("Transcription failed:", error)
            update_status(file["id"],"FAILED", secret)
    
    refresh_tasks()

tasks = get_tasks(secret)
if tasks != None:
    transcribe(tasks)
