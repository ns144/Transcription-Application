import unittest
import os
import sys
import json
import re

# Tests for the file_utils that are responsible for writing transcription files


class TestFileUtils(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    # Test the write_srt function - checks if created srt file can be read and if the content matches the expected result
    def test_write_srt(self):
        from utils.file_utils import write_srt

        segment1 = {"text": "Guten Morgen ", "start": 0.0, "end": 4.0}
        segment2 = {"text": "ich bin der Otto! ", "start": 5.0, "end": 8.0}

        segments = [segment1, segment2]

        result_dict = {"segments": segments}
        file_path = "test.srt"
        # Write SRT
        write_srt(result_dict, file_path)
        # Read SRT
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        content = []
        for line in lines:
            if not re.match(r'^\d+$', line.strip()) and "-->" not in line and line.strip():
                content.append(line.strip())

        content = "\n".join(content)
        self.assertEqual(
            content, "Guten Morgen\nich bin der Otto!", "Text does not match!")
        os.remove(file_path)

    # Test the write_txt function - checks if created txt file can be read and if the content matches the expected result
    def test_write_txt(self):
        from utils.file_utils import write_txt
        file_path = "test.txt"
        text = "Der Bundestag wäre ohne die FDP ärmer aber überlebensfähig."
        # Write TXT
        write_txt(text, file_path)
        # Read TXT
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        self.assertEqual(
            lines[0], "Der Bundestag wäre ohne die FDP ärmer aber überlebensfähig.", "Text does not match!")
        os.remove(file_path)

    # Test the write_docx function - checks if a docx file is created successfully
    def test_write_docx(self):
        from utils.file_utils import write_docx
        file_path = "test.docx"
        text = "Der Bundestag wäre ohne die FDP ärmer aber überlebensfähig."
        from speaker_segment import transcribed_segment
        segment1 = {"text": "Guten Morgen ", "start": 0.0, "end": 4.0}
        segment2 = {"text": "ich bin der Otto! ", "start": 5.0, "end": 8.0}

        segments = [transcribed_segment(
            "SPEAKER_01", [segment1, segment2])]
        write_docx(speaker_segments=segments,
                   scriptFilename=file_path, translated_segments=segments, translated=False)

        docx_exists = os.path.exists(file_path)

        self.assertEqual(
            docx_exists, True, "DOCX not created successfully!")
        os.remove(file_path)


if __name__ == '__main__':
    unittest.main()
