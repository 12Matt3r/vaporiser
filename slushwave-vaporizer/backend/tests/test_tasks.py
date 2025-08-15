import pytest
from unittest.mock import MagicMock

# Add parent dir to path to allow import of tasks
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tasks import adjust_task

def test_adjust_task(mocker):
    """
    Tests the adjust_task to ensure it calls the correct effect function.
    """
    # 1. Mock the effects module to spy on its functions
    mock_effects_module = MagicMock()
    mocker.patch('tasks.effects', mock_effects_module)

    # 2. Define task parameters
    base_file = '/path/to/base.mp3'
    effect_name = 'reverb'
    effect_params = {'wet_gain': 3}
    new_file_id = 'new_adjusted_file_123'

    # 3. Call the task directly
    result = adjust_task(base_file, effect_name, effect_params, new_file_id)

    # 4. Assert that the correct effect function was called
    expected_output_path = f'/path/to/{new_file_id}.mp3'
    mock_effects_module.apply_reverb.assert_called_once_with(
        base_file,
        expected_output_path,
        **effect_params
    )

    # 5. Assert the task result
    assert result['status'] == 'SUCCESS'
    assert result['result'] == expected_output_path
