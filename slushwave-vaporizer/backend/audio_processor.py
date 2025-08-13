# audio_processor.py

from pysndfx import AudioEffectsChain
import librosa
import numpy as np
import sys
import re

def analyze_audio(input_path):
    """
    Analyzes an audio file to extract musical features.

    :param input_path: Path to the input audio file.
    :return: A dictionary containing tempo (BPM) and key.
    """
    try:
        y, sr = librosa.load(input_path)

        # Get tempo
        tempo = librosa.feature.tempo(y=y, sr=sr)[0]

        # Get chroma features for key detection
        chromagram = librosa.feature.chroma_stft(y=y, sr=sr)
        # Use a simple method to estimate key from chroma
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

    :param input_path: Path to the input audio file.
    :param output_path: Path to save the processed audio file.
    :param options: A dictionary of effects and their parameters.
    :return: Path to the processed audio file.
    """
    if options is None:
        options = {}

    # --- New: Analyze audio to get features ---
    analysis = analyze_audio(input_path)
    if analysis:
        print(f"Audio Analysis Results: {analysis}")
        # In the future, these values will override the default options
        # For example: options['speed_ratio'] = calculate_new_speed(analysis['tempo'])

    # Default values similar to original script
    speed_ratio = options.get('speed_ratio', 0.75)
    pitch_shift = options.get('pitch_shift', -75)
    lowpass_cutoff = options.get('lowpass_cutoff', 3500)
    bass_boost = options.get('bass_boost', None)
    gain_db = options.get('gain_db', None)
    oops = options.get('oops', False)
    phaser = options.get('phaser', False)
    tremolo = options.get('tremolo', False)
    compand = options.get('compand', False)
    no_reverb = options.get('no_reverb', False)

    # Creating an audio effects chain
    if bass_boost:
        fx = AudioEffectsChain().custom(f'bass {bass_boost}')
        fx = fx.pitch(pitch_shift)
    else:
        fx = AudioEffectsChain().pitch(pitch_shift)

    if oops:
        fx = fx.custom("oops")

    if tremolo:
        fx = fx.tremolo(freq=500, depth=50)

    if phaser:
        fx = fx.phaser(0.9, 0.8, 2, 0.2, 0.5)

    if gain_db is not None:
        fx = fx.gain(db=gain_db)

    if compand:
        fx = fx.compand()

    fx = fx.speed(speed_ratio).lowpass(lowpass_cutoff)

    if not no_reverb:
        fx = fx.reverb()

    # Applying audio effects
    # This will fail if SoX is not installed
    try:
        fx(input_path, output_path)
    except Exception as e:
        # Provide a more informative error if SoX is likely missing
        if "sox: not found" in str(e) or "SoX" in str(e):
             raise RuntimeError("SoX command not found. Please ensure SoX is installed and in your system's PATH.") from e
        raise e

    return output_path
