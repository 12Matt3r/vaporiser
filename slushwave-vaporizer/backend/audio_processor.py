# audio_processor.py

import librosa
import numpy as np
import json
import os
import uuid
import effects
import soundfile as sf

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
    Analyzes an audio file to extract a fingerprint of musical features.
    """
    try:
        y, sr = librosa.load(input_path, sr=None)
        tempo = librosa.feature.tempo(y=y, sr=sr)[0]
        chromagram = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chromagram, axis=1)
        key_idx = np.argmax(chroma_mean)
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = notes[key_idx]
        spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spec_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)[0]

        return {
            'tempo': round(float(tempo)),
            'key': key,
            'brightness': round(float(np.mean(spec_centroid))),
            'spectral_width': round(float(np.mean(spec_bandwidth))),
            'avg_loudness': float(np.mean(rms))
        }
    except Exception as e:
        print(f"Error during audio analysis: {e}")
        return None

def find_and_extract_loop(input_path, output_dir, duration_seconds=10):
    # ... (code is unchanged)
    try:
        y, sr = librosa.load(input_path, sr=None)
        frame_length = int(duration_seconds * sr)
        rmse = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=frame_length//2)[0]
        start_frame_search = librosa.time_to_frames(30, sr=sr, hop_length=frame_length//2)
        if len(rmse) > start_frame_search:
            best_frame_index = np.argmax(rmse[start_frame_search:]) + start_frame_search
        else:
            best_frame_index = np.argmax(rmse)
        start_sample = librosa.frames_to_samples(best_frame_index, hop_length=frame_length//2)
        end_sample = min(start_sample + frame_length, len(y))
        loop_data = y[start_sample:end_sample]
        loop_path = os.path.join(output_dir, f"loop_{uuid.uuid4()}.wav")
        sf.write(loop_path, loop_data, sr)
        return loop_path
    except Exception as e:
        print(f"Error during loop detection: {e}")
        return input_path

def process_audio(input_path, output_path, options=None, reference_path=None):
    """
    Applies a chain of audio effects to the input file.
    If reference_path is provided, it will be used for style transfer.
    """
    if options is None: options = {}

    # --- Style Transfer Logic ---
    if reference_path:
        print("Reference track provided. Performing style transfer analysis...")
        target_analysis = analyze_audio(input_path)
        ref_analysis = analyze_audio(reference_path)

        if target_analysis and ref_analysis:
            # Create new options based on the analysis
            style_options = {}
            # Match tempo
            if target_analysis['tempo'] > 0:
                style_options['speed_ratio'] = ref_analysis['tempo'] / target_analysis['tempo']
            # Match brightness (map brightness to lowpass cutoff)
            # This is a simple heuristic, can be improved.
            # Brighter songs have higher centroid. We map this inversely to lowpass cutoff.
            # Max brightness around 4000. Let's map it to a 2000-8000 Hz range.
            brightness_scaled = 1 - (min(ref_analysis['brightness'], 4000) / 4000) # 0 (bright) to 1 (dark)
            style_options['lowpass_cutoff'] = 2000 + (brightness_scaled * 6000)

            # Match loudness
            if target_analysis['avg_loudness'] > 0:
                gain_ratio = ref_analysis['avg_loudness'] / target_analysis['avg_loudness']
                style_options['gain_db'] = 20 * np.log10(gain_ratio)

            print(f"Generated style transfer options: {style_options}")
            options.update(style_options) # Apply style options over preset
        else:
            print("Style transfer analysis failed. Proceeding with default preset.")

    # --- Preset Logic ---
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
        loop_config = options.get('loop_detection', {})
        if loop_config.get('enabled', False):
            loop_duration = loop_config.get('duration_seconds', 10)
            output_dir_for_loop = os.path.dirname(output_path)
            looped_file_path = find_and_extract_loop(current_input, output_dir_for_loop, loop_duration)
            if looped_file_path != current_input:
                current_input = looped_file_path
                temp_files.append(looped_file_path)

        effect_chain = []
        if options.get('bass_boost'): effect_chain.append(('bass_boost', {'gain': options['bass_boost']}))
        # ... (rest of the effect chain logic is the same)
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

        for i, (effect_name, params) in enumerate(effect_chain):
            is_last_effect = (i == len(effect_chain) - 1)
            current_output = output_path if is_last_effect else get_temp_file()
            effect_func = getattr(effects, f"apply_{effect_name}")
            effect_func(current_input, current_output, **params)
            current_input = current_output
    finally:
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    return output_path
