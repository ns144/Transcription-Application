import os
import subprocess
import requests
import json
from get_secret import get_secret
from transcription.speaker_diarization import speaker_diarization
from utils.file_utils import write_srt, write_txt, write_docx
from utils.s3_utils import upload_file, get_file
from utils.api_utils import update_status, get_tasks, shutdown_ec2
from transcription.transcription_utils import condense_speakers, transcribe_segments, transcribe_segments_no_print, transcribe_segments_pydup, transcribe_segments_faster_whisper, get_text
from transcription.whisper_v3 import transcribe_segments_whisperV3
import torch
from pathlib import Path
import time
import urllib.request
import logging
import sys

# create logger with 'spam_application'
logger = logging.getLogger('transcription-application')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler('/var/log/Python-Transcription-Application.log')
# fh = logging.FileHandler('Python-Transcription-Application.log')
fh.setLevel(logging.INFO)

formatter = logging.Formatter('[%(levelname)s] %(message)s')
fh.setFormatter(formatter)

logger.addHandler(fh)

# Redirect print statements to the logger

# class LoggerWriter:
#    def __init__(self, level):
#        self.level = level
#
#    def write(self, message):
#        if message.strip():  # Avoid logging empty strings from newlines
#            self.level(message)
#
#    def flush(self):
#        pass  # For compatibility with file-like objects
#
#
# sys.stdout = LoggerWriter(logger.info)
# sys.stderr = LoggerWriter(logger.error)

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


def refresh_tasks():
    Task = True
    while Task:
        tasks = get_tasks(secret)
        if tasks != None and tasks['transcripts'] != []:
            transcribe(tasks['transcripts'][0])
        else:
            print(f"No more Tasks in Queue - Shutting Down {instanceid}")
            shutdown_ec2(instanceid, secret)
            break


def transcribe(task):

    # Check Cuda availability
    print("GPU: " + str(torch.cuda.is_available()))
    print("Torch version:" + str(torch.__version__))

    file = task
    filename = str(file["fileNameWithExt"])
    filepath = Path(filename)
    processID = str(file["userId"])+"."+str(file["id"])
    try:
        update_status(file["id"], "PROCESSING", secret)
        logger.info(processID + " - Transcription of:"+filename)
        # Download file from S3
        get_file(filename, secret)
        # Normalization of Audio
        logger.info(processID + " - Convert File to Wav")
        subprocess.call(['ffmpeg', '-i', filename, "-ac", "1",
                        "-ar", "48000", 'audio.wav', '-y', '-loglevel', "quiet"])
        normed_audio = 'audio.wav'
        # Run speaker diarization
        logger.info(processID + " - Speaker Diarization")
        speaker_segments = speaker_diarization(normed_audio, secret)
        # Speaker parts are combined where multiple segments of a speaker are not interrupted by another speaker
        logger.info(processID + " - Condense Speakers")
        speaker_segments = condense_speakers(speaker_segments)
        # transcription of the condensed segments
        logger.info(processID + " - Transcribe Segments")
        # Transcription with FFMPEG
        # start = time.time()
        # transcribed_segments = transcribe_segments_no_print(normed_audio, speaker_segments)
        # end = time.time()
        # elapsed = end-start
        # print("Transcription with FFMPEG took:", elapsed, "Seconds")
        # Transcription with FFMPEG
        # start = time.time()
        # transcribed_segments = transcribe_segments(normed_audio, speaker_segments)
        # end = time.time()
        # elapsed = end-start
        # print("Transcription with FFMPEG took:", elapsed, "Seconds")
        # Transcription with Faster Whisper
        try:
            raise Exception("Do not use Faster Whisper!")
            start = time.time()
            transcribed_segments = transcribe_segments_faster_whisper(
                normed_audio, speaker_segments, "small")
            end = time.time()
            elapsed = end-start
            print("Transcription with Faster Whisper Small took:",
                  elapsed, "Seconds")
        except Exception as error:
            # print("Faster Whisper failed: ", error)
            # Transcription with WhisperV3
            start = time.time()
            transcribed_segments = transcribe_segments_whisperV3(
                normed_audio, speaker_segments)
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
        # File paths for srt, txt and docx
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
        update_status(file["id"], "SUCCESS", secret, text[0:500])
        logger.info(processID + " - Transcription Done")
    except Exception as error:
        logger.error("Transcription failed:", error)
        update_status(file["id"], "FAILED", secret)


refresh_tasks()
