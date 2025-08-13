import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the path so we can import vaporiser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaporiser import Vaporiser, parse_args

class TestVaporiser(unittest.TestCase):
    def setUp(self):
        self.args = self._create_mock_args()

    def _create_mock_args(self, output_name=None, audio_input="test.mp3", gif_file=None):
        args = MagicMock()
        args.output_name = output_name
        args.audio_input = audio_input
        args.speed_ratio = 0.75
        args.pitch_shift = -75
        args.lowpass_cutoff = 3500
        args.bass_boost = None
        args.gain_db = None
        args.oops = False
        args.phaser = False
        args.tremolo = False
        args.compand = False
        args.no_reverb = False
        args.gif_file = gif_file
        args.sobel_filter = False
        return args

    def test_vaporiser_instantiation(self):
        vaporiser = Vaporiser(self.args)
        self.assertIsNotNone(vaporiser)

    def test_output_filenames_default(self):
        vaporiser = Vaporiser(self.args)
        self.assertEqual(vaporiser.audio_output, "test_vaporised.mp3")
        self.assertEqual(vaporiser.video_output, "test_vaporised.mp4")

    def test_output_filenames_custom(self):
        args = self._create_mock_args(output_name="custom_output")
        vaporiser = Vaporiser(args)
        self.assertEqual(vaporiser.audio_output, "custom_output.mp3")
        self.assertEqual(vaporiser.video_output, "custom_output.mp4")

    @patch('vaporiser.AudioEffectsChain')
    def test_create_audio_effects_chain(self, mock_audio_effects_chain):
        vaporiser = Vaporiser(self.args)
        fx = vaporiser._create_audio_effects_chain()
        self.assertIsNotNone(fx)
        # Verify that the correct effects are called
        mock_audio_effects_chain.return_value.pitch.assert_called_with(-75)
        mock_audio_effects_chain.return_value.pitch.return_value.speed.assert_called_with(0.75)
        mock_audio_effects_chain.return_value.pitch.return_value.speed.return_value.lowpass.assert_called_with(3500)
        mock_audio_effects_chain.return_value.pitch.return_value.speed.return_value.lowpass.return_value.reverb.assert_called_once()

    @patch('vaporiser.Vaporiser._create_audio_effects_chain')
    def test_apply_audio_effects(self, mock_create_audio_effects_chain):
        mock_fx = MagicMock()
        mock_create_audio_effects_chain.return_value = mock_fx
        vaporiser = Vaporiser(self.args)
        vaporiser._apply_audio_effects()
        mock_fx.assert_called_once_with("test.mp3", "test_vaporised.mp3")

    @patch('vaporiser.movedit.AudioFileClip')
    @patch('vaporiser.movedit.VideoFileClip')
    def test_create_video(self, mock_video_file_clip, mock_audio_file_clip):
        args = self._create_mock_args(gif_file="test.gif")
        vaporiser = Vaporiser(args)

        # Mock the clips and their durations
        mock_audio_clip = MagicMock()
        mock_audio_clip.duration = 10
        mock_audio_file_clip.return_value = mock_audio_clip

        mock_video_clip = MagicMock()
        mock_video_clip.duration = 2
        mock_video_file_clip.return_value = mock_video_clip

        # Mock the loop and set_audio methods
        mock_looped_clip = MagicMock()
        mock_video_clip.loop.return_value = mock_looped_clip
        mock_final_clip = MagicMock()
        mock_looped_clip.set_audio.return_value = mock_final_clip


        vaporiser._create_video()

        mock_audio_file_clip.assert_called_once_with("test_vaporised.mp3")
        mock_video_file_clip.assert_called_once_with("test.gif")
        mock_video_clip.loop.assert_called_once_with(5.0)
        mock_looped_clip.set_audio.assert_called_once_with(mock_audio_clip)
        mock_final_clip.write_videofile.assert_called_once_with("test_vaporised.mp4")

if __name__ == '__main__':
    unittest.main()
