import sys
import subprocess


def transcode_file(filename: str, outfile: str):
    """
    Transcode the audio file using ffmpeg.
    The transcoded format should be 16kHz mono WAV.
    """

    output_filename = f"{outfile}.wav"

    command = [
        "ffmpeg",
        "-i",
        filename,
        "-ar",
        "16000",
        "-ac",
        "1",
        "-f",
        "wav",
        "-y",
        output_filename,
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Transcoding completed: {output_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error during transcoding: {e}")
        return False

    return True


if __name__ == "__main__":
    transcode_file(sys.argv[1], sys.argv[2])
