import React from 'react';

function StatusDisplay({ status, error, isLoading }) {
  return (
    <div className="status-section">
      <h2>Status</h2>
      {isLoading ? <div className="loader"></div> : <p>{status}</p>}
      {error && <p className="error">Error: {error}</p>}
    </div>
  );
}

export default StatusDisplay;
