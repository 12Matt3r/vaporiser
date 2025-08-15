import React from 'react';

function StatusDisplay({ status, error }) {
  return (
    <div className="status-section">
      <h2>Status</h2>
      <p>{status}</p>
      {error && <p className="error">Error: {error}</p>}
    </div>
  );
}

export default StatusDisplay;
