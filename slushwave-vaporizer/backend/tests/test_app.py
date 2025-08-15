import pytest
from io import BytesIO
from unittest.mock import MagicMock
import os

def test_hello_endpoint(client):
    """Tests the hello world endpoint."""
    response = client.get('/api/hello')
    assert response.status_code == 200
    assert response.json['message'] == 'Hello, World!'

def test_slushify_no_file(client):
    """Tests the slushify endpoint with no file part."""
    response = client.post('/api/slushify')
    assert response.status_code == 400
    assert 'error' in response.json
    assert response.json['error'] == 'No file part'

def test_slushify_empty_filename(client):
    """Tests the slushify endpoint with an empty filename."""
    data = {'file': (BytesIO(b'my file contents'), '')}
    response = client.post('/api/slushify', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert 'error' in response.json
    assert response.json['error'] == 'No selected file'

def test_slushify_dispatch_with_preset(client, mocker):
    """Tests the successful dispatch of a celery task with a specific preset."""
    mock_task = MagicMock()
    mock_task.id = 'test_task_id_123'
    mock_delay = mocker.patch('tasks.slushify_task.delay', return_value=mock_task)

    form_data = {
        'file': (BytesIO(b'my file contents'), 'test.mp3'),
        'preset': 'nightcore'
    }
    response = client.post('/api/slushify', data=form_data, content_type='multipart/form-data')

    assert response.status_code == 202
    assert response.json['task_id'] == 'test_task_id_123'

    called_options = mock_delay.call_args[0][2]
    assert called_options['preset'] == 'nightcore'

def test_slushify_dispatch_no_preset_defaults(client, mocker):
    """Tests that slushify defaults to the 'slushwave' preset."""
    mock_task = MagicMock()
    mock_task.id = 'test_task_id_456'
    mock_delay = mocker.patch('tasks.slushify_task.delay', return_value=mock_task)

    form_data = {'file': (BytesIO(b'my file contents'), 'test.mp3')}
    response = client.post('/api/slushify', data=form_data, content_type='multipart/form-data')

    assert response.status_code == 202
    assert response.json['task_id'] == 'test_task_id_456'

    called_options = mock_delay.call_args[0][2]
    assert called_options['preset'] == 'slushwave'

# Updated tests for the status endpoint
def test_taskstatus_pending(client, mocker):
    """Test status endpoint for a PENDING task."""
    mock_result = MagicMock()
    mock_result.state = 'PENDING'
    mocker.patch('app.celery_app.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'PENDING'

def test_taskstatus_progress(client, mocker):
    """Test status endpoint for a PROGRESS task."""
    mock_result = MagicMock()
    mock_result.state = 'PROGRESS'
    mock_result.info = {'status': 'Analyzing audio...'}
    mocker.patch('app.celery_app.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'PROGRESS'

def test_taskstatus_success(client, mocker):
    """Test status endpoint for a SUCCESS task."""
    mock_result = MagicMock()
    mock_result.state = 'SUCCESS'
    mock_result.info = {'result': '/path/to/output.mp3'}
    mocker.patch('app.celery_app.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'SUCCESS'

def test_taskstatus_failure(client, mocker):
    """Test status endpoint for a FAILURE task."""
    mock_result = MagicMock()
    mock_result.state = 'FAILURE'
    mock_result.info = 'Something went wrong'
    mocker.patch('app.celery_app.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'FAILURE'

def test_adjust_endpoint_success(client, mocker):
    """Tests the adjust endpoint for successful dispatch."""
    mocker.patch('os.listdir', return_value=['original_task_id.mp3'])
    mocker.patch('os.path.exists', return_value=True)

    mock_task = MagicMock()
    mock_task.id = 'adjust_task_456'
    mock_delay = mocker.patch('app.adjust_task.delay', return_value=mock_task)

    adj_data = {'effect_name': 'phaser', 'effect_params': {}}
    response = client.post('/api/adjust/original_task_id', json=adj_data)

    assert response.status_code == 202
    assert response.json['task_id'] == 'adjust_task_456'

    expected_base_path = 'slushwave-vaporizer/backend/outputs/original_task_id.mp3'
    # Assert that delay was called, we don't need to be super specific
    # about the new_file_id as it's a uuid.
    assert mock_delay.call_count == 1
    call_args = mock_delay.call_args[0]
    assert call_args[0] == expected_base_path
    assert call_args[1] == 'phaser'
    assert call_args[2] == {}
    assert isinstance(call_args[3], str) # new_file_id is a string

def test_adjust_endpoint_file_not_found(client, mocker):
    """Tests the adjust endpoint when the original file is not found."""
    mocker.patch('os.listdir', return_value=['another_file.mp3'])

    adj_data = {'effect_name': 'phaser', 'effect_params': {}}
    response = client.post('/api/adjust/original_task_id', json=adj_data)

    assert response.status_code == 404
    assert 'Original processed file not found' in response.json['error']

def test_adjust_endpoint_bad_data(client, mocker):
    """Tests the adjust endpoint with invalid request data."""
    mocker.patch('os.listdir', return_value=['original_task_id.mp3'])
    mocker.patch('os.path.exists', return_value=True)

    bad_data = {'effect_params': {}} # Missing 'effect_name'
    response = client.post('/api/adjust/original_task_id', json=bad_data)

    assert response.status_code == 400
    assert 'Invalid adjustment data' in response.json['error']

def test_serve_output_file(client, mocker):
    """Tests the file serving endpoint."""
    mock_send = mocker.patch('app.send_from_directory', return_value="file content")

    response = client.get('/api/outputs/test.mp3')

    assert response.status_code == 200
    assert response.data == b"file content"

    expected_dir = os.path.abspath('slushwave-vaporizer/backend/outputs')
    mock_send.assert_called_once_with(expected_dir, 'test.mp3')
