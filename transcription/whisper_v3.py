from transcription.transcription_utils import condense_segments, condense_speakers
from speaker_segment import transcribed_segment
import re
import time


def condense_chunks(segments: list, sentences: int = 1, inprecise: bool = True):
    segments_count = len(segments)
    summarized_segments = []
    tmp_text = ""
    score = 0
    new_id = 0
    new_start = True

    for index, segment in enumerate(segments):

        last_line = index >= segments_count-1
        # print("Segments count: ", segments_count, " Current Index: ", index)
        # when start save start of segment
        if (new_start):
            starttime = segment['timestamp'][0]
            new_start = False

        # add segment to text
        tmp_text += segment['text']

        # search for the last fullstop, questionmark, exclamation mark in the text
        # ATTENTION: for this we reverse the string
        match = re.search(r"[\.!?]", segment['text'][::-1])

        # if we have a match => add score because we finished one sentence
        if (match != None):
            score += 1

        # if sentence completed or end of text reached
        if (score >= sentences or last_line):
            # print("Last Line!")
            # note end time
            if segment['timestamp'][1] != None:
                endtime = segment['timestamp'][1]
            else:
                endtime = segment['timestamp'][0]

            # save segment
            new_segment = dict(id=new_id, start=starttime,
                               end=endtime, text=tmp_text)
            summarized_segments.append(new_segment)
            new_id = + 1

            # reset
            score = 0
            new_start = True
            tmp_text = ""

    return summarized_segments


def transcribe_segments_whisperV3(filename, speaker_segments, transcript_id):
    import torch
    from pydub import AudioSegment
    import numpy as np
    import tqdm
    import sys
    import os
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))
    from utils.json_utils import update_json
    transcribed_segments = []

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3-turbo"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=30,
        batch_size=16,
        torch_dtype=torch_dtype,
        device=device,
    )

    # load audio
    audio = AudioSegment.from_file(filename, format="wav")
    # convert to expected format
    if audio.frame_rate != 16000:  # 16 kHz
        audio = audio.set_frame_rate(16000)
    if audio.sample_width != 2:   # int16
        audio = audio.set_sample_width(2)
    if audio.channels != 1:       # mono
        audio = audio.set_channels(1)

    total = speaker_segments[-1].out_point
    last_update = time.time()
    interval = 3

    for segment in speaker_segments:
        percentage = int(
            (segment.in_point / speaker_segments[-1].in_point)*100)

        current_time = time.time()
        if current_time - last_update >= interval:
            last_update = current_time
            update_json("TRANSCRIPTION", prog_speaker=100,
                        prog_transcription=percentage, transcript_id=transcript_id)
        if percentage == 100:
            update_json("TRANSCRIPTION", prog_speaker=100,
                        prog_transcription=percentage, transcript_id=transcript_id)

        with tqdm.tqdm(total=total) as progress:
            # Slice Audio with pydup
            segment_in = int(segment.in_point*1000)
            segment_out = int(segment.out_point*1000)
            segmentAudio = audio[segment_in:segment_out]

            # transcription using OpenAI Whisper
            result = pipe(np.frombuffer(
                segmentAudio.raw_data, np.int16).flatten().astype(np.float32) / 32768.0, return_timestamps=True)
            # print(result)
            summarized_segments = condense_chunks(result['chunks'], 1)

            timecode_corrected_segments = []

            for s in summarized_segments:
                timecode_corrected_segments.append(
                    {'id': s['id'], 'start': segment.in_point + s['start'], 'end': segment.in_point+s['end'], 'text': s['text']})

            transcribed_segments.append(transcribed_segment(
                segment.speaker, timecode_corrected_segments))

            progress.update(segment.out_point)

    return transcribed_segments
