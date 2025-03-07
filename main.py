import os
import subprocess

from get_secret import get_secret
from transcription.speaker_diarization import speaker_diarization
from utils.file_utils import write_srt, write_txt, write_docx
from utils.s3_utils import upload_file, get_file
from utils.json_utils import heartbeat, update_json
from utils.api_utils import update_status, get_tasks, shutdown_ec2
from transcription.transcription_utils import condense_speakers, get_text
from transcription.whisper_v3 import transcribe_segments_whisperV3
import torch
from pathlib import Path
import time
import urllib.request
import logging
import threading
import json

# create logger with 'transcription_application'
logger = logging.getLogger('transcription-application')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
try:
    fh = logging.FileHandler('/var/log/Python-Transcription-Application.log')
except Exception as error:
    print(error)
    fh = logging.FileHandler('Python-Transcription-Application.log')
fh.setLevel(logging.INFO)

formatter = logging.Formatter('[%(levelname)s] %(message)s')
fh.setFormatter(formatter)

logger.addHandler(fh)

# Get instance id (for shutdown call to stop lambda)
try:
    instanceid = urllib.request.urlopen(
        'http://169.254.169.254/latest/meta-data/instance-id').read().decode()
except Exception as error:
    logger.error(f"Could not get EC2 id: {error}")
    instanceid = 0


# Get Secret
secret = get_secret()
# with open('env.json') as secret_file:
#    secret = json.load(secret_file)

stop_event = threading.Event()


def call_hearbeat(secret):
    while not stop_event.is_set():
        heartbeat(secret)
        time.sleep(5)


def start_hearbeat_thread(secret):
    # Clear the stop event before start
    stop_event.clear()
    # Start the progress reading thread
    hearbeat_thread = threading.Thread(
        target=call_hearbeat, args=(secret,), daemon=True)
    hearbeat_thread.start()
    return hearbeat_thread


def stop_heartbeat_thread():
    stop_event.set()

# Fetch new tasks - if no further task - initiate shutdown with Stop Lambda Call


def refresh_tasks():
    Task = True
    while Task:
        task = get_tasks(secret)
        if task != None and len(task) != 0:
            transcribe(task)
        else:
            print(f"No more Tasks in Queue - Shutting Down {instanceid}")
            time.sleep(5)
            shutdown_ec2(instanceid, secret)
            break


def transcribe(task):

    # Check Cuda availability
    print("GPU: " + str(torch.cuda.is_available()))
    print("Torch version:" + str(torch.__version__))

    file = task
    transcript_id = str(file["id"])
    filename = str(file["fileNameWithExt"])
    filepath = Path(filename)
    processID = str(file["userId"])+"."+str(file["id"])
    try:
        # Set status of transcript to PROCESSING / initialize JSON
        update_status(file["id"], "PROCESSING", secret)
        update_json("PROCESSING", 0, 0, transcript_id)

        logger.info(processID + " - Transcription of:"+filename)
        # Download file from S3
        get_file(filename, secret)
        # Normalization of Audio
        logger.info(processID + " - Convert File to Wav")
        subprocess.call(['ffmpeg', '-i', filename, "-ac", "1",
                        "-ar", "48000", 'audio.wav', '-y', '-loglevel', "quiet"])
        normed_audio = 'audio.wav'
        # Run speaker diarization
        try:
            logger.info(processID + " - Speaker Diarization")
            speaker_segments = speaker_diarization(
                normed_audio, secret, transcript_id)
        except Exception as error:
            logger.exception("Speaker Diarization failed:" + str(error))

        # Speaker parts are combined where multiple segments of a speaker are not interrupted by another speaker
        logger.info(processID + " - Condense Speakers")
        speaker_segments = condense_speakers(speaker_segments)
        # transcription of the condensed segments
        logger.info(processID + " - Transcribe Segments")

        # Transcription with Whisper V3
        start = time.time()
        transcribed_segments = transcribe_segments_whisperV3(
            normed_audio, speaker_segments, transcript_id)
        end = time.time()
        elapsed = end-start
        logger.info(
            f"{processID} - Transcription with Pydup / WhisperV3 Turbo took: {elapsed} Seconds")

        logger.info(processID + " - Write Files")
        # Raw text of transcription
        text = get_text(transcribed_segments)
        # print(text[0:100])
        os.remove(filename)
        # Generation of srt compatible dict
        srt_segments = []
        for segment in transcribed_segments:
            for s in segment.segments:
                srt_segments.append(s)
        segments_as_dict = dict()
        segments_as_dict["segments"] = srt_segments

        # File paths for srt, txt and docx - Write files
        srt_path = filepath.with_suffix('.srt')
        txt_path = filepath.with_suffix('.txt')
        docx_path = filepath.with_suffix('.docx')
        logger.info(processID + " - Write SRT File")
        write_srt(segments_as_dict, srt_path)
        upload_file(srt_path, secret)
        logger.info(processID + " - SRT File Done")
        logger.info(processID + " - Write TXT File")
        write_txt(text, txt_path)
        upload_file(txt_path, secret)
        logger.info(processID + " - TXT File Done")
        logger.info(processID + " - Write DOCX File")
        write_docx(speaker_segments=transcribed_segments, translated_segments=transcribed_segments,
                   scriptFilename=docx_path, sourcefile=file['displayFilename'], translated=False)
        upload_file(docx_path, secret)
        logger.info(processID + " - DOCX File Done")
        os.remove(srt_path)
        os.remove(txt_path)
        os.remove(docx_path)
        update_json("SUCCESS", prog_speaker=100,
                    prog_transcription=100, transcript_id=transcript_id)

        update_status(file["id"], "SUCCESS", secret, text[0:500], 100, 100)
        logger.info(processID + " - Transcription Done")
    except Exception as error:
        logger.exception("Transcription failed:" + str(error))
        update_status(file["id"], "FAILED", secret)


# Intitialize JSON for Heartbeat Thread
update_json("PROCESSING", 0, 0, 0)
# Start Heartbeat Thread
start_hearbeat_thread(secret)
refresh_tasks()
stop_heartbeat_thread()
