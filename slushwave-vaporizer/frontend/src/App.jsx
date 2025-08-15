import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://127.0.0.1:5000';

function App() {
  const [file, setFile] = useState(null);
  const [presets, setPresets] = useState({});
  const [selectedPreset, setSelectedPreset] = useState('');
  const [status, setStatus] = useState('Select a file to begin.');
  const [resultUrl, setResultUrl] = useState('');
  const [error, setError] = useState('');
  const [taskId, setTaskId] = useState('');

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/presets`)
      .then(response => {
        setPresets(response.data);
        if (Object.keys(response.data).length > 0) {
          setSelectedPreset(Object.keys(response.data)[0]);
        }
      })
      .catch(err => {
        console.error("Error fetching presets:", err);
        setError('Could not connect to the backend to fetch presets.');
      });
  }, []);

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(() => {
      axios.get(`${API_BASE_URL}/api/status/${taskId}`)
        .then(response => {
          const task = response.data;
          setStatus(task.status);
          if (task.state === 'SUCCESS') {
            const filename = task.result.split(/\/|\\/).pop(); // Handle both path separators
            setResultUrl(`${API_BASE_URL}/api/outputs/${filename}`);
            setTaskId('');
            clearInterval(interval);
          } else if (task.state === 'FAILURE') {
            setError(`Processing failed: ${task.status}`);
            setTaskId('');
            clearInterval(interval);
          }
        })
        .catch(err => {
          console.error("Error fetching status:", err);
          setError('Could not get task status from the backend.');
          setTaskId('');
          clearInterval(interval);
        });
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId]);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setStatus('File selected. Ready to slushify.');
    setError('');
    setResultUrl('');
  };

  const handlePresetChange = (event) => {
    setSelectedPreset(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('preset', selectedPreset);

    setStatus('Uploading...');
    setError('');
    setResultUrl('');

    try {
      const response = await axios.post(`${API_BASE_URL}/api/slushify`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setTaskId(response.data.task_id);
      setStatus('Processing... (this may take a while)');
    } catch (err) {
      console.error("Error uploading file:", err);
      setError('File upload failed. Please check the console for details.');
      setStatus('Upload failed.');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Slushwave Generator</h1>
        <p>Upload your audio track and get a slushified version.</p>
      </header>
      <main>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="file-upload">1. Choose Audio File</label>
            <input id="file-upload" type="file" accept="audio/*" onChange={handleFileChange} />
          </div>
          <div className="form-group">
            <label htmlFor="preset-select">2. Select a Preset</label>
            <select id="preset-select" value={selectedPreset} onChange={handlePresetChange} disabled={!Object.keys(presets).length}>
              {Object.entries(presets).map(([name, description]) => (
                <option key={name} value={name}>{name} - {description}</option>
              ))}
            </select>
          </div>
          <button type="submit" disabled={!file || taskId}>
            {taskId ? 'Processing...' : 'Slushify!'}
          </button>
        </form>
        <div className="status-section">
          <h2>Status</h2>
          <p>{status}</p>
          {error && <p className="error">Error: {error}</p>}
          {resultUrl && (
            <div className="result">
              <h3>Your track is ready!</h3>
              <a href={resultUrl} download target="_blank" rel="noopener noreferrer">
                Download Slushed Track
              </a>
              <br />
              <audio controls src={resultUrl}>
                Your browser does not support the audio element.
              </audio>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
