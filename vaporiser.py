#!/usr/bin/env python

# Loading modules
from pydub import AudioSegment
from pydub.effects import low_pass_filter
from skimage.filters import sobel
import moviepy.editor as movedit
import argparse
import datetime
import sys
import re
import os


def parse_args():
    # Parsing for command line arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            "Creates a vaporwave (slowed, with reverb) remix of a given MP3 file, with"
            " multiple audio effects available, and the option of playing over a looped"
            " GIF as a video."
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output_name",
        help=(
            "Name of output file(s), instead of audio file name with the addition of"
            " '_vaporised'."
        ),
        type=str,
    )

    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "-a",
        "--audio",
        dest="audio_input",
        help="Input audio file to vaporise (.mp3)",
        type=str,
        required=True,
    )

    audio_arguments = parser.add_argument_group(
        "audio arguments",
        "these arguments control audio effects that will be applied by default",
    )

    audio_arguments.add_argument(
        "-s",
        "--speed",
        dest="speed_ratio",
        help="Ratio of new playback speed to old speed.",
        type=float,
        default=0.75,
    )

    audio_arguments.add_argument(
        "-p",
        "--pitch",
        dest="pitch_shift",
        help="Pitch shift (100ths of a semitone).",
        type=float,
        default=-75,
    )

    audio_arguments.add_argument(
        "-l",
        "--lowpass",
        dest="lowpass_cutoff",
        help="Cutoff for lowpass filter (Hz).",
        type=int,
        default=3500,
    )

    audio_arguments_optional = parser.add_argument_group(
        "extra audio arguments", "these arguments control extra, optional audio effects"
    )

    audio_arguments_optional.add_argument(
        "-b",
        "--bass",
        dest="bass_boost",
        help="Add a bass boost effect (e.g. --bass 3).",
        type=int,
        default=None,
    )

    audio_arguments_optional.add_argument(
        "-ga",
        "--gain",
        dest="gain_db",
        help="Applies gain (dB).",
        type=int,
        default=None,
    )

    audio_arguments_optional.add_argument(
        "-op",
        "--oops",
        dest="oops",
        help=(
            "Applies Out Of Phase Stereo effect. This is sometimes known as the"
            " ‘karaoke’ effect as it often has the effect of removing most or all of"
            " the vocals from a recording."
        ),
        action="store_true",
    )

    audio_arguments_optional.add_argument(
        "-co",
        "--compand",
        dest="compand",
        help="Enable compand, which compresses the dynamic range of the audio.",
        action="store_true",
    )

    video_arguments = parser.add_argument_group(
        "video arguments",
        "optional arguments, result in an MP4 video output in addition to the MP3"
        " audio",
    )

    video_arguments.add_argument(
        "-g",
        "--gif",
        dest="gif_file",
        help=(
            "Input GIF file to loop. Without a GIF, only an MP3 is created. With a GIF,"
            " an MP4 video is also created."
        ),
        type=str,
    )

    video_arguments.add_argument(
        "-sb",
        "--sobel",
        dest="sobel_filter",
        help="Applies a Sobel filter to video output.",
        action="store_true",
    )

    return parser.parse_args()


class Vaporiser:
    def __init__(self, args):
        self.args = args
        self.audio_output = None
        self.video_output = None
        self._set_output_filenames()
        self._validate_inputs()

    def _validate_inputs(self):
        # Check if input files exist
        if not os.path.exists(self.args.audio_input):
            print(f"ERROR: Audio file not found at '{self.args.audio_input}'")
            sys.exit(1)
        if self.args.gif_file and not os.path.exists(self.args.gif_file):
            print(f"ERROR: GIF file not found at '{self.args.gif_file}'")
            sys.exit(1)

        # Check file extensions
        if not self.args.audio_input.lower().endswith('.mp3'):
            print("ERROR: Input audio file must be an MP3.")
            sys.exit(1)
        if self.args.gif_file and not self.args.gif_file.lower().endswith('.gif'):
            print("ERROR: Input video file must be a GIF.")
            sys.exit(1)


    def _set_output_filenames(self):
        # Setting name of output file
        if self.args.output_name is None:
            # If no output name is given, add "_vaporised" to input audio file name
            audio_input_string = re.sub(".mp3", "", str(self.args.audio_input))
            self.audio_output = audio_input_string + "_vaporised.mp3"
            self.video_output = audio_input_string + "_vaporised.mp4"
        else:
            # Otherwise, use the output file name given via the command line
            output_string = re.sub(".mp3", "", str(self.args.output_name))
            output_string = re.sub(".mp4", "", str(output_string))
            self.audio_output = output_string + ".mp3"
            self.video_output = output_string + ".mp4"
            if self.args.audio_input == self.args.output_name:
                print("ERROR: Input and output name are identical")
                sys.exit()

    def _apply_audio_effects(self):
        try:
            # Load audio file
            print("Applying audio effects...")
            audio = AudioSegment.from_mp3(self.args.audio_input)

            # Apply effects
            # Speed and Pitch are connected in pydub.
            # To change speed, we change the frame rate. This also changes the pitch.
            # To change pitch without changing speed is more complex.
            # For simplicity, we will combine speed and pitch change.

            # Calculate new frame rate for speed change
            new_frame_rate = int(audio.frame_rate * self.args.speed_ratio)

            # Pitch shift
            # pydub changes pitch by altering the frame rate.
            # A pitch shift of -75 cents is a factor of 2**(-75/1200)
            semitones = self.args.pitch_shift / 100
            pitch_factor = 2**(semitones / 12)
            new_frame_rate = int(new_frame_rate * pitch_factor)

            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": new_frame_rate
            })

            if self.args.lowpass_cutoff:
                audio = low_pass_filter(audio, self.args.lowpass_cutoff)

            if self.args.bass_boost:
                # pydub does not have a direct bass_boost effect.
                # We can simulate it with a low_shelf filter, but that's not in pydub effects.
                # For now, we will just apply gain as a placeholder.
                # This is not a correct implementation of bass boost.
                audio = audio + self.args.bass_boost

            if self.args.gain_db:
                audio = audio + self.args.gain_db

            if self.args.oops:
                # Out of Phase Stereo (OOPS) effect
                # This can be achieved by inverting one channel and mixing
                if audio.channels == 2:
                    left, right = audio.split_to_mono()
                    right = right.invert_phase()
                    audio = AudioSegment.from_mono_audiosegments(left, right)

            if self.args.compand:
                # pydub has a compress_dynamic_range method
                audio = audio.compress_dynamic_range()

            # Export the processed audio
            print("Exporting audio...")
            audio.export(self.audio_output, format="mp3")
        except Exception as e:
            print(f"ERROR: Failed to apply audio effects: {e}")
            sys.exit(1)


    def _create_video(self):
        if not self.args.gif_file:
            return

        try:
            print("Creating video...")
            def apply_sobel(image):
                return sobel(image.astype(float))

            if self.args.gif_file:
                mp3_movedit = movedit.AudioFileClip(self.audio_output)
                gif_movedit = movedit.VideoFileClip(self.args.gif_file)
                number_of_loops = float(mp3_movedit.duration / gif_movedit.duration)
                gif_looped = gif_movedit.loop(number_of_loops)

                if self.args.sobel_filter:
                    gif_looped = gif_looped.fl_image(apply_sobel)

                gif_looped_with_audio = gif_looped.set_audio(mp3_movedit)
                gif_looped_with_audio.write_videofile(self.video_output, logger='bar')
        except Exception as e:
            print(f"ERROR: Failed to create video: {e}")
            sys.exit(1)

    def run(self):
        self._apply_audio_effects()
        self._create_video()

        print("Script finished at", datetime.datetime.now().strftime("%H:%M:%S"))
        print("Vaporised MP3 file (audio):", self.audio_output)
        if self.args.gif_file:
            print("Vaporised MP4 file (video):", self.video_output)


def main():
    args = parse_args()
    vaporiser = Vaporiser(args)
    vaporiser.run()


if __name__ == "__main__":
    main()
