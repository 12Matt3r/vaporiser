import pytest
from io import BytesIO
from unittest.mock import MagicMock

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

# Updated tests for the async and preset flow
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

    # Assert that the task was called with the correct options
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


# Status tests remain the same
def test_taskstatus_pending(client, mocker):
    """Test status endpoint for a PENDING task."""
    mock_result = MagicMock()
    mock_result.state = 'PENDING'
    mocker.patch('tasks.slushify_task.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'PENDING'

def test_taskstatus_progress(client, mocker):
    """Test status endpoint for a PROGRESS task."""
    mock_result = MagicMock()
    mock_result.state = 'PROGRESS'
    mock_result.info = {'status': 'Analyzing audio...'}
    mocker.patch('tasks.slushify_task.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'PROGRESS'

def test_taskstatus_success(client, mocker):
    """Test status endpoint for a SUCCESS task."""
    mock_result = MagicMock()
    mock_result.state = 'SUCCESS'
    mock_result.info = {'result': '/path/to/output.mp3'}
    mocker.patch('tasks.slushify_task.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'SUCCESS'

def test_taskstatus_failure(client, mocker):
    """Test status endpoint for a FAILURE task."""
    mock_result = MagicMock()
    mock_result.state = 'FAILURE'
    mock_result.info = 'Something went wrong'
    mocker.patch('tasks.slushify_task.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'FAILURE'
