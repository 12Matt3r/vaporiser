import React from 'react';

function UploadForm({
  file,
  presets,
  selectedPreset,
  taskId,
  handleFileChange,
  handlePresetChange,
  handleSubmit,
}) {
  return (
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
  );
}

export default UploadForm;
