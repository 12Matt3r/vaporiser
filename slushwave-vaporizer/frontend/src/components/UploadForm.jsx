import React from 'react';

function UploadForm({
  presets,
  selectedPreset,
  taskId,
  handleFileChange,
  handleReferenceFileChange, // New prop
  handlePresetChange,
  handleSubmit,
}) {
  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="file-upload">1. Choose Target Audio File</label>
        <input id="file-upload" type="file" accept="audio/*" onChange={handleFileChange} required />
      </div>
      <div className="form-group">
        <label htmlFor="reference-file-upload">2. (Optional) Choose Reference Track</label>
        <input id="reference-file-upload" type="file" accept="audio/*" onChange={handleReferenceFileChange} />
      </div>
      <div className="form-group">
        <label htmlFor="preset-select">3. Select a Preset</label>
        <select id="preset-select" value={selectedPreset} onChange={handlePresetChange} disabled={!Object.keys(presets).length}>
          {Object.entries(presets).map(([name, description]) => (
            <option key={name} value={name}>{name} - {description}</option>
          ))}
        </select>
        <small>The preset will be overridden if a reference track is provided.</small>
      </div>
      <button type="submit" disabled={taskId}>
        {taskId ? 'Processing...' : 'Slushify!'}
      </button>
    </form>
  );
}

export default UploadForm;
