import unittest
import os
import sys
import json
import time

# Tests for the transcription_utils


class TestTranscriptionUtils(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    # Test if condense_speakers works as expected - segments of the same speakers should be merged
    def test_condense_speakers(self):
        from transcription.transcription_utils import condense_speakers
        from speaker_segment import speaker_segment

        speaker_segments = [speaker_segment(
            "SPEAKER_01", 0.0, 5.0), speaker_segment("SPEAKER_01", 10.0, 15.0)]
        # Same Speaker sequents should be merged
        condensed_speaker_segments = condense_speakers(speaker_segments)
        self.assertEqual(len(condensed_speaker_segments), 1,
                         "Should have condensed speaker but did not")

        speaker_segments = [speaker_segment(
            "SPEAKER_01", 0.0, 5.0), speaker_segment("SPEAKER_02", 10.0, 15.0)]
        # Different Speaker sequents should not be merged
        condensed_speaker_segments = condense_speakers(speaker_segments)
        self.assertEqual(len(condensed_speaker_segments), 2,
                         "Should not have condensed speakers!")

    # Test if condense_segments works as expected - text should be combined to complete sentences
    def test_condense_segments(self):
        from transcription.transcription_utils import condense_segments
        segment1 = {"text": "Guten Morgen ", "start": 0.0, "end": 4.0}
        segment2 = {"text": "ich bin der Otto! ", "start": 5.0, "end": 8.0}

        condensed_segments = condense_segments([segment1, segment2])
        self.assertEqual(len(condensed_segments), 1,
                         "Did not condense segments")
        self.assertEqual(
            condensed_segments[0]["start"], 0.0, "Start time of segments does not match!")
        self.assertEqual(
            condensed_segments[0]["end"], 8.0, "End time of segments does not match!")

        segment1 = {"text": "Guten Morgen! ", "start": 0.0, "end": 4.0}
        segment2 = {"text": "ich bin der Otto! ", "start": 5.0, "end": 8.0}
        condensed_segments = condense_segments([segment1, segment2])
        self.assertEqual(len(condensed_segments), 2,
                         "Should not have condensed segments")

    # Check if get_text returns the combined text of a list of segments
    def test_get_text(self):
        from transcription.transcription_utils import get_text
        from speaker_segment import transcribed_segment
        segment1 = {"text": "Guten Morgen ", "start": 0.0, "end": 4.0}
        segment2 = {"text": "ich bin der Otto! ", "start": 5.0, "end": 8.0}

        text = get_text([transcribed_segment(
            "SPEAKER_01", [segment1, segment2])])
        self.assertEqual(text, "SPEAKER_01: Guten Morgen ich bin der Otto!  \n",
                         "Text does not match")


if __name__ == '__main__':
    unittest.main()
