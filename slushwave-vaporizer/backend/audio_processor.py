# audio_processor.py

from pysndfx import AudioEffectsChain
import librosa
import numpy as np
import sys
import re
import json
import os

# --- Preset Loading ---
def load_presets():
    """Loads presets from presets.json"""
    preset_path = os.path.join(os.path.dirname(__file__), 'presets.json')
    try:
        with open(preset_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: presets.json not found at {preset_path}")
        return {}

PRESETS = load_presets()

def analyze_audio(input_path):
    """
    Analyzes an audio file to extract musical features.

    :param input_path: Path to the input audio file.
    :return: A dictionary containing tempo (BPM) and key.
    """
    try:
        y, sr = librosa.load(input_path)

        tempo = librosa.feature.tempo(y=y, sr=sr)[0]

        chromagram = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chromagram, axis=1)
        key_idx = np.argmax(chroma_mean)
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = notes[key_idx]

        return {
            'tempo': round(tempo),
            'key': key
        }
    except Exception as e:
        print(f"Error during audio analysis: {e}")
        return None

def process_audio(input_path, output_path, options=None):
    """
    Applies a chain of audio effects to the input file and saves it to the output file.
    """
    if options is None:
        options = {}

    # --- Apply Preset ---
    preset_name = options.get('preset')
    if preset_name and preset_name in PRESETS:
        # Use preset as a base, but allow overrides from other options
        base_options = PRESETS[preset_name].copy()
        base_options.update(options)
        options = base_options

    analysis = analyze_audio(input_path)
    if analysis:
        print(f"Audio Analysis Results: {analysis}")

    # Get effect parameters from options, with defaults
    speed_ratio = options.get('speed_ratio', 0.75)
    pitch_shift = options.get('pitch_shift', -75)
    lowpass_cutoff = options.get('lowpass_cutoff', None) # Allow null
    bass_boost = options.get('bass_boost', None)
    gain_db = options.get('gain_db', None)
    oops = options.get('oops', False)
    phaser = options.get('phaser', False)
    tremolo = options.get('tremolo', False)
    compand = options.get('compand', False)
    no_reverb = options.get('no_reverb', False)

    # Creating an audio effects chain
    fx = AudioEffectsChain()

    if bass_boost:
        fx.custom(f'bass {bass_boost}')

    if pitch_shift is not None:
        fx.pitch(pitch_shift)

    if oops:
        fx.custom("oops")

    if tremolo:
        fx.tremolo(freq=500, depth=50)

    if phaser:
        fx.phaser(0.9, 0.8, 2, 0.2, 0.5)

    if gain_db is not None:
        fx.gain(db=gain_db)

    if compand:
        fx.compand()

    if speed_ratio is not None:
        fx.speed(speed_ratio)

    if lowpass_cutoff is not None:
        fx.lowpass(lowpass_cutoff)

    if not no_reverb:
        fx.reverb()

    try:
        fx(input_path, output_path)
    except Exception as e:
        if "sox: not found" in str(e) or "SoX" in str(e):
             raise RuntimeError("SoX command not found. Please ensure SoX is installed and in your system's PATH.") from e
        raise e

    return output_path
