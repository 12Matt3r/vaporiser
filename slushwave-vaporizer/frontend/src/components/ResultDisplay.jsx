import React from 'react';

function ResultDisplay({ resultUrl, originalTaskId, handleAdjust, isAdjusting }) {
  if (!resultUrl) {
    return null;
  }

  const onSpeedChange = (e) => {
    handleAdjust(originalTaskId, 'speed', { ratio: parseFloat(e.target.value) });
  };

  const onPitchChange = (e) => {
    handleAdjust(originalTaskId, 'pitch_shift', { shift: parseInt(e.target.value, 10) });
  };

  const onLowpassChange = (e) => {
    handleAdjust(originalTaskId, 'lowpass', { cutoff: parseInt(e.target.value, 10) });
  };

  const onBassChange = (e) => {
    handleAdjust(originalTaskId, 'bass_boost', { gain: parseInt(e.target.value, 10) });
  };

  return (
    <div className="result">
      <h3>Your track is ready!</h3>
      <a href={resultUrl} download target="_blank" rel="noopener noreferrer">
        Download Slushed Track
      </a>
      <br />
      <audio controls key={resultUrl} style={{ marginTop: '1rem', width: '100%' }}>
        <source src={resultUrl} type="audio/mpeg" />
        Your browser does not support the audio element.
      </audio>

      <div className="post-processing">
        <h4>Fine-Tune Effects {isAdjusting && '(Processing adjustment...)'}</h4>

        <div className="slider-group">
            <label>Speed (0.5x - 1.5x)</label>
            <input type="range" min="0.5" max="1.5" step="0.05" defaultValue="1.0" onChange={onSpeedChange} disabled={isAdjusting} />
        </div>

        <div className="slider-group">
            <label>Pitch Shift (-6 semitones to +6)</label>
            <input type="range" min="-600" max="600" step="50" defaultValue="0" onChange={onPitchChange} disabled={isAdjusting} />
        </div>

        <div className="slider-group">
            <label>Low-pass Filter (1kHz - 10kHz)</label>
            <input type="range" min="1000" max="10000" step="100" defaultValue="10000" onChange={onLowpassChange} disabled={isAdjusting} />
        </div>

        <div className="slider-group">
            <label>Bass Boost (0-15 dB)</label>
            <input type="range" min="0" max="15" defaultValue="0" onChange={onBassChange} disabled={isAdjusting} />
        </div>

      </div>
    </div>
  );
}

export default ResultDisplay;
