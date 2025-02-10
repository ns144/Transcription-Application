import unittest
import os
import sys
import json


class TestTranscription(unittest.TestCase):
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')))

    def test_progress(self):
        from transcription.speaker_diarization import speaker_diarization
        from transcription.transcription_utils import condense_speakers
        from transcription.whisper_v3 import transcribe_segments_whisperV3
        with open('env.json') as secret_file:
            secret = json.load(secret_file)
        speaker_segments = speaker_diarization(
            "audio.wav", secret)
        print(speaker_segments)
        self.assertIsInstance(speaker_segments, list,
                              "Diarization did not return a list")

        speaker_segments = condense_speakers(speaker_segments)
        self.assertGreater(len(speaker_segments), 0,
                           "Condensed segments should not be empty")

        transcribed_segments = transcribe_segments_whisperV3(
            "audio.wav", speaker_segments)
        self.assertIsInstance(transcribed_segments, list,
                              "Transcription output is not a list")
        self.assertGreater(len(transcribed_segments), 0,
                           "No transcriptions generated")


if __name__ == '__main__':
    unittest.main()
