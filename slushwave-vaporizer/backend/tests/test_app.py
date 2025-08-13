import pytest
from io import BytesIO

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
    data = {
        'file': (BytesIO(b'my file contents'), '')
    }
    response = client.post('/api/slushify', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert 'error' in response.json
    assert response.json['error'] == 'No selected file'
