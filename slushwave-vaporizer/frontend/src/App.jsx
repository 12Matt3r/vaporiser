import { useState, useEffect } from 'react';
import axios from 'axios';
import UploadForm from './components/UploadForm';
import StatusDisplay from './components/StatusDisplay';
import ResultDisplay from './components/ResultDisplay';
import './App.css';

const API_BASE_URL = 'http://127.0.0.1:5000';

function App() {
  const [file, setFile] = useState(null);
  const [referenceFile, setReferenceFile] = useState(null); // New state for reference file
  const [presets, setPresets] = useState({});
  const [selectedPreset, setSelectedPreset] = useState('');
  const [status, setStatus] = useState('Select a file to begin.');
  const [resultUrl, setResultUrl] = useState('');
  const [error, setError] = useState('');

  const [primaryTaskId, setPrimaryTaskId] = useState('');
  const [adjustmentTaskId, setAdjustmentTaskId] = useState('');
  const [isAdjusting, setIsAdjusting] = useState(false);
  const [originalTaskId, setOriginalTaskId] = useState('');

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
    const taskId = primaryTaskId || adjustmentTaskId;
    if (!taskId) return;
    const interval = setInterval(() => {
      axios.get(`${API_BASE_URL}/api/status/${taskId}`)
        .then(response => {
          const task = response.data;
          setStatus(task.status);
          if (task.state === 'SUCCESS') {
            const filename = task.result.split(/\/|\\/).pop();
            setResultUrl(`${API_BASE_URL}/api/outputs/${filename}`);
            if (primaryTaskId) {
              setOriginalTaskId(primaryTaskId);
              setPrimaryTaskId('');
            }
            if (adjustmentTaskId) {
              setAdjustmentTaskId('');
              setIsAdjusting(false);
            }
            clearInterval(interval);
          } else if (task.state === 'FAILURE') {
            setError(`Processing failed: ${task.status}`);
            setPrimaryTaskId('');
            setAdjustmentTaskId('');
            setIsAdjusting(false);
            clearInterval(interval);
          }
        })
        .catch(err => {
          console.error("Error fetching status:", err);
          setError('Could not get task status from the backend.');
          setPrimaryTaskId('');
          setAdjustmentTaskId('');
          setIsAdjusting(false);
          clearInterval(interval);
        });
    }, 2000);
    return () => clearInterval(interval);
  }, [primaryTaskId, adjustmentTaskId]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setStatus('File selected. Ready to slushify.');
    setError('');
    setResultUrl('');
    setOriginalTaskId('');
  };

  const handleReferenceFileChange = (e) => {
    setReferenceFile(e.target.files[0]);
  };

  const handlePresetChange = (e) => {
    setSelectedPreset(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) { setError('Please select a file first.'); return; }
    const formData = new FormData();
    formData.append('file', file);
    formData.append('preset', selectedPreset);
    if (referenceFile) {
      formData.append('reference_file', referenceFile);
    }
    setStatus('Uploading...');
    setError('');
    setResultUrl('');
    setOriginalTaskId('');
    try {
      const response = await axios.post(`${API_G_BASE_URL}/api/slushify`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setPrimaryTaskId(response.data.task_id);
      setStatus('Processing... (this may take a while)');
    } catch (err) {
      console.error("Error uploading file:", err);
      setError('File upload failed.');
      setStatus('Upload failed.');
    }
  };

  const handleAdjust = async (baseTaskId, effectName, effectParams) => {
    if (!baseTaskId || isAdjusting) return;
    setIsAdjusting(true);
    setStatus(`Applying ${effectName} adjustment...`);
    setError('');
    try {
      const response = await axios.post(`${API_BASE_URL}/api/adjust/${baseTaskId}`, {
        effect_name: effectName,
        effect_params: effectParams,
      });
      setAdjustmentTaskId(response.data.task_id);
    } catch (err) {
      console.error("Error adjusting effect:", err);
      setError('Adjustment failed.');
      setIsAdjusting(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Slushwave Generator</h1>
        <p>Upload your audio track and get a slushified version.</p>
      </header>
      <main>
        <UploadForm
          presets={presets}
          selectedPreset={selectedPreset}
          taskId={primaryTaskId || adjustmentTaskId}
          handleFileChange={handleFileChange}
          handleReferenceFileChange={handleReferenceFileChange}
          handlePresetChange={handlePresetChange}
          handleSubmit={handleSubmit}
        />
        <StatusDisplay status={status} error={error} isLoading={!!(primaryTaskId || adjustmentTaskId)} />
        {resultUrl && (
          <ResultDisplay
            resultUrl={resultUrl}
            originalTaskId={originalTaskId}
            handleAdjust={handleAdjust}
            isAdjusting={isAdjusting}
          />
        )}
      </main>
    </div>
  );
}

export default App;
