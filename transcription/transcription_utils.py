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
        
        last_line = index >= segments_count
        
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
    model = whisper.load_model("base")
    
    transcribed_segments = []

    for segment in speaker_segments:
        # render a wav for the current segment for the transcription
        segmentName = "segment_" + str(segment.in_point) + ".wav"
        subprocess.call(['ffmpeg', '-i', filename, '-ss', str(segment.in_point), '-to', str(segment.out_point), segmentName, '-y'])
       
        # transcription using OpenAI Whisper
        result = model.transcribe(segmentName)
        summarized_segments = condense_segments(result['segments'], 1)

        timecode_corrected_segments = []

        for s in summarized_segments:
            timecode_corrected_segments.append({'id':s['id'],'start':segment.in_point + s['start'], 'end': segment.in_point+s['end'], 'text': s['text']})

        transcribed_segments.append(transcribed_segment(segment.speaker, timecode_corrected_segments))
        os.remove(segmentName)

    return transcribed_segments

def get_text(transcribed_segments):
    text = ""
    for segment in transcribed_segments:
        text += segment.speaker +": "
        for s in segment.segments:
            text += s["text"]
        text += " \n"
    return text