import unittest
import os
import sys
import json

# Tests the different components of the transcription pipeline based on an exemplary transcription of the test.wav file


class TestTranscription(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    def test_transcription(self):
        from transcription.speaker_diarization import speaker_diarization
        from transcription.transcription_utils import condense_speakers
        from transcription.whisper_v3 import transcribe_segments_whisperV3
        from speaker_segment import transcribed_segment
        from get_secret import get_secret
        secret = get_secret()

        test_file = "test.wav"

        # Check if speaker diarization returns a list of speakers
        speaker_segments = speaker_diarization(
            test_file, secret, 0)
        self.assertIsInstance(speaker_segments, list,
                              "Diarization did not return a list")

        # Check condense speakers combines the speaker_segments and reduces their count
        init_len = len(speaker_segments)
        speaker_segments = condense_speakers(speaker_segments)
        self.assertLess(len(speaker_segments), init_len,
                        "Condensed segments should be less than original segments!")

        # Check if transcription with whisperV3 runs successfully and returns a list of transcribed segments
        transcribed_segments = transcribe_segments_whisperV3(
            test_file, speaker_segments, 0)
        self.assertIsInstance(transcribed_segments, list,
                              "Transcription output is not a list")
        self.assertIsInstance(transcribed_segments[0], transcribed_segment,
                              "Transcription segment is not of instance transcribed_segment!")
        self.assertGreater(len(transcribed_segments), 0,
                           "No transcriptions generated")


if __name__ == '__main__':
    unittest.main()
