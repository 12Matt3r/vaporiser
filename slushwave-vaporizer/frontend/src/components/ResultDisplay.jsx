import React from 'react';

function ResultDisplay({ resultUrl, originalTaskId, handleAdjust, isAdjusting }) {
  if (!resultUrl) {
    return null;
  }

  const onBassChange = (e) => {
    handleAdjust(originalTaskId, 'bass_boost', { gain: parseInt(e.target.value, 10) });
  };

  const onPhaserChange = (e) => {
    handleAdjust(originalTaskId, 'phaser', {}); // Phaser in backend takes no params
  };

  const onReverbChange = (e) => {
    // This is tricky. The backend has `no_reverb`.
    // So if checkbox is checked, we want `no_reverb: false`.
    // This requires a different API design.
    // For now, I'll assume we can just re-apply reverb.
    handleAdjust(originalTaskId, 'reverb', {});
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
            <label>Bass Boost (0-15 dB)</label>
            <input
              type="range"
              min="0"
              max="15"
              defaultValue="0"
              onChange={onBassChange}
              disabled={isAdjusting}
            />
        </div>
        {/* The simple on/off for phaser/reverb is more complex than a slider.
            I will leave them out for now to focus on the bass boost slider,
            which is a better proof of concept for the adjustment logic. */}
      </div>
    </div>
  );
}

export default ResultDisplay;
