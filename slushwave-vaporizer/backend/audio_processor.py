# audio_processor.py

import librosa
import numpy as np
import json
import os
import uuid
import effects
import soundfile as sf

# ... (load_presets and analyze_audio are the same) ...
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

def find_and_extract_loop(input_path, output_dir, duration_seconds=10):
    """
    Finds a suitable loop in an audio file and saves it.
    Returns the path to the extracted loop file.
    """
    try:
        y, sr = librosa.load(input_path, sr=None) # Load with original sample rate

        # A simple heuristic: find the loudest section of the song.
        # This often corresponds to a chorus or other high-energy part.
        frame_length = int(duration_seconds * sr)

        # Calculate RMSE (Root-Mean-Square Energy) for each frame
        rmse = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=frame_length//2)[0]

        # Find the frame with the maximum energy
        # We start searching 30 seconds in to avoid intros.
        start_frame_search = librosa.time_to_frames(30, sr=sr, hop_length=frame_length//2)
        if len(rmse) > start_frame_search:
            best_frame_index = np.argmax(rmse[start_frame_search:]) + start_frame_search
        else:
            best_frame_index = np.argmax(rmse)

        # Get start and end samples of the best loop
        start_sample = librosa.frames_to_samples(best_frame_index, hop_length=frame_length//2)
        end_sample = start_sample + frame_length

        # Ensure the loop doesn't exceed the track length
        end_sample = min(end_sample, len(y))

        loop_data = y[start_sample:end_sample]

        # Save the loop to a new file
        loop_path = os.path.join(output_dir, f"loop_{uuid.uuid4()}.wav")
        sf.write(loop_path, loop_data, sr)

        return loop_path
    except Exception as e:
        print(f"Error during loop detection: {e}")
        # If loop detection fails, return the original file path to process the whole song
        return input_path

def process_audio(input_path, output_path, options=None):
    """
    Applies a chain of audio effects to the input file.
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
        temp_path = os.path.join(os.path.dirname(output_path), f"temp_{uuid.uuid4()}.wav")
        temp_files.append(temp_path)
        return temp_path

    try:
        # --- New: Loop Detection Step ---
        loop_config = options.get('loop_detection', {})
        if loop_config.get('enabled', False):
            print("Loop detection enabled. Finding loop...")
            loop_duration = loop_config.get('duration_seconds', 10)
            output_dir_for_loop = os.path.dirname(output_path)

            looped_file_path = find_and_extract_loop(current_input, output_dir_for_loop, loop_duration)

            # If a new loop file was created, use it as the input
            if looped_file_path != current_input:
                current_input = looped_file_path
                temp_files.append(looped_file_path) # Ensure it gets cleaned up

        # Dynamically build the chain of effects
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
