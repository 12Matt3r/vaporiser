import pytest
import numpy as np

# Add parent dir to path to allow import of audio_processor
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from audio_processor import analyze_audio, find_and_extract_loop


def test_analyze_audio(mocker):
    """
    Tests the analyze_audio function by mocking librosa calls.
    """
    # 1. Set up mock return values
    mock_y = np.zeros(22050 * 5) # 5 seconds of silence
    mock_sr = 22050
    mock_tempo = np.array([120.0])
    mock_chroma = np.zeros((12, 100))
    mock_chroma[7, :] = 1 # Make G the dominant note

    # 2. Configure mocks
    mocker.patch('audio_processor.librosa.load', return_value=(mock_y, mock_sr))
    mocker.patch('librosa.feature.tempo', return_value=mock_tempo)
    mocker.patch('librosa.feature.chroma_stft', return_value=mock_chroma)

    # 3. Call the function
    result = analyze_audio('dummy_path.mp3')

    # 4. Assert results
    assert result is not None
    assert result['tempo'] == 120
    assert result['key'] == 'G'

def test_find_and_extract_loop(mocker):
    """
    Tests the loop finding and extraction logic by mocking librosa and soundfile.
    """
    # 1. Setup Mocks
    sr = 22050
    loop_duration_seconds = 5
    # Create a dummy 40-second audio signal
    y = np.zeros(sr * 40)
    # Make the section around 35s the loudest, to test that the search
    # correctly starts after the 30s mark.
    y[sr * 35 : sr * 36] = 1.0

    mocker.patch('audio_processor.librosa.load', return_value=(y, sr))

    # Mock sf.write to avoid actual file I/O
    mock_write = mocker.patch('audio_processor.sf.write')

    # 2. Call the function
    loop_path = find_and_extract_loop('dummy_path.mp3', '/tmp', duration_seconds=loop_duration_seconds)

    # 3. Assertions
    assert loop_path.startswith('/tmp/loop_')

    # Check that sf.write was called
    mock_write.assert_called_once()

    # Check the data that was passed to sf.write
    # Correctly unpack the 3 arguments: path, data, samplerate
    _path, written_data, written_sr = mock_write.call_args[0]

    # Assert that the extracted loop has the correct duration and sample rate
    assert len(written_data) == loop_duration_seconds * sr
    assert written_sr == sr

    # Verify that the loudest part was selected. The peak we created should be in the written data.
    assert np.max(written_data) == 1.0
