import pytest
import numpy as np

# Add parent dir to path to allow import of audio_processor
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from audio_processor import analyze_audio, find_and_extract_loop, process_audio


def test_analyze_audio(mocker):
    """
    Tests the analyze_audio function by mocking librosa calls.
    """
    # 1. Set up mock return values
    mock_y = np.zeros(22050 * 5)
    mock_sr = 22050
    mocker.patch('audio_processor.librosa.load', return_value=(mock_y, mock_sr))

    # Mock all the feature extraction calls
    mocker.patch('librosa.feature.tempo', return_value=np.array([120.0]))
    mock_chroma = np.zeros((12, 100))
    mock_chroma[7, :] = 1 # Make G the dominant note
    mocker.patch('librosa.feature.chroma_stft', return_value=mock_chroma)
    mocker.patch('librosa.feature.spectral_centroid', return_value=np.array([[1500.0]]))
    mocker.patch('librosa.feature.spectral_bandwidth', return_value=np.array([[2000.0]]))
    mocker.patch('librosa.feature.rms', return_value=np.array([[0.5]]))

    # 2. Call the function
    result = analyze_audio('dummy_path.mp3')

    # 3. Assert results
    assert result is not None
    assert result['tempo'] == 120
    assert result['key'] == 'G'
    assert result['brightness'] == 1500
    assert result['spectral_width'] == 2000
    assert 'avg_loudness' in result
    assert round(result['avg_loudness'], 1) == 0.5


def test_find_and_extract_loop(mocker):
    """
    Tests the loop finding and extraction logic by mocking librosa and soundfile.
    """
    # 1. Setup Mocks
    sr = 22050
    loop_duration_seconds = 5
    y = np.zeros(sr * 40)
    y[sr * 35 : sr * 36] = 1.0

    mocker.patch('audio_processor.librosa.load', return_value=(y, sr))
    mock_write = mocker.patch('audio_processor.sf.write')

    # 2. Call the function
    loop_path = find_and_extract_loop('dummy_path.mp3', '/tmp', duration_seconds=loop_duration_seconds)

    # 3. Assertions
    assert loop_path.startswith('/tmp/loop_')
    mock_write.assert_called_once()

    _path, written_data, written_sr = mock_write.call_args[0]

    assert len(written_data) == loop_duration_seconds * sr
    assert written_sr == sr
    assert np.max(written_data) == 1.0

def test_process_audio_with_style_transfer(mocker):
    """
    Tests that process_audio correctly calculates and applies effects
    based on a reference track.
    """
    # 1. Mock the analysis function to return different fingerprints
    target_analysis = {'tempo': 100, 'brightness': 1000, 'avg_loudness': 0.5}
    ref_analysis = {'tempo': 150, 'brightness': 3000, 'avg_loudness': 0.25}
    mocker.patch('audio_processor.analyze_audio', side_effect=[target_analysis, ref_analysis])

    # 2. Mock the _apply_fx helper to prevent any SoX calls
    mock_apply_fx = mocker.patch('effects._apply_fx')

    # 3. Call process_audio with a reference path
    options = {'preset': 'slushwave'}
    process_audio('target.mp3', 'output.mp3', options=options, reference_path='ref.mp3')

    # 4. Assert that the helper was called for each effect in the chain
    # The slushwave preset has several effects. Let's check a few key ones.

    # The test can't easily know the intermediate filenames.
    # A better assertion is to check the *number* of calls to the helper.
    # The 'slushwave' preset has: speed, pitch, lowpass, phaser, compand, reverb.
    # And the style transfer adds: gain. So 7 effects.
    assert mock_apply_fx.call_count == 7

    # We can inspect the last call to see if it wrote to the final output file
    final_call_args = mock_apply_fx.call_args_list[-1]
    assert final_call_args[0][1] == 'output.mp3' # outfile is the second argument
