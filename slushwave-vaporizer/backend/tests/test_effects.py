import pytest
from unittest.mock import MagicMock, call

# Add parent dir to path to allow import of effects
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import effects

@pytest.fixture
def mock_fx_chain(mocker):
    """Fixture to mock the AudioEffectsChain."""
    # Create a mock instance of the chain
    mock_chain_instance = MagicMock()

    # When a method like .speed() is called, it should return the same mock
    # to allow for method chaining in the source code.
    mock_chain_instance.custom.return_value = mock_chain_instance
    mock_chain_instance.pitch.return_value = mock_chain_instance
    mock_chain_instance.tremolo.return_value = mock_chain_instance
    mock_chain_instance.phaser.return_value = mock_chain_instance
    mock_chain_instance.gain.return_value = mock_chain_instance
    mock_chain_instance.compand.return_value = mock_chain_instance
    mock_chain_instance.speed.return_value = mock_chain_instance
    mock_chain_instance.lowpass.return_value = mock_chain_instance
    mock_chain_instance.reverb.return_value = mock_chain_instance

    # Mock the class constructor to return our configured instance
    mocker.patch('effects.AudioEffectsChain', return_value=mock_chain_instance)

    return mock_chain_instance

def test_apply_speed(mocker, mock_fx_chain):
    """Tests that apply_speed configures the chain correctly."""
    mock_apply_helper = mocker.patch('effects._apply_fx')
    effects.apply_speed('in.wav', 'out.wav', ratio=0.5)
    mock_fx_chain.speed.assert_called_once_with(0.5)
    mock_apply_helper.assert_called_once_with('in.wav', 'out.wav', mock_fx_chain)

def test_apply_reverb(mocker, mock_fx_chain):
    """Tests that apply_reverb configures the chain correctly."""
    mock_apply_helper = mocker.patch('effects._apply_fx')
    effects.apply_reverb('in.wav', 'out.wav')
    mock_fx_chain.reverb.assert_called_once()
    mock_apply_helper.assert_called_once_with('in.wav', 'out.wav', mock_fx_chain)

def test_apply_pitch_shift(mocker, mock_fx_chain):
    """Tests that apply_pitch_shift configures the chain correctly."""
    mock_apply_helper = mocker.patch('effects._apply_fx')
    effects.apply_pitch_shift('in.wav', 'out.wav', shift=-150)
    mock_fx_chain.pitch.assert_called_once_with(-150)
    mock_apply_helper.assert_called_once_with('in.wav', 'out.wav', mock_fx_chain)

def test_apply_bass_boost(mocker, mock_fx_chain):
    """Tests that apply_bass_boost configures the chain correctly."""
    mock_apply_helper = mocker.patch('effects._apply_fx')
    effects.apply_bass_boost('in.wav', 'out.wav', gain=10)
    mock_fx_chain.custom.assert_called_once_with('bass 10')
    mock_apply_helper.assert_called_once_with('in.wav', 'out.wav', mock_fx_chain)
