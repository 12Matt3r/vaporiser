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
        args.compand = False
        args.gif_file = gif_file
        args.sobel_filter = False
        return args

    @patch('os.path.exists', return_value=True)
    def test_vaporiser_instantiation(self, mock_exists):
        vaporiser = Vaporiser(self.args)
        self.assertIsNotNone(vaporiser)

    @patch('os.path.exists', return_value=True)
    def test_output_filenames_default(self, mock_exists):
        vaporiser = Vaporiser(self.args)
        self.assertEqual(vaporiser.audio_output, "test_vaporised.mp3")
        self.assertEqual(vaporiser.video_output, "test_vaporised.mp4")

    @patch('os.path.exists', return_value=True)
    def test_output_filenames_custom(self, mock_exists):
        args = self._create_mock_args(output_name="custom_output")
        vaporiser = Vaporiser(args)
        self.assertEqual(vaporiser.audio_output, "custom_output.mp3")
        self.assertEqual(vaporiser.video_output, "custom_output.mp4")

    @patch('vaporiser.AudioSegment.from_mp3')
    @patch('vaporiser.low_pass_filter')
    @patch('os.path.exists', return_value=True)
    def test_apply_audio_effects(self, mock_exists, mock_low_pass_filter, mock_from_mp3):
        # Create a mock AudioSegment
        mock_audio = MagicMock()
        mock_audio.frame_rate = 44100
        mock_from_mp3.return_value = mock_audio

        # Mock the return value of low_pass_filter
        mock_low_pass_filter.return_value = mock_audio

        # Mock the spawn method
        mock_spawn = MagicMock()
        mock_audio._spawn.return_value = mock_spawn

        # Mock the compress_dynamic_range method
        mock_compress = MagicMock()
        mock_spawn.compress_dynamic_range.return_value = mock_compress

        vaporiser = Vaporiser(self.args)
        vaporiser._apply_audio_effects()

        mock_from_mp3.assert_called_with("test.mp3")
        mock_audio._spawn.assert_called_once()
        mock_low_pass_filter.assert_called_with(mock_spawn, 3500)

        # Check that export was called correctly
        mock_audio.export.assert_called_with("test_vaporised.mp3", format="mp3")


    @patch('vaporiser.movedit.AudioFileClip')
    @patch('vaporiser.movedit.VideoFileClip')
    @patch('os.path.exists', return_value=True)
    def test_create_video(self, mock_exists, mock_video_file_clip, mock_audio_file_clip):
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
        mock_final_clip.write_videofile.assert_called_once_with("test_vaporised.mp4", logger='bar')

class TestInputValidation(unittest.TestCase):
    def _create_mock_args(self, audio_input="test.mp3", gif_file=None):
        args = MagicMock()
        args.audio_input = audio_input
        args.gif_file = gif_file
        args.output_name = None
        return args

    @patch('sys.exit')
    @patch('os.path.exists')
    def test_valid_inputs(self, mock_exists, mock_exit):
        mock_exists.return_value = True
        args = self._create_mock_args()
        Vaporiser(args)
        mock_exit.assert_not_called()

    @patch('sys.exit')
    @patch('os.path.exists')
    def test_missing_audio_file(self, mock_exists, mock_exit):
        mock_exists.return_value = False
        args = self._create_mock_args()
        Vaporiser(args)
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('os.path.exists')
    def test_missing_gif_file(self, mock_exists, mock_exit):
        # os.path.exists should return True for the audio file, False for the gif
        mock_exists.side_effect = [True, False]
        args = self._create_mock_args(gif_file="test.gif")
        Vaporiser(args)
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('os.path.exists')
    def test_wrong_audio_extension(self, mock_exists, mock_exit):
        mock_exists.return_value = True
        args = self._create_mock_args(audio_input="test.wav")
        Vaporiser(args)
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('os.path.exists')
    def test_wrong_gif_extension(self, mock_exists, mock_exit):
        mock_exists.return_value = True
        args = self._create_mock_args(gif_file="test.mp4")
        Vaporiser(args)
        mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()
