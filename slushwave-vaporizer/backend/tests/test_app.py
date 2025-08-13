import pytest
from io import BytesIO
from unittest.mock import MagicMock

# Tests for error cases (no file, empty filename) remain the same.
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

# New tests for the async flow
def test_slushify_success_dispatch(client, mocker):
    """Tests the successful dispatch of a celery task."""
    # Mock the delay method
    mock_task = MagicMock()
    mock_task.id = 'test_task_id_123'
    mocker.patch('tasks.slushify_task.delay', return_value=mock_task)

    data = {'file': (BytesIO(b'my file contents'), 'test.mp3')}
    response = client.post('/api/slushify', data=data, content_type='multipart/form-data')

    assert response.status_code == 202
    assert response.json['task_id'] == 'test_task_id_123'
    assert '/api/status/test_task_id_123' in response.json['status_url']

def test_taskstatus_pending(client, mocker):
    """Test status endpoint for a PENDING task."""
    mock_result = MagicMock()
    mock_result.state = 'PENDING'
    mocker.patch('tasks.slushify_task.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'PENDING'
    assert response.json['status'] == 'Pending...'

def test_taskstatus_progress(client, mocker):
    """Test status endpoint for a PROGRESS task."""
    mock_result = MagicMock()
    mock_result.state = 'PROGRESS'
    mock_result.info = {'status': 'Analyzing audio...'}
    mocker.patch('tasks.slushify_task.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'PROGRESS'
    assert response.json['status'] == 'Analyzing audio...'

def test_taskstatus_success(client, mocker):
    """Test status endpoint for a SUCCESS task."""
    mock_result = MagicMock()
    mock_result.state = 'SUCCESS'
    mock_result.info = {'status': 'SUCCESS', 'result': '/path/to/output.mp3'}
    mocker.patch('tasks.slushify_task.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'SUCCESS'
    assert response.json['result'] == '/path/to/output.mp3'

def test_taskstatus_failure(client, mocker):
    """Test status endpoint for a FAILURE task."""
    mock_result = MagicMock()
    mock_result.state = 'FAILURE'
    mock_result.info = 'Something went wrong'
    mocker.patch('tasks.slushify_task.AsyncResult', return_value=mock_result)

    response = client.get('/api/status/some_task_id')
    assert response.status_code == 200
    assert response.json['state'] == 'FAILURE'
    assert response.json['status'] == 'Something went wrong'
