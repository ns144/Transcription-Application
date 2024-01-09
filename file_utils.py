def write_srt(result, srt_path):
    from whisper.utils import get_writer
    writer = get_writer("srt","")
    options = dict()
    options["max_line_width"] = None
    options["max_line_count"] = None
    options["highlight_words"] = False
    try:
        writer(result, srt_path, options)
    except:
        print("Attempting to use an older Version of Whisper")
        writer(result, srt_path)
    print("DONE writing SRT: " + str(srt_path))

def write_txt(text, txt_path):
    with open(txt_path, 'w') as f:
        f.write(text)
    print("DONE writing TXT: " + str(txt_path))