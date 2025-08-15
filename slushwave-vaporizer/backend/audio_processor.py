# audio_processor.py

import librosa
import numpy as np
import json
import os
import uuid
import effects # Import the new module

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
    """Analyzes an audio file to extract musical features."""
    try:
        y, sr = librosa.load(input_path)
        tempo = librosa.feature.tempo(y=y, sr=sr)[0]
        chromagram = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chromagram, axis=1)
        key_idx = np.argmax(chroma_mean)
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = notes[key_idx]
        return {'tempo': round(tempo), 'key': key}
    except Exception as e:
        print(f"Error during audio analysis: {e}")
        return None

def process_audio(input_path, output_path, options=None):
    """
    Applies a chain of audio effects to the input file by calling
    individual effect functions. Manages temporary files for the chain.
    """
    if options is None:
        options = {}

    preset_name = options.get('preset')
    if preset_name and preset_name in PRESETS:
        base_options = PRESETS[preset_name].copy()
        base_options.update(options)
        options = base_options

    temp_files = []
    current_input = input_path

    def get_temp_file():
        # Using .wav for intermediate files is often more stable with SoX
        temp_path = os.path.join(os.path.dirname(output_path), f"temp_{uuid.uuid4()}.wav")
        temp_files.append(temp_path)
        return temp_path

    try:
        # Dynamically build the chain of effects to apply
        effect_chain = []
        if options.get('bass_boost'): effect_chain.append(('bass_boost', {'gain': options['bass_boost']}))
        if options.get('pitch_shift'): effect_chain.append(('pitch_shift', {'shift': options['pitch_shift']}))
        if options.get('oops'): effect_chain.append(('oops', {}))
        if options.get('tremolo'): effect_chain.append(('tremolo', {'freq': 500, 'depth': 50}))
        if options.get('phaser'): effect_chain.append(('phaser', {}))
        if options.get('gain_db'): effect_chain.append(('gain', {'db': options['gain_db']}))
        if options.get('compand'): effect_chain.append(('compand', {}))
        if options.get('speed_ratio'): effect_chain.append(('speed', {'ratio': options['speed_ratio']}))
        if options.get('lowpass_cutoff'): effect_chain.append(('lowpass', {'cutoff': options['lowpass_cutoff']}))
        if not options.get('no_reverb', False): effect_chain.append(('reverb', {}))

        if not effect_chain:
            # If no effects, just copy the file
            import shutil
            shutil.copy(current_input, output_path)
            return output_path

        # Execute the chain
        for i, (effect_name, params) in enumerate(effect_chain):
            is_last_effect = (i == len(effect_chain) - 1)
            current_output = output_path if is_last_effect else get_temp_file()

            effect_func = getattr(effects, f"apply_{effect_name}")
            effect_func(current_input, current_output, **params)

            current_input = current_output

    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    return output_path
