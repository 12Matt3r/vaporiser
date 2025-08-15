# effects.py
from pysndfx import AudioEffectsChain

def _apply_fx(infile, outfile, fx_chain):
    """Helper to apply an effects chain and handle errors."""
    try:
        fx_chain(infile, outfile)
    except Exception as e:
        if "sox: not found" in str(e) or "SoX" in str(e):
             raise RuntimeError("SoX command not found. Please ensure SoX is installed and in your system's PATH.") from e
        raise e

def apply_bass_boost(infile, outfile, gain=5):
    fx = AudioEffectsChain().custom(f'bass {gain}')
    _apply_fx(infile, outfile, fx)

def apply_pitch_shift(infile, outfile, shift=-75):
    fx = AudioEffectsChain().pitch(shift)
    _apply_fx(infile, outfile, fx)

def apply_oops(infile, outfile):
    fx = AudioEffectsChain().custom("oops")
    _apply_fx(infile, outfile, fx)

def apply_tremolo(infile, outfile, freq=500, depth=50):
    fx = AudioEffectsChain().tremolo(freq, depth)
    _apply_fx(infile, outfile, fx)

def apply_phaser(infile, outfile):
    fx = AudioEffectsChain().phaser(0.9, 0.8, 2, 0.2, 0.5)
    _apply_fx(infile, outfile, fx)

def apply_gain(infile, outfile, db=0):
    fx = AudioEffectsChain().gain(db)
    _apply_fx(infile, outfile, fx)

def apply_compand(infile, outfile):
    fx = AudioEffectsChain().compand()
    _apply_fx(infile, outfile, fx)

def apply_speed(infile, outfile, ratio=0.75):
    fx = AudioEffectsChain().speed(ratio)
    _apply_fx(infile, outfile, fx)

def apply_lowpass(infile, outfile, cutoff=3500):
    fx = AudioEffectsChain().lowpass(cutoff)
    _apply_fx(infile, outfile, fx)

def apply_reverb(infile, outfile):
    fx = AudioEffectsChain().reverb()
    _apply_fx(infile, outfile, fx)
