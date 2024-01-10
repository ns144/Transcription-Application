from pyannote.audio import Pipeline
from speaker_segment import speaker_segment
import subprocess
import torch

def speaker_diarization(sourcefile, secret):
  # usage of pyannote pretrained model for speaker diarization
  pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=secret["HUG_TOKEN"])
  # check if CUDA capable GPU is available
  try:
      print("Attempting to use CUDA capable GPU")
      pipeline.to(torch.device("cuda"))
  except:
      print("Using CPU instead")
      pipeline.to(torch.device("cpu"))
      
  # sourcefile = 'audio.wav'
  # apply the pipeline to an audio file
  diarization = pipeline(sourcefile, min_speakers=2, max_speakers=8)

  speaker_segments = []
  
  for speech_turn, track, speaker in diarization.itertracks(yield_label=True):
    print(f"{speech_turn.start:4.1f} {speech_turn.end:4.1f} {speaker}")
    speaker_segments.append(speaker_segment(speaker,speech_turn.start,speech_turn.end))

  del pipeline
  torch.cuda.empty_cache()
  return speaker_segments