from pyannote.audio import Pipeline
from speaker_segment import speaker_segment
import torch
from pyannote.audio.pipelines.utils.hook import ProgressHook
import torchaudio
import json
import time
import sys
import os
from typing import Any, Mapping, Optional


class JSONProgressHook:

    def __init__(self, transcript_id, json_file="progress.json", interval=3, transient=False):
        self.transcript_id = transcript_id
        self.json_file = json_file
        self.interval = interval
        self.last_update = time.time()
        self.progress_data = {}  # Store step-wise progress

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __call__(self, step_name: str, step_artifact: Any, file: Optional[Mapping] = None, total: Optional[int] = None, completed: Optional[int] = None):
        sys.path.insert(0, os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..')))
        from utils.json_utils import update_json
        if completed is None:
            completed = total = 1  # Default behavior as in the original ProgressHook

        if step_name == "segmentation":
            percentage = (completed / total) * 20 if total else 20
        elif step_name == "embeddings":
            percentage = 20+(completed / total) * 80 if total else 100
        elif step_name == "speaker_counting":
            percentage = 20
        else:
            percentage = 100
        percentage = int(percentage)

        current_time = time.time()
        if current_time - self.last_update >= self.interval:
            self.last_update = current_time
            update_json("SPEAKER_DIARIZATION", prog_speaker=percentage,
                        transcript_id=self.transcript_id)
        if percentage == 100:
            update_json("SPEAKER_DIARIZATION", prog_speaker=percentage,
                        transcript_id=self.transcript_id)


def speaker_diarization(sourcefile, secret, transcript_id):
    sys.path.insert(0, '../utils')
    # usage of pyannote pretrained model for speaker diarization
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=secret["HUG_TOKEN"])
    # check if CUDA capable GPU is available
    try:
        print("Attempting to use CUDA capable GPU")
        pipeline.to(torch.device("cuda"))
    except:
        print("Using CPU instead")
        pipeline.to(torch.device("cpu"))

    # Load audio in memory
    waveform, sample_rate = torchaudio.load(sourcefile)
    audio_in_memory = {"waveform": waveform, "sample_rate": sample_rate}
    # sourcefile = 'audio.wav'
    # apply the pipeline to an audio file
    with JSONProgressHook(transcript_id) as hook:
        diarization = pipeline(audio_in_memory, hook=hook)

    speaker_segments = []

    for speech_turn, track, speaker in diarization.itertracks(yield_label=True):
        # print(f"{speech_turn.start:4.1f} {speech_turn.end:4.1f} {speaker}")
        speaker_segments.append(speaker_segment(
            speaker, speech_turn.start, speech_turn.end))

    del pipeline
    torch.cuda.empty_cache()
    return speaker_segments
