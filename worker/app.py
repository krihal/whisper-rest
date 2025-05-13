import logging
import requests
import subprocess
import traceback

from enum import Enum
from settings import get_settings
from time import sleep
from pathlib import Path
from random import randint


class JobStatusEnum(str, Enum):
    """
    Enum representing the status of a job.
    """

    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


settings = get_settings()

api_broker_url = settings.API_BROKER_URL
api_file_storage_dir = settings.API_FILE_STORAGE_DIR
api_version = settings.API_VERSON
api_url = f"{api_broker_url}/api/{api_version}/transcriber"


def get_logger():
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


logger = get_logger()


def transcode_file(filename: str):
    """
    Transcode the audio file using ffmpeg.
    The transcoded format should be 16kHz mono WAV.
    """

    output_filename = f"{filename}.wav"

    command = [
        "ffmpeg",
        "-i",
        str(Path(api_file_storage_dir) / filename),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-f",
        "wav",
        "-y",
        str(Path(api_file_storage_dir) / output_filename),
    ]

    try:
        ffmpeg_cmd = " ".join(command)
        logger.debug(f"Transcoding command: {ffmpeg_cmd}")
        result = subprocess.run(command, check=True, capture_output=True)

        # Check exit code
        if result.returncode != 0:
            logger.error(f"Error during transcoding: {result.stderr.decode()}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during transcoding: {e}")
        raise e
    else:
        logger.info(f"Transcoding completed: {output_filename}")

    return True


def transcribe_file(filename: str, language: str, model: str, output_format: str):
    """
    Transcribe the audio file using whisper.cpp, we expect the executable
    to be in PATH.
    """
    command = [
        "whisper.cpp",
        "-l",
        language,
        f"-o{output_format.lower()}",
        "-of",
        str(Path(api_file_storage_dir) / filename),
        "-m",
        model,
        "-f",
        str(Path(api_file_storage_dir) / f"{filename}.wav"),
    ]

    try:
        whisper_cmd = " ".join(command)
        logger.debug(f"Transcription command: {whisper_cmd}")
        result = subprocess.run(command, check=True, capture_output=True)

        # Check exit code
        if result.returncode != 0:
            logger.error(f"Error during transcription: {result.stderr.decode()}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during transcription: {e}")
        raise e
    else:
        logger.info(f"Transcription completed: {filename}")

    return True


def get_next_job(url: str) -> dict:
    """
    Get the next job from the API broker.
    """
    response = requests.get(f"{api_url}/next")
    response.raise_for_status()
    job = response.json()["result"]

    if job == {}:
        return {}
    if job["status"] != JobStatusEnum.IN_PROGRESS:
        logger.info(f"Job {job['uuid']} is not in_progress. Skipping.")
        return {}

    return job


def get_file(uuid: str) -> bool:
    """
    Download the file from the API broker.
    """

    response = requests.get(f"{api_url}/{uuid}/file")
    response.raise_for_status()

    if response.status_code != 200:
        logger.error(f"Error downloading file: {response.status_code}")
        raise Exception("File not downloaded")

    file_path = Path(api_file_storage_dir) / uuid

    with open(file_path, "wb") as f:
        f.write(response.content)

    return True


def put_status(uuid: str, status: JobStatusEnum, error: str) -> bool:
    """
    Update the job status in the API broker.
    """
    try:
        response = requests.put(
            f"{api_url}/{uuid}", json={"status": status, "error": error}
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error updating job status: {e}")
        return False
    return True


def put_file(uuid: str, output_format: str) -> bool:
    """
    Upload the file to the API broker.
    """

    file_path = Path(api_file_storage_dir) / f"{uuid}.{output_format}"
    with open(file_path, "rb") as fd:
        response = requests.put(f"{api_url}/{uuid}/result", files={"file": fd})
        response.raise_for_status()


def get_model(model_type: str, language: str) -> str:
    """
    Return the correct model file based on
    model type and language.

    If langauge = sv then use kb-whisper else
    use the default whisper model.
    """

    file_path = "models/"
    file_path += "sv" if language == "sv" else "en"

    match model_type:
        case "tiny":
            file_path += "_tiny"
        case "base":
            file_path += "_base"
        case "large":
            file_path += "_large"
        case _:
            file_path += "_base"

    return f"{file_path}.bin"


def main():
    """
    Main function to fetch jobs and process them.
    """
    logger.info(f"Starting transcription service, server URL: {api_broker_url}")

    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode is enabled.")

    while True:
        try:
            # Sleep for a random time between 5 and 10 seconds
            # to avoid hammering the API broker.
            sleep_time = randint(5, 10)
            logger.debug(f"Sleeping for {sleep_time} seconds before checking for jobs.")
            sleep(sleep_time)

            if not (job := get_next_job(api_broker_url)):
                continue

            uuid = job["uuid"]
            language = job["language"]
            model_type = job["model_type"]
            model = get_model(model_type, language)
            output_format = job["output_format"]

            logger.info(f"Processing job {uuid}:")
            logger.info(f"  Language: {language}")
            logger.info(f"  Model Type: {model_type}")
            logger.info(f"  Model: {model}")
            logger.info(f"  Output Format: {output_format}")

            # Download the file
            get_file(uuid)

            # Transcode the file
            transcode_file(uuid)

            # Transcribe the file
            transcribe_file(uuid, language, model, output_format)

            # Upload the resulting SRT
            put_file(f"{uuid}", output_format)

            logger.info(f"Job {uuid} completed successfully.")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            continue
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            continue
        except Exception as e:
            put_status(uuid, JobStatusEnum.FAILED, error=str(e))
            logger.error(f"Error processing job {uuid}: {e}")
            traceback.print_exc()
            continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")
        logger.info("Transcription service stopped.")
