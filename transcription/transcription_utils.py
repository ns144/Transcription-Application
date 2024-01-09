import re

# condense transcribed words into full sentences
def condenseSegments(segments:list, sentences:int=1, inprecise:bool=True):
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
def condenseSpeakers(speaker_segments):
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