import pytest
import numpy as np

# Add parent dir to path to allow import of audio_processor
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from audio_processor import analyze_audio


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
    mocker.patch('librosa.load', return_value=(mock_y, mock_sr))
    mocker.patch('librosa.feature.tempo', return_value=mock_tempo)
    mocker.patch('librosa.feature.chroma_stft', return_value=mock_chroma)

    # 3. Call the function
    result = analyze_audio('dummy_path.mp3')

    # 4. Assert results
    assert result is not None
    assert result['tempo'] == 120
    assert result['key'] == 'G'
