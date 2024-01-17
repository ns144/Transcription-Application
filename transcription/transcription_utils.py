import re
import subprocess
import whisper
import os
from speaker_segment import transcribed_segment
# condense transcribed words into full sentences
def condense_segments(segments:list, sentences:int=1, inprecise:bool=True):
    segments_count = len(segments)
    summarized_segments = []
    tmp_text = ""
    score = 0
    new_id = 0
    new_start = True
    
    for index, segment in enumerate(segments):
        
        last_line = index >= segments_count-1
        #print("Segments count: ", segments_count, " Current Index: ", index)
        #when start save start of segment
        if(new_start):    
            starttime = segment['start']
            new_start = False
        
        #add segment to text
        tmp_text += segment['text']
        
        #search for the last fullstop, questionmark, exclamation mark in the text
        #ATTENTION: for this we reverse the string
        match = re.search(r"[\.!?]", segment['text'][::-1])
        
        #if we have a match => add score because we finished one sentence
        if (match != None):
            score += 1
        
        #if sentence completed or end of text reached
        if (score >= sentences or last_line):
            #print("Last Line!")
            #note end time
            endtime = segment['end']
            
            #save segment
            new_segment = dict(id=new_id, start=starttime, end=endtime, text=tmp_text)
            summarized_segments.append(new_segment)
            new_id =+ 1
            
            #reset
            score = 0
            new_start = True
            tmp_text = ""    
    
            
    return summarized_segments

# speaker parts are combined where multiple segments of a speaker are not interrupted by another speaker 
def condense_speakers(speaker_segments):
    condensedSpeakers = []

    latest_timestamp = 0
    
    for segment in speaker_segments:

        if len(condensedSpeakers) !=0:

            if condensedSpeakers[-1].out_point > latest_timestamp:
                latest_timestamp = condensedSpeakers[-1].out_point

            if segment.in_point > latest_timestamp:

                if condensedSpeakers[-1].speaker == segment.speaker and condensedSpeakers[-1].out_point == latest_timestamp:
                    latest_segment = condensedSpeakers[-1]
                    latest_segment.out_point = segment.out_point

                    condensedSpeakers[-1] = latest_segment

                else:
                    condensedSpeakers.append(segment)

            else:
                condensedSpeakers.append(segment)

        else:
            condensedSpeakers.append(segment)


    return condensedSpeakers


def transcribe_segments(filename, speaker_segments):
    model = whisper.load_model("small")
    
    transcribed_segments = []

    for segment in speaker_segments:
        # render a wav for the current segment for the transcription
        print("TRANSCRIPTION OF SEGMENT:", str(segment.in_point))
        segmentName = "segment_" + str(segment.in_point) + ".wav"
        subprocess.call(['ffmpeg', '-i', filename, '-ss', str(segment.in_point), '-to', str(segment.out_point), segmentName, '-y','-loglevel', "quiet"])
       
        # transcription using OpenAI Whisper
        result = model.transcribe(segmentName)
        
        summarized_segments = condense_segments(result['segments'], 1)
        timecode_corrected_segments = []

        for s in summarized_segments:
            timecode_corrected_segments.append({'id':s['id'],'start':segment.in_point + s['start'], 'end': segment.in_point+s['end'], 'text': s['text']})

        transcribed_segments.append(transcribed_segment(segment.speaker, timecode_corrected_segments))
        os.remove(segmentName)

    return transcribed_segments

def transcribe_segments_no_print(filename, speaker_segments):
    model = whisper.load_model("small")
    
    transcribed_segments = []

    for segment in speaker_segments:
        # render a wav for the current segment for the transcription
        #print("TRANSCRIPTION OF SEGMENT:", str(segment.in_point))
        segmentName = "segment_" + str(segment.in_point) + ".wav"
        subprocess.call(['ffmpeg', '-i', filename, '-ss', str(segment.in_point), '-to', str(segment.out_point), segmentName, '-y','-loglevel', "quiet"])
       
        # transcription using OpenAI Whisper
        result = model.transcribe(segmentName)
        summarized_segments = condense_segments(result['segments'], 1)

        timecode_corrected_segments = []

        for s in summarized_segments:
            timecode_corrected_segments.append({'id':s['id'],'start':segment.in_point + s['start'], 'end': segment.in_point+s['end'], 'text': s['text']})

        transcribed_segments.append(transcribed_segment(segment.speaker, timecode_corrected_segments))
        os.remove(segmentName)

    return transcribed_segments

def transcribe_segments_pydup(filename, speaker_segments):
    from pydub import AudioSegment
    import numpy as np
    import tqdm
    model = whisper.load_model("small")
    transcribed_segments = []

    # load audio 
    audio = AudioSegment.from_file(filename,format="wav")
    ## convert to expected format
    if audio.frame_rate != 16000: # 16 kHz
        audio = audio.set_frame_rate(16000)
    if audio.sample_width != 2:   # int16
        audio = audio.set_sample_width(2)
    if audio.channels != 1:       # mono
        audio = audio.set_channels(1)        

    total = speaker_segments[-1].out_point

    for segment in speaker_segments:
        with tqdm.tqdm(total=total) as progress:
            # Slice Audio with pydup
            segment_in = int(segment.in_point*1000)
            segment_out = int(segment.out_point*1000)
            segmentAudio = audio[segment_in:segment_out]

            # transcription using OpenAI Whisper
            result = model.transcribe(np.frombuffer(segmentAudio.raw_data, np.int16).flatten().astype(np.float32) / 32768.0)
            summarized_segments = condense_segments(result['segments'], 1)

            timecode_corrected_segments = []

            for s in summarized_segments:
                timecode_corrected_segments.append({'id':s['id'],'start':segment.in_point + s['start'], 'end': segment.in_point+s['end'], 'text': s['text']})

            transcribed_segments.append(transcribed_segment(segment.speaker, timecode_corrected_segments))
            
            progress.update(segment.out_point)

    return transcribed_segments

def transcribe_segments_faster_whisper(filename, speaker_segments):
    from pydub import AudioSegment
    import numpy as np
    import tqdm
    from faster_whisper import WhisperModel

    #model_size = "large-v3"
    model_size = "small"
    # Run on GPU with FP16
    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    transcribed_segments = []

    # load audio 
    audio = AudioSegment.from_file(filename,format="wav")
    ## convert to expected format
    if audio.frame_rate != 16000: # 16 kHz
        audio = audio.set_frame_rate(16000)
    if audio.sample_width != 2:   # int16
        audio = audio.set_sample_width(2)
    if audio.channels != 1:       # mono
        audio = audio.set_channels(1)        

    total = speaker_segments[-1].out_point

    for segment in speaker_segments:
        with tqdm.tqdm(total=total) as progress:
            # Slice Audio with pydup
            segment_in = int(segment.in_point*1000)
            segment_out = int(segment.out_point*1000)
            segmentAudio = audio[segment_in:segment_out]

            # transcription using Faster Whisper
            segments, info = model.transcribe(np.frombuffer(segmentAudio.raw_data, np.int16).flatten().astype(np.float32) / 32768.0, beam_size=5)
            segments = list(segments)  # The transcription will actually run here.

            whisper_segs = []
            for fastseg in segments:
                whisper_seg = {"id": fastseg.id, "start": fastseg.start, "end": fastseg.end, "text": fastseg.text}
                whisper_segs.append(whisper_seg)

            summarized_segments = condense_segments(whisper_segs, 1)

            timecode_corrected_segments = []

            for s in summarized_segments:
                timecode_corrected_segments.append({'id':s['id'],'start':segment.in_point + s['start'], 'end': segment.in_point+s['end'], 'text': s['text']})

            transcribed_segments.append(transcribed_segment(segment.speaker, timecode_corrected_segments))
            
            progress.update(segment.out_point)

    return transcribed_segments

def get_text(transcribed_segments):
    text = ""
    for segment in transcribed_segments:
        text += segment.speaker +": "
        for s in segment.segments:
            text += s["text"]
        text += " \n"
    return text

